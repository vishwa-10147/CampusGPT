# ==============================================================================
# CampusGPT Backend — Document Models
# ==============================================================================
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID as UUIDType

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.models.base import Base, TimestampMixin, UUIDMixin

# Import Vector type from pgvector
from pgvector.sqlalchemy import Vector


class Document(Base, UUIDMixin, TimestampMixin):
    """Document model for uploaded files."""

    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    original_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    uploaded_by: Mapped[Optional[UUIDType]] = mapped_column(
        UUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        index=True,
        nullable=False,
    )  # pending, processing, ready, failed
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    uploader: Mapped[Optional["User"]] = relationship(back_populates="documents", lazy="selectin")
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    ingestion_jobs: Mapped[List["IngestionJob"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Table-level indexes
    __table_args__ = (
        Index("ix_documents_uploaded_by_status", "uploaded_by", "status"),
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename!r}, status={self.status})>"


class DocumentChunk(Base, UUIDMixin, TimestampMixin):
    """Document chunk with embedding for RAG."""

    __tablename__ = "document_chunks"

    document_id: Mapped[UUIDType] = mapped_column(
        UUID,
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(settings.embedding_dimension),
        nullable=True,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    page_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="chunks", lazy="selectin")

    # Table-level indexes
    __table_args__ = (
        Index("ix_document_chunks_document_id_chunk_index", "document_id", "chunk_index"),
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"


class IngestionJob(Base, UUIDMixin, TimestampMixin):
    """Async document ingestion job tracking."""

    __tablename__ = "ingestion_jobs"

    document_id: Mapped[UUIDType] = mapped_column(
        UUID,
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="queued",
        index=True,
        nullable=False,
    )  # queued, processing, completed, failed
    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="ingestion_jobs", lazy="selectin")

    def __repr__(self) -> str:
        return f"<IngestionJob(id={self.id}, document_id={self.document_id}, status={self.status})>"