from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import Principal, get_current_user, require_roles
from app.database import get_db
from app.models import Question, Topic
from app.schemas import TopicCreate, TopicRead

router = APIRouter(prefix="/topics", tags=["topics"])


@router.post("", response_model=TopicRead, status_code=status.HTTP_201_CREATED)
def create_topic(
    payload: TopicCreate,
    db: Session = Depends(get_db),
    _: Principal = Depends(require_roles("admin", "teacher")),
):
    duplicate = db.scalar(
        select(Topic.id).where(Topic.subject == payload.subject, Topic.name == payload.name)
    )
    if duplicate:
        raise HTTPException(status.HTTP_409_CONFLICT, "Topic already exists for this subject")
    topic = Topic(**payload.model_dump())
    db.add(topic)
    db.commit()
    return topic


@router.get("", response_model=list[TopicRead])
def list_topics(
    subject: str | None = None,
    db: Session = Depends(get_db),
    _: Principal = Depends(get_current_user),
):
    query = select(Topic).order_by(Topic.subject, Topic.name)
    if subject:
        query = query.where(Topic.subject == subject)
    # Question counts let students build quizzes without ever seeing the answer keys.
    counts = dict(
        db.execute(
            select(Question.topic_id, func.count())
            .where(Question.is_validated.is_(True))
            .group_by(Question.topic_id)
        ).all()
    )
    return [
        TopicRead.model_validate(t).model_copy(update={"question_count": counts.get(t.id, 0)})
        for t in db.scalars(query)
    ]
