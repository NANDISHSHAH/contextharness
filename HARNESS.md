# Context Harness

**Context Harness** combines two layers into one closed loop:

| Layer | Role | Implementation |
|-------|------|----------------|
| **Runtime** | What the model sees | ContextPack — `context build`, `harvest`, graph, compiler |
| **Harness** | How the agent works | Hooks, skills, MCP, `AGENTS.md`, validation |

Inspired by the [Helpline AI Layer](https://github.com/coleam00/helpline) pattern and ContextPack’s context runtime.

## Quick start

```bash
uv sync --extra dev --extra harness
context init .
context build .
context harness install .    # optional on other repos
context harness validate
```

## Components in this repo

| Component | Location |
|-----------|----------|
| Session orientation hook | `.cursor/hooks.json` → `context harness session-start` |
| Stop / doc drift hook | `context harness stop-validate` |
| MCP server | `.mcp.json` → `context-harness-mcp` |
| Skills | `.cursor/skills/harvest-review`, `scoped-tests` |
| Read-only explorer | `.cursor/agents/explorer.md` |
| Validator | `tooling/validate/validate_harness.py` |

## MCP tools

| Tool | Purpose |
|------|---------|
| `project_outline` | Staleness + graph hubs + orientation |
| `find_symbol` | Entity lookup in the index |
| `graph_neighbours` | Dependency neighbourhood |
| `harvest_context` | Full multi-source agent pack |
| `compile_context` | Token-budgeted code-only pack |

## Closed loop

```text
sessionStart → orient (graph hubs, stale index warning)
     ↓
agent works → MCP harvest_context / skills
     ↓
stop → validate docs vs graph → follow-up suggestions
```

## Install on another repository

```bash
context init /path/to/repo
context build /path/to/repo
context harness install /path/to/repo
```

Copy `HARNESS.md` and adjust `AGENTS.md` for your services and conventions.

## Validate end-to-end

```bash
uv run python tooling/validate/validate_harness.py
```

## Docs

- [Context Harness guide](docs/guides/context-harness.md)
- [Vision](docs/product/context-harness-vision.md)
