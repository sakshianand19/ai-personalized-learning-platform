"""End-to-end API flows over a real (in-memory) database."""

API = "/api/v1"


def _answer_all(questions, *, correct_topics: set[int], answer_key: dict[int, str]):
    answers = []
    for q in questions:
        right = answer_key[q["id"]]
        wrong = next(o for o in q["options"] if o != right)
        answers.append({"question_id": q["id"], "answer": right if q["topic_id"] in correct_topics else wrong})
    return answers


def _answer_key(client) -> dict[int, str]:
    return {
        q["id"]: q["correct_answer"]
        for q in client.get(f"{API}/questions", params={"validated_only": False}).json()
    }


def test_health_and_landing_page(client):
    assert client.get("/health").json()["llm_provider"] == "heuristic"
    assert "Personalized Learning" in client.get("/").text


def test_student_crud_and_duplicate_email(client):
    payload = {"name": "Asha", "email": "Asha@Example.com", "grade_level": 8}
    created = client.post(f"{API}/students", json=payload)
    assert created.status_code == 201
    assert created.json()["email"] == "asha@example.com"
    assert client.post(f"{API}/students", json=payload).status_code == 409
    assert client.get(f"{API}/students/999").status_code == 404
    assert client.post(f"{API}/students", json=payload | {"grade_level": 13}).status_code == 422


def test_assessment_hides_answers_and_grading_drives_gap_report(client, seeded):
    topics = {t["name"]: t["id"] for t in client.get(f"{API}/topics").json()}
    created = client.post(
        f"{API}/assessments",
        json={"title": "Diagnostic", "topic_ids": list(topics.values()), "questions_per_topic": 4},
    )
    assert created.status_code == 201
    assessment = created.json()
    assert len(assessment["questions"]) == 12
    assert "correct_answer" not in assessment["questions"][0]

    # The student gets every Fractions question wrong and everything else right.
    strong = {topics["Photosynthesis"], topics["Linear Equations"]}
    answers = _answer_all(assessment["questions"], correct_topics=strong, answer_key=_answer_key(client))
    result = client.post(
        f"{API}/assessments/{assessment['id']}/submit", json={"student_id": 1, "answers": answers}
    ).json()
    assert result["correct"] == 8 and result["total"] == 12
    assert result["score"] == 66.67
    assert all(r["correct_answer"] for r in result["responses"])

    report = client.get(f"{API}/students/1/learning-gaps").json()
    assert [g["topic_name"] for g in report["gaps"]] == ["Fractions"]
    assert report["gaps"][0]["severity"] == "high"
    statuses = {p["topic_name"]: p["status"] for p in report["progress"]}
    # 4/4 correct is strong but, after smoothing, not yet enough evidence for "mastered".
    assert statuses["Photosynthesis"] == "in_progress"

    path = client.get(f"{API}/students/1/learning-path").json()["steps"]
    assert path[0]["topic_name"] == "Fractions"
    assert path[0]["target_difficulty"] == "easy"
    assert path[0]["recommended_content"]


def test_homework_targets_weakest_topic_and_cannot_be_resubmitted(client, seeded):
    topics = {t["name"]: t["id"] for t in client.get(f"{API}/topics").json()}
    key = _answer_key(client)
    assessment = client.post(
        f"{API}/assessments", json={"title": "Diag", "topic_ids": [topics["Linear Equations"]]}
    ).json()
    answers = _answer_all(assessment["questions"], correct_topics=set(), answer_key=key)
    client.post(f"{API}/assessments/{assessment['id']}/submit", json={"student_id": 1, "answers": answers})

    homework = client.post(f"{API}/homework/generate", json={"student_id": 1, "num_questions": 3})
    assert homework.status_code == 201
    homework = homework.json()
    assert homework["topic_id"] == topics["Linear Equations"]
    assert len(homework["questions"]) == 3
    # Low mastery -> easiest questions are chosen first.
    assert homework["questions"][0]["difficulty"] == "easy"

    answers = [{"question_id": q["id"], "answer": key[q["id"]]} for q in homework["questions"]]
    submitted = client.post(f"{API}/homework/{homework['id']}/submit", json={"answers": answers})
    assert submitted.json()["score"] == 100.0
    assert client.get(f"{API}/homework/{homework['id']}").json()["status"] == "completed"
    assert client.post(f"{API}/homework/{homework['id']}/submit", json={"answers": answers}).status_code == 409
    listed = client.get(f"{API}/homework", params={"student_id": 1, "status": "completed"}).json()
    assert [h["id"] for h in listed] == [homework["id"]]


def test_submitting_foreign_question_is_rejected(client, seeded):
    assessment = client.post(f"{API}/assessments", json={"title": "A", "question_ids": [1]}).json()
    response = client.post(
        f"{API}/assessments/{assessment['id']}/submit",
        json={"student_id": 1, "answers": [{"question_id": 2, "answer": "x"}]},
    )
    assert response.status_code == 422


def test_assessment_requires_a_question_source(client):
    assert client.post(f"{API}/assessments", json={"title": "Empty"}).status_code == 422
