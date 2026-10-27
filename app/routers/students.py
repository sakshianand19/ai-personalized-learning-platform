from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import Student, Submission
from app.routers.common import get_or_404
from app.schemas import (
    ContentSummary,
    GapReport,
    LearningGapRead,
    LearningPath,
    LearningPathStep,
    StudentCreate,
    StudentRead,
    SubmissionSummary,
    TopicProgress,
)
from app.services import gap_analyzer, personalization

router = APIRouter(prefix="/students", tags=["students"])


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Student.id).where(Student.email == payload.email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "A student with this email already exists")
    student = Student(**payload.model_dump() | {"email": payload.email.lower()})
    db.add(student)
    db.commit()
    return student


@router.get("", response_model=list[StudentRead])
def list_students(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.scalars(select(Student).order_by(Student.id).offset(skip).limit(min(limit, 200))).all()


@router.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Student, student_id)


@router.get("/{student_id}/submissions", response_model=list[SubmissionSummary])
def list_submissions(student_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """The student's most recent graded assessments and homework."""
    get_or_404(db, Student, student_id)
    return db.scalars(
        select(Submission)
        .where(Submission.student_id == student_id)
        .order_by(Submission.id.desc())
        .limit(min(limit, 50))
    ).all()


@router.get("/{student_id}/learning-gaps", response_model=GapReport)
def learning_gaps(
    student_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
):
    """Identify topics where the student's mastery is below the target threshold."""
    get_or_404(db, Student, student_id)
    analysis = gap_analyzer.analyze_student(
        db,
        student_id,
        threshold=settings.mastery_threshold,
        min_attempts=settings.min_attempts_for_gap,
    )
    return GapReport(
        student_id=student_id,
        overall_mastery=analysis.overall_mastery,
        gaps=[LearningGapRead.model_validate(g, from_attributes=True) for g in analysis.gaps],
        progress=[TopicProgress.model_validate(p, from_attributes=True) for p in analysis.progress],
    )


@router.get("/{student_id}/learning-path", response_model=LearningPath)
def learning_path(
    student_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
):
    """A personalised, ordered study plan: weakest topics first, with level-matched content."""
    get_or_404(db, Student, student_id)
    analysis = gap_analyzer.analyze_student(
        db,
        student_id,
        threshold=settings.mastery_threshold,
        min_attempts=settings.min_attempts_for_gap,
    )
    steps = personalization.build_learning_path(db, analysis)
    return LearningPath(
        student_id=student_id,
        steps=[
            LearningPathStep(
                order=step.order,
                topic_id=step.progress.topic_id,
                topic_name=step.progress.topic_name,
                subject=step.progress.subject,
                status=step.progress.status,
                mastery=step.progress.mastery,
                target_difficulty=step.target_difficulty,
                recommended_content=[ContentSummary.model_validate(c) for c in step.content],
            )
            for step in steps
        ],
    )
