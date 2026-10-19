# ==============================================================================
# CampusGPT Backend — Apply Database Migrations
# ==============================================================================
"""Bring the database schema up to date (run before starting the API).

Databases created before migrations existed were built with create_all and
have tables but no alembic_version table. Those are stamped at the baseline
revision (0001) first, so the later migrations apply on top of them instead
of trying to recreate existing tables.

    python scripts/migrate.py
"""
import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

BASELINE_REVISION = "0001"


async def _existing_tables() -> set[str]:
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect() as conn:
            return set(await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names()))
    finally:
        await engine.dispose()


def main() -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))

    tables = asyncio.run(_existing_tables())
    if "users" in tables and "alembic_version" not in tables:
        print(f"Existing schema without migration history: stamping at {BASELINE_REVISION}")
        command.stamp(config, BASELINE_REVISION)

    command.upgrade(config, "head")
    print("Database schema is up to date")


if __name__ == "__main__":
    main()
