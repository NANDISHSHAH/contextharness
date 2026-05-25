"""Swappable embedding providers."""

from __future__ import annotations

import hashlib
import math

from contextpack.core.config import get_settings


class HashEmbeddingProvider:
    """Deterministic local embeddings — no API key required."""

    dim = 384

    async def embed(self, text: str) -> list[float]:
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [_hash_vector(t, self.dim) for t in texts]


class OpenAIEmbeddingProvider:
    def __init__(self, model: str = "text-embedding-3-small") -> None:
        self.model = model
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY required for OpenAI embeddings")
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def embed(self, text: str) -> list[float]:
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(model=self.model, input=texts)
        return [list(d.embedding) for d in resp.data]


def get_embedding_provider():
    settings = get_settings()
    provider = settings.embedding_provider.lower()
    if provider == "openai":
        return OpenAIEmbeddingProvider()
    if provider in ("azure", "azure_foundry"):
        from contextpack.embeddings.azure import AzureFoundryEmbeddingProvider

        return AzureFoundryEmbeddingProvider()
    if provider == "ollama":
        from contextpack.embeddings.ollama import OllamaEmbeddingProvider

        return OllamaEmbeddingProvider()
    return HashEmbeddingProvider()


def _hash_vector(text: str, dim: int) -> list[float]:
    digest = hashlib.sha256(text.encode()).digest()
    vals: list[float] = []
    for i in range(dim):
        b = digest[i % len(digest)]
        vals.append((b / 127.5) - 1.0)
    norm = math.sqrt(sum(v * v for v in vals)) or 1.0
    return [v / norm for v in vals]
