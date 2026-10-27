"""Question validation: deterministic structural rules plus an optional LLM review."""

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

MIN_QUESTION_LENGTH = 10
MAX_OPTIONS = 6
DISCOURAGED_OPTIONS = {"all of the above", "none of the above"}


class QuestionDraft(BaseModel):
    """A multiple-choice question that has not been persisted yet."""

    text: str
    options: list[str]
    correct_answer: str
    explanation: str = ""
    difficulty: Literal["easy", "medium", "hard"] = "medium"


class LLMReview(BaseModel):
    answer_is_correct: bool = Field(description="The marked answer is factually correct.")
    is_unambiguous: bool = Field(description="Exactly one option is defensibly correct.")
    is_relevant: bool = Field(description="The question is grounded in the given context/topic.")
    clarity_score: int = Field(ge=1, le=5, description="1 = confusing, 5 = perfectly clear.")
    feedback: str = Field(description="One or two sentences of reviewer feedback.")


@dataclass
class ValidationResult:
    is_valid: bool
    issues: list[str] = field(default_factory=list)
    reviewed_by: str = "rules"
    llm_review: dict[str, Any] | None = None


_REVIEW_PARSER = PydanticOutputParser(pydantic_object=LLMReview)
_REVIEW_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a meticulous assessment reviewer for school students. Review the "
            "multiple-choice question for factual correctness, ambiguity, relevance and "
            "clarity. Respond with JSON only.\n{format_instructions}",
        ),
        (
            "human",
            "Topic: {topic}\nContext:\n{context}\n\nQuestion: {text}\nOptions:\n{options}\n"
            "Marked correct answer: {correct_answer}",
        ),
    ]
).partial(format_instructions=_REVIEW_PARSER.get_format_instructions())


def normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def structural_issues(question: QuestionDraft) -> list[str]:
    issues: list[str] = []
    if len(question.text.strip()) < MIN_QUESTION_LENGTH:
        issues.append("Question text is too short.")

    options = [normalize(o) for o in question.options]
    if len(options) < 2:
        issues.append("A question needs at least two options.")
    if len(options) > MAX_OPTIONS:
        issues.append(f"A question can have at most {MAX_OPTIONS} options.")
    if any(not o for o in options):
        issues.append("Options must not be empty.")
    if len(set(options)) != len(options):
        issues.append("Options must be unique.")
    if normalize(question.correct_answer) not in options:
        issues.append("The correct answer must match one of the options.")
    if DISCOURAGED_OPTIONS & set(options):
        issues.append("Avoid 'all of the above' / 'none of the above' options.")
    return issues


def _llm_review(
    question: QuestionDraft, *, topic: str, context: str | None, llm: BaseChatModel
) -> LLMReview:
    chain = _REVIEW_PROMPT | llm | _REVIEW_PARSER
    return chain.invoke(
        {
            "topic": topic,
            "context": (context or "(none provided)")[:6000],
            "text": question.text,
            "options": "\n".join(f"- {o}" for o in question.options),
            "correct_answer": question.correct_answer,
        }
    )


def validate_question(
    question: QuestionDraft,
    *,
    topic: str = "",
    context: str | None = None,
    llm: BaseChatModel | None = None,
) -> ValidationResult:
    issues = structural_issues(question)
    # Don't spend LLM tokens on questions that are already structurally broken.
    if issues or llm is None:
        return ValidationResult(is_valid=not issues, issues=issues)

    try:
        review = _llm_review(question, topic=topic, context=context, llm=llm)
    except Exception:
        logger.warning("LLM question review failed; using rule-based result only", exc_info=True)
        return ValidationResult(is_valid=True)

    if not review.answer_is_correct:
        issues.append("Reviewer: the marked correct answer appears to be wrong.")
    if not review.is_unambiguous:
        issues.append("Reviewer: more than one option could be considered correct.")
    if not review.is_relevant:
        issues.append("Reviewer: the question is not grounded in the provided content.")
    if review.clarity_score < 3:
        issues.append(f"Reviewer: wording is unclear (clarity {review.clarity_score}/5).")

    return ValidationResult(
        is_valid=not issues,
        issues=issues,
        reviewed_by="rules+llm",
        llm_review=review.model_dump(),
    )
