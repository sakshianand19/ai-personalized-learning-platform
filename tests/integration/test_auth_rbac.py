"""Login and role-based access control.

Seeded ids: staff 1 = admin, 2 = Ms. Priya Verma, 3 = Mr. Rohan Mehta.
Students 1-4 are in Priya's class (1 = Demo Student, 2 = Aarav), 5-6 in Rohan's.
"""

import time

import pytest

from app.config import get_settings
from app.security import create_token, decode_token, hash_password, verify_password
from tests.conftest import ADMIN_INVITE_CODE

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
    ("email", "password", "role", "name"),
    [
        ("admin@learnpath.example", "Admin@123", "admin", "Neha Kapoor"),
        ("priya.verma@learnpath.example", "Teacher@123", "teacher", "Ms. Priya Verma"),
        ("Aarav@Student.example", "Student@123", "student", "Aarav Sharma"),
    ],
)
def test_login_finds_the_role_from_the_account(anonymous_client, seeded, email, password, role, name):
    response = anonymous_client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["role"] == role and body["user"]["name"] == name
    assert body["expires_in"] == get_settings().session_hours * 3600

    me = anonymous_client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.json()["name"] == name


def test_role_cannot_be_chosen_at_login(anonymous_client, seeded):
    # A student asking to be an admin still gets a student session.
    body = anonymous_client.post(
        f"{API}/auth/login", json={"email": "aarav@student.example", "password": "Student@123", "role": "admin"}
    ).json()
    assert body["user"]["role"] == "student"


@pytest.mark.parametrize(
    ("email", "password"),
    [("admin@learnpath.example", "wrong-password"), ("nobody@learnpath.example", "Admin@123")],
)
def test_login_rejects_bad_credentials(anonymous_client, seeded, email, password):
    response = anonymous_client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


# --- Sign-up ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("payload", "role"),
    [
        ({"name": "Riya Sen", "email": "Riya@Mail.example", "role": "student", "grade_level": 9}, "student"),
        ({"name": "Mr. Arjun Das", "email": "arjun@mail.example", "role": "teacher", "subject": "History"}, "teacher"),
        ({"name": "Kiran Rao", "email": "kiran@mail.example", "role": "admin", "invite_code": ADMIN_INVITE_CODE}, "admin"),
    ],
)
def test_signup_creates_an_account_and_signs_it_in(anonymous_client, admin_invites, payload, role):
    response = anonymous_client.post(f"{API}/auth/signup", json=payload | {"password": "Welcome@123"})
    assert response.status_code == 201
    session = response.json()
    assert session["user"]["role"] == role
    assert session["user"]["email"] == payload["email"].lower()
    assert "password" not in str(session["user"])

    headers = {"Authorization": f"Bearer {session['access_token']}"}
    assert anonymous_client.get(f"{API}/auth/me", headers=headers).json()["role"] == role
    login = anonymous_client.post(f"{API}/auth/login", json={"email": payload["email"], "password": "Welcome@123"})
    assert login.json()["user"]["role"] == role


def test_signed_up_users_get_their_roles_permissions(anonymous_client, admin_invites, seeded):
    def signup(**fields):
        body = anonymous_client.post(f"{API}/auth/signup", json=fields | {"password": "Welcome@123"}).json()
        return {"Authorization": f"Bearer {body['access_token']}"}, body["user"]["id"]

    student, student_id = signup(name="Riya", email="riya@mail.example", role="student", grade_level=9)
    teacher, _ = signup(name="Arjun", email="arjun@mail.example", role="teacher")
    admin, _ = signup(name="Kiran", email="kiran@mail.example", role="admin", invite_code=admin_invites)

    assert anonymous_client.get(f"{API}/students/{student_id}/learning-gaps", headers=student).status_code == 200
    assert anonymous_client.get(f"{API}/students", headers=student).status_code == 403
    # A new teacher starts with an empty class and can't see other classes.
    assert anonymous_client.get(f"{API}/students", headers=teacher).json() == []
    assert anonymous_client.get(f"{API}/students/{AARAV}", headers=teacher).status_code == 403
    assert anonymous_client.get(f"{API}/reports/platform", headers=admin).status_code == 200
    # New students start unassigned until an admin places them in a class.
    assert anonymous_client.get(f"{API}/students/{student_id}", headers=admin).json()["teacher_id"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "No grade", "email": "a@mail.example", "role": "student"},
        {"name": "Short pw", "email": "b@mail.example", "role": "teacher", "password": "short"},
        {"name": "Bad role", "email": "c@mail.example", "role": "owner"},
        {"name": "Bad email", "email": "not-an-email", "role": "admin"},
        {"name": "", "email": "d@mail.example", "role": "admin"},
    ],
)
def test_signup_validation(anonymous_client, payload):
    response = anonymous_client.post(f"{API}/auth/signup", json={"password": "Welcome@123"} | payload)
    assert response.status_code == 422


