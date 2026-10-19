# ==============================================================================
# CampusGPT Backend — Citation Builder
# ==============================================================================
from typing import List, Dict, Any, Optional
from uuid import UUID
from dataclasses import dataclass

from app.rag.retriever import RetrievedChunk


@dataclass
class Citation:
    """Structured citation for an answer."""
    document_id: UUID
    filename: str
    original_name: str
    chunk_index: int
    page_number: Optional[int]
    similarity_score: float
    text_snippet: str  # short preview shown in the UI
    content: str = ""  # full chunk text given to the model


def build_citations(
    retrieved_chunks: List[RetrievedChunk],
    max_snippet_length: int = 300,
) -> List[Citation]:
    """
    Build citations from retrieved chunks.
    
    Args:
        retrieved_chunks: Chunks from vector search
        max_snippet_length: Maximum length of text snippet
    """
    citations = []
    for rc in retrieved_chunks:
        chunk = rc.chunk
        document = chunk.document

        # Create snippet
        snippet = chunk.content[:max_snippet_length]
        if len(chunk.content) > max_snippet_length:
            snippet += "..."

        citation = Citation(
            document_id=chunk.document_id,
            filename=document.filename,
            original_name=document.original_name,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            similarity_score=round(rc.similarity, 4),
            text_snippet=snippet,
            content=chunk.content,
        )
        citations.append(citation)

    return citations


def citations_to_dict(citations: List[Citation]) -> List[Dict[str, Any]]:
    """Convert citations to JSON-serializable dicts."""
    return [
        {
            "document_id": str(c.document_id),
            "filename": c.filename,
            "original_name": c.original_name,
            "chunk_index": c.chunk_index,
            "page_number": c.page_number,
            "similarity_score": c.similarity_score,
            "text_snippet": c.text_snippet,
        }
        for c in citations
    ]


def format_citations_for_prompt(citations: List[Citation]) -> str:
    """
    Format citations as a string for inclusion in the LLM prompt.
    """
    if not citations:
        return "No relevant sources found."

    lines = ["Sources:"]
    for i, c in enumerate(citations, 1):
        page_info = f", page {c.page_number}" if c.page_number else ""
        lines.append(
            f"[{i}] {c.original_name}{page_info} "
            f"(chunk {c.chunk_index}, similarity: {c.similarity_score:.2f}): "
            f"{c.content or c.text_snippet}"
        )
    return "\n".join(lines)