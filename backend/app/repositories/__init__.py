# ==============================================================================
# CampusGPT Backend — Repositories Package
# ==============================================================================
from app.repositories.base import BaseRepository
from app.repositories.user_repo import UserRepository
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.document_repo import DocumentRepository, DocumentChunkRepository, IngestionJobRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ConversationRepository",
    "MessageRepository",
    "DocumentRepository",
    "DocumentChunkRepository",
    "IngestionJobRepository",
]