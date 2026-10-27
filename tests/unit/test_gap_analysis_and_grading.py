import pytest

from app.models import Topic, TopicMastery
from app.services.gap_analyzer import analyze, classify
from app.services.grading import normalize_answer, smoothed_mastery
from app.services.personalization import target_difficulty


def _mastery(topic_id: int, attempts: int, correct: int, mastery: float) -> TopicMastery:
    return TopicMastery(topic_id=topic_id, attempts=attempts, correct=correct, mastery=mastery)


TOPICS = [
    Topic(id=1, subject="Math", name="Fractions"),
    Topic(id=2, subject="Math", name="Algebra"),
    Topic(id=3, subject="Science", name="Cells"),
    Topic(id=4, subject="Science", name="Energy"),
]


def test_smoothed_mastery_pulls_small_samples_toward_half():
    assert smoothed_mastery(0, 0) == 0.5
    assert smoothed_mastery(1, 1) == pytest.approx(0.6667, abs=1e-4)
    assert smoothed_mastery(10, 10) == pytest.approx(0.9167, abs=1e-4)


def test_normalize_answer():
    assert normalize_answer("  Carbon   Dioxide ") == "carbon dioxide"


@pytest.mark.parametrize(
    ("mastery", "attempts", "expected"),
    [
        (None, 0, "needs_assessment"),
        (0.2, 1, "needs_assessment"),
        (0.3, 4, "gap"),
        (0.7, 4, "in_progress"),
        (0.9, 4, "mastered"),
    ],
)
def test_classify(mastery, attempts, expected):
    assert classify(mastery, attempts, threshold=0.6, min_attempts=2) == expected


def test_analyze_orders_gaps_by_severity_and_computes_overall():
    masteries = [
        _mastery(1, attempts=4, correct=0, mastery=0.17),
        _mastery(2, attempts=4, correct=2, mastery=0.5),
        _mastery(3, attempts=4, correct=4, mastery=0.9),
    ]
    result = analyze(TOPICS, masteries, threshold=0.6, min_attempts=2)

    assert [g.topic_name for g in result.gaps] == ["Fractions", "Algebra"]
    assert [g.severity for g in result.gaps] == ["high", "medium"]
    assert "0 of 4" in result.gaps[0].reason
    statuses = {p.topic_name: p.status for p in result.progress}
    assert statuses == {
        "Fractions": "gap",
        "Algebra": "gap",
        "Cells": "mastered",
        "Energy": "needs_assessment",
    }
    assert result.overall_mastery == pytest.approx((0.17 + 0.5 + 0.9) / 3, abs=1e-4)


def test_analyze_with_no_activity():
    result = analyze(TOPICS, [], threshold=0.6, min_attempts=2)
    assert result.gaps == [] and result.overall_mastery is None


@pytest.mark.parametrize(
    ("mastery", "expected"), [(None, "easy"), (0.3, "easy"), (0.6, "medium"), (0.9, "hard")]
)
def test_target_difficulty(mastery, expected):
    assert target_difficulty(mastery) == expected
