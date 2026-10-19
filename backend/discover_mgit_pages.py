
import os
from pathlib import Path
from dotenv import load_dotenv
from firecrawl import Firecrawl

load_dotenv()

api_key = os.getenv("FIRECRAWL_API_KEY")
website = os.getenv("COLLEGE_WEBSITE", "https://mgit.ac.in/")

if not api_key:
    raise RuntimeError("FIRECRAWL_API_KEY is missing from backend/.env")

client = Firecrawl(api_key=api_key)

print(f"Discovering pages under {website} ...")
result = client.map(website)

urls = sorted({
    link.url
    for link in result.links
    if getattr(link, "url", None)
})

output = Path("mgit_discovered_urls.txt")
output.write_text("\n".join(urls), encoding="utf-8")

print(f"\nDiscovered {len(urls)} URLs.")
print(f"Saved to: {output.resolve()}")

for url in urls[:50]:
    print(url)
