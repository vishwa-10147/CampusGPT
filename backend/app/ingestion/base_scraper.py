# ==============================================================================
# CampusGPT Backend — Base Scraper
# ==============================================================================
import asyncio
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl

from app.core.config import settings


@dataclass
class ScrapedDocument:
    """A document scraped from a website."""
    url: str
    title: str
    content: str
    metadata: dict = field(default_factory=dict)
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    source_type: str = "web"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime to ISO string
        data["scraped_at"] = self.scraped_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ScrapedDocument":
        """Create from dictionary (JSON deserialization)."""
        data = data.copy()
        data["scraped_at"] = datetime.fromisoformat(data["scraped_at"])
        return cls(**data)

    def save_to_file(self, filepath: str) -> None:
        """Save this document to a JSON file."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "ScrapedDocument":
        """Load document from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


class RobotsTxtParser:
    """Simple robots.txt parser for crawl permissions."""

    def __init__(self):
        self._cache: dict[str, tuple[bool, set[str]]] = {}

    async def can_fetch(self, client: httpx.AsyncClient, base_url: str, path: str) -> bool:
        """Check if path is allowed by robots.txt."""
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        if robots_url not in self._cache:
            try:
                resp = await client.get(robots_url, timeout=10)
                if resp.status_code == 200:
                    allowed, disallowed = self._parse_robots(resp.text)
                    self._cache[robots_url] = (allowed, disallowed)
                else:
                    self._cache[robots_url] = (True, set())
            except Exception:
                self._cache[robots_url] = (True, set())

        allowed, disallowed = self._cache[robots_url]

        # Check if path is disallowed
        for pattern in disallowed:
            if path.startswith(pattern):
                return False

        return True

    def _parse_robots(self, text: str) -> tuple[bool, set[str]]:
        """Parse robots.txt and return (global_allowed, disallowed_paths)."""
        disallowed = set()
        current_agent = None

        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            if key == "user-agent":
                current_agent = value
            elif key == "disallow" and (current_agent == "*" or "bot" in current_agent.lower()):
                if value:
                    disallowed.add(value)

        return True, disallowed


