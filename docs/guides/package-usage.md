# Package usage (Python SDK)

## Install as a library

```bash
uv pip install -e .   # editable install from repo root
# or after publish: pip install contextpack
```

---

## Minimal example

```python
import asyncio
from contextpack import Project

async def main():
    project = Project("./my-service")
    await project.init()
    await project.build()

    ctx = await project.harvest("Explain the payment pipeline")
    print(ctx.extra_instructions)

asyncio.run(main())
```

Runnable script: [`examples/01_basic_package_usage.py`](../../examples/01_basic_package_usage.py)

---

## API surface (`Project`)

| Method | Returns | Description |
|--------|---------|-------------|
| `init()` | — | Create `.contextpack/`, SQLite schema |
| `build()` | `(ProjectMap, BuildStats)` | Full index pipeline; also extracts workflows and saves file hashes |
| `incremental_build()` | `(ProjectMap, BuildStats, ChangeSet)` | Re-parse only changed files; falls back to full build if no baseline |
| `recent_changes(limit=50)` | `list[dict]` | Query the SQLite change log |
| `compile(query, token_budget=8000)` | `ContextPack` | Code-only, token-budgeted pack |
| `harvest(query, branch_name=None)` | `AggregatedAgentContext` | All sources (code + guidelines + tests + optional Jira) |
| `ask(question, use_llm=False)` | `str` | Offline or LLM answer |
| `ask_llm(question, llm=None)` | `str` | Force LLM path |
| `graph_summary()` | `str` | Text graph excerpt |
| `hub_entities(limit=12)` | `list[tuple]` | Top entities by graph degree |
| `workflows()` | `list[dict]` | Workflows extracted during last build |
| `agent_memory(agent_id)` | `AgentMemory` | Per-agent fact store |
| `shared_memory()` | `SharedMemory` | Cross-agent fact view |

---

## Working with context artifacts

### Inspect compiled code memory

```python
pack = await project.compile("authentication middleware", token_budget=4000)
for summary in pack.summaries:
    print(summary)
print(pack.graph_excerpt)
```

### Inject into Cursor

```python
from contextpack.adapters import CursorAdapter

payload = CursorAdapter().inject(agent_ctx)
# payload["extra_instructions"] → attach to agent run
```

### Inject into LangGraph state

```python
from contextpack.adapters import LangGraphAdapter

state_update = LangGraphAdapter().inject(agent_ctx)
# {"state": {"agent_context": {...}}}
```

---

## Custom harvester

```python
from contextpack.harvester import ContextHarvester
from contextpack.harvester.fetchers import CodeContextFetcher, ProductGuidelinesFetcher

harvester = ContextHarvester(fetchers=[
    CodeContextFetcher(),
    ProductGuidelinesFetcher(),
    MyCustomFetcher(),
])

sections = await harvester.harvest("upload pipeline", project_map)
```

---

## Incremental builds (Phase 3)

```python
# First build saves the baseline hashes
pmap, stats = await project.build()

# Subsequent calls only re-parse changed files
pmap, stats, changeset = await project.incremental_build()
print(changeset.summary)                    # "[abc1234] 2 modified, 1 added"
for fc in changeset.files_changed:
    print(fc.change_type, fc.path)

# Query the full change log
rows = await project.recent_changes(limit=20)
```

## Workflow extraction (Phase 5)

```python
# Workflows are extracted during build — no extra step needed
await project.build()

workflows = await project.workflows()
for wf in workflows:
    print(wf["name"], "→", " → ".join(wf.get("steps", [])[:4]))
```

## Multi-agent memory (Phase 5)

```python
# Agent 1 records findings
reviewer = project.agent_memory("reviewer")
await reviewer.store_decision("Use JWT — not session cookies")
await reviewer.store_constraint("Never expose raw user IDs")

# Agent 2 reads everything
shared = project.shared_memory()
facts = await shared.recall_all(query="auth")
prompt_block = await shared.format_for_prompt()
```

## Rebuild policy

- Run `build()` after significant code changes or when switching branches
- Use `incremental_build()` / `context watch` during active coding sessions
- CI: run `build()` for reproducibility; cache `.contextpack/` keyed on source hash

---

## Performance tips

| Setting | Effect |
|---------|--------|
| `CONTEXTPACK_VECTOR_STORE=sqlite` | Fast startup (default) |
| `CONTEXTPACK_EMBEDDING_PROVIDER=hash` | No network for embeddings |
| `chroma` extra + env | Heavier, persistent ANN index |

---

## Related

- [Azure Foundry](azure-foundry.md)
- [Configuration](../reference/configuration.md)
- [Module reference](../reference/modules.md)
