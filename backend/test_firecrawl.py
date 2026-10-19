
import os
from dotenv import load_dotenv
from firecrawl import Firecrawl

load_dotenv()

api_key = os.getenv("FIRECRAWL_API_KEY")
website = os.getenv("COLLEGE_WEBSITE")

if not api_key or not website:
    raise RuntimeError(
        "Set FIRECRAWL_API_KEY and COLLEGE_WEBSITE in backend/.env"
    )

client = Firecrawl(api_key=api_key)

print(f"Testing Firecrawl against: {website}")

result = client.scrape(website, formats=["markdown"])

content = result.markdown or ""

print("\n--- Metadata ---")
print(result.metadata)

print("\n--- Extracted content preview ---")
print(content[:3000] if content else "No Markdown content returned.")

if not content.strip():
    raise RuntimeError("Scrape returned no Markdown content.")

print("\nFirecrawl test passed.")
