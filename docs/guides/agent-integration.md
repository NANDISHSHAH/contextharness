# Agent integration patterns

## Integration model

ContextPack is a **context supplier**. Your agent framework owns:

- Tool calling
- Multi-step reasoning
- Human approval
- Memory across sessions (optional Phase 3/4)

ContextPack owns:

- Repository understanding
- Context selection & compression
- Multi-source harvest
- Provider-neutral prompt envelopes

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Orchestrator │────▶│ ContextPack  │────▶│ Model API    │
│ LangGraph /  │     │ build/harvest│     │ Azure/etc.   │
│ CrewAI / CI  │     └──────────────┘     └──────────────┘
└──────────────┘
```

---

## Pattern A — PR review agent (meetup architecture)

**Trigger:** GitLab MR / GitHub PR

**Steps:**

1. Checkout branch
2. `context build` (or restore cache)
3. `harvest(query="functional review", branch_name=branch)`
4. Pass `extra_instructions` + diff to LLM
5. Post structured comment (AC coverage, behaviour, code smells)

**Fetchers used:**

| Fetcher | PR review value |
|---------|-----------------|
| Code | Changed module dependencies |
| Guidelines | Team conventions |
| Behaviour | Test expectations |
| Jira | Acceptance criteria |

---

## Pattern B — Cursor / IDE copilot

```python
ctx = await project.harvest(user_query)
payload = CursorAdapter().inject(ctx)
# Attach payload["extra_instructions"] to composer/agent
```

Keeps IDE UX while centralizing context logic in ContextPack.

---

## Pattern C — LangGraph node

```python
async def load_context(state):
    ctx = await project.harvest(state["task"])
    return LangGraphAdapter().inject(ctx)

graph.add_node("context", load_context)
```

Downstream nodes read `state["agent_context"]`.

---

## Pattern D — Headless CI quality gate

```bash
context build .
context harvest "security-sensitive changes in auth" .
```

Fail build if guardrails report missing guidelines when policy requires them.

---

## Pattern E — Azure Foundry agent service

```python
answer = await project.ask_llm(
    question,
    llm=AzureFoundryLLM(deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"]),
)
```

Deploy agent runner in same region as Foundry endpoint for latency.

---

## Recommended prompt envelope

**System:**

```text
You are a domain-aware software engineering agent.
Use only the provided context. If a section was skipped, say so explicitly.
Cite file paths and symbol names when making claims.
```

**User:** `AggregatedAgentContext.extra_instructions` + task question + optional diff

Do not duplicate large code blobs if compiler summaries already cover them.

---

## Session caching

| Artifact | Cache key |
|----------|-----------|
| `.contextpack/` directory | lockfile + commit SHA |
| `project_map.json` | invalidate on source change |
| Harvest output | per (commit, query, branch) — optional Redis |

---

## Observability

Enable structlog in long-running agents:

```python
from contextpack.observability import configure_logging
configure_logging()
```

Log events: `build_complete`, `fetcher_failed`, entity counts.

---

## Related

- [Context harvester](../architecture/context-harvester.md)
- [Azure Foundry](azure-foundry.md)
- [Package usage](package-usage.md)
