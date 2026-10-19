# ==============================================================================
# CampusGPT Backend — Admin API Routes
# ==============================================================================
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.api.deps import get_current_admin_user, get_document_service
from app.schemas.document import DocumentListResponse, DocumentResponse, DocumentChunkResponse
from app.services.document_service import DocumentService
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/documents", response_model=DocumentListResponse)
async def list_all_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
    doc_service: DocumentService = Depends(get_document_service),
    admin: User = Depends(get_current_admin_user),
):
    """List all documents (admin)."""
    return await doc_service.list_all_documents(
        page=page, page_size=page_size, status=status_filter
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document_admin(
    document_id: UUID,
    doc_service: DocumentService = Depends(get_document_service),
    admin: User = Depends(get_current_admin_user),
):
    """Get document details (admin)."""
    document = await doc_service.get_document(document_id, is_admin=True)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.get("/documents/{document_id}/chunks", response_model=list[DocumentChunkResponse])
async def get_document_chunks(
    document_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    doc_service: DocumentService = Depends(get_document_service),
    admin: User = Depends(get_current_admin_user),
):
    """Get document chunks (admin)."""
    # This would need a new method in DocumentService
    # For now, return empty list
    return []


@router.get("/stats")
async def get_system_stats(
    doc_service: DocumentService = Depends(get_document_service),
    admin: User = Depends(get_current_admin_user),
):
    """Get system statistics (admin)."""
    from app.repositories.user_repo import UserRepository
    from app.repositories.conversation_repo import ConversationRepository
    from app.repositories.document_repo import DocumentRepository
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.database import get_db

    # This would need access to multiple repositories
    # For MVP, return basic stats
    return {
        "message": "Admin stats endpoint - to be implemented with full repository access",
        "admin_user": admin.email,
    }