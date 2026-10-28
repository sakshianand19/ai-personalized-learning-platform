"""Aggregated views for teachers (their class) and admins (the whole platform)."""

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import Principal, require_roles
from app.config import Settings, get_settings
from app.database import get_db
from app.models import (
    Assessment,
    Homework,
    LearningContent,
    Question,
    Staff,
    Student,
    Submission,
    Topic,
    TopicMastery,
)
from app.routers.common import get_or_404
from app.schemas import (
    ActivityItem,
    ClassReport,
    ClassStudent,
    ClassTopic,
    PlatformCounts,
    PlatformReport,
    StudentTopicMastery,
    TopicInventory,
)
from app.services import gap_analyzer

router = APIRouter(prefix="/reports", tags=["reports"])


def _average(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


@router.get("/class", response_model=ClassReport)
def class_report(
    teacher_id: int | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: Principal = Depends(require_roles("admin", "teacher")),
):
    """Mastery and gaps for a teacher's students (or every student when no teacher is given).

    Teachers always get their own class; only admins can look at another teacher's class.
    """
    if user.role == "teacher":
        if teacher_id not in (None, user.id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Teachers can only view their own class")
        teacher_id = user.id
    if teacher_id is not None:
        get_or_404(db, Staff, teacher_id)
    student_query = select(Student).order_by(Student.name)
    if teacher_id is not None:
        student_query = student_query.where(Student.teacher_id == teacher_id)
    students = list(db.scalars(student_query))
    student_ids = [s.id for s in students]
    topics = list(db.scalars(select(Topic).order_by(Topic.subject, Topic.name)))

    # Three queries in total for the whole class, however many students it has.
    masteries: dict[int, list[TopicMastery]] = defaultdict(list)
    for row in db.scalars(select(TopicMastery).where(TopicMastery.student_id.in_(student_ids))):
        masteries[row.student_id].append(row)
    activity = {
        sid: (count, last)
        for sid, count, last in db.execute(
            select(Submission.student_id, func.count(), func.max(Submission.submitted_at))
            .where(Submission.student_id.in_(student_ids))
            .group_by(Submission.student_id)
        )
    }

    class_students: list[ClassStudent] = []
    topic_values: dict[int, list[float]] = defaultdict(list)
    topic_gaps: dict[int, int] = defaultdict(int)
    for student in students:
        analysis = gap_analyzer.analyze(
            topics,
            masteries[student.id],
            threshold=settings.mastery_threshold,
            min_attempts=settings.min_attempts_for_gap,
        )
        for progress in analysis.progress:
            if progress.mastery is not None and progress.attempts:
                topic_values[progress.topic_id].append(progress.mastery)
            if progress.status == "gap":
                topic_gaps[progress.topic_id] += 1
        count, last = activity.get(student.id, (0, None))
        class_students.append(
            ClassStudent(
                id=student.id,
                name=student.name,
                email=student.email,
                grade_level=student.grade_level,
                overall_mastery=analysis.overall_mastery,
                gap_topics=[g.topic_name for g in analysis.gaps],
                submissions=count,
                last_active=last,
                topics=[
                    StudentTopicMastery(topic_id=p.topic_id, mastery=p.mastery, status=p.status)
                    for p in analysis.progress
                ],
            )
        )

    return ClassReport(
        teacher_id=teacher_id,
        student_count=len(students),
        average_mastery=_average(
            [s.overall_mastery for s in class_students if s.overall_mastery is not None]
        ),
        students_with_gaps=sum(1 for s in class_students if s.gap_topics),
        submissions=sum(s.submissions for s in class_students),
        topics=[
            ClassTopic(
                topic_id=t.id,
                topic_name=t.name,
                subject=t.subject,
                average_mastery=_average(topic_values[t.id]),
                assessed_students=len(topic_values[t.id]),
                students_with_gap=topic_gaps[t.id],
            )
            for t in topics
        ],
        students=class_students,
    )


@router.get("/platform", response_model=PlatformReport)
def platform_report(db: Session = Depends(get_db), _: Principal = Depends(require_roles("admin"))):
    """Platform-wide counts, content inventory and recent activity for admins."""

    def count(model, *where) -> int:
        return db.scalar(select(func.count()).select_from(model).where(*where)) or 0

    staff_counts = dict(db.execute(select(Staff.role, func.count()).group_by(Staff.role)).all())
    content_counts = dict(
        db.execute(select(LearningContent.topic_id, func.count()).group_by(LearningContent.topic_id)).all()
    )
    question_counts = dict(
        db.execute(
            select(Question.topic_id, func.count())
            .where(Question.is_validated.is_(True))
            .group_by(Question.topic_id)
        ).all()
    )
    recent = db.execute(
        select(Submission, Student.name)
        .join(Student, Student.id == Submission.student_id)
        .order_by(Submission.id.desc())
        .limit(8)
    ).all()

    return PlatformReport(
        counts=PlatformCounts(
            students=count(Student),
            teachers=staff_counts.get("teacher", 0),
            admins=staff_counts.get("admin", 0),
            topics=count(Topic),
            content=count(LearningContent),
            questions=count(Question),
            validated_questions=count(Question, Question.is_validated.is_(True)),
            assessments=count(Assessment),
            homework=count(Homework),
            submissions=count(Submission),
        ),
        average_score=(
            round(score, 2) if (score := db.scalar(select(func.avg(Submission.score)))) is not None else None
        ),
        topics=[
            TopicInventory(
                topic_id=t.id,
                topic_name=t.name,
                subject=t.subject,
                content_count=content_counts.get(t.id, 0),
                question_count=question_counts.get(t.id, 0),
            )
            for t in db.scalars(select(Topic).order_by(Topic.subject, Topic.name))
        ],
        recent_activity=[
            ActivityItem(
                submission_id=s.id,
                student_id=s.student_id,
                student_name=name,
                kind="homework" if s.homework_id else "assessment",
                score=s.score,
                submitted_at=s.submitted_at,
            )
            for s, name in recent
        ],
    )
