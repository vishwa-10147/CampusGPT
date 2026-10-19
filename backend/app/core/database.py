# ==============================================================================
# CampusGPT Backend — Database Connection
# ==============================================================================
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.models.base import Base


# ------------------------------------------------------------------------------
# Engine & Session Factory
# ------------------------------------------------------------------------------
engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    poolclass=NullPool if settings.is_development else None,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ------------------------------------------------------------------------------
# Dependency for FastAPI
# ------------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ------------------------------------------------------------------------------
# Lifecycle Management
# ------------------------------------------------------------------------------
async def init_db() -> None:
    """Initialize database - create tables and pgvector extension."""
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()


@asynccontextmanager
async def lifespan_db():
    """Context manager for database lifecycle (useful for scripts/tests)."""
    await init_db()
    try:
        yield
    finally:
        await close_db()