# Configuration reference

All settings load from environment variables and optional `.env` via `pydantic-settings`.

---

## Core

| Variable | Default | Description |
|----------|---------|-------------|
| `CONTEXTPACK_EMBEDDING_PROVIDER` | `hash` | `hash`, `openai`, `azure_foundry` |
| `CONTEXTPACK_VECTOR_STORE` | `sqlite` | `sqlite` (fast) or `chroma` (optional extra) |
| `CONTEXTPACK_GUIDELINES_MAX_CHARS` | `12000` | Max chars for guideline files |
| `CONTEXTPACK_LLM_PROVIDER` | _(empty)_ | `azure_foundry` or `openai` when using `--llm` |
| `CONTEXTPACK_MAX_EMBED_ENTITIES` | `2000` | Max entities sent to the embedder per build. Hub nodes (high graph degree) always fill first; entities beyond the cap are stored in SQLite but skipped for vector search. |
| `CONTEXTPACK_EMBED_HUBS_FIRST` | `true` | When `true`, graph hub nodes are always embedded regardless of the cap. Set to `false` to embed strictly in parse order. |

---

## OpenAI (direct API)

| Variable | Required when |
|----------|---------------|
| `OPENAI_API_KEY` | `CONTEXTPACK_EMBEDDING_PROVIDER=openai` or `CONTEXTPACK_LLM_PROVIDER=openai` |

---

## Azure AI Foundry / Azure OpenAI

| Variable | Required when |
|----------|---------------|
| `AZURE_OPENAI_ENDPOINT` | Azure chat or embeddings |
| `AZURE_OPENAI_API_KEY` | Azure chat or embeddings |
| `AZURE_OPENAI_DEPLOYMENT` | Azure chat (`--llm`) |
| `AZURE_OPENAI_API_VERSION` | `2024-10-21` default |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | `azure_foundry` embeddings |

### Inference endpoint (alternative)

| Variable | Description |
|----------|-------------|
| `AZURE_USE_INFERENCE_ENDPOINT` | `true` to use Model Inference URL |
| `AZURE_AI_INFERENCE_ENDPOINT` | e.g. `https://<project>.services.ai.azure.com` |

---

## Jira (optional product intent)

| Variable | Description |
|----------|-------------|
| `JIRA_BASE_URL` | e.g. `https://company.atlassian.net` |
| `JIRA_EMAIL` | Service account email |
| `JIRA_API_TOKEN` | API token |

Ticket id parsed from branch name or query (`PROJ-123`).

---

## Programmatic access

```python
from contextpack.core.config import get_settings

settings = get_settings()
print(settings.vector_store)
print(settings.context_dir(Path("./repo")))
```

---

## Example `.env` profiles

### Offline development

```env
CONTEXTPACK_EMBEDDING_PROVIDER=hash
CONTEXTPACK_VECTOR_STORE=sqlite
CONTEXTPACK_MAX_EMBED_ENTITIES=2000
```

### Azure enterprise

```env
CONTEXTPACK_LLM_PROVIDER=azure_foundry
CONTEXTPACK_EMBEDDING_PROVIDER=azure_foundry
AZURE_OPENAI_ENDPOINT=https://myresource.openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
CONTEXTPACK_VECTOR_STORE=sqlite
```

### Full cloud (OpenAI.com)

```env
OPENAI_API_KEY=sk-...
CONTEXTPACK_EMBEDDING_PROVIDER=openai
CONTEXTPACK_LLM_PROVIDER=openai
```

---

## Ignore rules

The scanner applies three layers in order:

1. **Built-in directory list** — `node_modules`, `.venv`, `dist`, `build`, `.next`, `vendor`, `generated`, and 25+ more.
2. **Built-in file patterns** — `*.d.ts`, `*.min.js`, `*.map`, lock files (`package-lock.json`, `yarn.lock`, etc.), protobuf generated (`*_pb2.py`, `*.pb.go`).
3. **`.gitignore`** — read from repo root, applied via `fnmatch`.
4. **`.contextpackignore`** — same `.gitignore` syntax, project-specific overrides. Place at repo root.

Example `.contextpackignore`:

```
# skip a non-standard build output dir
output/
# skip auto-generated OpenAPI client
src/generated/
# skip all fixture JSON
tests/fixtures/*.json
```

## Related

- [Build performance](../guides/build-performance.md)
- [Azure Foundry guide](../guides/azure-foundry.md)
- [Getting started](../guides/getting-started.md)
