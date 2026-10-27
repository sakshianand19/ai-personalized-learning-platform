import pytest

from app.services.question_validator import QuestionDraft, structural_issues, validate_question
from tests.conftest import fake_llm

GOOD = QuestionDraft(
    text="Which gas do plants release during photosynthesis?",
    options=["Oxygen", "Nitrogen", "Carbon dioxide", "Helium"],
    correct_answer="Oxygen",
)

POSITIVE_REVIEW = {
    "answer_is_correct": True,
    "is_unambiguous": True,
    "is_relevant": True,
    "clarity_score": 5,
    "feedback": "Clear and accurate.",
}


def test_well_formed_question_has_no_structural_issues():
    assert structural_issues(GOOD) == []


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"text": "Gas?"}, "too short"),
        ({"options": ["Oxygen"]}, "at least two options"),
        ({"options": ["Oxygen", "oxygen ", "Helium"]}, "unique"),
        ({"correct_answer": "Argon"}, "must match one of the options"),
        ({"options": ["Oxygen", "None of the above"]}, "all of the above"),
        ({"options": ["Oxygen", ""]}, "must not be empty"),
    ],
)
def test_structural_rules_flag_bad_questions(changes, expected):
    issues = structural_issues(GOOD.model_copy(update=changes))
    assert any(expected in issue for issue in issues), issues


def test_answer_matching_ignores_case_and_whitespace():
    assert structural_issues(GOOD.model_copy(update={"correct_answer": "  oxygen "})) == []


def test_without_llm_only_rules_are_applied():
    result = validate_question(GOOD, llm=None)
    assert result.is_valid and result.reviewed_by == "rules" and result.llm_review is None


def test_llm_review_approves_good_question():
    result = validate_question(GOOD, topic="Photosynthesis", llm=fake_llm(POSITIVE_REVIEW))
    assert result.is_valid
    assert result.reviewed_by == "rules+llm"
    assert result.llm_review["clarity_score"] == 5


def test_llm_review_rejects_wrong_or_ambiguous_question():
    review = POSITIVE_REVIEW | {"answer_is_correct": False, "is_unambiguous": False, "clarity_score": 2}
    result = validate_question(GOOD, llm=fake_llm(review))
    assert not result.is_valid
    assert len(result.issues) == 3


def test_structurally_invalid_question_skips_llm_call():
    model = fake_llm(POSITIVE_REVIEW)
    result = validate_question(GOOD.model_copy(update={"correct_answer": "Argon"}), llm=model)
    assert not result.is_valid
    assert model.i == 0  # the fake model's response cursor never advanced


def test_unparseable_llm_output_falls_back_to_rules():
    result = validate_question(GOOD, llm=fake_llm("this is not json"))
    assert result.is_valid and result.reviewed_by == "rules"
