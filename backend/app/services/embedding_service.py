# ==============================================================================
# CampusGPT Backend — Embedding Service
# ==============================================================================
from typing import List, Optional

from app.ai.base import EmbeddingProvider, EmbeddingResponse
from app.ai.openai_adapter import OpenAIEmbeddingProvider
from app.ai.local_adapter import LocalEmbeddingProvider
from app.core.config import settings


class EmbeddingService:
    """Embedding provider management."""

    def __init__(self):
        self._provider: Optional[EmbeddingProvider] = None
        self._initialize_provider()

    def _initialize_provider(self) -> None:
        """Initialize the configured embedding provider."""
        # For MVP, embedding provider follows LLM provider
        provider_name = settings.llm_provider.lower()

        if provider_name == "openai":
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")
            self._provider = OpenAIEmbeddingProvider()
        elif provider_name == "local":
            if not settings.local_llm_base_url:
                raise ValueError("LOCAL_LLM_BASE_URL is required for local embeddings")
            self._provider = LocalEmbeddingProvider()
        else:
            raise ValueError(f"Unknown embedding provider: {provider_name}")

    @property
    def provider(self) -> EmbeddingProvider:
        if not self._provider:
            self._initialize_provider()
        return self._provider

    @property
    def dimension(self) -> int:
        return self.provider.dimension

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> EmbeddingResponse:
        """Generate embeddings for texts."""
        # Process in batches to avoid token limits
        batch_size = 100
        all_embeddings = []
        total_tokens = 0

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = await self.provider.embed(batch, model)
            all_embeddings.extend(response.embeddings)
            total_tokens += response.tokens_used

        return EmbeddingResponse(
            embeddings=all_embeddings,
            tokens_used=total_tokens,
            model=model or self.provider.default_model,
        )

    async def embed_single(self, text: str, model: Optional[str] = None) -> List[float]:
        """Generate embedding for a single text."""
        response = await self.embed([text], model)
        return response.embeddings[0]

    async def health_check(self) -> bool:
        return await self.provider.health_check()


# Global instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service