"""Login and role-based access control.

Seeded ids: staff 1 = admin, 2 = Ms. Priya Verma, 3 = Mr. Rohan Mehta.
Students 1-4 are in Priya's class (1 = Demo Student, 2 = Aarav), 5-6 in Rohan's.
"""

import time

import pytest

from app.config import get_settings
from app.security import create_token, decode_token, hash_password, verify_password

API = "/api/v1"
ADMIN, PRIYA, ROHAN = 1, 2, 3
DEMO, AARAV, ANANYA = 1, 2, 5


# --- Password hashing and tokens ------------------------------------------------


def test_password_hashing():
    stored = hash_password("Secret123!")
    assert stored.startswith("pbkdf2_sha256$") and "Secret123!" not in stored
    assert verify_password("Secret123!", stored)
    assert not verify_password("secret123!", stored)
    assert not verify_password("anything", "not-a-hash")
    assert hash_password("same") != hash_password("same")  # random salt


def test_tokens_reject_tampering_and_expiry():
    secret = "s3cret"
    token = create_token({"sub": 7, "role": "student"}, secret, 60)
    assert decode_token(token, secret)["sub"] == 7
    assert decode_token(token, "other-secret") is None

    payload, signature = token.split(".")
    forged = create_token({"sub": 7, "role": "admin"}, "attacker", 60).split(".")[0]
    assert decode_token(f"{forged}.{signature}", secret) is None
    assert decode_token("garbage", secret) is None

    expired = create_token({"sub": 7, "role": "student"}, secret, -1)
    assert decode_token(expired, secret) is None


# --- Login --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("role", "email", "password", "name"),
    [
        ("admin", "admin@learnpath.example", "Admin@123", "Neha Kapoor"),
        ("teacher", "priya.verma@learnpath.example", "Teacher@123", "Ms. Priya Verma"),
        ("student", "Aarav@Student.example", "Student@123", "Aarav Sharma"),
    ],
)
def test_login_for_each_role(anonymous_client, seeded, role, email, password, name):
    response = anonymous_client.post(f"{API}/auth/login", json={"email": email, "password": password, "role": role})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["role"] == role and body["user"]["name"] == name
    assert body["expires_in"] == get_settings().session_hours * 3600

    me = anonymous_client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.json()["name"] == name


@pytest.mark.parametrize(
    ("email", "password", "role"),
    [
        ("admin@learnpath.example", "wrong-password", "admin"),
        ("nobody@learnpath.example", "Admin@123", "admin"),
        ("priya.verma@learnpath.example", "Teacher@123", "admin"),  # right password, wrong role
        ("aarav@student.example", "Student@123", "teacher"),
    ],
)
def test_login_rejects_bad_credentials(anonymous_client, seeded, email, password, role):
    response = anonymous_client.post(f"{API}/auth/login", json={"email": email, "password": password, "role": role})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password for this role"


def test_new_accounts_can_log_in_and_never_expose_passwords(client, anonymous_client, seeded):
    created = client.post(
        f"{API}/students",
        json={"name": "Meera", "email": "meera@school.example", "grade_level": 6, "password": "Welcome@1"},
    ).json()
    assert "password" not in created and "password_hash" not in created
    login = anonymous_client.post(
        f"{API}/auth/login", json={"email": "meera@school.example", "password": "Welcome@1", "role": "student"}
    )
    assert login.status_code == 200

    short = client.post(f"{API}/staff", json={"name": "T", "email": "t@school.example", "role": "teacher", "password": "short"})
    assert short.status_code == 422


def test_deleted_account_session_is_rejected(client, as_user, seeded):
    client.delete(f"{API}/students/{AARAV}")
    assert as_user("student", AARAV).get(f"{API}/auth/me").status_code == 401


# --- Authentication is required ----------------------------------------------------


@pytest.mark.parametrize(
    "path", ["/students", "/topics", "/questions", "/staff", "/reports/platform", "/students/1/learning-gaps"]
)
def test_api_requires_a_session(anonymous_client, seeded, path):
    assert anonymous_client.get(f"{API}{path}").status_code == 401


