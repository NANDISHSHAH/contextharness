# ContextPack + Context Harness

[License: MIT](LICENSE)
[Python 3.11+](https://www.python.org/downloads/)
[Version](pyproject.toml)

**ContextPack** is a universal AI context runtime — graph-native code understanding, compression, and multi-source harvesting for any repository.

**Context Harness** is the workflow layer on top: Cursor/Claude hooks, MCP tools, skills, and doc/graph validation — a closed loop between *how agents work* and *what they see*. Phases 6–9 extend the harness with deterministic skill gates, semantic contract verification, trust-aware context compilation, and adaptive self-improvement.

See [HARNESS.md](HARNESS.md) for the full architecture.

---

## How it works

ContextPack harvests **parallel context sources** and aggregates them into one agent-ready pack:


| Source         | Fetcher                    | What you get                            |
| -------------- | -------------------------- | --------------------------------------- |
| Code           | `CodeContextFetcher`       | Call graphs, symbols, cross-module deps |
| Guidelines     | `ProductGuidelinesFetcher` | `.pr-review/guidelines.md`, `AGENTS.md` |
| Test behaviour | `TestBehaviourFetcher`     | Expected behaviour names from tests     |
| Product intent | `JiraIntentFetcher`        | Ticket AC & description (optional)      |


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
>
> - `uv sync --extra harness` — MCP server for Cursor / Claude
> - `uv sync --extra chroma` — ChromaDB vector store (default is SQLite, no extra needed)
> - `uv sync --extra dev` — tests, linting, MkDocs

### Run `context` from anywhere (Optional)

To use the `context` command from any directory without `uv run`, add this alias to your shell config:

**For bash** (`~/.bashrc`):
```bash
alias context='(cd /path/to/contextharness && uv run context)'
```

**For zsh** (`~/.zshrc`):
```bash
alias context='(cd /path/to/contextharness && uv run context)'
```

Then reload your shell:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

Now you can run `context` from any directory:
```bash
context init /path/to/any/repo
context build /path/to/any/repo --vibe
```

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

```bash
# Phase 6 — skill gates before edits
context skills plan "src/auth/middleware.py,src/auth/tokens.py" ./my-repo
context skills run  "src/auth/middleware.py" ./my-repo --blast-radius 8

# Phase 7 — semantic contracts
context contracts show validate_token ./my-repo
context contracts check ./my-repo

# Phase 8 — context health
context debt ./my-repo

# Phase 9 — adaptive intelligence
context coupling ./my-repo
context patterns ./my-repo
```

**Cursor:** enable `.mcp.json` → `context-harness` server and drop `.cursor/hooks.json` into your repo for automatic session orientation and stop validation.

---

## CLI reference


| Command                   | Description                                                            |
| ------------------------- | ---------------------------------------------------------------------- |
| `context init`            | Create `.contextpack/` workspace                                       |
| `context build`           | Scan → parse → graph → embed → index + extract workflows               |
| `context build --vibe`    | Same, with animated Pac-Man display and token/cost summary             |
| `context harvest`         | Multi-source context aggregation                                       |
| `context ask`             | Answer a question using harvested context                              |
| `context ask --vibe`      | Same, with thinking spinner and token trace panel                      |
| `context graph`           | Show a graph excerpt                                                   |
| `context watch`           | Watch for changes and rebuild incrementally                            |
| `context changes`         | Show file changes from incremental builds                              |
| `context workflows`       | List workflows extracted from the codebase                             |
| `context skills plan`     | Compute SkillPlan: risk score, policies, required gates *(Phase 6)*    |
| `context skills run`      | Run full gate: route → enforce → execute → record evidence *(Phase 6)* |
| `context skills history`  | Evidence bundle audit trail *(Phase 6)*                                |
| `context contracts show`  | Show extracted contracts for a symbol *(Phase 7)*                      |
| `context contracts check` | Validate invariants.yml rules against codebase *(Phase 7)*             |
| `context debt`            | Per-module context debt report *(Phase 8)*                             |
| `context locks`           | Active agent file locks / conflict table *(Phase 8)*                   |
| `context patterns`        | Recurring skill failure patterns with proactive hints *(Phase 9)*      |
| `context coupling`        | Architectural coupling trend (last 30 days) *(Phase 9)*                |
| `context snapshots`       | List / diff semantic state snapshots *(Phase 9)*                       |


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

Runnable examples: `[examples/README.md](examples/README.md)`

```bash
python examples/01_basic_package_usage.py      # no API key needed
python examples/02_azure_foundry_agent.py      # requires Azure Foundry env vars
python examples/03_incremental_watch.py        # incremental builds + change log
python examples/04_workflows_agent_memory.py   # workflow extraction + shared memory
python examples/05_skill_engine.py             # Phase 6 — skill gates (no API key)
python examples/06_contracts.py                # Phase 7 — semantic contracts
python examples/07_governance.py               # Phase 8 — trust, debt, locks
python examples/08_adaptive.py                 # Phase 9 — failure patterns, coupling, playbook
```

### Phase 6 — skill gate before an edit

```python
from contextpack.skills import SkillManifest, SkillVerifierLoop
from pathlib import Path

manifest = SkillManifest.load(Path("./my-repo"))
loop = SkillVerifierLoop(Path(".contextpack/memory.db"))

result = await loop.verify(
    changed_files=["src/auth/middleware.py"],
    repo_path=Path("./my-repo"),
    manifest=manifest,
    blast_radius=12,
    hub_centralities={"src/auth/middleware.py": 0.91},
    agent_id="my_agent",
)
print(result.to_text())
# ✅ ALLOWED  risk: 0.73  blast_radius: 12
# Evidence bundle: act_8f3k2
```

### Phase 7 — semantic contracts

```python
from contextpack.contracts import ContractExtractor, IntentPreserver
from pathlib import Path

# Extract contracts from AST
extractor = ContractExtractor()
contracts = extractor.extract_from_file(
    Path("src/auth/tokens.py"),
    Path("src/auth/tokens.py").read_text(),
)
# → preconditions, postconditions, raises, trust_score per symbol

# Check a proposed patch against test-inferred invariants
preserver = IntentPreserver()
invariants = preserver.extract_invariants(list(Path("tests/").rglob("test_*.py")))
result = preserver.check_preserved(invariants, proposed_code, "validate_token")
print(result.ok, result.violations)
```

### Phase 8 — trust-aware context

```python
from contextpack.governance import TrustScorer, AgentLockTable

# Score context chunks by source trust tier
scorer = TrustScorer()
score = scorer.score_chunk("test", "tests/test_auth.py", days_since_modified=2, ci_verified=True, test_coverage=0.94)
print(score.label, score.score)   # T1:GroundTruth  1.0

# Multi-agent conflict detection
locks = AgentLockTable(Path(".contextpack/memory.db"))
await locks.acquire("agent_a", files=["src/auth/tokens.py"])
conflict = await locks.check_conflicts("agent_b", files=["src/auth/tokens.py"], symbols=[])
print(conflict.to_text())
```

### Phase 9 — adaptive intelligence

```python
from contextpack.adaptive import FailurePatternStore, PlaybookLearner, CouplingMonitor

# Proactive failure briefing
store = FailurePatternStore(Path(".contextpack/memory.db"))
patterns = await store.list_proactive("src/auth/middleware.py")
for p in patterns:
    print(p.to_briefing())

# Auto-propose skills.yml entries from evidence
learner = PlaybookLearner()
proposals = learner.propose([b.model_dump() for b in bundles])
print(learner.format_proposals(proposals))

# Architectural coupling decay
monitor = CouplingMonitor(Path(".contextpack/memory.db"))
trend = await monitor.trend(days=30)
print(trend.to_text())
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

See `[examples/02_azure_foundry_agent.py](examples/02_azure_foundry_agent.py)` for a complete working script.

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
HybridRetriever → ContextCompiler (token budget + trust-aware filtering)
    │
    ▼
ContextHarvester (parallel fetchers)
    │
    ▼
ContextAggregator → AggregatedAgentContext
    │
    ▼
Adapters (Claude / OpenAI / Cursor / LangGraph)
    │
    ▼
Context Harness
    ├── Skills Engine  (manifest → router → DAG executor → verifier → evidence)   [Phase 6]
    ├── Contract Layer (extractor → registry → invariant guard → intent preserver) [Phase 7]
    ├── Governance     (trust tiers → debt scores → provenance chains → locks)     [Phase 8]
    └── Adaptive       (failure patterns → coupling monitor → playbook learner)    [Phase 9]
```

---

## Configuration

Copy `.env.example` to `.env` and set the relevant keys:


| Variable                         | Purpose                                               |
| -------------------------------- | ----------------------------------------------------- |
| `CONTEXTPACK_LLM_PROVIDER`       | `azure_foundry` or `openai`                           |
| `AZURE_OPENAI_*`                 | Endpoint, key, deployment from Azure AI Foundry       |
| `CONTEXTPACK_EMBEDDING_PROVIDER` | `hash` (local, default), `azure_foundry`, or `openai` |
| `CONTEXTPACK_VECTOR_STORE`       | `sqlite` (default) or `chroma`                        |
| `JIRA_*`                         | Optional — product intent from Jira tickets           |


---

## Team guidelines

Place domain rules for agents in any of these files; ContextPack picks them up automatically:

```
.pr-review/guidelines.md
.contextpack/guidelines.md
AGENTS.md
```

If none are present, guideline-based checks are skipped gracefully.

For skill policies and architectural invariants:

```
.contextpack/skills.yml      ← which gates run on which files (Phase 6)
.contextpack/invariants.yml  ← architectural rules: no_direct_import, no_cycles (Phase 7)
```

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

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) or read directly in `[docs/](docs/index.md)`.