def test_emails_are_unique_across_all_accounts(anonymous_client, client, seeded):
    taken_by_student = {"name": "X", "email": "AARAV@student.example", "role": "teacher", "password": "Welcome@123"}
    assert anonymous_client.post(f"{API}/auth/signup", json=taken_by_student).status_code == 409
    taken_by_staff = {"name": "X", "email": "admin@learnpath.example", "role": "student", "grade_level": 5,
                      "password": "Welcome@123"}
    assert anonymous_client.post(f"{API}/auth/signup", json=taken_by_staff).status_code == 409
    # Admin-created accounts follow the same rule.
    staff_with_student_email = {"name": "X", "email": "diya@student.example", "role": "teacher", "password": "Welcome@123"}
    assert client.post(f"{API}/staff", json=staff_with_student_email).status_code == 409


def test_new_accounts_can_log_in_and_never_expose_passwords(client, anonymous_client, seeded):
    created = client.post(
        f"{API}/students",
        json={"name": "Meera", "email": "meera@school.example", "grade_level": 6, "password": "Welcome@1"},
    ).json()
    assert "password" not in created and "password_hash" not in created
    login = anonymous_client.post(
        f"{API}/auth/login", json={"email": "meera@school.example", "password": "Welcome@1"}
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


# --- Admin invite code ------------------------------------------------------------------

ADMIN_SIGNUP = {"name": "Kiran Rao", "email": "kiran@mail.example", "role": "admin", "password": "Welcome@123"}


def test_admin_signup_is_off_without_a_configured_code(anonymous_client):
    response = anonymous_client.post(f"{API}/auth/signup", json=ADMIN_SIGNUP | {"invite_code": "anything"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin sign-up is not available"
    assert anonymous_client.get("/health").json()["admin_signup"] is False
    # Students and teachers can still sign up.
    teacher = {"name": "T", "email": "t@mail.example", "role": "teacher", "password": "Welcome@123"}
    assert anonymous_client.post(f"{API}/auth/signup", json=teacher).status_code == 201


@pytest.mark.parametrize("code", [None, "", "wrong-code", ADMIN_INVITE_CODE + "x", ADMIN_INVITE_CODE.upper()])
def test_admin_signup_rejects_missing_or_wrong_codes(anonymous_client, admin_invites, code):
    payload = ADMIN_SIGNUP | ({"invite_code": code} if code is not None else {})
    response = anonymous_client.post(f"{API}/auth/signup", json=payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid admin invite code"
    # No account was created.
    login = anonymous_client.post(f"{API}/auth/login", json={"email": ADMIN_SIGNUP["email"], "password": "Welcome@123"})
    assert login.status_code == 401


def test_admin_signup_with_the_right_code(anonymous_client, admin_invites):
    response = anonymous_client.post(f"{API}/auth/signup", json=ADMIN_SIGNUP | {"invite_code": f"  {admin_invites} "})
    assert response.status_code == 201
    assert response.json()["user"]["role"] == "admin"


def test_invite_code_is_ignored_for_other_roles(anonymous_client):
    student = {"name": "S", "email": "s@mail.example", "role": "student", "grade_level": 5,
               "password": "Welcome@123", "invite_code": "irrelevant"}
    assert anonymous_client.post(f"{API}/auth/signup", json=student).status_code == 201
