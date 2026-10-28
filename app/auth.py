"""Authentication and role-based access control (RBAC) dependencies.

Roles:
* ``admin``: everything, including user and class management.
* ``teacher``: their own class's students, reports and homework, plus content tools.
* ``student``: only their own data, quizzes and homework.
"""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import Student
from app.routers.common import get_or_404
from app.security import decode_token

ROLES = ("admin", "teacher", "student")
STAFF_ROLES = ("admin", "teacher")

_bearer = HTTPBearer(auto_error=False, description="Session token from POST /api/v1/auth/login")


@dataclass(frozen=True)
class Principal:
    id: int
    role: str
    name: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> Principal:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Not signed in", headers={"WWW-Authenticate": "Bearer"}
    )
    if credentials is None:
        raise unauthorized
    claims = decode_token(credentials.credentials, settings.secret_key)
    if claims is None or claims.get("role") not in ROLES:
        unauthorized.detail = "Session is invalid or has expired"
        raise unauthorized
    return Principal(id=int(claims["sub"]), role=claims["role"], name=claims.get("name", ""))


def require_roles(*roles: str):
    """Dependency factory: allow only the given roles."""

    def dependency(user: Principal = Depends(get_current_user)) -> Principal:
        if user.role not in roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, f"This action requires the {' or '.join(roles)} role"
            )
        return user

    return dependency


def ensure_can_submit(user: Principal, student_id: int) -> None:
    """Answers are submitted by the student themself (admins may submit for support/testing)."""
    if user.role == "admin" or (user.role == "student" and user.id == student_id):
        return
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the student can submit their own answers")


def ensure_student_access(db: Session, user: Principal, student_id: int) -> Student:
    """Admins see every student, teachers only their own class, students only themselves."""
    if user.role == "student" and user.id != student_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Students can only access their own data")
    student = get_or_404(db, Student, student_id)
    if user.role == "teacher" and student.teacher_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This student is not in your class")
    return student
