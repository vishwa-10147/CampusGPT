# ==============================================================================
# CampusGPT Backend — Site Boilerplate Removal
# ==============================================================================
import re
from collections import Counter
from typing import Iterable, List, Set


# Animated counters scraped before they ran: "0+", "0%", "0LPA"
_EMPTY_COUNTER = re.compile(r"^\d+\s*(%|\+|[a-z]{1,3})?\+?$")


def _normalize(line: str) -> str:
    return line.strip().lstrip("#-*· ").strip().lower()


def find_boilerplate_lines(page_texts: Iterable[str], min_page_fraction: float = 0.25) -> Set[str]:
    """Lines (normalized) that appear on at least min_page_fraction of the pages.

    Menus, sidebars ("Recent events", "Related links") and footers repeat on
    nearly every page of a site; real content does not.
    """
    texts = list(page_texts)
    if len(texts) < 4:
        return set()  # too few pages to tell boilerplate from content
    counts = Counter()
    for text in texts:
        counts.update({_normalize(line) for line in text.split("\n") if _normalize(line)})
    threshold = max(2, int(len(texts) * min_page_fraction))
    return {line for line, count in counts.items() if count >= threshold}


def strip_boilerplate(text: str, boilerplate: Set[str], title: str = "") -> str:
    """Remove boilerplate lines from one page, keeping lines that name the page itself."""
    own_title = _normalize(title)
    kept: List[str] = []
    for line in text.split("\n"):
        normalized = _normalize(line)
        if _EMPTY_COUNTER.match(normalized):
            continue
        if normalized in boilerplate and not (own_title and (own_title in normalized or normalized in own_title)):
            continue
        kept.append(line)
    # Collapse the blank runs left behind
    result = "\n".join(kept)
    while "\n\n\n" in result:
        result = result.replace("\n\n\n", "\n\n")
    return result.strip()