Key guides:


| Guide                                                             | What you learn                                   |
| ----------------------------------------------------------------- | ------------------------------------------------ |
| [Getting started](docs/guides/getting-started.md)                 | Install, first build, first harvest              |
| [Build performance](docs/guides/build-performance.md)             | Tiered embedding, skip patterns, timing          |
| [Incremental builds](docs/guides/incremental-builds.md)           | File-hash delta, watch mode, change log          |
| [Workflows & agent memory](docs/guides/workflows-agent-memory.md) | Call chain extraction, per-agent + shared memory |
| [Context Harness](docs/guides/context-harness.md)                 | Hooks, MCP, skills, validation                   |
| [Azure AI Foundry](docs/guides/azure-foundry.md)                  | On-prem/VNet setup                               |
| [Architecture overview](docs/architecture/overview.md)            | Full system design                               |
| [Next phases plan](docs/product/PLAN_NEXT_PHASES.md)              | Phases 6–9 design & research backing             |


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


| Phase | Status | Scope                                                                                                 |
| ----- | ------ | ----------------------------------------------------------------------------------------------------- |
| 1     | Done   | Scanner, parser, graph, embeddings, retrieval                                                         |
| 2     | Done   | Compiler, harvester, aggregator                                                                       |
| 3     | Done   | Incremental watch mode, file-hash delta tracking, git-diff change log                                 |
| 4     | Done   | Context Harness — hooks, MCP, skills, validate                                                        |
| 5     | Done   | WorkflowExtractor (call chains, API surface, class lifecycles), multi-agent shared memory             |
| 6     | Done   | Pre-Skill Engine — skill manifest, router, DAG executor, blast radius enforcement, evidence audit     |
| 7     | Done   | Semantic Contract Layer — AST extraction, registry, invariant guard, intent preserver, anti-patterns  |
| 8     | Done   | Context Governance & Trust — 5-tier scoring, debt tracker, provenance chains, agent lock table        |
| 9     | Done   | Adaptive Intelligence — failure pattern memory, coupling monitor, context snapshots, playbook learner |


---

## License

MIT — see [LICENSE](LICENSE).