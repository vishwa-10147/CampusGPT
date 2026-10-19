# ==============================================================================
# CampusGPT Backend — Database Initialization Script
# ==============================================================================
"""Run this script to initialize the database with tables and pgvector extension."""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import init_db, close_db


async def main():
    print("Initializing database...")
    try:
        await init_db()
        print("✓ Database initialized successfully")
        print("  - pgvector extension enabled")
        print("  - All tables created")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        sys.exit(1)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())