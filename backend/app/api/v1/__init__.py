# ==============================================================================
# CampusGPT Backend — API v1 Package
# ==============================================================================
from app.api.v1 import auth, conversations, messages, documents, admin

__all__ = ["auth", "conversations", "messages", "documents", "admin"]