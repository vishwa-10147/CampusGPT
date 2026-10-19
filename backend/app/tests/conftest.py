# ==============================================================================
# CampusGPT Backend — Test Configuration
# ==============================================================================
import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.core.config import settings


# Tests create and drop every table, so they must never touch the dev database.
# Default: the dev URL with "_test" appended to the database name.
_main_url = make_url(settings.database_url)
TEST_DATABASE_URL = make_url(
    os.environ.get("TEST_DATABASE_URL")
    or _main_url.set(database=f"{_main_url.database}_test").render_as_string(hide_password=False)
)
if TEST_DATABASE_URL.database == _main_url.database:
    raise RuntimeError("TEST_DATABASE_URL points at the main database; refusing to run tests against it")

# Most tests hit auth endpoints far faster than the real limit allows, and
# sign in straight after registering; the dedicated tests turn these back on.
settings.rate_limit_enabled = False
settings.require_email_verification = False


async def _ensure_test_database() -> None:
    """Create the test database if it doesn't exist yet."""
    admin_engine = create_async_engine(
        TEST_DATABASE_URL.set(database="postgres"), poolclass=NullPool, isolation_level="AUTOCOMMIT"
    )
    async with admin_engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DATABASE_URL.database}
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{TEST_DATABASE_URL.database}"'))
    await admin_engine.dispose()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def test_engine():
    """Create test database engine."""
    await _ensure_test_database()
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Start clean even if an earlier run was interrupted before teardown
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncSession:
    """Create a test database session with transaction rollback."""
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(test_session) -> AsyncClient:
    """Create test client with overridden database dependency."""
    def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# Test utilities
@pytest.fixture
def sample_user_data():
    return {
        "email": "test@college.edu",
        "password": "securepassword123",
        "password_confirm": "securepassword123",
        "full_name": "Test User",
    }


@pytest.fixture
def sample_admin_data():
    return {
        "email": "admin@college.edu",
        "password": "adminpassword123",
        "password_confirm": "adminpassword123",
        "full_name": "Admin User",
    }

# ------------------------------------------------------------------------------
# Signed-in clients
# ------------------------------------------------------------------------------
@pytest_asyncio.fixture
async def make_client(test_session):
    """Factory for clients signed in as a fresh user: `await make_client(admin=True)`."""
    from uuid import uuid4
    from app.repositories.user_repo import UserRepository

    def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db
    clients = []

    async def factory(*, admin: bool = False) -> AsyncClient:
        email = f"user-{uuid4().hex[:10]}@college.edu"
        password = "securepassword123"
        ac = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        clients.append(ac)
        response = await ac.post("/api/v1/auth/register", json={
            "email": email, "password": password, "password_confirm": password, "full_name": "Test User",
        })
        assert response.status_code == 201, response.text
        if admin:
            user = await UserRepository(test_session).get_by_email(email)
            user.is_admin = True
            await test_session.commit()
        response = await ac.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        ac.user_id = (await ac.get("/api/v1/auth/me")).json()["id"]
        return ac

    yield factory
    for ac in clients:
        await ac.aclose()
    app.dependency_overrides.clear()


# ------------------------------------------------------------------------------
# Fake AI providers (deterministic, no Ollama needed)
# ------------------------------------------------------------------------------
def fake_embedding(text_value: str) -> list[float]:
    """Bag-of-words vector: texts sharing words point in similar directions."""
    import math
    import re
    import zlib

    vector = [0.0] * settings.embedding_dimension
    for word in re.findall(r"[a-z]+", text_value.lower()):
        vector[zlib.crc32(word.encode()) % len(vector)] += 1.0
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector] if any(vector) else [1.0] + [0.0] * (len(vector) - 1)


class FakeEmbeddingService:
    dimension = settings.embedding_dimension

    async def embed(self, texts, model=None):
        from app.ai.base import EmbeddingResponse
        return EmbeddingResponse(embeddings=[fake_embedding(t) for t in texts], tokens_used=0, model="fake")

    async def embed_single(self, text_value, model=None):
        return fake_embedding(text_value)


class FakeLLM:
    """Answers with a fixed sentence and records the prompts it was given."""
    reply = "Here is what the sources say [1]."

    def __init__(self):
        self.prompts = []

    async def chat(self, messages, model=None, temperature=0.7, max_tokens=None):
        from app.ai.base import ChatResponse
        self.prompts.append(messages[-1].content)
        return ChatResponse(content=self.reply, tokens_used=42, model="fake")

    async def chat_stream(self, messages, model=None, temperature=0.7, max_tokens=None):
        from app.ai.base import StreamChunk
        self.prompts.append(messages[-1].content)
        for word in self.reply.split(" "):
            yield StreamChunk(content=word + " ", done=False)
        yield StreamChunk(content="", done=True, tokens_used=42)


@pytest.fixture
def fake_ai(monkeypatch, test_engine, tmp_path):
    """Swap in fake embedding/LLM providers and run background processing on the test DB."""
    from app.api.v1 import documents as documents_routes
    from app.services import file_service, rag_service

    llm = FakeLLM()
    embeddings = FakeEmbeddingService()
    monkeypatch.setattr(rag_service, "get_llm_service", lambda: llm)
    monkeypatch.setattr(rag_service, "get_embedding_service", lambda: embeddings)
    monkeypatch.setattr(file_service, "get_embedding_service", lambda: embeddings)
    monkeypatch.setattr(
        documents_routes,
        "async_session_maker",
        async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False),
    )
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    # Bag-of-words vectors score lower than real embeddings
    monkeypatch.setattr(settings, "similarity_threshold", 0.1)
    return llm
