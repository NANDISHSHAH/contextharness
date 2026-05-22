# Product Requirements Document — ContextPack + Context Harness

**Version:** 0.2
**Status:** Alpha
**Date:** 2026-05-21

---

## 1. Problem

AI coding assistants fail in predictable ways when working on real codebases:

- **Vector search ≠ relevance.** Embedding-based retrieval misses dependency chains and critical paths.
- **No shared project memory.** Every session rebuilds context from scratch; answers are inconsistent across engineers.
- **Context window abuse.** Teams dump entire folders into prompts — high cost, low signal. Build pipelines index everything including generated files, lock files, and vendored code that has zero semantic value.
- **Product context is orphaned.** Agents never see Jira acceptance criteria, team review guidelines, or behaviour encoded in test names.
- **Vendor lock-in at the context layer.** Context shaped for one IDE or API must be rebuilt for every platform switch.

The missing layer is not another embedding index. It is a **context runtime**.

---

## 2. Product Overview

**ContextPack** is a universal AI context runtime: graph-native code understanding, multi-source harvesting, token-budget compilation, and provider-neutral adapters.

**Context Harness** is the workflow layer on top: Cursor/Claude hooks, MCP tools, skills, and doc/graph validation — the closed loop between how agents work and what they see.

Together they deliver **grounded, auditable, portable context** for any AI agent or LLM pipeline.

---

## 3. Target Users

| Persona | Pain today | Value |
|---------|-----------|-------|
| Platform / DevEx engineer | Builds ad-hoc RAG per project | One runtime for all agents |
| Individual developer (Cursor/Claude) | Manual `@file` selection, stale context | Auto-harvested context at session start |
| Security / compliance team | No repeatable code-review scope | Scoped harvest on any subgraph |
| New hire / onboarding | Architecture tours take weeks | Dependency-aware Q&A in minutes |
| ML platform (regulated enterprise) | Must stay inside Azure VNet | Azure AI Foundry support, no openai.com data path |

---

## 4. Goals

1. A developer can run `context build ./repo` + `context ask "..."` and receive a structurally correct answer naming real modules and relationships.
2. CI can run `context harvest` on a PR branch and feed code graph + Jira AC + guidelines + test behaviour to an LLM reviewer in one call.
3. Cursor/Claude agents auto-orient at session start and self-validate docs at session end — zero manual prompt engineering.
4. The same harvested pack works with Claude, OpenAI, Azure AI Foundry, Cursor, and LangGraph without rebuilding prompts.
5. Cold-start time stays under 5 seconds (SQLite default, lazy imports, no Chroma unless opted in).

---

## 5. Non-Goals

- SaaS multi-tenant platform
- UI dashboard or visual graph explorer
- Agent marketplace
- Replacing LangGraph/CrewAI orchestration
- Support for non-Python/TypeScript/JavaScript repositories (Phase 1 scope)

---

## 6. Feature Requirements

### 6.1 Context Runtime (ContextPack)

| # | Requirement | Priority |
|---|-------------|----------|
| R1 | Scan a repo and build a dependency graph (NetworkX) from Python, TS, JS source | P0 |
| R2 | Embed chunks and store in SQLite vector store (default) or ChromaDB (opt-in) | P0 |
| R3 | Hybrid retrieval combining vector similarity and graph traversal | P0 |
| R4 | Token-budget context compiler — include most relevant symbols within a cap | P0 |
| R5 | Parallel context harvester: code + guidelines + test behaviour + Jira (optional) | P0 |
| R6 | Context aggregator outputting `extra_instructions` block | P0 |
| R7 | Adapters for Claude, OpenAI, Cursor, LangGraph, Azure AI Foundry | P0 |
| R8 | CLI: `init`, `build`, `harvest`, `ask`, `graph`, `watch` | P0 |
| R9 | Python SDK: `Project.init()`, `.build()`, `.harvest()`, `.ask()` — `build()` returns `(ProjectMap, BuildStats)` | P0 |
| R10 | Azure AI Foundry support (inference endpoint + embeddings, no openai.com) | P1 |
| R11 | Smart ignore: `.gitignore` + `.contextpackignore` + expanded dir/file patterns | P0 ✓ |
| R12 | Tiered embedding: hub nodes always embedded, budget cap `CONTEXTPACK_MAX_EMBED_ENTITIES` | P0 ✓ |
| R13 | Per-step build profiling: `BuildStats` dataclass, summary table printed after every build | P0 ✓ |
| R14 | Incremental index updates (file-level diff, not full rebuild) | P2 (Phase 3) |
| R15 | Git diff analyser for PR-scoped context | P2 (Phase 3) |

### 6.2 Context Harness (Workflow Layer)

