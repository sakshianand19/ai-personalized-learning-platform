"""Learning-gap identification from per-topic mastery."""

from dataclasses import asdict, dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Topic, TopicMastery

Status = Literal["gap", "needs_assessment", "in_progress", "mastered"]

MASTERED_THRESHOLD = 0.85
HIGH_SEVERITY_THRESHOLD = 0.4


@dataclass(frozen=True)
class TopicProgress:
    topic_id: int
    topic_name: str
    subject: str
    attempts: int
    correct: int
    mastery: float | None
    status: Status


@dataclass(frozen=True)
class LearningGap(TopicProgress):
    severity: Literal["high", "medium"]
    reason: str
    recommended_action: str


@dataclass(frozen=True)
class GapAnalysis:
    overall_mastery: float | None
    gaps: list[LearningGap]
    progress: list[TopicProgress]


def classify(mastery: float | None, attempts: int, *, threshold: float, min_attempts: int) -> Status:
    if mastery is None or attempts < min_attempts:
        return "needs_assessment"
    if mastery < threshold:
        return "gap"
    if mastery < MASTERED_THRESHOLD:
        return "in_progress"
    return "mastered"


def _to_gap(progress: TopicProgress) -> LearningGap:
    assert progress.mastery is not None
    accuracy = progress.correct / progress.attempts
    if progress.mastery < HIGH_SEVERITY_THRESHOLD:
        severity = "high"
        action = (
            f"Revisit the foundational material on {progress.topic_name} and complete "
            "easy practice homework before moving on."
        )
    else:
        severity = "medium"
        action = f"Practise medium-difficulty questions on {progress.topic_name}."
    reason = (
        f"Answered {progress.correct} of {progress.attempts} questions correctly "
        f"({accuracy:.0%}); mastery {progress.mastery:.2f} is below the target."
    )
    return LearningGap(**asdict(progress), severity=severity, reason=reason, recommended_action=action)


def analyze(
    topics: list[Topic],
    masteries: list[TopicMastery],
    *,
    threshold: float,
    min_attempts: int,
) -> GapAnalysis:
    """Pure analysis over already-loaded rows (unit-testable without a database)."""
    by_topic = {m.topic_id: m for m in masteries}
    progress: list[TopicProgress] = []
    for topic in topics:
        row = by_topic.get(topic.id)
        attempts = row.attempts if row else 0
        mastery = row.mastery if row else None
        progress.append(
            TopicProgress(
                topic_id=topic.id,
                topic_name=topic.name,
                subject=topic.subject,
                attempts=attempts,
                correct=row.correct if row else 0,
                mastery=mastery,
                status=classify(mastery, attempts, threshold=threshold, min_attempts=min_attempts),
            )
        )

    gaps = sorted(
        (_to_gap(p) for p in progress if p.status == "gap"),
        key=lambda g: (g.mastery, -g.attempts),
    )
    assessed = [m for m in masteries if m.attempts]
    overall = (
        round(sum(m.mastery * m.attempts for m in assessed) / sum(m.attempts for m in assessed), 4)
        if assessed
        else None
    )
    return GapAnalysis(overall_mastery=overall, gaps=gaps, progress=progress)


def analyze_student(db: Session, student_id: int, *, threshold: float, min_attempts: int) -> GapAnalysis:
    topics = list(db.scalars(select(Topic).order_by(Topic.subject, Topic.name)))
    masteries = list(db.scalars(select(TopicMastery).where(TopicMastery.student_id == student_id)))
    return analyze(topics, masteries, threshold=threshold, min_attempts=min_attempts)
