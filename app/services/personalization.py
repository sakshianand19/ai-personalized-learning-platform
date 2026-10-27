"""Personalised learning paths and adaptive homework question selection."""

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LearningContent, Question, Response, Submission
from app.services.gap_analyzer import GapAnalysis, Status, TopicProgress

DIFFICULTY_RANK = {"easy": 0, "medium": 1, "hard": 2}
# Gaps first (worst first), then untested topics, then reinforcement, then mastered.
STATUS_PRIORITY: dict[Status, int] = {"gap": 0, "needs_assessment": 1, "in_progress": 2, "mastered": 3}
CONTENT_PER_STEP = 2


@dataclass(frozen=True)
class PathStep:
    order: int
    progress: TopicProgress
    target_difficulty: str
    content: list[LearningContent]


def target_difficulty(mastery: float | None) -> str:
    """Pick the difficulty that keeps a student in their zone of proximal development."""
    if mastery is None or mastery < 0.4:
        return "easy"
    if mastery < 0.75:
        return "medium"
    return "hard"


def _closest_by_difficulty(items, target: str):
    goal = DIFFICULTY_RANK[target]
    return sorted(items, key=lambda item: (abs(DIFFICULTY_RANK.get(item.difficulty, 1) - goal), item.id))


def build_learning_path(db: Session, analysis: GapAnalysis) -> list[PathStep]:
    ordered = sorted(
        analysis.progress,
        key=lambda p: (STATUS_PRIORITY[p.status], p.mastery if p.mastery is not None else 0.0),
    )
    # Load content for every topic in one query to avoid N+1 lookups.
    content_by_topic: dict[int, list[LearningContent]] = defaultdict(list)
    for content in db.scalars(select(LearningContent)):
        content_by_topic[content.topic_id].append(content)

    steps = []
    for order, progress in enumerate(ordered, start=1):
        target = target_difficulty(progress.mastery)
        content = _closest_by_difficulty(content_by_topic[progress.topic_id], target)
        steps.append(PathStep(order, progress, target, content[:CONTENT_PER_STEP]))
    return steps


def pick_focus_topic(db: Session, analysis: GapAnalysis) -> int | None:
    """The topic homework should target when none is requested: the most urgent one with questions."""
    topics_with_questions = set(
        db.scalars(select(Question.topic_id).where(Question.is_validated.is_(True)).distinct())
    )
    candidates = [p for p in analysis.progress if p.topic_id in topics_with_questions]
    if not candidates:
        return None
    best = min(
        candidates,
        key=lambda p: (STATUS_PRIORITY[p.status], p.mastery if p.mastery is not None else 0.0),
    )
    return best.topic_id


def select_homework_questions(
    db: Session, *, student_id: int, topic_id: int, mastery: float | None, limit: int
) -> list[Question]:
    """Prefer questions the student hasn't answered correctly yet, near their level."""
    already_correct = set(
        db.scalars(
            select(Response.question_id)
            .join(Submission, Submission.id == Response.submission_id)
            .where(Submission.student_id == student_id, Response.is_correct.is_(True))
        )
    )
    candidates = db.scalars(
        select(Question).where(Question.topic_id == topic_id, Question.is_validated.is_(True))
    ).all()
    goal = DIFFICULTY_RANK[target_difficulty(mastery)]
    ranked = sorted(
        candidates,
        key=lambda q: (
            q.id in already_correct,
            abs(DIFFICULTY_RANK.get(q.difficulty, 1) - goal),
            q.id,
        ),
    )
    return ranked[:limit]