| # | Requirement | Priority |
|---|-------------|----------|
| H1 | `sessionStart` hook: inject orientation briefing, warn if index is stale | P0 |
| H2 | `stop` hook: validate `AGENTS.md` against graph hubs, suggest updates | P0 |
| H3 | MCP server (`context-harness-mcp`) exposing `harvest_context`, `find_symbol` | P0 |
| H4 | `harvest-review` skill for pre-edit context harvest | P0 |
| H5 | `scoped-tests` skill for targeted test discovery | P0 |
| H6 | Read-only `explorer` agent for repo navigation | P0 |
| H7 | `context harness` CLI (`orient`, `validate`, `install`) | P0 |
| H8 | Multi-agent shared memory / cross-agent context store | P2 (Phase 5) |
| H9 | Auto-harvest on `beforeSubmitPrompt` hook (opt-in) | P2 (Phase 5) |

### 6.3 Performance & Operations

| # | Requirement | Priority |
|---|-------------|----------|
| P1 | Default cold start under 5 seconds (SQLite, lazy imports) | P0 |
| P2 | Batch SQLite writes — no per-entity connection overhead | P0 |
| P3 | Chroma opt-in only (`uv sync --extra chroma`) | P0 |
| P4 | `context watch` for debounced partial re-parse on file change | P1 |
| P5 | Skip generated/vendored files: `.d.ts`, `.min.js`, `*.map`, lock files, protobuf generated | P0 ✓ |
| P6 | Build summary table — per-phase time, files scanned/skipped, token estimate, embed vs store-only counts | P0 ✓ |

---

## 7. Key Use Cases

1. **Domain-aware PR review** — CI harvests code graph + Jira AC + guidelines for a branch; LLM bot flags AC gaps before human review.
2. **Onboarding copilot** — Daily `context build` on monorepo; new engineers get dependency-aware answers with real module names.
3. **Security change analysis** — Scoped harvest on auth subgraph; guardrails flag missing `SECURITY.md`.
4. **Enterprise Azure agent** — On-prem/VNet agent uses Azure Foundry for both chat and embeddings; no data leaves the tenant.
5. **Cursor/IDE augmentation** — Session auto-briefing + on-demand `harvest-review` skill replaces manual `@file` selection.
6. **LangGraph multi-step workflow** — `load_context` node produces a pack; downstream nodes operate on structured context, not raw files.

---

## 8. Architecture Summary

```
Repository
    │
    ▼
SmartIgnore (.gitignore + .contextpackignore + built-in patterns)
    │
    ▼
Scanner → Parsers → ContextGraph (NetworkX)
    │                      │
    │               Hub scoring (degree centrality)
    │                      │
    ▼                      ▼
TieredChunking → Embeddings (hubs first, budget cap) → SQLite / ChromaDB
    │
    ▼
HybridRetriever → ContextCompiler (token budget)
    │
    ▼
ContextHarvester (parallel fetchers)
    │
    ▼
ContextAggregator → AggregatedAgentContext
    │
    ▼
Adapters (Claude / OpenAI / Cursor / LangGraph / Azure)
    │
    ▼
Context Harness (hooks · MCP · skills · validate)
```

**Build output** (every run):
```
  scan      0.3s    1,234 files scanned  |  778 skipped
  parse     1.2s    789 entities  (from 456 files)
  graph     0.1s    912 nodes  1,456 edges  12 hubs
  chunk     0.2s    2,100 chunks  ~84K tokens estimated
  embed     0.8s    2,100 embedded  |  340 store-only
  store     0.4s    789 entities → memory.db
  total     3.0s
```

---

## 9. Roadmap

| Phase | Status | Theme |
|-------|--------|-------|
| 1 — Foundation | Done | Scanner, graph, embeddings, retrieval |
| 2 — Context intelligence | Done | Compiler, harvester, aggregator, adapters |
| 3 — Live memory | Planned | Incremental updates, git diff, temporal memory |
| 4 — Context Harness MVP | Done | Hooks, MCP, skills, validator |
| 5 — Live harness | Planned | Multi-agent memory, workflow extraction, cloud sync |

---

## 10. Success Metrics

| Metric | Target |
|--------|--------|
| `context build` cold start | < 5 s (SQLite, small repo) |
| Files skipped on real JS/TS project | ≥ 50% of files filtered (node_modules, dist, .d.ts, lock files) |
| Embedding reduction vs naïve approach | ≥ 60% fewer embeddings on repos > 500 entities via tiered cap |
| Token budget compliance | Harvested pack stays within configured limit 100% of the time |
| PR review accuracy | Catches AC gaps caught manually in ≥ 80% of test PRs |
| Onboarding time reduction | New engineers self-serve architecture questions in < 1 day |
| Platform portability | Same `harvest()` output usable by Claude, OpenAI, and Azure Foundry without modification |
| Build observability | Every build prints per-phase time + skip/embed counts with no extra flags |

---

## 11. Open Questions

1. What is the right default token budget? (Current: uncapped, user-configured)
2. Should Phase 3 incremental updates be event-driven (fswatch) or CI-triggered only?
3. Is a hosted/cloud-sync option for team-shared indexes ever in scope, or hard non-goal?
4. Which additional fetchers to prioritise in Phase 5: Confluence, Slack, or BrowserStack MCP?
