# AGENTS.md — Context Harness

This repository uses **Context Harness**: ContextPack runtime (graph + harvest) plus Cursor/Claude workflow artifacts.

## Critical modules

| Area | Path | Notes |
|------|------|-------|
| Runtime SDK | `contextpack/core/project.py` | `Project` — build, harvest, ask |
| Graph | `contextpack/graph/engine.py` | `ContextGraph` — hubs, neighbours |
| Harvester | `contextpack/harvester/` | `ContextHarvester` — multi-source fetch |
| Harness | `contextpack/harness/` | orientation, validation, install |
| MCP | `contextpack/mcp/server.py` | `harvest_context`, `find_symbol` tools |

## Commands

```bash
uv sync --extra dev --extra harness
context init .
context build .
context harvest "your task" .
context harness orient
context harness validate
```

## Agent workflow

1. **Session** — `sessionStart` hook injects graph orientation (or warns if index stale).
2. **Task** — MCP `harvest_context` or CLI `context harvest` before large edits.
3. **Stop** — `stop` hook suggests `AGENTS.md` updates when docs drift from graph hubs.

## Guidelines

Team rules may also live in `.contextpack/guidelines.md` or `.pr-review/guidelines.md`.