def test_invalid_and_expired_tokens_are_rejected(anonymous_client, seeded):
    secret = get_settings().secret_key
    for token in ["nonsense", create_token({"sub": 1, "role": "admin"}, "wrong-key", 60),
                  create_token({"sub": 1, "role": "admin"}, secret, -5),
                  create_token({"sub": 1, "role": "superuser"}, secret, 60)]:
        response = anonymous_client.get(f"{API}/students", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401, token


def test_public_pages_stay_open(anonymous_client):
    assert anonymous_client.get("/health").status_code == 200
    assert anonymous_client.get("/").status_code == 200


# --- Student role -------------------------------------------------------------------


def test_student_sees_only_their_own_data(as_user, seeded):
    student = as_user("student", AARAV)
    assert student.get(f"{API}/students/{AARAV}/learning-gaps").status_code == 200
    assert student.get(f"{API}/students/{AARAV}/submissions").status_code == 200
    for path in [f"/students/{DEMO}", f"/students/{DEMO}/learning-gaps", f"/homework?student_id={DEMO}"]:
        assert student.get(f"{API}{path}").status_code == 403, path


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("get", "/students", None),
        ("get", "/questions", None),  # the question bank contains answer keys
        ("get", "/staff", None),
        ("get", "/reports/class", None),
        ("get", "/reports/platform", None),
        ("post", "/topics", {"subject": "X", "name": "Y"}),
        ("post", "/questions/validate", {"text": "Which is right?", "options": ["a", "b"], "correct_answer": "a"}),
        ("delete", "/students/3", None),
    ],
)
def test_student_cannot_use_staff_features(as_user, seeded, method, path, body):
    response = getattr(as_user("student", AARAV), method)(f"{API}{path}", **({"json": body} if body else {}))
    assert response.status_code == 403


def test_student_quiz_flow_and_submission_rules(as_user, seeded):
    student = as_user("student", AARAV)
    topics = student.get(f"{API}/topics").json()
    assert all(t["question_count"] == 4 for t in topics)  # counts, never answer keys

    assessment = student.post(f"{API}/assessments", json={"title": "Practice", "topic_ids": [topics[0]["id"]]}).json()
    assert "correct_answer" not in assessment["questions"][0]
    answers = [{"question_id": q["id"], "answer": q["options"][0]} for q in assessment["questions"]]

    ok = student.post(f"{API}/assessments/{assessment['id']}/submit", json={"student_id": AARAV, "answers": answers})
    assert ok.status_code == 200
    as_someone_else = student.post(f"{API}/assessments/{assessment['id']}/submit", json={"student_id": DEMO, "answers": answers})
    assert as_someone_else.status_code == 403

    homework = student.post(f"{API}/homework/generate", json={"student_id": AARAV}).json()
    assert student.get(f"{API}/homework/{homework['id']}").status_code == 200
    assert student.post(f"{API}/homework/generate", json={"student_id": DEMO}).status_code == 403


# --- Teacher role -------------------------------------------------------------------


def test_teacher_is_limited_to_their_class(as_user, seeded):
    teacher = as_user("teacher", PRIYA)

    roster = teacher.get(f"{API}/students").json()
    assert {s["id"] for s in roster} == {1, 2, 3, 4}
    # Asking for another teacher's roster still only returns their own class.
    assert {s["id"] for s in teacher.get(f"{API}/students", params={"teacher_id": ROHAN}).json()} == {1, 2, 3, 4}

    assert teacher.get(f"{API}/students/{AARAV}/learning-gaps").status_code == 200
    assert teacher.get(f"{API}/students/{ANANYA}/learning-gaps").status_code == 403
    assert teacher.post(f"{API}/homework/generate", json={"student_id": AARAV}).status_code == 201
    assert teacher.post(f"{API}/homework/generate", json={"student_id": ANANYA}).status_code == 403

    assert teacher.get(f"{API}/reports/class").json()["student_count"] == 4
    assert teacher.get(f"{API}/reports/class", params={"teacher_id": ROHAN}).status_code == 403
    assert teacher.get(f"{API}/questions").status_code == 200


def test_teacher_cannot_manage_users_or_submit_answers(as_user, seeded):
    teacher = as_user("teacher", PRIYA)
    assert teacher.get(f"{API}/staff").status_code == 403
    assert teacher.get(f"{API}/reports/platform").status_code == 403
    assert teacher.delete(f"{API}/students/{AARAV}").status_code == 403
    assert teacher.patch(f"{API}/students/{AARAV}", json={"teacher_id": ROHAN}).status_code == 403
    new_student = {"name": "X", "email": "x@school.example", "grade_level": 5, "password": "Passw0rd!"}
    assert teacher.post(f"{API}/students", json=new_student).status_code == 403

    homework = teacher.post(f"{API}/homework/generate", json={"student_id": AARAV}).json()
    answers = {"answers": [{"question_id": homework["questions"][0]["id"], "answer": "x"}]}
    assert teacher.post(f"{API}/homework/{homework['id']}/submit", json=answers).status_code == 403


# --- Admin role ---------------------------------------------------------------------


def test_admin_can_see_any_class_and_manage_users(as_user, seeded):
    admin = as_user("admin", ADMIN)
    assert admin.get(f"{API}/reports/class", params={"teacher_id": ROHAN}).json()["student_count"] == 2
    assert admin.get(f"{API}/reports/platform").status_code == 200
    assert admin.patch(f"{API}/students/{ANANYA}", json={"teacher_id": PRIYA}).json()["teacher_id"] == PRIYA
    assert admin.get(f"{API}/staff").status_code == 200


def test_session_expiry_is_configured():
    assert get_settings().session_hours > 0
    token = create_token({"sub": 1, "role": "admin"}, "k", 1)
    time.sleep(1.1)
    assert decode_token(token, "k") is None
