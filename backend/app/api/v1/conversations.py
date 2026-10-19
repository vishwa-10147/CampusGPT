# ==============================================================================
# CampusGPT Backend — Conversations API Routes
# ==============================================================================
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.api.deps import get_current_user_id, get_conversation_service
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
)
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    user_id: UUID = Depends(get_current_user_id),
    conv_service: ConversationService = Depends(get_conversation_service),
):
    """Create a new conversation."""
    return await conv_service.create_conversation(user_id, data)


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: UUID = Depends(get_current_user_id),
    conv_service: ConversationService = Depends(get_conversation_service),
):
    """List user's conversations with pagination."""
    return await conv_service.list_conversations(user_id, page=page, page_size=page_size)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    conv_service: ConversationService = Depends(get_conversation_service),
):
    """Get a conversation with its messages."""
    conversation = await conv_service.get_conversation(conversation_id, user_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    data: ConversationUpdate,
    user_id: UUID = Depends(get_current_user_id),
    conv_service: ConversationService = Depends(get_conversation_service),
):
    """Update conversation title."""
    conversation = await conv_service.update_conversation(conversation_id, user_id, data)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    conv_service: ConversationService = Depends(get_conversation_service),
):
    """Soft delete a conversation."""
    success = await conv_service.delete_conversation(conversation_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")