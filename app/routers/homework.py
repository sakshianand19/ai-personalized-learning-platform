from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import Principal, ensure_can_submit, ensure_student_access, get_current_user
from app.config import Settings, get_settings
from app.database import get_db
from app.models import Homework, Topic, utcnow
from app.routers.common import answers_to_map, get_or_404, submission_to_read
from app.schemas import HomeworkGenerate, HomeworkRead, HomeworkSubmit, SubmissionRead
from app.services import gap_analyzer, personalization
from app.services.grading import InvalidSubmission, grade_submission

router = APIRouter(prefix="/homework", tags=["homework"])


def _load_homework(db: Session, homework_id: int) -> Homework:
    homework = db.scalar(
        select(Homework).where(Homework.id == homework_id).options(selectinload(Homework.questions))
    )
    if homework is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Homework {homework_id} not found")
    return homework


@router.post("/generate", response_model=HomeworkRead, status_code=status.HTTP_201_CREATED)
def generate_homework(
    payload: HomeworkGenerate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: Principal = Depends(get_current_user),
):
    """Assign adaptive homework, targeting the student's weakest topic unless one is given.

    Students can assign practice to themselves; teachers to students in their class; admins to anyone.
    """
    ensure_student_access(db, user, payload.student_id)
    analysis = gap_analyzer.analyze_student(
        db,
        payload.student_id,
        threshold=settings.mastery_threshold,
        min_attempts=settings.min_attempts_for_gap,
    )
    topic_id = payload.topic_id or personalization.pick_focus_topic(db, analysis)
    if topic_id is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "No validated questions available")
    topic = get_or_404(db, Topic, topic_id)

    mastery = next((p.mastery for p in analysis.progress if p.topic_id == topic_id), None)
    questions = personalization.select_homework_questions(
        db,
        student_id=payload.student_id,
        topic_id=topic_id,
        mastery=mastery,
        limit=payload.num_questions,
    )
    if not questions:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"No validated questions for topic '{topic.name}'"
        )

    homework = Homework(
        student_id=payload.student_id,
        topic_id=topic_id,
        title=f"{topic.name} practice",
        due_at=utcnow() + timedelta(days=payload.due_in_days) if payload.due_in_days is not None else None,
        questions=questions,
    )
    db.add(homework)
    db.commit()
    return homework


@router.get("", response_model=list[HomeworkRead])
def list_homework(
    student_id: int,
    status_filter: Literal["assigned", "completed"] | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    user: Principal = Depends(get_current_user),
):
    ensure_student_access(db, user, student_id)
    query = (
        select(Homework)
        .where(Homework.student_id == student_id)
        .options(selectinload(Homework.questions))
        .order_by(Homework.id.desc())
    )
    if status_filter:
        query = query.where(Homework.status == status_filter)
    return db.scalars(query).all()


@router.get("/{homework_id}", response_model=HomeworkRead)
def get_homework(
    homework_id: int, db: Session = Depends(get_db), user: Principal = Depends(get_current_user)
):
    homework = _load_homework(db, homework_id)
    ensure_student_access(db, user, homework.student_id)
    return homework


@router.post("/{homework_id}/submit", response_model=SubmissionRead)
def submit_homework(
    homework_id: int,
    payload: HomeworkSubmit,
    db: Session = Depends(get_db),
    user: Principal = Depends(get_current_user),
):
    homework = _load_homework(db, homework_id)
    ensure_can_submit(user, homework.student_id)
    if homework.status == "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, "Homework has already been submitted")
    homework.status = "completed"
    homework.completed_at = utcnow()
    try:
        submission = grade_submission(
            db,
            student_id=homework.student_id,
            questions=homework.questions,
            answers=answers_to_map(payload.answers),
            homework_id=homework.id,
        )
    except InvalidSubmission as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    return submission_to_read(submission, homework.questions)
