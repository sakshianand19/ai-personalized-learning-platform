from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Topic
from app.schemas import TopicCreate, TopicRead

router = APIRouter(prefix="/topics", tags=["topics"])


@router.post("", response_model=TopicRead, status_code=status.HTTP_201_CREATED)
def create_topic(payload: TopicCreate, db: Session = Depends(get_db)):
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
def list_topics(subject: str | None = None, db: Session = Depends(get_db)):
    query = select(Topic).order_by(Topic.subject, Topic.name)
    if subject:
        query = query.where(Topic.subject == subject)
    return db.scalars(query).all()
