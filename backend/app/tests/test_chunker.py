# ==============================================================================
# CampusGPT Backend — Chunker Tests
# ==============================================================================
import re

from app.rag.chunker import clean_text, split_pdf_by_pages, split_text_recursive

LIBRARY_POLICY = """# MGIT Central Library Policy

The MGIT Central Library is open from 8:00 AM to 8:00 PM on weekdays and from 9:00 AM to 2:00 PM on Saturdays. It is closed on Sundays and public holidays.

Undergraduate students may borrow up to 4 books at a time for 14 days. Postgraduate students may borrow up to 6 books for 21 days.

The late return fine is 5 rupees per book per day. Lost books must be replaced or paid for at twice the listed price.

The digital library provides access to IEEE Xplore and Springer journals from any campus computer."""

SENTENCES = [
    "It is closed on Sundays and public holidays.",
    "The late return fine is 5 rupees per book per day.",
    "Lost books must be replaced or paid for at twice the listed price.",
    "The digital library provides access to IEEE Xplore and Springer journals from any campus computer.",
]


def test_chunks_never_cut_a_sentence():
    chunks = split_text_recursive(clean_text(LIBRARY_POLICY), chunk_size=200, chunk_overlap=60)
    assert len(chunks) > 1
    for sentence in SENTENCES:
        assert any(sentence in c.content for c in chunks), sentence


def test_sentences_are_not_glued_together():
    text = " ".join(c.content for c in split_text_recursive(clean_text(LIBRARY_POLICY), 200, 60))
    # The old splitter dropped ". " and produced "priceThe"
    assert not re.search(r"[a-z][A-Z]", text.replace("IEEE", "").replace("MGIT", ""))


def test_chunks_respect_size_limit():
    for chunk in split_text_recursive(clean_text(LIBRARY_POLICY), chunk_size=150, chunk_overlap=40):
        assert len(chunk.content) <= 150


def test_overlap_repeats_whole_sentences_only():
    chunks = split_text_recursive(
        "Alpha one is here. Beta two is here. Gamma three is here. Delta four is here.",
        chunk_size=40,
        chunk_overlap=20,
    )
    assert [c.content for c in chunks] == [
        "Alpha one is here. Beta two is here.",
        "Beta two is here. Gamma three is here.",
        "Gamma three is here. Delta four is here.",
    ]


def test_oversized_sentence_splits_on_words():
    long_sentence = " ".join(f"word{i}" for i in range(100)) + "."
    chunks = split_text_recursive(long_sentence, chunk_size=80, chunk_overlap=0)
    assert all(len(c.content) <= 80 for c in chunks)
    assert " ".join(c.content for c in chunks) == long_sentence


def test_decimals_and_lowercase_continuations_do_not_split():
    chunks = split_text_recursive("The CGPA cutoff is 7.5 for approx. two thirds of seats.", 30, 0)
    assert any("7.5" in c.content for c in chunks)
    assert all(not c.content.startswith("5") for c in chunks)


def test_clean_text_keeps_paragraph_breaks():
    assert clean_text("Line one  \r\nLine   two\n\n\n\nNext paragraph​") == (
        "Line one\nLine two\n\nNext paragraph"
    )


def test_pdf_pages_keep_page_numbers_and_global_index():
    chunks = split_pdf_by_pages([(1, "Page one text."), (2, ""), (3, "Page three text.")])
    assert [(c.page_number, c.chunk_index) for c in chunks] == [(1, 0), (3, 1)]


def test_prompt_context_uses_full_chunk_not_preview():
    from uuid import uuid4
    from app.rag.citation import Citation
    from app.rag.prompts import build_rag_prompt

    full = "Opening hours are listed first. " * 12 + "The late return fine is 5 rupees per book per day."
    citation = Citation(
        document_id=uuid4(), filename="f.md", original_name="Library", chunk_index=0,
        page_number=None, similarity_score=0.6, text_snippet=full[:300] + "...", content=full,
    )
    assert "5 rupees per book per day" in build_rag_prompt("What is the fine?", [citation])
