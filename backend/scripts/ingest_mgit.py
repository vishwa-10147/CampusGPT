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
from app.ingestion.mgit_scraper import MGITScraper
from app.ingestion.base_scraper import ScrapedDocument
from app.core.config import settings


async def main():
    """Main ingestion entry point."""
    print("=" * 60)
    print("CampusGPT — MGIT Website Ingestion")
    print("=" * 60)

    # Initialize database
    await init_db()

    # Step 1: Scrape and save raw data
    print("\n📥 Step 1: Scraping MGIT website...")
    async with MGITScraper(
        base_url=settings.mgit_base_url,
        delay_seconds=settings.mgit_scrape_delay_seconds,
        max_pages=settings.mgit_max_pages,
        allowed_paths=settings.mgit_allowed_paths.split(",") if settings.mgit_allowed_paths else [],
        respect_robots=settings.scraper_respect_robots_txt,
    ) as scraper:
        documents = await scraper.scrape(settings.mgit_base_url)

    print(f"Scraped {len(documents)} pages from MGIT")

    # Save scraped data to disk
    if documents:
        scraper.save_documents(documents, "data/scraped/mgit")
        print(f"💾 Saved {len(documents)} scraped documents to data/scraped/mgit/")

    if not documents:
        print("⚠️ No content extracted from MGIT")
        await close_db()
        return {"status": "no_content", "message": "No content extracted from MGIT", "pages_scraped": 0, "documents_ingested": 0}

    # Step 2: Ingest into RAG
    print("\n📥 Step 2: Ingesting into RAG...")
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