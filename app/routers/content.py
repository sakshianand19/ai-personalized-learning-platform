from fastapi import APIRouter, Depends, status
from langchain_core.language_models import BaseChatModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LearningContent, Question, Topic
from app.routers.common import get_or_404
from app.schemas import (
    ContentCreate,
    ContentRead,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    QuestionBase,
    RejectedQuestion,
)
from app.services import content_processor
from app.services.llm import get_llm
from app.services.question_validator import validate_question

router = APIRouter(prefix="/content", tags=["content"])


@router.post("", response_model=ContentRead, status_code=status.HTTP_201_CREATED)
def create_content(
    payload: ContentCreate,
    db: Session = Depends(get_db),
    llm: BaseChatModel | None = Depends(get_llm),
):
    """Store learning material after summarising it and extracting key concepts and difficulty."""
    topic = get_or_404(db, Topic, payload.topic_id)
    analysis, engine = content_processor.analyze_content(
        payload.body, subject=topic.subject, topic=topic.name, llm=llm
    )
    content = LearningContent(
        **payload.model_dump(),
        summary=analysis.summary,
        key_concepts=analysis.key_concepts,
        difficulty=analysis.difficulty,
        processed_by=engine,
    )
    db.add(content)
    db.commit()
    return content


@router.get("", response_model=list[ContentRead])
def list_content(topic_id: int | None = None, db: Session = Depends(get_db)):
    query = select(LearningContent).order_by(LearningContent.id)
    if topic_id is not None:
        query = query.where(LearningContent.topic_id == topic_id)
    return db.scalars(query).all()


@router.get("/{content_id}", response_model=ContentRead)
def get_content(content_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, LearningContent, content_id)


@router.post("/{content_id}/questions", response_model=GenerateQuestionsResponse)
def generate_questions(
    content_id: int,
    payload: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
    llm: BaseChatModel | None = Depends(get_llm),
):
    """Generate questions from the material, validate each one and keep only those that pass."""
    content = get_or_404(db, LearningContent, content_id)
    topic = db.get(Topic, content.topic_id)
    drafts, engine = content_processor.generate_questions(
        content.body,
        topic=topic.name,
        count=payload.count,
        difficulty=payload.difficulty or content.difficulty,
        key_concepts=content.key_concepts,
        llm=llm,
    )

    accepted: list[Question] = []
    rejected: list[RejectedQuestion] = []
    for draft in drafts:
        result = validate_question(draft, topic=topic.name, context=content.body, llm=llm)
        if not result.is_valid:
            rejected.append(
                RejectedQuestion(question=QuestionBase(**draft.model_dump()), issues=result.issues)
            )
            continue
        accepted.append(
            Question(
                **draft.model_dump(),
                topic_id=content.topic_id,
                content_id=content.id,
                is_validated=True,
                validation_notes=[f"validated by {result.reviewed_by}"],
            )
        )
    db.add_all(accepted)
    db.commit()
    return GenerateQuestionsResponse(generated_by=engine, accepted=accepted, rejected=rejected)
