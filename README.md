# ContextPack + Context Harness

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0--alpha-orange)](pyproject.toml)

**ContextPack** is a universal AI context runtime — graph-native code understanding, compression, and multi-source harvesting for any repository.

**Context Harness** is the workflow layer on top: Cursor/Claude hooks, MCP tools, skills, and doc/graph validation — a closed loop between _how agents work_ and _what they see_.

See [HARNESS.md](HARNESS.md) for the full architecture.

---

## How it works

ContextPack harvests **parallel context sources** and aggregates them into one agent-ready pack:

| Source | Fetcher | What you get |
|--------|---------|--------------|
| Code | `CodeContextFetcher` | Call graphs, symbols, cross-module deps |
| Guidelines | `ProductGuidelinesFetcher` | `.pr-review/guidelines.md`, `AGENTS.md` |
| Test behaviour | `TestBehaviourFetcher` | Expected behaviour names from tests |
| Product intent | `JiraIntentFetcher` | Ticket AC & description (optional) |

The **Context Aggregator** merges these into an `<extra_instructions>` block ready for Claude, OpenAI, Cursor, or LangGraph.

---

## Install

```bash
git clone git@github.com:NANDISHSHAH/contextharness.git
cd contextharness

uv sync
uv pip install -e .

# Verify
python -c "from contextpack import Project; print('ok')"
```

> **Optional extras**
> - `uv sync --extra harness` — MCP server for Cursor / Claude
> - `uv sync --extra chroma` — ChromaDB vector store (default is SQLite, no extra needed)
> - `uv sync --extra dev` — tests, linting, MkDocs

---

## Quick start (CLI)

```bash
context init ./my-repo
context build ./my-repo           # plain summary table
context build ./my-repo --vibe    # animated Pac-Man display + token/cost footer
context harvest "review upload pipeline" ./my-repo
context harness orient    # session briefing
context harness validate  # check AGENTS.md vs graph hubs
```

```bash
context ask "How does authentication work?" ./my-repo
context ask "Explain auth" ./my-repo --vibe   # thinking spinner + token trace
context ask "Explain auth" ./my-repo --llm    # uses Azure Foundry / OpenAI from .env
```

**Cursor:** enable `.mcp.json` → `context-harness` server and drop `.cursor/hooks.json` into your repo for automatic session orientation and stop validation.

---

## CLI reference

| Command | Description |
|---------|-------------|
| `context init` | Create `.contextpack/` workspace |
| `context build` | Scan → parse → graph → embed → index + extract workflows |
| `context build --vibe` | Same, with animated Pac-Man display and token/cost summary |
| `context harvest` | Multi-source context aggregation |
| `context ask` | Answer a question using harvested context |
| `context ask --vibe` | Same, with thinking spinner and token trace panel |
| `context graph` | Show a graph excerpt |
| `context watch` | Watch for changes and rebuild incrementally |
| `context changes` | Show file changes from incremental builds |
| `context workflows` | List workflows extracted from the codebase |

---

## Python SDK

```python
import asyncio
from contextpack import Project

async def main():
    project = Project("./repo")
    await project.init()
    await project.build()

    # Full agent context: code + guidelines + tests + optional Jira
    agent_ctx = await project.harvest(
        "Explain upload pipeline",
        branch_name="feature/PROJ-123-upload",
    )
    print(agent_ctx.extra_instructions)

    # Offline answer — no cloud API required
    print(await project.ask("How does authentication work?"))

asyncio.run(main())
```

Runnable examples: [`examples/README.md`](examples/README.md)

```bash
python examples/01_basic_package_usage.py      # no API key needed
python examples/02_azure_foundry_agent.py      # requires Azure Foundry env vars
```

---

## Azure AI Foundry

Use a model deployed in **Azure AI Foundry**. Copy the endpoint, key, and deployment name from **Foundry → Deployments**.

```env
CONTEXTPACK_LLM_PROVIDER=azure_foundry
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_DEPLOYMENT=<deployment-name>

# Optional: embeddings from the same Foundry resource
CONTEXTPACK_EMBEDDING_PROVIDER=azure_foundry
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
```

```python
from contextpack.llm import AzureFoundryLLM
from contextpack.adapters import AzureFoundryAdapter

ctx = await project.harvest("How does auth work?")
system, user = AzureFoundryAdapter().build_prompt(ctx)
llm = AzureFoundryLLM()
answer = await llm.complete(system, f"{user}\n\nQuestion: How does auth work?")
```

Some Foundry setups use an inference project URL (`*.services.ai.azure.com`) instead of the OpenAI-compatible endpoint:

```env
AZURE_USE_INFERENCE_ENDPOINT=true
AZURE_AI_INFERENCE_ENDPOINT=https://<project>.services.ai.azure.com
```

See [`examples/02_azure_foundry_agent.py`](examples/02_azure_foundry_agent.py) for a complete working script.

---

## Architecture

```text
Repository
    │
    ▼
Scanner → Parsers → ContextGraph (NetworkX)
    │                      │
    ▼                      ▼
Chunking → Embeddings → SQLite (default) / ChromaDB (optional)
    │
    ▼
HybridRetriever → ContextCompiler (token budget)
    │
    ▼
ContextHarvester (parallel fetchers)
    │
    ▼
ContextAggregator → AggregatedAgentContext
    │
    ▼
Adapters (Claude / OpenAI / Cursor / LangGraph)
```

---

## Configuration

Copy `.env.example` to `.env` and set the relevant keys:

| Variable | Purpose |
|----------|---------|
| `CONTEXTPACK_LLM_PROVIDER` | `azure_foundry` or `openai` |
| `AZURE_OPENAI_*` | Endpoint, key, deployment from Azure AI Foundry |
| `CONTEXTPACK_EMBEDDING_PROVIDER` | `hash` (local, default), `azure_foundry`, or `openai` |
| `CONTEXTPACK_VECTOR_STORE` | `sqlite` (default) or `chroma` |
| `JIRA_*` | Optional — product intent from Jira tickets |

---

## Team guidelines

Place domain rules for agents in any of these files; ContextPack picks them up automatically:

```
.pr-review/guidelines.md
.contextpack/guidelines.md
AGENTS.md
```

If none are present, guideline-based checks are skipped gracefully.

---

## Demo

Run the tiny-api sample app (builds in under a second):

```bash
chmod +x demo/scripts/*.sh
./demo/scripts/demo-01-setup.sh    # install harness on tiny-api
./demo/scripts/demo-02-build.sh    # build index with timing
./demo/scripts/demo-03-harvest.sh "review auth and billing"
```

- [demo/USER-JOURNEY.md](demo/USER-JOURNEY.md) — visual walkthrough with Mermaid flows
- [demo/tiny-api/](demo/tiny-api/) — the sample app

---

## Documentation

Full product and architecture docs (MkDocs):

```bash
uv sync --extra dev
mkdocs serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) or read directly in [`docs/`](docs/index.md).

---

## Development

```bash
uv sync --extra dev
pytest
ruff check contextpack tests
mypy contextpack
```

---

## Roadmap

| Phase | Status | Scope |
|-------|--------|-------|
| 1 | Done | Scanner, parser, graph, embeddings, retrieval |
| 2 | Done | Compiler, harvester, aggregator |
| 3 | Done | Incremental watch mode, file-hash delta tracking, git-diff change log |
| 4 | Done | Context Harness — hooks, MCP, skills, validate |
| 5 | Done | WorkflowExtractor (call chains, API surface, class lifecycles), multi-agent shared memory |

---

## License

MIT — see [LICENSE](LICENSE).
