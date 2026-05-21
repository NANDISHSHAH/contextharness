#!/usr/bin/env python3
"""
Azure AI Foundry model + ContextPack complete agent context.

This uses your Foundry *deployment* endpoint — NOT api.openai.com.

Setup (.env in repo root or export env vars):
  CONTEXTPACK_LLM_PROVIDER=azure_foundry
  AZURE_OPENAI_ENDPOINT=https://<resource-name>.openai.azure.com/
  AZURE_OPENAI_API_KEY=<key-from-foundry-project>
  AZURE_OPENAI_DEPLOYMENT=<deployment-name>     # e.g. gpt-4o, my-gpt-4o

Optional — embeddings from same Foundry resource:
  CONTEXTPACK_EMBEDDING_PROVIDER=azure_foundry
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

Optional — Foundry *inference* project URL (OpenAI-compatible, not classic AOAI path):
  AZURE_USE_INFERENCE_ENDPOINT=true
  AZURE_AI_INFERENCE_ENDPOINT=https://<project>.services.ai.azure.com

Run:
  python examples/02_azure_foundry_agent.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent / "sample_repo"


def _check_env() -> bool:
    required = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print("Missing Azure Foundry env vars:", ", ".join(missing))
        print("Copy .env.example → .env and fill values from Azure AI Foundry → Deployments.")
        return False
    return True


async def main() -> None:
    if not _check_env():
        sys.exit(1)

    from contextpack import Project
    from contextpack.adapters import AzureFoundryAdapter
    from contextpack.llm import AzureFoundryLLM

    project = Project(REPO)
    await project.init()
    await project.build()

    query = "How does authentication work in this codebase?"
    agent_ctx = await project.harvest(query, branch_name="feature/DEMO-1-auth")

    # --- Option A: manual control (adapter + LLM) ---
    adapter = AzureFoundryAdapter()
    system, user_context = adapter.build_prompt(agent_ctx)
    llm = AzureFoundryLLM()
    answer = await llm.complete(
        system,
        f"{user_context}\n\n---\n\n**Question:** {query}",
    )
    print("=== Azure Foundry answer (manual) ===\n")
    print(answer)

    # --- Option B: one-liner on Project ---
    print("\n=== Azure Foundry answer (Project.ask_llm) ===\n")
    answer2 = await project.ask_llm(query, llm=llm)
    print(answer2[:1500])


if __name__ == "__main__":
    if not REPO.exists():
        print(f"Missing sample repo: {REPO}", file=sys.stderr)
        sys.exit(1)
    asyncio.run(main())
