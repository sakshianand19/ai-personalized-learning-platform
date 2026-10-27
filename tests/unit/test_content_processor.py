from app.services import content_processor as cp
from app.services.question_validator import structural_issues
from tests.conftest import fake_llm

TEXT = (
    "Photosynthesis is the process plants use to make their own food. It happens inside "
    "chloroplasts, which contain chlorophyll. Chlorophyll absorbs sunlight. Oxygen is "
    "released as a by-product of photosynthesis. Plants absorb carbon dioxide through stomata."
)


def test_split_sentences():
    assert cp.split_sentences("One. Two! Three? ") == ["One.", "Two!", "Three?"]


def test_key_concepts_skip_stopwords_and_rank_by_frequency():
    concepts = cp.extract_key_concepts(TEXT)
    assert concepts[0] == "photosynthesis"
    assert "chlorophyll" in concepts
    assert not set(concepts) & cp.STOPWORDS


def test_difficulty_estimate_scales_with_complexity():
    assert cp.estimate_difficulty("The cat sat. The dog ran. We had fun.") == "easy"
    hard = (
        "Electrochemical gradients established across thylakoid membranes facilitate "
        "chemiosmotic phosphorylation, whereby transmembrane proton translocation drives "
        "adenosine triphosphate biosynthesis through conformational rotation of synthase "
        "complexes embedded within photosynthetic organelles."
    )
    assert cp.estimate_difficulty(hard) == "hard"


def test_heuristic_analysis_summary_is_first_sentences():
    analysis = cp.heuristic_analysis(TEXT)
    assert analysis.summary.startswith("Photosynthesis is the process")
    assert analysis.summary.count(".") == 2


def test_analyze_content_uses_llm_chain():
    llm = fake_llm(
        {
            "summary": "Plants turn light into food.",
            "key_concepts": ["photosynthesis", " chlorophyll ", ""],
            "difficulty": "easy",
        }
    )
    analysis, engine = cp.analyze_content(TEXT, subject="Science", topic="Photosynthesis", llm=llm)
    assert engine == "llm"
    assert analysis.summary == "Plants turn light into food."
    assert analysis.key_concepts == ["photosynthesis", "chlorophyll"]


def test_analyze_content_falls_back_on_bad_llm_output():
    analysis, engine = cp.analyze_content(TEXT, subject="S", topic="T", llm=fake_llm("oops"))
    assert engine == "heuristic"
    assert analysis.key_concepts


def test_heuristic_questions_are_structurally_valid():
    drafts = cp.heuristic_questions(
        TEXT, key_concepts=cp.extract_key_concepts(TEXT), count=3, difficulty="easy"
    )
    assert len(drafts) == 3
    for draft in drafts:
        assert "_____" in draft.text
        assert structural_issues(draft) == []
    # The answer position is rotated across questions.
    assert len({d.options.index(d.correct_answer) for d in drafts}) > 1


def test_generate_questions_with_llm_respects_count():
    question = {
        "text": "Which pigment absorbs sunlight?",
        "options": ["Chlorophyll", "Melanin", "Keratin", "Haemoglobin"],
        "correct_answer": "Chlorophyll",
        "explanation": "Chlorophyll absorbs light.",
        "difficulty": "easy",
    }
    llm = fake_llm({"questions": [question, question, question]})
    drafts, engine = cp.generate_questions(
        TEXT, topic="Photosynthesis", count=2, difficulty="easy", key_concepts=[], llm=llm
    )
    assert engine == "llm"
    assert len(drafts) == 2
