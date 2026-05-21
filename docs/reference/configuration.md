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

## Related

- [Azure Foundry guide](../guides/azure-foundry.md)
- [Getting started](../guides/getting-started.md)
