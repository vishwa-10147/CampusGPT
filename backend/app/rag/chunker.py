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


def split_text_recursive(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    separators: Optional[List[str]] = None,
) -> List[TextChunk]:
    """
    Split text recursively using hierarchical separators.
    
    This is similar to LangChain's RecursiveCharacterTextSplitter but simpler.
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""]

    def _split(text: str, separators: List[str]) -> List[str]:
        if not separators:
            return [text]

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            # Character-level split
            return list(text)

        splits = text.split(separator)
        result = []
        for split in splits:
            if len(split) <= chunk_size:
                result.append(split)
            else:
                # Recursively split with next separator
                result.extend(_split(split, remaining_separators))
        return result

    # Initial split
    splits = _split(text, separators)

    # Now combine splits into chunks with overlap
    chunks = []
    current_chunk = ""
    chunk_index = 0

    for split in splits:
        # If adding this split would exceed chunk_size, finalize current chunk
        if current_chunk and len(current_chunk) + len(split) > chunk_size:
            chunks.append(TextChunk(content=current_chunk.strip(), chunk_index=chunk_index))
            chunk_index += 1

            # Start new chunk with overlap
            if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                current_chunk = current_chunk[-chunk_overlap:] + split
            else:
                current_chunk = split
        else:
            current_chunk += split

    # Add final chunk
    if current_chunk.strip():
        chunks.append(TextChunk(content=current_chunk.strip(), chunk_index=chunk_index))

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
    """Clean extracted text."""
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    # Remove zero-width characters
    text = re.sub(r'[\u200b-\u200f\ufeff]', '', text)
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    return text.strip()