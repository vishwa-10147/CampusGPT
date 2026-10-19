# ==============================================================================
# CampusGPT Backend — Boilerplate Removal Tests
# ==============================================================================
from app.ingestion.boilerplate import find_boilerplate_lines, strip_boilerplate

SIDEBAR = "## RECENT EVENTS\n## MAGISTECH 2026\n- Upcoming Events"
PAGES = {
    "MAGISTECH 2026": "## MAGISTECH 2026\nA two-day national symposium on 16-17 October.\n" + SIDEBAR,
    "Placements": "The T & P Cell arranges campus interviews.\n" + SIDEBAR,
    "Library": "The library opens at 8 AM.\n" + SIDEBAR,
    "Hostel": "Separate hostels for boys and girls.\n" + SIDEBAR,
}


def test_sidebar_lines_are_removed_from_other_pages():
    boilerplate = find_boilerplate_lines(PAGES.values())
    cleaned = strip_boilerplate(PAGES["Placements"], boilerplate, "Placements")
    assert cleaned == "The T & P Cell arranges campus interviews."


def test_page_keeps_its_own_title_even_if_it_is_in_the_sidebar():
    boilerplate = find_boilerplate_lines(PAGES.values())
    cleaned = strip_boilerplate(PAGES["MAGISTECH 2026"], boilerplate, "MAGISTECH 2026")
    assert cleaned.startswith("## MAGISTECH 2026\nA two-day national symposium")
    assert "RECENT EVENTS" not in cleaned


def test_too_few_pages_strips_nothing():
    assert find_boilerplate_lines(list(PAGES.values())[:3]) == set()


def test_unanimated_counters_are_dropped_but_real_numbers_stay():
    text = "## 0+\n## 0%\n## 0LPA\nOver 500 students were placed in 2026."
    assert strip_boilerplate(text, set()) == "Over 500 students were placed in 2026."
