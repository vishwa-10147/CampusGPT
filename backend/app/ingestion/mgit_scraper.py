# ==============================================================================
# CampusGPT Backend — MGIT College Scraper
# ==============================================================================
import re
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.ingestion.base_scraper import BaseScraper, ScrapedDocument


class MGITScraper(BaseScraper):
    """Scraper for MGIT (Mahatma Gandhi Institute of Technology) website."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # MGIT-specific selectors
        self.content_selectors = [
            "main.content",
            ".page-content",
            ".entry-content",
            "#main-content",
            ".content-area",
            "article",
            ".container .row",
            "main",
        ]

        self.title_selectors = [
            "h1.page-title",
            ".page-header h1",
            "h1.entry-title",
            "header h1",
            "h1",
        ]

        # Links to ignore
        self.ignore_patterns = [
            r"\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar)$",
            r"/wp-admin",
            r"/wp-login",
            r"/wp-json",
            r"\?.*",  # query params
            r"#.*",   # fragments
            r"javascript:",
            r"mailto:",
            r"tel:",
        ]

    async def extract_content(self, soup: BeautifulSoup, url: str) -> ScrapedDocument:
        """Extract structured content from MGIT page."""
        # Extract title
        title = self._extract_title(soup)

        # Extract main content
        content = self._extract_main_content(soup)

        # Extract metadata
        metadata = {
            "source_url": url,
            "source_name": "MGIT Official Website",
            "college": "Mahatma Gandhi Institute of Technology",
            "college_code": "MGIT",
        }

        # Add page-specific metadata
        metadata.update(self._extract_metadata(soup, url))

        return ScrapedDocument(
            url=url,
            title=title,
            content=content,
            metadata=metadata,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        for selector in self.title_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text:
                    return text

        # Fallback to <title> tag
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)

        return "Untitled"

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content area, removing navigation, footer, etc."""
        # Remove unwanted elements
        for unwanted in soup.select(
            "nav, header, footer, aside, .sidebar, .navigation, "
            ".menu, .breadcrumb, .social-links, .ads, .advertisement, "
            "script, style, noscript, .cookie-banner, .popup, modal"
        ):
            unwanted.decompose()

        # Try content selectors in order
        main_content = None
        for selector in self.content_selectors:
            elem = soup.select_one(selector)
            if elem:
                main_content = elem
                break

        if not main_content:
            main_content = soup.find("body")

        if not main_content:
            return ""

        # Get text with structure preserved
        text_parts = []
        for elem in main_content.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "th", "blockquote"]):
            text = elem.get_text(strip=True)
            if text:
                tag = elem.name
                if tag.startswith("h"):
                    text_parts.append(f"\n## {text}\n")
                elif tag == "li":
                    text_parts.append(f"- {text}")
                elif tag in ("td", "th"):
                    text_parts.append(text)
                else:
                    text_parts.append(text)

        content = "\n".join(text_parts)

        # Clean up
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = re.sub(r" {2,}", " ", content)

        return content.strip()

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> dict:
        """Extract page metadata."""
        metadata = {}

        # Meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                metadata[f"meta_{name.replace(':', '_')}"] = content

        # Open Graph
        og_title = soup.find("meta", property="og:title")
        if og_title:
            metadata["og_title"] = og_title.get("content")

        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            metadata["og_description"] = og_desc.get("content")

        # Determine page category from URL
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if path:
            parts = path.split("/")
            metadata["page_category"] = parts[0]
            if len(parts) > 1:
                metadata["page_subcategory"] = parts[1]

        return metadata

    async def find_links(self, soup: BeautifulSoup, current_url: str) -> list[str]:
        """Find internal links to follow."""
        links = []
        base_netloc = urlparse(self.base_url).netloc

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()

            # Skip ignored patterns
            if any(re.search(pattern, href) for pattern in self.ignore_patterns):
                continue

            # Must be same domain
            parsed = urlparse(href)
            if parsed.netloc and parsed.netloc != base_netloc:
                continue

            # Normalize
            if parsed.path:
                links.append(href)

        # Also look for links in nav menus, sidebars, etc.
        # WordPress sites often have navigation in different places
        for nav in soup.select("nav a, .menu a, .sidebar a, .widget a, footer a"):
            if nav.get("href"):
                href = nav["href"].strip()
                if href.startswith("http") or href.startswith("/"):
                    parsed = urlparse(href)
                    if not parsed.netloc or parsed.netloc == base_netloc:
                        links.append(href)

        return list(set(links))  # Deduplicate