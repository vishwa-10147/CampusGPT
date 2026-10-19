# ==============================================================================
# CampusGPT Backend — Anthropic (Claude) Adapter
# ==============================================================================
from typing import AsyncGenerator, List, Optional

import anthropic

from app.ai.base import LLMProvider, ChatMessage, ChatResponse, StreamChunk
from app.core.config import settings

DEFAULT_MAX_TOKENS = 16000

# On a safety decline, the API re-runs the request on a fallback model it picks
FALLBACK_HEADERS = {"anthropic-beta": "server-side-fallback-2026-07-01"}
FALLBACK_BODY = {"fallbacks": "default"}


class AnthropicLLMProvider(LLMProvider):
    """Claude via the Anthropic Messages API.

    Embeddings are not offered by Anthropic; pair this with a local or OpenAI
    embedding provider (see EmbeddingService).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        self._api_key = api_key or settings.anthropic_api_key
        self._default_model = default_model or settings.anthropic_model

        if not self._api_key:
            raise ValueError("Anthropic API key is required")

        self._client = anthropic.AsyncAnthropic(api_key=self._api_key)

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def default_model(self) -> str:
        return self._default_model

    @staticmethod
    def _split_system(messages: List[ChatMessage]) -> tuple[str, list[dict]]:
        """The Messages API takes system text separately from the turns."""
        system = "\n\n".join(m.content for m in messages if m.role == "system")
        turns = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        return system, turns

    def _request(self, messages: List[ChatMessage], model: Optional[str], max_tokens: Optional[int]) -> dict:
        # temperature is intentionally not sent: current Claude models reject sampling params
        system, turns = self._split_system(messages)
        request = {
            "model": model or self._default_model,
            "max_tokens": max_tokens or DEFAULT_MAX_TOKENS,
            "messages": turns,
            "extra_headers": FALLBACK_HEADERS,
            "extra_body": FALLBACK_BODY,
        }
        if system:
            request["system"] = system
        return request

    @staticmethod
    def _check_refusal(message) -> None:
        if message.stop_reason == "refusal":
            raise RuntimeError("The model declined to answer this request.")

    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        response = await self._client.messages.create(**self._request(messages, model, max_tokens))
        self._check_refusal(response)
        return ChatResponse(
            content="".join(b.text for b in response.content if b.type == "text"),
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            model=response.model,
        )

    async def chat_stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        async with self._client.messages.stream(**self._request(messages, model, max_tokens)) as stream:
            async for text in stream.text_stream:
                yield StreamChunk(content=text, done=False)
            final = await stream.get_final_message()

        self._check_refusal(final)
        yield StreamChunk(
            content="",
            done=True,
            tokens_used=final.usage.input_tokens + final.usage.output_tokens,
        )

    async def embed(self, texts: List[str], model: Optional[str] = None):
        raise NotImplementedError("Anthropic has no embeddings API; configure a separate embedding provider")

    async def health_check(self) -> bool:
        try:
            # SDK 0.39 has no models resource; call the endpoint through the client
            await self._client.get("/v1/models", cast_to=object, options={"params": {"limit": 1}})
            return True
        except anthropic.APIError:
            return False
