# ==============================================================================
# CampusGPT Backend — AI Package
# ==============================================================================
from app.ai.base import (
    LLMProvider,
    EmbeddingProvider,
    ChatMessage,
    ChatResponse,
    StreamChunk,
    EmbeddingResponse,
)
from app.ai.openai_adapter import OpenAILLMProvider, OpenAIEmbeddingProvider
from app.ai.local_adapter import LocalLLMProvider, LocalEmbeddingProvider

__all__ = [
    # Base
    "LLMProvider",
    "EmbeddingProvider",
    "ChatMessage",
    "ChatResponse",
    "StreamChunk",
    "EmbeddingResponse",
    # OpenAI
    "OpenAILLMProvider",
    "OpenAIEmbeddingProvider",
    # Local
    "LocalLLMProvider",
    "LocalEmbeddingProvider",
]