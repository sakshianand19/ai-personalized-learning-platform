import hmac

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Principal, get_current_user
from app.config import Settings, get_settings
from app.database import get_db
from app.models import Staff, Student
from app.routers.common import ensure_email_available
from app.schemas import LoginRequest, LoginResponse, SignupRequest, UserInfo
from app.security import create_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# Verified against when an email is unknown, so a miss takes as long as a wrong password.
_TIMING_DECOY_HASH = hash_password("timing-decoy-password")


def _find_account(db: Session, email: str) -> tuple[Staff | Student, str] | None:
    staff = db.scalar(select(Staff).where(Staff.email == email))
    if staff is not None:
        return staff, staff.role
    student = db.scalar(select(Student).where(Student.email == email))
    if student is not None:
        return student, "student"
    return None


def _user_info(user: Staff | Student, role: str) -> UserInfo:
    return UserInfo(
        id=user.id, name=user.name, email=user.email, role=role, subject=getattr(user, "subject", "")
    )


def _session(user: Staff | Student, role: str, settings: Settings) -> LoginResponse:
    ttl = settings.session_hours * 3600
    token = create_token({"sub": user.id, "role": role, "name": user.name}, settings.secret_key, ttl)
    return LoginResponse(access_token=token, expires_in=ttl, user=_user_info(user, role))


def _check_admin_invite(code: str | None, settings: Settings) -> None:
    if not settings.admin_signup_enabled:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin sign-up is not available")
    # Constant-time comparison so the code can't be guessed character by character.
    if not code or not hmac.compare_digest(code.strip().encode(), settings.admin_invite_code.encode()):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid admin invite code")


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Sign in with email and password. The account's role decides what the user can access."""
    found = _find_account(db, payload.email.strip().lower())
    if found is None:
        verify_password(payload.password, _TIMING_DECOY_HASH)
    # Same message whether the email or the password is wrong, so accounts can't be probed.
    if found is None or not verify_password(payload.password, found[0].password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    user, role = found
    return _session(user, role, settings)


@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Create an account with the chosen role and sign it in.

    Students start without a teacher; an admin assigns them to a class. Admin accounts need the
    ``ADMIN_INVITE_CODE``; without one configured, admin sign-up is switched off.
    """
    if payload.role == "admin":
        _check_admin_invite(payload.invite_code, settings)
    email = payload.email.strip().lower()
    ensure_email_available(db, email)
    password_hash = hash_password(payload.password)
    if payload.role == "student":
        user = Student(
            name=payload.name.strip(),
            email=email,
            grade_level=payload.grade_level,
            password_hash=password_hash,
        )
    else:
        user = Staff(
            name=payload.name.strip(),
            email=email,
            role=payload.role,
            subject=payload.subject.strip() if payload.role == "teacher" else "",
            password_hash=password_hash,
        )
    db.add(user)
    db.commit()
    return _session(user, payload.role, settings)


@router.get("/me", response_model=UserInfo)
def me(user: Principal = Depends(get_current_user), db: Session = Depends(get_db)):
    """The signed-in user. Fails if the account was deleted after the token was issued."""
    record = db.get(Student if user.role == "student" else Staff, user.id)
    if record is None or (user.role != "student" and record.role != user.role):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "This account no longer exists")
    return _user_info(record, user.role)
