# ==============================================================================
# CampusGPT Backend — Document Schemas
# ==============================================================================
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class DocumentUploadResponse(BaseModel):
    """Document upload response."""
    id: UUID
    filename: str
    original_name: str
    mime_type: str
    size_bytes: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    """Document detail response."""
    id: UUID
    filename: str
    original_name: str
    mime_type: str
    size_bytes: int
    uploaded_by: Optional[UUID]
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    chunk_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Paginated document list response."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentChunkResponse(BaseModel):
    """Document chunk response (admin)."""
    id: UUID
    document_id: UUID
    chunk_index: int
    page_number: Optional[int] = None
    content_preview: str
    has_embedding: bool
    metadata: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IngestionJobResponse(BaseModel):
    """Ingestion job status response."""
    id: UUID
    document_id: UUID
    status: str
    progress: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)