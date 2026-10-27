"""Content processing and question validation endpoints, with and without an LLM."""

API = "/api/v1"

BODY = (
    "Fractions describe parts of a whole. The numerator counts the parts taken and the "
    "denominator counts equal parts in the whole. Equivalent fractions such as 1/2 and 2/4 "
    "represent the same amount. Adding fractions requires a common denominator."
)

QUESTION = {
    "text": "Which fraction is equivalent to 2/4?",
    "options": ["1/2", "1/4", "2/2", "4/2"],
    "correct_answer": "1/2",
    "explanation": "2/4 simplifies to 1/2.",
    "difficulty": "easy",
}

GOOD_REVIEW = {
    "answer_is_correct": True,
    "is_unambiguous": True,
    "is_relevant": True,
    "clarity_score": 5,
    "feedback": "Good question.",
}
BAD_REVIEW = GOOD_REVIEW | {"answer_is_correct": False, "feedback": "Wrong key."}


def _topic(client) -> int:
    return client.post(f"{API}/topics", json={"subject": "Mathematics", "name": "Fractions"}).json()["id"]


def test_content_is_processed_with_heuristics_without_llm(client):
    response = client.post(f"{API}/content", json={"topic_id": _topic(client), "title": "Intro", "body": BODY})
    assert response.status_code == 201
    content = response.json()
    assert content["processed_by"] == "heuristic"
    assert content["summary"].startswith("Fractions describe parts")
    assert "fractions" in content["key_concepts"]


def test_content_is_processed_by_llm_chain(client, use_llm):
    topic_id = _topic(client)
    use_llm({"summary": "Fractions are parts of a whole.", "key_concepts": ["numerator"], "difficulty": "easy"})
    content = client.post(f"{API}/content", json={"topic_id": topic_id, "title": "Intro", "body": BODY}).json()
    assert content["processed_by"] == "llm"
    assert content["key_concepts"] == ["numerator"]


def test_content_for_unknown_topic_is_404(client):
    assert client.post(f"{API}/content", json={"topic_id": 42, "title": "x", "body": BODY}).status_code == 404


def test_generated_questions_are_validated_and_persisted(client, use_llm):
    topic_id = _topic(client)
    content = client.post(f"{API}/content", json={"topic_id": topic_id, "title": "Intro", "body": BODY}).json()

    broken = QUESTION | {"correct_answer": "3/4"}  # fails structural rules -> never reviewed
    wrong_key = QUESTION | {"text": "Which fraction equals one half exactly?"}
    # Responses are consumed in order: generation, then one review per structurally valid question.
    use_llm({"questions": [QUESTION, broken, wrong_key]}, GOOD_REVIEW, BAD_REVIEW)

    result = client.post(f"{API}/content/{content['id']}/questions", json={"count": 3}).json()
    assert result["generated_by"] == "llm"
    assert [q["text"] for q in result["accepted"]] == [QUESTION["text"]]
    assert result["accepted"][0]["validation_notes"] == ["validated by rules+llm"]
    assert len(result["rejected"]) == 2

    stored = client.get(f"{API}/questions", params={"topic_id": topic_id}).json()
    assert [q["id"] for q in stored] == [result["accepted"][0]["id"]]


def test_heuristic_question_generation(client):
    topic_id = _topic(client)
    content = client.post(f"{API}/content", json={"topic_id": topic_id, "title": "Intro", "body": BODY}).json()
    result = client.post(f"{API}/content/{content['id']}/questions", json={"count": 2}).json()
    assert result["generated_by"] == "heuristic"
    assert len(result["accepted"]) == 2


def test_validate_endpoint(client, use_llm):
    report = client.post(f"{API}/questions/validate", json=QUESTION | {"correct_answer": "9/9"}).json()
    assert not report["is_valid"] and report["reviewed_by"] == "rules"

    use_llm(BAD_REVIEW)
    report = client.post(f"{API}/questions/validate", json=QUESTION | {"context": BODY}).json()
    assert not report["is_valid"]
    assert report["llm_review"]["feedback"] == "Wrong key."


def test_create_question_rejects_invalid_and_accepts_valid(client):
    topic_id = _topic(client)
    bad = client.post(f"{API}/questions", json=QUESTION | {"topic_id": topic_id, "options": ["1/2", "1/2"]})
    assert bad.status_code == 422
    assert "unique" in str(bad.json()["detail"]["issues"])

    good = client.post(f"{API}/questions", json=QUESTION | {"topic_id": topic_id})
    assert good.status_code == 201 and good.json()["is_validated"]
