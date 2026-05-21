# Context Harness guide

Install the full stack: ContextPack runtime + Cursor/Claude harness artifacts.

## Install

```bash
uv sync --extra dev --extra harness
context init .
context build .
```

On a **new** repository:

```bash
context harness install /path/to/repo
context build /path/to/repo
```

## Cursor integration

This repo ships:

| File | Purpose |
|------|---------|
| `.cursor/hooks.json` | `sessionStart`, `stop` |
| `.mcp.json` | `context-harness` MCP server |
| `.cursor/skills/` | `harvest-review`, `scoped-tests` |
| `.cursor/agents/explorer.md` | Read-only mapper subagent |
| `AGENTS.md` | Human + agent conventions |

Enable MCP in Cursor and reload hooks after editing `hooks.json`.

## CLI

```bash
context harness orient          # same text as sessionStart
context harness validate        # AGENTS.md vs graph hubs
context harness session-start   # hook entry (stdin JSON)
context harness stop-validate     # hook entry
context harness install .       # copy templates
```

## MCP tools

Start server manually:

```bash
CONTEXTPACK_ROOT=. uv run --extra harness context-harness-mcp
```

| Tool | When to use |
|------|-------------|
| `project_outline` | Start of session; check staleness |
| `find_symbol` | Resolve a class/function name |
| `graph_neighbours` | Impact analysis around a symbol |
| `harvest_context` | Full agent pack for a task |
| `compile_context` | Code-only, token-budgeted pack |

## Validate

```bash
uv run python tooling/validate/validate_harness.py
pytest tests/test_harness.py -q
```

## Related

- [Vision](../product/context-harness-vision.md)
- [Agent integration](agent-integration.md)
