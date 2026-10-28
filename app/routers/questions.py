from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.language_models import BaseChatModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.database import get_db
from app.models import LearningContent, Question, Topic
from app.routers.common import get_or_404
from app.schemas import QuestionCreate, QuestionRead, QuestionValidateRequest, ValidationReport
from app.services.llm import get_llm
from app.services.question_validator import QuestionDraft, validate_question

# The question bank includes answer keys, so only staff may read or change it.
router = APIRouter(
    prefix="/questions", tags=["questions"], dependencies=[Depends(require_roles("admin", "teacher"))]
)


@router.post("/validate", response_model=ValidationReport)
def validate(payload: QuestionValidateRequest, llm: BaseChatModel | None = Depends(get_llm)):
    """Check a question without saving it: structural rules plus an LLM review when available."""
    draft = QuestionDraft(**payload.model_dump(exclude={"context"}))
    result = validate_question(draft, context=payload.context, llm=llm)
    return ValidationReport(**result.__dict__)


@router.post("", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
def create_question(
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    llm: BaseChatModel | None = Depends(get_llm),
):
    topic = get_or_404(db, Topic, payload.topic_id)
    context = None
    if payload.content_id is not None:
        context = get_or_404(db, LearningContent, payload.content_id).body

    draft = QuestionDraft(**payload.model_dump(exclude={"topic_id", "content_id"}))
    result = validate_question(draft, topic=topic.name, context=context, llm=llm)
    if not result.is_valid:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            {"message": "Question failed validation", "issues": result.issues},
        )
    question = Question(
        **payload.model_dump(),
        is_validated=True,
        validation_notes=[f"validated by {result.reviewed_by}"],
    )
    db.add(question)
    db.commit()
    return question


@router.get("", response_model=list[QuestionRead])
def list_questions(
    topic_id: int | None = None, validated_only: bool = True, db: Session = Depends(get_db)
):
    query = select(Question).order_by(Question.id)
    if topic_id is not None:
        query = query.where(Question.topic_id == topic_id)
    if validated_only:
        query = query.where(Question.is_validated.is_(True))
    return db.scalars(query).all()
