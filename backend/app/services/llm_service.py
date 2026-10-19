# ==============================================================================
# CampusGPT Backend — LLM Service
# ==============================================================================
from typing import Optional, AsyncGenerator
from uuid import UUID

from app.ai.base import (
    LLMProvider,
    ChatMessage,
    ChatResponse,
    StreamChunk,
)
from app.ai.openai_adapter import OpenAILLMProvider
from app.ai.local_adapter import LocalLLMProvider
from app.ai.anthropic_adapter import AnthropicLLMProvider
from app.core.config import settings


class LLMService:
    """LLM provider management and chat operations."""

    def __init__(self):
        self._provider: Optional[LLMProvider] = None
        self._initialize_provider()

    def _initialize_provider(self) -> None:
        """Initialize the configured LLM provider."""
        provider_name = settings.llm_provider.lower()

        if provider_name == "openai":
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            self._provider = OpenAILLMProvider()
        elif provider_name == "local":
            if not settings.local_llm_base_url:
                raise ValueError("LOCAL_LLM_BASE_URL is required for local provider")
            self._provider = LocalLLMProvider()
        elif provider_name == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
            self._provider = AnthropicLLMProvider()
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

    @property
    def provider(self) -> LLMProvider:
        """Get the active LLM provider."""
        if not self._provider:
            self._initialize_provider()
        return self._provider

    @property
    def provider_name(self) -> str:
        return self.provider.name

    @property
    def default_model(self) -> str:
        return self.provider.default_model

    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        """Non-streaming chat completion."""
        return await self.provider.chat(messages, model, temperature, max_tokens)

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Streaming chat completion."""
        async for chunk in self.provider.chat_stream(messages, model, temperature, max_tokens):
            yield chunk

    async def health_check(self) -> bool:
        """Check if LLM provider is available."""
        return await self.provider.health_check()


# Global instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service