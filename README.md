# ContextPack + Context Harness

**ContextPack** is a universal AI context runtime — graph-native understanding, compression, and multi-source harvesting.

**Context Harness** is the workflow layer on top: Cursor/Claude hooks, MCP tools, skills, and doc/graph validation — the closed loop between *how agents work* and *what they see*.

See [HARNESS.md](HARNESS.md) for the full combo. Inspired by [Helpline’s AI Layer](https://github.com/coleam00/helpline) + ContextPack runtime.

## Meetup-inspired: complete context for agents

Based on domain-aware PR review architecture, ContextPack harvests **parallel context sources** and aggregates them into one agent-ready pack:

| Source | Fetcher | What you get |
|--------|---------|----------------|
| Code | `CodeContextFetcher` | Call graphs, symbols, cross-module deps |
| Product guidelines | `ProductGuidelinesFetcher` | `.pr-review/guidelines.md`, `AGENTS.md`, … |
| Product behaviour | `TestBehaviourFetcher` | Expected behaviour from test names |
| Product intent | `JiraIntentFetcher` | Ticket AC & description (optional) |

The **Context Aggregator** merges these into `<extra_instructions>` with clear headings — ready for Claude, OpenAI, Cursor, or LangGraph.

## Install as a package

```bash
git clone <your-repo>
cd contextharness   # or contextpack

uv sync
uv pip install -e .

# Verify
python -c "from contextpack import Project; print('ok')"
```

Runnable examples: [`examples/README.md`](examples/README.md)

```bash
python examples/01_basic_package_usage.py      # no API key
python examples/02_azure_foundry_agent.py      # Azure Foundry LLM
```

## Quick start (CLI)

```bash
uv sync --extra harness   # MCP server for Cursor
context init ./my-repo
context build ./my-repo
context harvest "review upload pipeline" ./my-repo
context harness orient    # session briefing (same as sessionStart hook)
context harness validate  # AGENTS.md vs graph hubs
```

**Cursor:** enable `.mcp.json` → `context-harness` and use `.cursor/hooks.json` (auto orientation + stop validation).

```bash
context ask "How does authentication work?" ./my-repo
context ask "Explain auth" ./my-repo --llm   # uses Azure Foundry / OpenAI from .env
```

## Python SDK

```python
import asyncio
from contextpack import Project
from contextpack.adapters import AzureFoundryAdapter

async def main():
    project = Project("./repo")
    await project.init()
    await project.build()

    # Complete agent context (code + guidelines + tests + optional Jira)
    agent_ctx = await project.harvest(
        "Explain upload pipeline",
        branch_name="feature/PROJ-123-upload",
    )
    print(agent_ctx.extra_instructions)

    # Offline answer (no cloud API)
    print(await project.ask("How authentication works?"))

    # Azure AI Foundry — uses deployment endpoint, NOT api.openai.com
    answer = await project.ask("How authentication works?", use_llm=True)
    print(answer)

asyncio.run(main())
```

## Azure AI Foundry (not direct OpenAI API)

Use a model **deployed in Azure AI Foundry**. Copy endpoint, key, and deployment name from **Foundry → Deployments**.

```env
CONTEXTPACK_LLM_PROVIDER=azure_foundry
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<foundry-key>
AZURE_OPENAI_DEPLOYMENT=<deployment-name>

# Optional: embeddings from same Foundry resource
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

**Inference project URL** (some Foundry setups use `*.services.ai.azure.com` instead of `*.openai.azure.com`):

```env
AZURE_USE_INFERENCE_ENDPOINT=true
AZURE_AI_INFERENCE_ENDPOINT=https://<project>.services.ai.azure.com
```

See [`examples/02_azure_foundry_agent.py`](examples/02_azure_foundry_agent.py) for a full script.

## CLI

| Command | Description |
|---------|-------------|
| `context init` | Create `.contextpack/` workspace |
| `context build` | Scan → parse → graph → embed → index |
| `context harvest` | Multi-source context aggregation |
| `context ask` | Answer using full harvested context |
| `context graph` | Show graph excerpt |
| `context watch` | Rebuild on file changes |

## Architecture

```text
Repository
    │
    ▼
Scanner → Parsers → ContextGraph (NetworkX)
    │                      │
    ▼                      ▼
Chunking → Embeddings → ChromaDB
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

## Why was startup slow?

Three things caused multi-minute “warm up”:

1. **ChromaDB** — first `import chromadb` pulls in ONNX Runtime (~100MB+) and can take **2–5 minutes** on a cold machine. Default is now **`sqlite`** vector store (instant).
2. **`uv sync`** — the initial install downloaded 118 packages including Chroma, MkDocs, and Mypy (~2+ min). Use `uv sync` without `--all-extras` for a lean dev install.
3. **Eager imports** — parsers and Chroma loaded at import time; these are now **lazy**.

Use Chroma only when you need it:

```bash
uv sync --extra chroma
export CONTEXTPACK_VECTOR_STORE=chroma
```

## Configuration

Copy `.env.example` to `.env`:

- `CONTEXTPACK_LLM_PROVIDER=azure_foundry` — chat via Foundry deployment
- `AZURE_OPENAI_*` — endpoint, key, deployment from Azure AI Foundry
- `CONTEXTPACK_EMBEDDING_PROVIDER=hash` — local, no API key (default)
- `azure_foundry` / `openai` — cloud embeddings
- `JIRA_*` — optional product intent from tickets

## Team guidelines (product context)

Add domain rules for agents:

```text
.pr-review/guidelines.md   # up to 12k chars (meetup convention)
.contextpack/guidelines.md
AGENTS.md
```

If missing, guideline-based checks are skipped gracefully.

## Documentation

Full product & architecture docs (MkDocs):

```bash
uv sync --extra dev
mkdocs serve
```

Open http://127.0.0.1:8000 — or read directly in [`docs/`](docs/index.md).

## Development

```bash
uv sync --extra dev
pytest
ruff check contextpack tests
mypy contextpack
```

## Roadmap

- **Phase 1** ✓ Scanner, parser, graph, embeddings, retrieval
- **Phase 2** ✓ Compiler, harvester, aggregator
- **Phase 3** Watch, incremental updates, git diff memory
- **Phase 4** ✓ Context Harness (hooks, MCP, skills, validate)
- **Phase 5** Multi-agent memory, workflow extraction

## License

MIT
