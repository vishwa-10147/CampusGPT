# ==============================================================================
# CampusGPT Backend — OpenAI Adapter
# ==============================================================================
import os
from typing import AsyncGenerator, List, Optional

from openai import AsyncOpenAI

from app.ai.base import (
    LLMProvider,
    EmbeddingProvider,
    ChatMessage,
    ChatResponse,
    StreamChunk,
    EmbeddingResponse,
)
from app.core.config import settings


class OpenAILLMProvider(LLMProvider):
    """OpenAI LLM provider (also works with compatible APIs)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        self._api_key = api_key or settings.openai_api_key
        self._base_url = base_url or settings.openai_base_url
        self._default_model = default_model or settings.openai_model

        if not self._api_key:
            raise ValueError("OpenAI API key is required")

        self._client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )

    @property
    def name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return self._default_model

    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        response = await self._client.chat.completions.create(
            model=model or self._default_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return ChatResponse(
            content=response.choices[0].message.content or "",
            tokens_used=response.usage.total_tokens if response.usage else 0,
            model=response.model,
        )

    async def chat_stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        stream = await self._client.chat.completions.create(
            model=model or self._default_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        total_tokens = 0
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield StreamChunk(content=chunk.choices[0].delta.content, done=False)

            if chunk.usage:
                total_tokens = chunk.usage.total_tokens

        yield StreamChunk(content="", done=True, tokens_used=total_tokens)

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> EmbeddingResponse:
        # Use embeddings model
        embedding_model = model or settings.openai_embedding_model
        response = await self._client.embeddings.create(
            model=embedding_model,
            input=texts,
        )
        return EmbeddingResponse(
            embeddings=[d.embedding for d in response.data],
            tokens_used=response.usage.total_tokens if response.usage else 0,
            model=embedding_model,
        )

    async def health_check(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI Embedding provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        self._api_key = api_key or settings.openai_api_key
        self._base_url = base_url or settings.openai_base_url
        self._default_model = default_model or settings.openai_embedding_model

        if not self._api_key:
            raise ValueError("OpenAI API key is required")

        self._client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )

    @property
    def name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return self._default_model

    @property
    def dimension(self) -> int:
        # text-embedding-3-small = 1536, text-embedding-3-large = 3072
        if "large" in self._default_model:
            return 3072
        return 1536

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> EmbeddingResponse:
        embedding_model = model or self._default_model
        response = await self._client.embeddings.create(
            model=embedding_model,
            input=texts,
        )
        return EmbeddingResponse(
            embeddings=[d.embedding for d in response.data],
            tokens_used=response.usage.total_tokens if response.usage else 0,
            model=embedding_model,
        )

    async def health_check(self) -> bool:
        try:
            await self._client.embeddings.create(
                model=self._default_model,
                input=["test"],
            )
            return True
        except Exception:
            return False