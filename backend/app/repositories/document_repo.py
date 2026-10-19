# ==============================================================================
# CampusGPT Backend — Document Repository
# ==============================================================================
from datetime import datetime
from typing import Optional, Sequence, List
from uuid import UUID

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document, DocumentChunk, IngestionJob
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Document repository with document-specific queries."""

    def __init__(self, session: AsyncSession):
        super().__init__(Document, session)

    async def get_user_documents(
        self,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> Sequence[Document]:
        """Get documents uploaded by a user."""
        query = select(Document).where(Document.uploaded_by == user_id)

        if status:
            query = query.where(Document.status == status)

        query = query.order_by(Document.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_user_documents(self, user_id: UUID, status: Optional[str] = None) -> int:
        """Count user's documents."""
        query = select(func.count(Document.id)).where(Document.uploaded_by == user_id)

        if status:
            query = query.where(Document.status == status)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_all_documents(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> Sequence[Document]:
        """Get all documents (admin)."""
        query = select(Document).options(selectinload(Document.uploader))

        if status:
            query = query.where(Document.status == status)

        query = query.order_by(Document.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_all_documents(self, status: Optional[str] = None) -> int:
        """Count all documents (admin)."""
        query = select(func.count(Document.id))

        if status:
            query = query.where(Document.status == status)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_with_chunks(self, document_id: UUID) -> Optional[Document]:
        """Get document with its chunks."""
        result = await self.session.execute(
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.chunks))
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        document_id: UUID,
        status: str,
        completed_at: Optional[datetime] = None,
    ) -> Optional[Document]:
        """Update document status."""
        from datetime import datetime
        document = await self.get(document_id)
        if not document:
            return None
        document.status = status
        if completed_at:
            document.completed_at = completed_at
        elif status in ("ready", "failed"):
            document.completed_at = datetime.now(datetime.now().astimezone().tzinfo)
        await self.session.flush()
        await self.session.refresh(document)
        return document


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    """Document chunk repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(DocumentChunk, session)

    async def get_document_chunks(
        self,
        document_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[DocumentChunk]:
        """Get chunks for a document."""
        result = await self.session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_document_chunks(self, document_id: UUID) -> int:
        """Count chunks for a document."""
        result = await self.session.execute(
            select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == document_id)
        )
        return result.scalar_one()

    async def bulk_create_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Bulk create chunks."""
        self.session.add_all(chunks)
        await self.session.flush()
        for chunk in chunks:
            await self.session.refresh(chunk)
        return chunks

    async def delete_document_chunks(self, document_id: UUID) -> int:
        """Delete all chunks for a document."""
        result = await self.session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        return result.rowcount


class IngestionJobRepository(BaseRepository[IngestionJob]):
    """Ingestion job repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(IngestionJob, session)

    async def get_by_document(self, document_id: UUID) -> Optional[IngestionJob]:
        """Get latest ingestion job for a document."""
        result = await self.session.execute(
            select(IngestionJob)
            .where(IngestionJob.document_id == document_id)
            .order_by(IngestionJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_job(self, document_id: UUID) -> IngestionJob:
        """Create a new ingestion job."""
        return await self.create(document_id=document_id, status="queued", progress=0)

    async def update_progress(
        self,
        job_id: UUID,
        status: str,
        progress: int,
        error_message: Optional[str] = None,
    ) -> Optional[IngestionJob]:
        """Update job progress."""
        from datetime import datetime
        job = await self.get(job_id)
        if not job:
            return None
        job.status = status
        job.progress = progress
        if error_message:
            job.error_message = error_message
        if status == "processing" and not job.started_at:
            job.started_at = datetime.now(datetime.now().astimezone().tzinfo)
        if status in ("completed", "failed"):
            job.completed_at = datetime.now(datetime.now().astimezone().tzinfo)
        await self.session.flush()
        await self.session.refresh(job)
        return job