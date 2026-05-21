"""LLM provider factory."""

from __future__ import annotations

from contextpack.core.config import get_settings
from contextpack.core.protocols import LLMProvider
from contextpack.llm.azure_foundry import AzureFoundryLLM
from contextpack.llm.openai_direct import OpenAIDirectLLM


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider in ("azure", "azure_foundry", "azure-foundry"):
        return AzureFoundryLLM()
    if provider == "openai":
        return OpenAIDirectLLM()
    raise ValueError(
        f"Unknown LLM provider: {provider}. "
        "Use azure_foundry or openai, and set credentials in .env"
    )
