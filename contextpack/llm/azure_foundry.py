"""
Azure AI Foundry / Azure OpenAI chat completions.

Uses your Foundry deployment endpoint (not api.openai.com).
Works with deployments created in Azure AI Foundry Model Catalog.
"""

from __future__ import annotations

from openai import AsyncAzureOpenAI, AsyncOpenAI

from contextpack.core.config import get_settings


class AzureFoundryLLM:
    """
    Chat via Azure AI Foundry deployment.

    Set in .env (from Foundry → Deployments → endpoint & key):
      AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
      AZURE_OPENAI_API_KEY=...
      AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
    """

    def __init__(
        self,
        *,
        deployment: str | None = None,
        api_version: str | None = None,
        use_inference_endpoint: bool = False,
    ) -> None:
        settings = get_settings()
        self.deployment = deployment or settings.azure_openai_deployment or ""
        self.api_version = api_version or settings.azure_openai_api_version

        if not self.deployment:
            raise ValueError("AZURE_OPENAI_DEPLOYMENT is required")

        api_key = settings.azure_openai_api_key
        if not api_key:
            raise ValueError("AZURE_OPENAI_API_KEY is required")

        if use_inference_endpoint or settings.azure_use_inference_endpoint:
            # Foundry Model Inference / project endpoint (OpenAI-compatible, not api.openai.com)
            base = (settings.azure_ai_inference_endpoint or settings.azure_openai_endpoint or "").rstrip("/")
            if not base:
                raise ValueError("AZURE_AI_INFERENCE_ENDPOINT or AZURE_OPENAI_ENDPOINT is required")
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=base if base.endswith("/v1") else f"{base}/openai/v1",
                default_query={"api-version": self.api_version},
            )
            self._model = self.deployment  # inference routes by deployment/model name in path or body
            self._azure_mode = False
        else:
            endpoint = settings.azure_openai_endpoint
            if not endpoint:
                raise ValueError("AZURE_OPENAI_ENDPOINT is required")
            self._client = AsyncAzureOpenAI(
                azure_endpoint=endpoint.rstrip("/"),
                api_key=api_key,
                api_version=self.api_version,
            )
            self._model = self.deployment
            self._azure_mode = True

    async def complete(self, system: str, user: str) -> str:
        if self._azure_mode:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
            )
        else:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
            )
        return resp.choices[0].message.content or ""
