# ==============================================================================
# CampusGPT Backend — AI Provider Abstraction
# ==============================================================================
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional
from dataclasses import dataclass


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class ChatResponse:
    """Complete chat response (non-streaming)."""
    content: str
    tokens_used: int
    model: str


@dataclass
class StreamChunk:
    """A single chunk in a streaming response."""
    content: str
    done: bool = False
    tokens_used: Optional[int] = None


@dataclass
class EmbeddingResponse:
    """Embedding response."""
    embeddings: List[List[float]]
    tokens_used: int
    model: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model name."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        """Non-streaming chat completion."""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Streaming chat completion."""
        pass

    @abstractmethod
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> EmbeddingResponse:
        """Generate embeddings for texts."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is available."""
        pass


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers (separate from LLM for flexibility)."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension."""
        pass

    @abstractmethod
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> EmbeddingResponse:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass