# ==============================================================================
# CampusGPT Backend — MGIT Ingestion Script
# ==============================================================================
"""Run this script to scrape MGIT website and ingest into RAG."""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import init_db, close_db, async_session_maker
from app.ingestion.ingestion_service import run_mgit_ingestion


async def main():
    """Main ingestion entry point."""
    print("=" * 60)
    print("CampusGPT — MGIT Website Ingestion")
    print("=" * 60)

    # Initialize database
    await init_db()

    async with async_session_maker() as session:
        try:
            result = await run_mgit_ingestion(session)
            print("\n" + "=" * 60)
            print("INGESTION RESULT:")
            print("=" * 60)
            for key, value in result.items():
                print(f"  {key}: {value}")

            if result.get("status") == "success":
                print("\n✅ Ingestion completed successfully!")
                print(f"   Pages scraped: {result['pages_scraped']}")
                print(f"   Documents ingested: {result['documents_ingested']}")
            else:
                print(f"\n⚠️  Ingestion status: {result.get('status')}")
                print(f"   Message: {result.get('message')}")

        except Exception as e:
            print(f"\n❌ Ingestion failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await close_db()


if __name__ == "__main__":
    asyncio.run(main())