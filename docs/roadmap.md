# Roadmap

## Phase 1 — Foundation ✓

**Goal:** Repository understanding

| Capability | Status |
|------------|--------|
| Repository scanner | ✓ |
| Python / TS / JS parsers | ✓ |
| Dependency graph (NetworkX) | ✓ |
| Semantic chunking | ✓ |
| Embedding providers (hash, OpenAI, Azure) | ✓ |
| Vector store (SQLite default, Chroma optional) | ✓ |
| Hybrid retrieval | ✓ |
| SQLite entity store | ✓ |

---

## Phase 2 — Context intelligence ✓

**Goal:** Context optimization for agents

| Capability | Status |
|------------|--------|
| Context compiler (token budget) | ✓ |
| Context harvester (parallel fetchers) | ✓ |
| Context aggregator (`extra_instructions`) | ✓ |
| Product guidelines fetcher | ✓ |
| Test behaviour fetcher | ✓ |
| Jira intent fetcher | ✓ |
| Runtime adapters (Claude, OpenAI, Cursor, LangGraph, Azure) | ✓ |
| CLI + Project SDK | ✓ |

---

## Phase 3 — Live memory ✓

**Goal:** Continuous cognition — re-index only what changed

| Capability | Status | Notes |
|------------|--------|-------|
| File-hash snapshot (`file_hashes.json`) | ✓ | SHA-256 per file, saved after every build |
| `incremental_build()` SDK method | ✓ | Re-parses only added / modified files |
| Entity delta tracking | ✓ | Which entities were added, removed, or modified per file |
| Git commit stamping | ✓ | Git HEAD recorded on every change event |
| SQLite change log (`file_changes` table) | ✓ | Full audit trail queryable via `recent_changes()` |
| Smart watch mode | ✓ | `context watch` uses incremental builds; prints diff panel |
| `context changes` CLI | ✓ | Table view of recent file changes |
| MCP tool: `get_recent_changes` | ✓ | Query change log from Cursor / Claude |
| `contextpack.memory` module | ✓ | Low-level API: `load_hashes`, `diff_hashes`, `build_changeset` |

**Guide:** [Incremental builds & change tracking](guides/incremental-builds.md)
**Example:** [`examples/03_incremental_watch.py`](../examples/03_incremental_watch.py)

---

## Phase 4 — Context Harness ✓

**Goal:** AI Layer + ContextPack closed loop

| Capability | Status |
|------------|--------|
| Harness module (staleness, orient, validate, install) | ✓ |
| Cursor hooks (`sessionStart`, `stop`) | ✓ |
| MCP server (`context-harness-mcp`) | ✓ |
| Skills (`harvest-review`, `scoped-tests`) | ✓ |
| Read-only `explorer` agent | ✓ |
| `context harness` CLI | ✓ |
| End-to-end validator | ✓ |

---

## Phase 5 — Live harness ✓

**Goal:** Deeper automation — workflow understanding and multi-agent coordination

| Capability | Status | Notes |
|------------|--------|-------|
| `WorkflowExtractor` — API surface detection | ✓ | Routes/endpoints grouped by service file |
| `WorkflowExtractor` — call chain detection | ✓ | Entry-point → dependency traversal up to depth 5 |
| `WorkflowExtractor` — class lifecycle detection | ✓ | Class + methods → ordered lifecycle flow |
| Workflow persistence (`workflows` table) | ✓ | `extract_and_store()` runs during every `build()` |
| `context workflows` CLI | ✓ | List all extracted workflows |
| MCP tool: `list_workflows` | ✓ | Query from Cursor / Claude |
| `AgentMemory` | ✓ | Per-agent fact store: decisions, observations, constraints, task state |
| `SharedMemory` | ✓ | Cross-agent recall + prompt injection via `format_for_prompt()` |
| SQLite `agent_memory` table | ✓ | Persistent across sessions |
| MCP tools: `agent_memory_store`, `agent_memory_recall` | ✓ | Write/read from Cursor / Claude |
| Compiler: processing-flow detection | ✓ | Detects parse → validate → save chains in compiled packs |

**Guide:** [Workflows & multi-agent memory](guides/workflows-agent-memory.md)
**Example:** [`examples/04_workflows_agent_memory.py`](../examples/04_workflows_agent_memory.py)

---

## Phase 6 — Planned

**Goal:** Team-scale and deeper integrations

| Capability | Target |
|------------|--------|
| Additional fetchers | Confluence, Slack, BrowserStack MCP |
| Cloud sync (optional) | Team-shared context indexes |
| Auto-harvest on `beforeSubmitPrompt` | Optional Cursor hook |
| Deeper architecture analysis | Service boundary inference |
| Git history context | Commit messages, blame hints in harvest |

---

## Non-goals (unchanged)

- SaaS multi-tenant platform
- UI dashboard
- Agent marketplace
- Replacing LangGraph / CrewAI orchestration

---

## Versioning

Current package version: **0.1.0** (alpha)

API may evolve; pin the version in production agents.
