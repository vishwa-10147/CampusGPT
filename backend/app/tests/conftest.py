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

# Most tests hit auth endpoints far faster than the real limit allows
settings.rate_limit_enabled = False


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