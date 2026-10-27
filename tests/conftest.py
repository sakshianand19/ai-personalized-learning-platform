import os

# Configure before the app (and its engine) is imported. Explicit empty Azure values
# also override anything in a local .env, so tests never call a real model.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SEED_DEMO_DATA"] = "false"
for key in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT"):
    os.environ[key] = ""

import json  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from langchain_core.language_models.fake_chat_models import FakeListChatModel  # noqa: E402

from app.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.seed import seed_demo_data  # noqa: E402
from app.services.llm import get_llm  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def seeded(db):
    seed_demo_data(db)
    return db


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def fake_llm(*responses: dict | str) -> FakeListChatModel:
    """A LangChain chat model that replays canned (JSON) responses in order."""
    return FakeListChatModel(
        responses=[r if isinstance(r, str) else json.dumps(r) for r in responses]
    )


@pytest.fixture
def use_llm():
    """Route the API's ``get_llm`` dependency to a fake model built from canned responses."""

    def _install(*responses: dict | str) -> FakeListChatModel:
        model = fake_llm(*responses)
        app.dependency_overrides[get_llm] = lambda: model
        return model

    return _install
