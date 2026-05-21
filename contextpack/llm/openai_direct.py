"""Direct OpenAI API (api.openai.com) — not Azure."""

from __future__ import annotations

from openai import AsyncOpenAI

from contextpack.core.config import get_settings


class OpenAIDirectLLM:
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY required for direct OpenAI")
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = model

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
