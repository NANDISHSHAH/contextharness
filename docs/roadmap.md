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

## Phase 3 — Live memory (planned)

**Goal:** Continuous cognition

| Capability | Target |
|------------|--------|
| Incremental index updates | File-level diff, not full rebuild |
| Git diff analyser | PR-scoped context |
| Temporal memory | Session + commit lineage |
| Watcher optimisation | Debounced partial re-parse |
| Git history context | Commit messages, blame hints |

---

## Phase 4 — Context Harness ✓ (MVP)

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

## Phase 5 — Live harness (planned)

**Goal:** Deeper automation

| Capability | Target |
|------------|--------|
| Multi-agent shared memory | Cross-agent context store |
| Workflow extraction | Detect pipelines from code + CI |
| Deeper architecture analysis | Service boundary inference |
| Additional fetchers | Confluence, Slack, BrowserStack MCP |
| Cloud sync (optional) | Team-shared context indexes |
| Auto-harvest on `beforeSubmitPrompt` | Optional hook |

---

## Non-goals (unchanged)

- SaaS multi-tenant platform
- UI dashboard
- Agent marketplace
- Replacing LangGraph/CrewAI orchestration

---

## How to contribute by phase

| Phase | Suggested contributions |
|-------|-------------------------|
| 3 | Git diff module, incremental Chroma/SQLite updates |
| 4 | New `ContextFetcher` implementations, skill YAML format |

---

## Versioning

Current package version: **0.1.0** (alpha)

API may evolve; pin version in production agents.
