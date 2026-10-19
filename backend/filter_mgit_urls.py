
from pathlib import Path
from urllib.parse import urlparse

source = Path("mgit_discovered_urls.txt")
output = Path("mgit_selected_urls.txt")

if not source.exists():
    raise FileNotFoundError(
        "Run discover_mgit_pages.py first."
    )

# Start with pages relevant to the CampusGPT knowledge base.
keywords = (
    "about",
    "academic",
    "academics",
    "admission",
    "department",
    "syllabus",
    "curriculum",
    "regulation",
    "examination",
    "exam",
    "calendar",
    "placement",
    "facility",
    "facilities",
    "library",
    "contact",
    "scholarship",
    "announcement",
    "notice",
    "faculty",
    "research",
    "hostel",
    "transport",
    "fee",
)

# Exclude obvious technical, test, and non-page paths.
excluded_parts = (
    "/ajax",
    "/wp-admin",
    "/wp-json",
    "/feed",
)

selected = set()

for raw_url in source.read_text(encoding="utf-8").splitlines():
    url = raw_url.strip()
    if not url:
        continue

    parsed = urlparse(url)

    # Restrict results to the official MGIT hostname.
    if parsed.scheme != "https" or parsed.hostname != "mgit.ac.in":
        continue

    path = parsed.path.rstrip("/").lower()

    if any(part in path for part in excluded_parts):
        continue

    if any(word in path for word in keywords):
        selected.add(f"https://mgit.ac.in{path}")

# Keep the output deterministic.
urls = sorted(selected)
output.write_text("\n".join(urls), encoding="utf-8")

print(f"Discovered URLs: {len(source.read_text(encoding='utf-8').splitlines())}")
print(f"Selected candidate URLs: {len(urls)}")
print(f"Saved to: {output.resolve()}")

for url in urls[:60]:
    print(url)
