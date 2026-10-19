# ==============================================================================
# CampusGPT Backend — Test Configuration
# ==============================================================================
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.core.config import settings


# Use the main database for tests (in dev environment)
# In production, you'd want a separate test database
TEST_DATABASE_URL = settings.database_url


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
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