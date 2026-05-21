"""Format context packs for Azure Foundry chat deployments."""

from __future__ import annotations

from contextpack.adapters.claude import ClaudeAdapter
from contextpack.core.models import AggregatedAgentContext, ContextPack


class AzureFoundryAdapter(ClaudeAdapter):
    """
    Returns messages payload for Azure OpenAI / Foundry chat.completions.

    Pair with AzureFoundryLLM.complete(system, user).
    """

    def inject(self, context: ContextPack | AggregatedAgentContext) -> dict:
        payload = super().inject(context)
        return {
            "deployment": None,  # set via AZURE_OPENAI_DEPLOYMENT env
            "messages": [
                {"role": "system", "content": payload["system"]},
                *payload["messages"],
            ],
            "temperature": 0.2,
        }

    def build_prompt(self, context: ContextPack | AggregatedAgentContext) -> tuple[str, str]:
        """Split system + user for AzureFoundryLLM.complete()."""
        payload = super().inject(context)
        return payload["system"], payload["messages"][0]["content"]
