# ==============================================================================
# CampusGPT Backend — File Processing Service
# ==============================================================================
from typing import List, Tuple, Optional, BinaryIO
from pathlib import Path
from uuid import UUID

from app.rag.chunker import split_pdf_by_pages, split_text_recursive, TextChunk, clean_text
from app.services.embedding_service import get_embedding_service
from app.repositories.document_repo import DocumentRepository, DocumentChunkRepository, IngestionJobRepository
from app.models.document import Document, DocumentChunk


class FileProcessingService:
    """Document text extraction, chunking, and embedding."""

    def __init__(self, session):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.chunk_repo = DocumentChunkRepository(session)
        self.job_repo = IngestionJobRepository(session)
        self.embedding = get_embedding_service()

    async def process_document(self, document_id: UUID) -> bool:
        """
        Process a document: extract text, chunk, embed, store.
        Returns True on success, False on failure.
        """
        document = await self.doc_repo.get_with_chunks(document_id)
        if not document:
            return False

        # Update status to processing
        await self.doc_repo.update_status(document_id, "processing")
        job = await self.job_repo.get_by_document(document_id)
        if job:
            await self.job_repo.update_progress(job.id, "processing", 10)

        try:
            # 1. Extract text by page
            storage_path = Path("/app/uploads") / document.filename
            pages = self._extract_text_by_page(storage_path, document.mime_type)

            if job:
                await self.job_repo.update_progress(job.id, "processing", 30)

            # 2. Chunk text
            chunks = split_pdf_by_pages(pages)
            chunks = [clean_text(c.content) for c in chunks]  # Clean each chunk

            # Filter empty chunks
            chunks = [c for c in chunks if c.strip()]
            if not chunks:
                raise ValueError("No extractable text found in document")

            if job:
                await self.job_repo.update_progress(job.id, "processing", 50)

            # 3. Generate embeddings
            texts = [c for c in chunks]
            embedding_response = await self.embedding.embed(texts)
            embeddings = embedding_response.embeddings

            if job:
                await self.job_repo.update_progress(job.id, "processing", 70)

            # 4. Create chunk records with embeddings
            chunk_records = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_record = DocumentChunk(
                    document_id=document_id,
                    content=chunk,
                    embedding=embedding,
                    chunk_index=i,
                    page_number=None,  # Could extract from split_pdf_by_pages
                    metadata={"char_count": len(chunk)},
                )
                chunk_records.append(chunk_record)

            await self.chunk_repo.bulk_create_chunks(chunk_records)

            if job:
                await self.job_repo.update_progress(job.id, "processing", 90)

            # 5. Update document status
            await self.doc_repo.update_status(document_id, "ready")
            if job:
                await self.job_repo.update_progress(job.id, "completed", 100)

            return True

        except Exception as e:
            # Update status to failed
            await self.doc_repo.update_status(document_id, "failed")
            if job:
                await self.job_repo.update_progress(job.id, "failed", 0, str(e))
            return False

    def _extract_text_by_page(self, file_path: Path, mime_type: str) -> List[Tuple[int, str]]:
        """Extract text from file by page."""
        if mime_type == "application/pdf":
            return self._extract_pdf_pages(file_path)
        elif mime_type in ("text/plain", "text/markdown"):
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            return [(1, text)]
        else:
            raise ValueError(f"Unsupported file type: {mime_type}")

    def _extract_pdf_pages(self, file_path: Path) -> List[Tuple[int, str]]:
        """Extract text from PDF by page."""
        import pypdf

        pages = []
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for i, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                pages.append((i, text))
        return pages