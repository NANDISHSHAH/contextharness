"""Azure OpenAI / Foundry embedding deployments."""

from __future__ import annotations

from openai import AsyncAzureOpenAI

from contextpack.core.config import get_settings


class AzureFoundryEmbeddingProvider:
    """Embeddings from an Azure Foundry embedding deployment (not OpenAI.com)."""

    def __init__(self, deployment: str | None = None) -> None:
        settings = get_settings()
        self.deployment = deployment or settings.azure_openai_embedding_deployment or ""
        if not self.deployment:
            raise ValueError("AZURE_OPENAI_EMBEDDING_DEPLOYMENT is required for Azure embeddings")

        endpoint = settings.azure_openai_endpoint
        api_key = settings.azure_openai_api_key
        if not endpoint or not api_key:
            raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY required")

        self._client = AsyncAzureOpenAI(
            azure_endpoint=endpoint.rstrip("/"),
            api_key=api_key,
            api_version=settings.azure_openai_api_version,
        )

    async def embed(self, text: str) -> list[float]:
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(model=self.deployment, input=texts)
        return [list(d.embedding) for d in resp.data]
