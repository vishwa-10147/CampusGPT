# ==============================================================================
# CampusGPT Backend — Documents API Routes
# ==============================================================================
import io
import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.api.deps import get_current_user_id, get_current_user, get_document_service, get_current_admin_user
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentListResponse,
)
from app.services.document_service import DocumentService
from app.models.user import User
from app.core.database import async_session_maker
from app.ingestion.ingestion_service import IngestionService
from app.services.file_service import FileProcessingService

router = APIRouter(prefix="/documents", tags=["Documents"])


class IngestMgitRequest(BaseModel):
    """Request to trigger MGIT website ingestion."""
    start_url: Optional[str] = None
    max_pages: Optional[int] = None


class IngestMgitResponse(BaseModel):
    """Response from MGIT ingestion."""
    status: str
    pages_scraped: int
    documents_ingested: int
    source: str
    timestamp: str
    message: Optional[str] = None


@router.post("/ingest/mgit", response_model=IngestMgitResponse)
async def ingest_mgit(
    background_tasks: BackgroundTasks,
    request: IngestMgitRequest = IngestMgitRequest(),
    admin: User = Depends(get_current_admin_user),
):
    """Trigger MGIT website scraping and ingestion (admin only)."""
    # Run in background to avoid timeout
    result = {"status": "started", "message": "Ingestion started in background"}

    async def run_ingestion():
        async with async_session_maker() as session:
            service = IngestionService(session)
            return await service.scrape_and_ingest_mgit(
                start_url=request.start_url,
                max_pages=request.max_pages,
            )

    background_tasks.add_task(run_ingestion)
    return IngestMgitResponse(**result)


@router.post("/ingest/mgit/sync", response_model=IngestMgitResponse)
async def ingest_mgit_sync(
    request: IngestMgitRequest = IngestMgitRequest(),
    admin: User = Depends(get_current_admin_user),
):
    """Trigger MGIT website scraping and ingestion synchronously (admin only)."""
    async with async_session_maker() as session:
        service = IngestionService(session)
        result = await service.scrape_and_ingest_mgit(
            start_url=request.start_url,
            max_pages=request.max_pages,
        )
        return IngestMgitResponse(**result)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: UUID = Depends(get_current_user_id),
    doc_service: DocumentService = Depends(get_document_service),
):
    """Upload a document for processing."""
    # Read file content
    content = await file.read()
    size = len(content)

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename required")

    content_type = file.content_type or "application/octet-stream"

    # Create file-like object
    file_obj = io.BytesIO(content)

    try:
        document = await doc_service.upload_document(
            user_id=user_id,
            file=file_obj,
            filename=file.filename,
            content_type=content_type,
            size=size,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    background_tasks.add_task(process_uploaded_document, document.id)
    return document


async def process_uploaded_document(document_id: UUID) -> None:
    """Extract, chunk and embed an uploaded document in its own DB session."""
    async with async_session_maker() as session:
        await FileProcessingService(session).process_document(document_id)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    user_id: UUID = Depends(get_current_user_id),
    doc_service: DocumentService = Depends(get_document_service),
):
    """List user's documents."""
    return await doc_service.list_user_documents(
        user_id, page=page, page_size=page_size, status=status_filter
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    """Get document details."""
    document = await doc_service.get_document(document_id, user.id, user.is_admin)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    """Clear a document's chunks and run processing again."""
    try:
        document = await doc_service.reset_for_reprocessing(document_id, user.id, user.is_admin)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    background_tasks.add_task(process_uploaded_document, document_id)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    """Delete a document."""
    success = await doc_service.delete_document(document_id, user.id, user.is_admin)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")