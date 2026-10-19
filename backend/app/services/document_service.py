# ==============================================================================
# CampusGPT Backend — Document Service
# ==============================================================================
import os
import shutil
from pathlib import Path
from typing import Optional, Sequence, BinaryIO
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.document_repo import DocumentRepository, DocumentChunkRepository, IngestionJobRepository
from app.schemas.document import DocumentUploadResponse, DocumentResponse, DocumentListResponse
from app.models.document import Document


class DocumentService:
    """Document management business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.chunk_repo = DocumentChunkRepository(session)
        self.job_repo = IngestionJobRepository(session)

        # Ensure upload directory exists
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _validate_file(self, filename: str, content_type: str, size: int) -> None:
        """Validate uploaded file."""
        # Check size
        max_size = settings.max_upload_size_mb * 1024 * 1024
        if size > max_size:
            raise ValueError(f"File too large. Maximum size: {settings.max_upload_size_mb}MB")

        # Check MIME type
        if content_type not in settings.allowed_mime_types:
            raise ValueError(f"File type not allowed. Allowed: {', '.join(settings.allowed_mime_types)}")

        # Check extension matches MIME type
        ext = Path(filename).suffix.lower()
        mime_ext_map = {
            "application/pdf": [".pdf"],
            "text/plain": [".txt"],
            "text/markdown": [".md", ".markdown"],
        }
        allowed_exts = mime_ext_map.get(content_type, [])
        if allowed_exts and ext not in allowed_exts:
            raise ValueError(f"File extension {ext} doesn't match content type {content_type}")

    def _generate_storage_filename(self, original_filename: str) -> str:
        """Generate a secure storage filename."""
        import uuid
        ext = Path(original_filename).suffix.lower()
        return f"{uuid.uuid4()}{ext}"

    async def upload_document(
        self,
        user_id: UUID,
        file: BinaryIO,
        filename: str,
        content_type: str,
        size: int,
        visibility: str = "private",
    ) -> DocumentUploadResponse:
        """Upload a document and create processing job."""
        # Validate
        self._validate_file(filename, content_type, size)

        # Generate storage path
        storage_filename = self._generate_storage_filename(filename)
        storage_path = self.upload_dir / storage_filename

        # Save file
        with open(storage_path, "wb") as f:
            shutil.copyfileobj(file, f)

        # Create document record
        document = await self.doc_repo.create(
            filename=storage_filename,
            original_name=filename,
            mime_type=content_type,
            size_bytes=size,
            uploaded_by=user_id,
            status="pending",
            visibility=visibility,
        )

        # Create ingestion job; commit now so the background processor can see it
        await self.job_repo.create_job(document.id)
        await self.session.commit()

        return DocumentUploadResponse.model_validate(document)

    async def get_document(self, document_id: UUID, user_id: Optional[UUID] = None, is_admin: bool = False) -> Optional[DocumentResponse]:
        """Get document by ID."""
        document = await self.doc_repo.get(document_id)
        if not document:
            return None

        # Check access
        if not is_admin and document.uploaded_by != user_id:
            return None

        chunk_count = await self.chunk_repo.count_document_chunks(document_id)
        return DocumentResponse.model_validate(document).model_copy(update={"chunk_count": chunk_count})

    async def list_user_documents(
        self,
        user_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> DocumentListResponse:
        """List user's documents."""
        offset = (page - 1) * page_size

        documents = await self.doc_repo.get_user_documents(
            user_id, offset=offset, limit=page_size, status=status
        )
        total = await self.doc_repo.count_user_documents(user_id, status)

        doc_responses = []
        for doc in documents:
            chunk_count = await self.chunk_repo.count_document_chunks(doc.id)
            doc_responses.append(DocumentResponse.model_validate(doc).model_copy(update={"chunk_count": chunk_count}))

        return DocumentListResponse(
            documents=doc_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def list_all_documents(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        status: Optional[str] = None,
    ) -> DocumentListResponse:
        """List all documents (admin)."""
        offset = (page - 1) * page_size

        documents = await self.doc_repo.get_all_documents(
            offset=offset, limit=page_size, status=status
        )
        total = await self.doc_repo.count_all_documents(status)

        doc_responses = []
        for doc in documents:
            chunk_count = await self.chunk_repo.count_document_chunks(doc.id)
            doc_responses.append(DocumentResponse.model_validate(doc).model_copy(update={"chunk_count": chunk_count}))

        return DocumentListResponse(
            documents=doc_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def delete_document(self, document_id: UUID, user_id: UUID, is_admin: bool = False) -> bool:
        """Delete a document and its chunks."""
        document = await self.doc_repo.get(document_id)
        if not document:
            return False

        # Check access
        if not is_admin and document.uploaded_by != user_id:
            return False

        # Delete file from storage
        storage_path = self.upload_dir / document.filename
        if storage_path.exists():
            storage_path.unlink()

        # Delete chunks (cascades from document delete, but explicit for job cleanup)
        await self.chunk_repo.delete_document_chunks(document_id)

        # Delete document (cascades to jobs)
        await self.doc_repo.delete(document_id)

        return True

    async def reset_for_reprocessing(
        self, document_id: UUID, user_id: UUID, is_admin: bool = False
    ) -> Optional[DocumentResponse]:
        """Drop existing chunks and mark the document pending again."""
        document = await self.doc_repo.get(document_id)
        if not document or (not is_admin and document.uploaded_by != user_id):
            return None
        if not (self.upload_dir / document.filename).exists():
            raise ValueError("Original file is not stored, so it can't be reprocessed")

        await self.chunk_repo.delete_document_chunks(document_id)
        await self.doc_repo.update_status(document_id, "pending")
        if not await self.job_repo.get_by_document(document_id):
            await self.job_repo.create_job(document_id)
        await self.session.commit()
        return await self.get_document(document_id, user_id, is_admin)

    def get_storage_path(self, document: Document) -> Path:
        """Get the filesystem path for a document."""
        return self.upload_dir / document.filename