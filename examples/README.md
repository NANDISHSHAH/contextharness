# ContextPack examples

## Install the package first

```bash
cd /path/to/contextharness
uv sync
uv pip install -e .
```

## 1 — Basic package usage (no cloud API)

```bash
python examples/01_basic_package_usage.py
```

Shows: `Project` → `build()` → `harvest()` → adapter injection → offline `ask()`.

## 2 — Azure AI Foundry model (not direct OpenAI API)

1. In [Azure AI Foundry](https://ai.azure.com), open your project → **Deployments**.
2. Copy **Endpoint**, **Key**, and **Deployment name**.
3. Configure `.env`:

```env
CONTEXTPACK_LLM_PROVIDER=azure_foundry
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=your-chat-deployment

# optional: better embeddings from same resource
CONTEXTPACK_EMBEDDING_PROVIDER=azure_foundry
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
```

4. Run:

```bash
python examples/02_azure_foundry_agent.py
```

Or CLI:

```bash
context build examples/sample_repo
context ask "Explain authentication" examples/sample_repo --llm
```

### Foundry inference endpoint (alternative)

If your project uses the **Model Inference** URL instead of the classic `*.openai.azure.com` host:

```env
AZURE_USE_INFERENCE_ENDPOINT=true
AZURE_AI_INFERENCE_ENDPOINT=https://YOUR-PROJECT.services.ai.azure.com
AZURE_OPENAI_DEPLOYMENT=your-model-deployment
```

## 3 — Incremental builds & change tracking (Phase 3)

```bash
python examples/03_incremental_watch.py
```

Shows: full build → `incremental_build()` with no changes → touch a file → incremental build with delta → query the SQLite change log → `contextpack.memory` low-level helpers.

No API key needed.

## 4 — Workflows & multi-agent memory (Phase 5)

```bash
python examples/04_workflows_agent_memory.py
```

Shows: `WorkflowExtractor` detecting call chains and API surfaces → `project.workflows()` → `AgentMemory` storing decisions/constraints/observations → `SharedMemory` reading across agents → `format_for_prompt()` for LLM injection.

No API key needed.

---

## Sample repo

`examples/sample_repo/` — minimal Python auth module + `.pr-review/guidelines.md` for harvester demos.
