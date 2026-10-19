# ==============================================================================
# CampusGPT Backend — RAG Package
# ==============================================================================
from app.rag.chunker import (
    split_text_recursive,
    split_pdf_by_pages,
    clean_text,
    TextChunk,
)
from app.rag.retriever import VectorRetriever, RetrievedChunk
from app.rag.citation import Citation, build_citations, citations_to_dict, format_citations_for_prompt
from app.rag.prompts import (
    SYSTEM_PROMPT,
    RAG_PROMPT_TEMPLATE,
    NO_CONTEXT_PROMPT,
    SUMMARIZATION_PROMPT,
    COMPARISON_PROMPT,
    build_rag_prompt,
)

__all__ = [
    # Chunker
    "split_text_recursive",
    "split_pdf_by_pages",
    "clean_text",
    "TextChunk",
    # Retriever
    "VectorRetriever",
    "RetrievedChunk",
    # Citation
    "Citation",
    "build_citations",
    "citations_to_dict",
    "format_citations_for_prompt",
    # Prompts
    "SYSTEM_PROMPT",
    "RAG_PROMPT_TEMPLATE",
    "NO_CONTEXT_PROMPT",
    "SUMMARIZATION_PROMPT",
    "COMPARISON_PROMPT",
    "build_rag_prompt",
]