class BaseScraper(ABC):
    """Base class for web scrapers with rate limiting and robots.txt compliance."""

    def __init__(
        self,
        base_url: str,
        delay_seconds: float = 2.0,
        max_pages: int = 100,
        allowed_paths: Optional[list[str]] = None,
        respect_robots: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.delay_seconds = delay_seconds
        self.max_pages = max_pages
        self.allowed_paths = allowed_paths or []
        self.respect_robots = respect_robots

        self._client: Optional[httpx.AsyncClient] = None
        self._robots_parser = RobotsTxtParser()
        self._visited: set[str] = set()
        self._last_request_time: float = 0

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": getattr(settings, "SCRAPER_USER_AGENT", "CampusGPT-Bot/1.0"),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    @abstractmethod
    async def extract_content(self, soup: BeautifulSoup, url: str) -> ScrapedDocument:
        """Extract structured content from a page. Must be implemented by subclasses."""
        pass

    @abstractmethod
    async def find_links(self, soup: BeautifulSoup, url: str) -> list[str]:
        """Find links to follow. Must be implemented by subclasses."""
        pass

    async def _rate_limit(self):
        """Enforce rate limiting between requests."""
        import time
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay_seconds:
            await asyncio.sleep(self.delay_seconds - elapsed)
        self._last_request_time = time.time()

    async def _fetch(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a URL and return parsed HTML."""
        if not self._client:
            raise RuntimeError("Scraper not initialized. Use async context manager.")

        await self._rate_limit()

        try:
            resp = await self._client.get(url)
            if resp.status_code != 200:
                return None

            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type:
                return None

            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _is_allowed_path(self, url: str) -> bool:
        """Check if URL path is in allowed paths."""
        if not self.allowed_paths:
            return True

        parsed = urlparse(url)
        path = parsed.path

        for allowed in self.allowed_paths:
            if path.startswith(allowed.rstrip("/")):
                return True

        return False

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and query params."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    async def scrape(self, start_url: Optional[str] = None) -> list[ScrapedDocument]:
        """Main scraping loop."""
        start_url = start_url or self.base_url
        queue = [self._normalize_url(start_url)]
        documents = []

        print(f"[DEBUG] Starting scrape from: {start_url}")
        print(f"[DEBUG] Allowed paths: {self.allowed_paths}")
        print(f"[DEBUG] Max pages: {self.max_pages}")

        while queue and len(self._visited) < self.max_pages:
            url = queue.pop(0)
            norm_url = self._normalize_url(url)

            if norm_url in self._visited:
                print(f"[DEBUG] Already visited: {norm_url}")
                continue

            # Check allowed paths
            if not self._is_allowed_path(norm_url):
                print(f"[DEBUG] Path not allowed: {norm_url}")
                continue

            # Check robots.txt
            if self.respect_robots:
                allowed = await self._robots_parser.can_fetch(self._client, self.base_url, urlparse(norm_url).path)
                if not allowed:
                    print(f"[DEBUG] Disallowed by robots.txt: {norm_url}")
                    continue

            self._visited.add(norm_url)
            print(f"[DEBUG] Scraping [{len(documents)+1}/{self.max_pages}]: {norm_url}")

            soup = await self._fetch(norm_url)
            if not soup:
                print(f"[DEBUG] Failed to fetch: {norm_url}")
                continue

            # Extract content
            try:
                doc = await self.extract_content(soup, norm_url)
                if doc.content.strip():
                    documents.append(doc)
                    print(f"[DEBUG] Extracted content: {len(doc.content)} chars")
                else:
                    print(f"[DEBUG] No content extracted from: {norm_url}")
            except Exception as e:
                print(f"[DEBUG] Error extracting content from {norm_url}: {e}")

            # Find new links
            try:
                links = await self.find_links(soup, norm_url)
                print(f"[DEBUG] Found {len(links)} links on {norm_url}")
                for link in links:
                    abs_url = urljoin(norm_url, link)
                    norm_link = self._normalize_url(abs_url)
                    if norm_link not in self._visited and self._is_allowed_path(norm_link):
                        queue.append(norm_link)
            except Exception as e:
                print(f"[DEBUG] Error finding links on {norm_url}: {e}")

        print(f"[DEBUG] Scraping complete. Visited: {len(self._visited)}, Documents: {len(documents)}")
        return documents

    def save_documents(self, documents: list["ScrapedDocument"], output_dir: str = "data/scraped") -> int:
        """Save all scraped documents to JSON files in output_dir."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved = 0
        for i, doc in enumerate(documents):
            # Create filename from URL
            parsed = urlparse(doc.url)
            safe_name = parsed.path.strip("/").replace("/", "_") or "index"
            safe_name = re.sub(r"[^\w\-]", "_", safe_name)[:100]
            filename = f"{i:04d}_{safe_name}.json"
            filepath = output_path / filename

            try:
                doc.save_to_file(str(filepath))
                saved += 1
            except Exception as e:
                print(f"Error saving {doc.url}: {e}")

        # Also save a summary index
        # Prepare filename pattern (avoid backslash in f-string)
        safe_path_pattern = re.compile(r'[^\w\-]')
        index = {
            "scraped_at": datetime.utcnow().isoformat(),
            "source": self.base_url,
            "total_documents": len(documents),
            "saved_count": saved,
            "documents": [
                {"index": i, "url": d.url, "title": d.title, "filename": f"{i:04d}_{safe_path_pattern.sub('_', urlparse(d.url).path.strip('/').replace('/', '_')[:100])}.json"}
                for i, d in enumerate(documents)
            ]
        }
        index_path = output_path / "_index.json"
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        print(f"Saved {saved}/{len(documents)} documents to {output_path}")
        return saved

    @classmethod
    def load_documents(cls, input_dir: str = "data/scraped") -> list["ScrapedDocument"]:
        """Load all documents from a directory."""
        input_path = Path(input_dir)
        documents = []
        for filepath in sorted(input_path.glob("*.json")):
            if filepath.name == "_index.json":
                continue
            try:
                doc = ScrapedDocument.load_from_file(str(filepath))
                documents.append(doc)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
        print(f"Loaded {len(documents)} documents from {input_path}")
        return documents