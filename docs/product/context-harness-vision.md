# Context Harness vision

Context Harness unifies **ContextPack** (context runtime) with an **AI Layer**-style harness (hooks, skills, MCP, agents) into one closed loop.

## Two layers, one product

```text
┌──────────────────────────────────────────────────────────────┐
│  HARNESS — workflow                                           │
│  sessionStart / stop hooks · skills · MCP · AGENTS.md        │
└────────────────────────────┬─────────────────────────────────┘
                             │ triggers & validates
┌────────────────────────────▼─────────────────────────────────┐
│  RUNTIME — understanding                                      │
│  build · graph · harvest · compile · adapters                 │
└──────────────────────────────────────────────────────────────┘
```

## What each side contributes

| Helpline-style harness | ContextPack runtime | Combined |
|------------------------|---------------------|----------|
| When to orient the agent | What the graph contains | Session briefing from real hubs |
| Skills for conventions | Guidelines fetcher | Same rules in harvest + skills |
| AST / outline MCP | Hybrid retrieval + compile | `harvest_context` + `find_symbol` |
| Stop hook reflection | Indexed truth | Doc vs graph validation |

## Closed-loop behaviours

1. **sessionStart** — inject orientation; warn if `.contextpack` is stale vs git HEAD.
2. **Task work** — MCP `harvest_context` or skill `harvest-review` before large edits.
3. **stop** — `validate_harness_docs` suggests `AGENTS.md` updates for undocumented graph hubs.

## Related

- [Context Harness guide](../guides/context-harness.md)
- [HARNESS.md](../../HARNESS.md)
- [vs alternatives](comparison.md)
