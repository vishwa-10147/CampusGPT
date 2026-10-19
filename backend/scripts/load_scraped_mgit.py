# ==============================================================================
# CampusGPT Backend — Load Saved MGIT Pages
# ==============================================================================
"""Load already-scraped MGIT pages (data/scraped/mgit/*.json) into the knowledge base.

Unlike ingest_mgit.py this never contacts the website. Repeated scrape runs leave
several files per URL, so only the newest copy of each page is loaded. Pages that
are already in the database are skipped, so the script is safe to re-run; pass
--replace to delete and re-ingest them (e.g. after changing the chunker).

    docker compose exec backend python scripts/load_scraped_mgit.py [--replace]
"""
import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.database import async_session_maker, close_db, init_db
from app.ingestion.base_scraper import ScrapedDocument
from app.ingestion.boilerplate import find_boilerplate_lines, strip_boilerplate
from app.ingestion.ingestion_service import IngestionService, scraped_filename
from app.models.document import Document

SCRAPED_DIR = Path(__file__).parent.parent / "data" / "scraped" / "mgit"
SOURCE_NAME = "mgit"


def load_latest_pages(directory: Path) -> list[ScrapedDocument]:
    """Read every saved page, keeping the most recent scrape of each URL."""
    latest: dict[str, dict] = {}
    for path in sorted(directory.glob("*.json")):
        if path.name.endswith("_index.json"):
            continue
        page = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(page, dict) or not page.get("url") or not page.get("content", "").strip():
            continue
        # "https://mgit.ac.in" and "https://mgit.ac.in/" are the same page
        if not page["url"].endswith("/"):
            page["url"] += "/"
        current = latest.get(page["url"])
        if current is None or page.get("scraped_at", "") > current.get("scraped_at", ""):
            latest[page["url"]] = page

    # Sidebars and menus repeat on most pages; drop them so chunks hold page content
    boilerplate = find_boilerplate_lines(page["content"] for page in latest.values())

    return [
        ScrapedDocument(
            url=page["url"],
            title=page.get("title") or page["url"],
            content=strip_boilerplate(page["content"], boilerplate, page.get("title", "")),
            scraped_at=datetime.fromisoformat(page["scraped_at"]) if page.get("scraped_at") else datetime.utcnow(),
            source_type=page.get("source_type", "web"),
        )
        for page in latest.values()
    ]


async def main(replace: bool) -> None:
    pages = [page for page in load_latest_pages(SCRAPED_DIR) if page.content.strip()]
    print(f"Found {len(pages)} unique pages in {SCRAPED_DIR}")

    await init_db()
    loaded = skipped = failed = 0
    try:
        async with async_session_maker() as session:
            service = IngestionService(session)
            for number, page in enumerate(pages, 1):
                filename = scraped_filename(SOURCE_NAME, page.url)
                existing = await session.scalar(select(Document).where(Document.filename == filename))
                if existing and not replace:
                    skipped += 1
                    continue
                if existing:
                    await session.delete(existing)
                    await session.commit()

                docs = await service.ingest_scraped_documents([page], SOURCE_NAME)
                ok = bool(docs) and docs[0].status == "ready"
                loaded += ok
                failed += not ok
                print(f"[{number}/{len(pages)}] {'ok  ' if ok else 'FAIL'} {page.url}")
    finally:
        await close_db()

    print(f"\nDone: {loaded} loaded, {skipped} already present, {failed} failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--replace", action="store_true", help="re-ingest pages that are already loaded")
    asyncio.run(main(parser.parse_args().replace))
