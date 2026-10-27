from collections.abc import Iterator

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.models import Base, Topic


def _make_engine(url: str):
    if url.startswith("sqlite"):
        kwargs: dict = {"connect_args": {"check_same_thread": False}}
        if url in ("sqlite://", "sqlite:///:memory:"):
            # Share one in-memory database across connections (used by the test suite).
            kwargs["poolclass"] = StaticPool
        sqlite_engine = create_engine(url, **kwargs)

        @event.listens_for(sqlite_engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record):
            # SQLite ignores ON DELETE CASCADE / SET NULL unless this is switched on.
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

        return sqlite_engine
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5)


engine = _make_engine(get_settings().sqlalchemy_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(seed: bool = False) -> None:
    Base.metadata.create_all(engine)
    if not seed:
        return
    from app.seed import seed_demo_data

    with SessionLocal() as db:
        if db.scalar(select(Topic.id).limit(1)) is None:
            seed_demo_data(db)
