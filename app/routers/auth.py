from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Principal, get_current_user
from app.config import Settings, get_settings
from app.database import get_db
from app.models import Staff, Student
from app.schemas import LoginRequest, LoginResponse, UserInfo
from app.security import create_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _find_user(db: Session, role: str, email: str) -> Staff | Student | None:
    if role == "student":
        return db.scalar(select(Student).where(Student.email == email))
    return db.scalar(select(Staff).where(Staff.email == email, Staff.role == role))


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Sign in as a student, teacher or admin and receive a bearer token."""
    user = _find_user(db, payload.role, payload.email.strip().lower())
    # Same message whether the email or the password is wrong, so accounts can't be probed.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password for this role")
    ttl = settings.session_hours * 3600
    token = create_token({"sub": user.id, "role": payload.role, "name": user.name}, settings.secret_key, ttl)
    return LoginResponse(
        access_token=token,
        expires_in=ttl,
        user=UserInfo(id=user.id, name=user.name, email=user.email, role=payload.role),
    )


@router.get("/me", response_model=UserInfo)
def me(user: Principal = Depends(get_current_user), db: Session = Depends(get_db)):
    """The signed-in user. Fails if the account was deleted after the token was issued."""
    record = db.get(Student if user.role == "student" else Staff, user.id)
    if record is None or (user.role != "student" and record.role != user.role):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "This account no longer exists")
    return UserInfo(id=record.id, name=record.name, email=record.email, role=user.role)
