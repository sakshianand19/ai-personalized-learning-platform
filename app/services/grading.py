"""Grading of assessment/homework submissions and per-topic mastery tracking."""

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Question, Response, Submission, TopicMastery

# Harder questions move mastery more than easy ones.
DIFFICULTY_WEIGHTS = {"easy": 0.8, "medium": 1.0, "hard": 1.3}


class InvalidSubmission(ValueError):
    pass


@dataclass
class _TopicTally:
    attempts: int = 0
    correct: int = 0
    weighted_attempts: float = 0.0
    weighted_correct: float = 0.0


def normalize_answer(value: str) -> str:
    return " ".join(value.strip().lower().split())


def smoothed_mastery(weighted_correct: float, weighted_attempts: float) -> float:
    """Beta(1, 1)-smoothed accuracy so one lucky/unlucky answer doesn't dominate."""
    return round((weighted_correct + 1) / (weighted_attempts + 2), 4)


def grade_submission(
    db: Session,
    *,
    student_id: int,
    questions: list[Question],
    answers: Mapping[int, str],
    assessment_id: int | None = None,
    homework_id: int | None = None,
) -> Submission:
    """Grade answers against ``questions``, persist the submission and update mastery."""
    by_id = {q.id: q for q in questions}
    unknown = sorted(set(answers) - set(by_id))
    if unknown:
        raise InvalidSubmission(f"Questions not part of this activity: {unknown}")

    submission = Submission(
        student_id=student_id, assessment_id=assessment_id, homework_id=homework_id
    )
    tallies: dict[int, _TopicTally] = defaultdict(_TopicTally)
    correct_count = 0

    for question_id, answer in answers.items():
        question = by_id[question_id]
        is_correct = normalize_answer(answer) == normalize_answer(question.correct_answer)
        correct_count += is_correct
        submission.responses.append(
            Response(question_id=question_id, answer=answer, is_correct=is_correct)
        )
        weight = DIFFICULTY_WEIGHTS.get(question.difficulty, 1.0)
        tally = tallies[question.topic_id]
        tally.attempts += 1
        tally.correct += is_correct
        tally.weighted_attempts += weight
        tally.weighted_correct += weight * is_correct

    # Unanswered questions count against the score but not against topic mastery.
    submission.correct = correct_count
    submission.total = len(questions)
    submission.score = round(100 * correct_count / len(questions), 2) if questions else 0.0

    _update_mastery(db, student_id, tallies)
    db.add(submission)
    db.commit()
    return submission


def _update_mastery(db: Session, student_id: int, tallies: dict[int, _TopicTally]) -> None:
    if not tallies:
        return
    # One query for all affected topics instead of one per topic.
    existing = {
        row.topic_id: row
        for row in db.scalars(
            select(TopicMastery).where(
                TopicMastery.student_id == student_id, TopicMastery.topic_id.in_(tallies)
            )
        )
    }
    for topic_id, tally in tallies.items():
        row = existing.get(topic_id)
        if row is None:
            row = TopicMastery(
                student_id=student_id,
                topic_id=topic_id,
                attempts=0,
                correct=0,
                weighted_attempts=0.0,
                weighted_correct=0.0,
            )
            db.add(row)
        row.attempts += tally.attempts
        row.correct += tally.correct
        row.weighted_attempts += tally.weighted_attempts
        row.weighted_correct += tally.weighted_correct
        row.mastery = smoothed_mastery(row.weighted_correct, row.weighted_attempts)
