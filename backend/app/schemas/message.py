# ==============================================================================
# CampusGPT Backend — Message Schemas
# ==============================================================================
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class MessageCreate(BaseModel):
    """Create message request."""
    content: str = Field(..., min_length=1, max_length=50000)
    stream: bool = Field(default=True)


class MessageResponse(BaseModel):
    """Message response."""
    id: UUID
    conversation_id: UUID
    role: str  # "user" | "assistant" | "system"
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    tokens_used: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SourceCitation(BaseModel):
    """Source citation for RAG responses."""
    document_id: UUID
    filename: str
    chunk_index: int
    page_number: Optional[int] = None
    similarity_score: float
    text_snippet: str


class StreamingToken(BaseModel):
    """Single token in streaming response."""
    token: str
    message_id: Optional[UUID] = None
    done: bool = False
    sources: Optional[List[SourceCitation]] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None