import os

# Configure before the app (and its engine) is imported. Explicit empty Azure values
# also override anything in a local .env, so tests never call a real model.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SEED_DEMO_DATA"] = "false"
for key in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT", "ADMIN_INVITE_CODE"):
    os.environ[key] = ""

import json  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from langchain_core.language_models.fake_chat_models import FakeListChatModel  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.database import SessionLocal, engine  # noqa: E402
from app.security import create_token  # noqa: E402
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


def auth_headers(role: str, user_id: int, name: str = "Test user") -> dict[str, str]:
    """Headers for a signed session token, as if that user had logged in."""
    token = create_token({"sub": user_id, "role": role, "name": name}, get_settings().secret_key, 3600)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def anonymous_client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client(anonymous_client):
    """Signed in as an admin, who may call every endpoint; RBAC itself is tested separately."""
    anonymous_client.headers.update(auth_headers("admin", 1, "Test admin"))
    return anonymous_client


ADMIN_INVITE_CODE = "test-admin-invite"


@pytest.fixture
def admin_invites():
    """Enable admin sign-up with ``ADMIN_INVITE_CODE`` (it's off when no code is configured)."""
    settings = get_settings().model_copy(update={"admin_invite_code": ADMIN_INVITE_CODE})
    app.dependency_overrides[get_settings] = lambda: settings
    return ADMIN_INVITE_CODE


@pytest.fixture
def as_user():
    """Build a separate client signed in as a specific role and user id."""
    clients = []

    def _make(role: str, user_id: int) -> TestClient:
        test_client = TestClient(app, headers=auth_headers(role, user_id))
        clients.append(test_client)
        return test_client

    yield _make
    for test_client in clients:
        test_client.close()


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
