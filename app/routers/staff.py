from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.database import get_db
from app.models import Staff
from app.routers.common import ensure_email_available, get_or_404
from app.schemas import Role, StaffCreate, StaffRead
from app.security import hash_password

# Managing staff accounts is an admin-only capability.
router = APIRouter(prefix="/staff", tags=["staff"], dependencies=[Depends(require_roles("admin"))])


@router.post("", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
def create_staff(payload: StaffCreate, db: Session = Depends(get_db)):
    email = payload.email.lower()
    ensure_email_available(db, email)
    member = Staff(
        **payload.model_dump(exclude={"password"}) | {"email": email},
        password_hash=hash_password(payload.password),
    )
    db.add(member)
    db.commit()
    return member


@router.get("", response_model=list[StaffRead])
def list_staff(role: Role | None = None, db: Session = Depends(get_db)):
    query = select(Staff).order_by(Staff.role, Staff.id)
    if role:
        query = query.where(Staff.role == role)
    return db.scalars(query).all()


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff(staff_id: int, db: Session = Depends(get_db)):
    """Remove a staff member. A teacher's students stay, unassigned."""
    member = get_or_404(db, Staff, staff_id)
    if member.role == "admin" and db.scalar(
        select(Staff.id).where(Staff.role == "admin", Staff.id != staff_id).limit(1)
    ) is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cannot remove the last admin")
    db.delete(member)
    db.commit()
