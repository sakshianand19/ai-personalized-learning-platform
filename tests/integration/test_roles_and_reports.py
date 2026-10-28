"""Staff management, class assignment and the teacher/admin reports."""

API = "/api/v1"


def _staff(client, role):
    return {s["name"]: s for s in client.get(f"{API}/staff", params={"role": role}).json()}


def test_seed_creates_staff_and_a_class(client, seeded):
    teachers = _staff(client, "teacher")
    assert set(teachers) == {"Ms. Priya Verma", "Mr. Rohan Mehta"}
    assert list(_staff(client, "admin")) == ["Neha Kapoor"]

    priya = teachers["Ms. Priya Verma"]["id"]
    roster = client.get(f"{API}/students", params={"teacher_id": priya}).json()
    assert {s["name"] for s in roster} == {"Demo Student", "Aarav Sharma", "Diya Patel", "Kabir Singh"}


def test_staff_crud_and_guards(client, seeded):
    created = client.post(
        f"{API}/staff", json={"name": "Mr. Arjun Das", "email": "Arjun@School.example", "role": "teacher", "password": "Passw0rd!"}
    )
    assert created.status_code == 201
    assert created.json()["email"] == "arjun@school.example"
    duplicate = client.post(f"{API}/staff", json={"name": "X", "email": "arjun@school.example", "role": "admin", "password": "Passw0rd!"})
    assert duplicate.status_code == 409
    assert client.post(f"{API}/staff", json={"name": "X", "email": "x@y.zz", "role": "owner", "password": "Passw0rd!"}).status_code == 422

    admin = _staff(client, "admin")["Neha Kapoor"]["id"]
    assert client.delete(f"{API}/staff/{admin}").status_code == 409  # the last admin stays


def test_deleting_a_teacher_unassigns_their_students(client, seeded):
    rohan = _staff(client, "teacher")["Mr. Rohan Mehta"]["id"]
    assert client.delete(f"{API}/staff/{rohan}").status_code == 204
    assert client.get(f"{API}/students", params={"teacher_id": rohan}).json() == []
    ananya = next(s for s in client.get(f"{API}/students").json() if s["name"] == "Ananya Rao")
    assert ananya["teacher_id"] is None


def test_student_assignment_update_and_delete(client, seeded):
    teachers = _staff(client, "teacher")
    priya, rohan = teachers["Ms. Priya Verma"]["id"], teachers["Mr. Rohan Mehta"]["id"]
    admin = _staff(client, "admin")["Neha Kapoor"]["id"]

    bad = client.post(f"{API}/students", json={"name": "A", "email": "a@b.cc", "grade_level": 5, "teacher_id": admin, "password": "Passw0rd!"})
    assert bad.status_code == 422  # admins can't have a class

    student = client.post(
        f"{API}/students", json={"name": "Meera", "email": "meera@b.cc", "grade_level": 6, "teacher_id": priya,
        "password": "Passw0rd!"}
    ).json()
    moved = client.patch(f"{API}/students/{student['id']}", json={"teacher_id": rohan, "grade_level": 7}).json()
    assert moved["teacher_id"] == rohan and moved["grade_level"] == 7 and moved["name"] == "Meera"
    unassigned = client.patch(f"{API}/students/{student['id']}", json={"teacher_id": None}).json()
    assert unassigned["teacher_id"] is None

    # Deleting a student with history removes their submissions too.
    aarav = next(s for s in client.get(f"{API}/students").json() if s["name"] == "Aarav Sharma")
    before = client.get(f"{API}/reports/platform").json()["counts"]["submissions"]
    assert client.delete(f"{API}/students/{aarav['id']}").status_code == 204
    assert client.get(f"{API}/students/{aarav['id']}").status_code == 404
    assert client.get(f"{API}/reports/platform").json()["counts"]["submissions"] == before - 1


def test_class_report_for_a_teacher(client, seeded):
    priya = _staff(client, "teacher")["Ms. Priya Verma"]["id"]
    report = client.get(f"{API}/reports/class", params={"teacher_id": priya}).json()

    assert report["student_count"] == 4
    students = {s["name"]: s for s in report["students"]}
    assert students["Aarav Sharma"]["gap_topics"] == ["Fractions"]
    assert students["Diya Patel"]["gap_topics"] == []
    assert students["Demo Student"]["overall_mastery"] is None
    assert students["Demo Student"]["submissions"] == 0
    assert len(students["Kabir Singh"]["topics"]) == 3
    assert report["students_with_gaps"] == sum(1 for s in report["students"] if s["gap_topics"])

    topics = {t["topic_name"]: t for t in report["topics"]}
    assert topics["Fractions"]["assessed_students"] == 3  # the demo student hasn't taken a quiz
    assert topics["Fractions"]["students_with_gap"] >= 1


def test_class_report_without_teacher_covers_everyone(client, seeded):
    report = client.get(f"{API}/reports/class").json()
    assert report["student_count"] == 6
    assert client.get(f"{API}/reports/class", params={"teacher_id": 999}).status_code == 404


def test_platform_report(client, seeded):
    report = client.get(f"{API}/reports/platform").json()
    counts = report["counts"]
    assert (counts["students"], counts["teachers"], counts["admins"], counts["topics"]) == (6, 2, 1, 3)
    assert counts["validated_questions"] == 12
    assert counts["submissions"] == 5
    assert 0 < report["average_score"] <= 100
    assert all(t["question_count"] == 4 and t["content_count"] == 1 for t in report["topics"])
    assert {a["kind"] for a in report["recent_activity"]} == {"assessment"}
