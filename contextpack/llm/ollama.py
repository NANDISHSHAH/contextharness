"""Ollama local model inference (OpenAI-compatible endpoint)."""

from __future__ import annotations

from openai import AsyncOpenAI

from contextpack.core.config import get_settings


class OllamaLLM:
    """
    Chat completions via a locally-running Ollama server.

    Ollama exposes an OpenAI-compatible API. Defaults assume the server
    is running on http://localhost:11434.

    Set in .env:
      CONTEXTPACK_LLM_PROVIDER=ollama
      OLLAMA_BASE_URL=http://localhost:11434   (optional)
      OLLAMA_MODEL=llama3.2                    (optional)
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
        self._model = model or settings.ollama_model

    async def complete(self, system: str, user: str) -> str:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""
