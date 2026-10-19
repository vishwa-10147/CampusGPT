# ==============================================================================
# CampusGPT Backend — Local LLM Adapter (Ollama, LM Studio, vLLM)
# ==============================================================================
import asyncio
from typing import AsyncGenerator, List, Optional

import httpx

from app.ai.base import (
    LLMProvider,
    EmbeddingProvider,
    ChatMessage,
    ChatResponse,
    StreamChunk,
    EmbeddingResponse,
)
from app.core.config import settings


class LocalLLMProvider(LLMProvider):
    """Local LLM provider (Ollama, LM Studio, vLLM - OpenAI compatible)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        api_key: str = "not-needed",
    ):
        self._base_url = (base_url or settings.local_llm_base_url or "").rstrip("/")
        self._default_model = default_model or settings.local_llm_model

        if not self._base_url:
            raise ValueError("Local LLM base URL is required")

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=120.0,
            headers={"Authorization": f"Bearer {api_key}"} if api_key != "not-needed" else {},
        )

    @property
    def name(self) -> str:
        return "local"

    @property
    def default_model(self) -> str:
        return self._default_model or "unknown"

    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        payload = {
            "model": model or self._default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        response = await self._client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        return ChatResponse(
            content=data["choices"][0]["message"]["content"] or "",
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
            model=data.get("model", self._default_model),
        )

    async def chat_stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        payload = {
            "model": model or self._default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        async with self._client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            total_tokens = 0
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        import json
                        data = json.loads(data_str)
                        if data["choices"] and data["choices"][0].get("delta", {}).get("content"):
                            yield StreamChunk(content=data["choices"][0]["delta"]["content"], done=False)
                        if data.get("usage"):
                            total_tokens = data["usage"].get("total_tokens", 0)
                    except json.JSONDecodeError:
                        continue

            yield StreamChunk(content="", done=True, tokens_used=total_tokens)

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> EmbeddingResponse:
        raise NotImplementedError("Local embedding not implemented. Use a dedicated embedding provider.")

    async def health_check(self) -> bool:
        try:
            response = await self._client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        await self._client.aclose()


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider (Ollama, etc.)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        self._base_url = (base_url or settings.local_llm_base_url or "").rstrip("/")
        self._default_model = default_model or settings.local_embedding_model

        if not self._base_url:
            raise ValueError("Local LLM base URL is required")

        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=60.0)
        # Semaphore to limit concurrent requests to Ollama
        self._semaphore = asyncio.Semaphore(2)  # Max 2 concurrent requests

    @property
    def name(self) -> str:
        return "local"

    @property
    def default_model(self) -> str:
        return self._default_model or "unknown"

    @property
    def dimension(self) -> int:
        if "nomic" in (self._default_model or "").lower():
            return 768
        if "mxbai" in (self._default_model or "").lower():
            return 1024
        return 768

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> EmbeddingResponse:
        embedding_model = model or self._default_model
        all_embeddings = []

        for text in texts:
            # Use semaphore to limit concurrent requests
            async with self._semaphore:
                # Retry up to 3 times
                for attempt in range(3):
                    try:
                        # Truncate to 4000 chars to avoid Ollama 500 errors
                        truncated_text = text[:4000]
                        response = await self._client.post(
                            "/api/embeddings",
                            json={"model": embedding_model, "prompt": truncated_text},
                            timeout=60.0,
                        )

                        if response.status_code != 200:
                            error_text = response.text[:200] if response.text else "No response body"
                            print(f"Ollama API error {response.status_code}: {error_text}")
                            if attempt < 2:
                                await asyncio.sleep(1 * (attempt + 1))
                                continue
                            all_embeddings.append([0.0] * self.dimension)
                            break

                        if not response.content:
                            if attempt < 2:
                                await asyncio.sleep(1)
                                continue
                            all_embeddings.append([0.0] * self.dimension)
                            break

                        try:
                            data = response.json()
                        except Exception as e:
                            print(f"JSON parse error: {e}, response text: {response.text[:200]}")
                            if attempt < 2:
                                await asyncio.sleep(1)
                                continue
                            all_embeddings.append([0.0] * self.dimension)
                            break

                        if data is None:
                            if attempt < 2:
                                await asyncio.sleep(1)
                                continue
                            all_embeddings.append([0.0] * self.dimension)
                            break

                        if not isinstance(data, dict):
                            print(f"Unexpected data type: {type(data)}, value: {data}")
                            if attempt < 2:
                                await asyncio.sleep(1)
                                continue
                            all_embeddings.append([0.0] * self.dimension)
                            break

                        if "embedding" in data:
                            all_embeddings.append(data["embedding"])
                            break
                        else:
                            print(f"Unexpected response format: {data}")
                            if attempt < 2:
                                await asyncio.sleep(1)
                                continue
                            all_embeddings.append([0.0] * self.dimension)
                            break

                    except Exception as e:
                        if attempt < 2:
                            await asyncio.sleep(1 * (attempt + 1))
                            continue
                        print(f"Error embedding text after retries: {e}")
                        all_embeddings.append([0.0] * self.dimension)
                        break

        return EmbeddingResponse(
            embeddings=all_embeddings,
            tokens_used=0,
            model=embedding_model,
        )

    async def health_check(self) -> bool:
        try:
            response = await self._client.post(
                "/api/embeddings",
                json={"model": self._default_model, "prompt": "test"},
                timeout=10.0,
            )
            if response.status_code != 200:
                return False
            data = response.json()
            return data is not None and "embedding" in data
        except Exception:
            return False

    async def close(self):
        await self._client.aclose()