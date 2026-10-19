# ==============================================================================
# CampusGPT Backend — Ingestion Package
# ==============================================================================
from app.ingestion.base_scraper import BaseScraper, ScrapedDocument, RobotsTxtParser
from app.ingestion.mgit_scraper import MGITScraper
from app.ingestion.ingestion_service import IngestionService, run_mgit_ingestion

__all__ = [
    "BaseScraper",
    "ScrapedDocument",
    "RobotsTxtParser",
    "MGITScraper",
    "IngestionService",
    "run_mgit_ingestion",
]