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

| Method | Description |
|--------|-------------|
| `init()` | Create `.contextpack/`, SQLite schema |
| `build()` | Full index pipeline; returns `ProjectMap` |
| `compile(query, token_budget=8000)` | `ContextPack` only (code memory) |
| `harvest(query, branch_name=None)` | `AggregatedAgentContext` (all sources) |
| `ask(question, use_llm=False)` | Offline or LLM answer |
| `ask_llm(question, llm=None)` | Force LLM path |
| `graph_summary()` | Text graph excerpt |

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

## Rebuild policy

- Run `build()` after significant code changes
- Use `context watch` for debounced auto-rebuild (MVP: full rebuild)
- CI: cache `.contextpack/` keyed by `pyproject.lock` + source hash

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
