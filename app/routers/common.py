from typing import TypeVar

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Base, Question, Submission
from app.schemas import AnswerIn, ResponseRead, SubmissionRead

ModelT = TypeVar("ModelT", bound=Base)


def get_or_404(db: Session, model: type[ModelT], obj_id: int) -> ModelT:
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{model.__name__} {obj_id} not found")
    return obj


def answers_to_map(answers: list[AnswerIn]) -> dict[int, str]:
    # If a question is answered twice, the last answer wins.
    return {a.question_id: a.answer for a in answers}


def submission_to_read(submission: Submission, questions: list[Question]) -> SubmissionRead:
    by_id = {q.id: q for q in questions}
    return SubmissionRead(
        id=submission.id,
        student_id=submission.student_id,
        correct=submission.correct,
        total=submission.total,
        score=submission.score,
        submitted_at=submission.submitted_at,
        responses=[
            ResponseRead(
                question_id=r.question_id,
                answer=r.answer,
                is_correct=r.is_correct,
                correct_answer=by_id[r.question_id].correct_answer,
                explanation=by_id[r.question_id].explanation,
            )
            for r in submission.responses
        ],
    )
