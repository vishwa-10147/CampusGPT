# ==============================================================================
# CampusGPT Backend — Conversation Schemas
# ==============================================================================
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.message import MessageResponse


class ConversationCreate(BaseModel):
    """Create conversation request."""
    title: Optional[str] = Field(default=None, max_length=500)


class ConversationUpdate(BaseModel):
    """Update conversation request."""
    title: str = Field(..., min_length=1, max_length=500)


class ConversationResponse(BaseModel):
    """Conversation response."""
    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    message_count: int = 0
    last_message_preview: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(ConversationResponse):
    """A single conversation with its messages, oldest first."""
    messages: List[MessageResponse] = []


class ConversationListResponse(BaseModel):
    """Paginated conversation list response."""
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int