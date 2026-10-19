# ==============================================================================
# CampusGPT Backend — Text Chunking
# ==============================================================================
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import re


@dataclass
class TextChunk:
    """A chunk of text with metadata."""
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# A sentence ends at . ! or ? followed by whitespace and a character that isn't
# lowercase, so lowercase continuations ("approx. two") and decimals stay intact.
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[^a-z\s])")
_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")


def _split_units(text: str, chunk_size: int) -> List[tuple[str, str]]:
    """Break text into (separator_before, sentence) pairs.

    The separator records whether a sentence followed another sentence (" "),
    a line break ("\\n") or a paragraph break ("\\n\\n"), so chunks keep the
    original structure. Only a single sentence longer than chunk_size is cut,
    and then on word boundaries.
    """
    units: List[tuple[str, str]] = []
    for p_index, paragraph in enumerate(_PARAGRAPH_BREAK.split(text)):
        for l_index, line in enumerate(paragraph.split("\n")):
            for s_index, sentence in enumerate(_SENTENCE_BOUNDARY.split(line.strip())):
                sentence = sentence.strip()
                if not sentence:
                    continue
                if s_index > 0:
                    sep = " "
                elif l_index > 0:
                    sep = "\n"
                else:
                    sep = "\n\n" if p_index > 0 else ""

                if len(sentence) <= chunk_size:
                    units.append((sep, sentence))
                    continue

                piece = ""
                for word in sentence.split():
                    if piece and len(piece) + 1 + len(word) > chunk_size:
                        units.append((sep, piece))
                        sep, piece = " ", word
                    else:
                        piece = f"{piece} {word}" if piece else word
                if piece:
                    units.append((sep, piece))
    return units


def _joined_length(units: List[tuple[str, str]]) -> int:
    """Length of the units once joined (the first unit's separator is dropped)."""
    if not units:
        return 0
    return sum(len(sep) + len(unit) for sep, unit in units) - len(units[0][0])


def _join(units: List[tuple[str, str]]) -> str:
    return "".join(unit if i == 0 else sep + unit for i, (sep, unit) in enumerate(units)).strip()


def split_text_recursive(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[TextChunk]:
    """
    Split text into chunks of at most chunk_size characters without cutting sentences.

    Chunks are packed from whole sentences and keep paragraph and line breaks.
    Overlap repeats the previous chunk's trailing whole sentences (up to
    chunk_overlap characters), never a partial sentence.
    """
    chunks: List[TextChunk] = []
    current: List[tuple[str, str]] = []

    for unit in _split_units(text, chunk_size):
        if current and _joined_length(current + [unit]) > chunk_size:
            chunks.append(TextChunk(content=_join(current), chunk_index=len(chunks)))

            # Carry over whole trailing sentences that fit the overlap budget
            overlap: List[tuple[str, str]] = []
            for prev in reversed(current):
                if _joined_length([prev] + overlap) > chunk_overlap:
                    break
                overlap.insert(0, prev)
            current = overlap if _joined_length(overlap + [unit]) <= chunk_size else []

        current.append(unit)

    if current:
        chunks.append(TextChunk(content=_join(current), chunk_index=len(chunks)))

    return chunks


def split_pdf_by_pages(
    pages: List[tuple[int, str]],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[TextChunk]:
    """
    Split PDF pages into chunks, preserving page numbers.

    Args:
        pages: List of (page_number, text) tuples
    """
    all_chunks = []
    chunk_index = 0

    for page_num, page_text in pages:
        if not page_text.strip():
            continue

        page_chunks = split_text_recursive(page_text, chunk_size, chunk_overlap)
        for chunk in page_chunks:
            chunk.page_number = page_num
            chunk.chunk_index = chunk_index
            all_chunks.append(chunk)
            chunk_index += 1

    return all_chunks


def clean_text(text: str) -> str:
    """Normalise whitespace while keeping line and paragraph breaks for the chunker."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Remove zero-width characters
    text = re.sub(r"[​-‏﻿]", "", text)
    # Collapse runs of spaces/tabs, trim around line breaks, cap blank lines at one
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
