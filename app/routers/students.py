from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Principal, ensure_student_access, get_current_user, require_roles
from app.config import Settings, get_settings
from app.database import get_db
from app.models import Staff, Student, Submission
from app.routers.common import ensure_email_available, get_or_404
from app.security import hash_password
from app.schemas import (
    ContentSummary,
    GapReport,
    LearningGapRead,
    LearningPath,
    LearningPathStep,
    StudentCreate,
    StudentRead,
    StudentUpdate,
    SubmissionSummary,
    TopicProgress,
)
from app.services import gap_analyzer, personalization

router = APIRouter(prefix="/students", tags=["students"])


def _check_teacher(db: Session, teacher_id: int | None) -> None:
    if teacher_id is None:
        return
    teacher = db.get(Staff, teacher_id)
    if teacher is None or teacher.role != "teacher":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Teacher {teacher_id} not found")


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    _: Principal = Depends(require_roles("admin")),
):
    ensure_email_available(db, payload.email)
    _check_teacher(db, payload.teacher_id)
    student = Student(
        **payload.model_dump(exclude={"password"}) | {"email": payload.email.lower()},
        password_hash=hash_password(payload.password),
    )
    db.add(student)
    db.commit()
    return student


@router.get("", response_model=list[StudentRead])
def list_students(
    teacher_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: Principal = Depends(require_roles("admin", "teacher")),
):
    """Admins see everyone; teachers only ever see their own class."""
    if user.role == "teacher":
        teacher_id = user.id
    query = select(Student).order_by(Student.id).offset(skip).limit(min(limit, 200))
    if teacher_id is not None:
        query = query.where(Student.teacher_id == teacher_id)
    return db.scalars(query).all()


@router.get("/{student_id}", response_model=StudentRead)
def get_student(
    student_id: int, db: Session = Depends(get_db), user: Principal = Depends(get_current_user)
):
    return ensure_student_access(db, user, student_id)


@router.patch("/{student_id}", response_model=StudentRead)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    _: Principal = Depends(require_roles("admin")),
):
    student = get_or_404(db, Student, student_id)
    changes = payload.model_dump(exclude_unset=True)
    if "teacher_id" in changes:
        _check_teacher(db, changes["teacher_id"])
    for field, value in changes.items():
        if value is not None or field == "teacher_id":
            setattr(student, field, value)
    db.commit()
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int, db: Session = Depends(get_db), _: Principal = Depends(require_roles("admin"))
):
    """Delete a student and, via cascades, their submissions, homework and mastery."""
    db.delete(get_or_404(db, Student, student_id))
    db.commit()


@router.get("/{student_id}/submissions", response_model=list[SubmissionSummary])
def list_submissions(
    student_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    user: Principal = Depends(get_current_user),
):
    """The student's most recent graded assessments and homework."""
    ensure_student_access(db, user, student_id)
    return db.scalars(
        select(Submission)
        .where(Submission.student_id == student_id)
        .order_by(Submission.id.desc())
        .limit(min(limit, 50))
    ).all()


@router.get("/{student_id}/learning-gaps", response_model=GapReport)
def learning_gaps(
    student_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: Principal = Depends(get_current_user),
):
    """Identify topics where the student's mastery is below the target threshold."""
    ensure_student_access(db, user, student_id)
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
    student_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: Principal = Depends(get_current_user),
):
    """A personalised, ordered study plan: weakest topics first, with level-matched content."""
    ensure_student_access(db, user, student_id)
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
