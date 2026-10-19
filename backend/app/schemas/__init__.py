# ==============================================================================
# CampusGPT Backend — Schemas Package
# ==============================================================================
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
    MessageResponse as AuthMessageResponse,
)
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
)
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    SourceCitation,
    StreamingToken,
)
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentChunkResponse,
    IngestionJobResponse,
)

__all__ = [
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "UserResponse",
    "AuthMessageResponse",
    # Conversation
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationListResponse",
    # Message
    "MessageCreate",
    "MessageResponse",
    "SourceCitation",
    "StreamingToken",
    # Document
    "DocumentUploadResponse",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentChunkResponse",
    "IngestionJobResponse",
]