from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import Principal, ensure_can_submit, get_current_user, require_roles
from app.database import get_db
from app.models import Assessment, Question, Student
from app.routers.common import answers_to_map, get_or_404, submission_to_read
from app.schemas import AssessmentCreate, AssessmentRead, AssessmentSubmit, SubmissionRead
from app.services.grading import InvalidSubmission, grade_submission

router = APIRouter(prefix="/assessments", tags=["assessments"])


def _load_assessment(db: Session, assessment_id: int) -> Assessment:
    assessment = db.scalar(
        select(Assessment)
        .where(Assessment.id == assessment_id)
        .options(selectinload(Assessment.questions))
    )
    if assessment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Assessment {assessment_id} not found")
    return assessment


@router.post("", response_model=AssessmentRead, status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: AssessmentCreate,
    db: Session = Depends(get_db),
    _: Principal = Depends(get_current_user),
):
    """Build an assessment from explicit question ids and/or a sample of each topic's questions."""
    questions: dict[int, Question] = {}
    if payload.question_ids:
        found = db.scalars(select(Question).where(Question.id.in_(payload.question_ids))).all()
        missing = set(payload.question_ids) - {q.id for q in found}
        if missing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Questions not found: {sorted(missing)}")
        questions.update({q.id: q for q in found})
    for topic_id in payload.topic_ids or []:
        sample = db.scalars(
            select(Question)
            .where(Question.topic_id == topic_id, Question.is_validated.is_(True))
            .order_by(Question.id)
            .limit(payload.questions_per_topic)
        ).all()
        questions.update({q.id: q for q in sample})
    if not questions:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "No validated questions found for this assessment"
        )

    assessment = Assessment(title=payload.title, questions=list(questions.values()))
    db.add(assessment)
    db.commit()
    return assessment


@router.get("", response_model=list[AssessmentRead])
def list_assessments(
    db: Session = Depends(get_db), _: Principal = Depends(require_roles("admin", "teacher"))
):
    return db.scalars(
        select(Assessment).options(selectinload(Assessment.questions)).order_by(Assessment.id)
    ).all()


@router.get("/{assessment_id}", response_model=AssessmentRead)
def get_assessment(
    assessment_id: int, db: Session = Depends(get_db), _: Principal = Depends(get_current_user)
):
    return _load_assessment(db, assessment_id)


@router.post("/{assessment_id}/submit", response_model=SubmissionRead)
def submit_assessment(
    assessment_id: int,
    payload: AssessmentSubmit,
    db: Session = Depends(get_db),
    user: Principal = Depends(get_current_user),
):
    """Grade a student's answers and update their per-topic mastery."""
    ensure_can_submit(user, payload.student_id)
    assessment = _load_assessment(db, assessment_id)
    get_or_404(db, Student, payload.student_id)
    try:
        submission = grade_submission(
            db,
            student_id=payload.student_id,
            questions=assessment.questions,
            answers=answers_to_map(payload.answers),
            assessment_id=assessment.id,
        )
    except InvalidSubmission as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    return submission_to_read(submission, assessment.questions)
