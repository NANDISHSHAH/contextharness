"""Ollama local embeddings (OpenAI-compatible endpoint)."""

from __future__ import annotations

from openai import AsyncOpenAI

from contextpack.core.config import get_settings


class OllamaEmbeddingProvider:
    """
    Embeddings via a locally-running Ollama server.

    Requires an embedding-capable model to be pulled, e.g.:
      ollama pull nomic-embed-text

    Set in .env:
      CONTEXTPACK_EMBEDDING_PROVIDER=ollama
      OLLAMA_BASE_URL=http://localhost:11434       (optional)
      OLLAMA_EMBEDDING_MODEL=nomic-embed-text      (optional)
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()
        base = (base_url or settings.ollama_base_url).rstrip("/")
        if not base.endswith("/v1"):
            base = f"{base}/v1"
        self._client = AsyncOpenAI(
            api_key=settings.ollama_api_key or "ollama",
            base_url=base,
        )
        self.model = model or settings.ollama_embedding_model

    async def embed(self, text: str) -> list[float]:
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(model=self.model, input=texts)
        return [list(d.embedding) for d in resp.data]
