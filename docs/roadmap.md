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

## Phase 6 — Pre-Skill Engine ⬡ Planned

**Goal:** The harness becomes a gatekeeper — deterministic gates before the agent touches any file.

> Full spec: [docs/product/PLAN_NEXT_PHASES.md](product/PLAN_NEXT_PHASES.md#phase-6--pre-skill-engine)

| Capability | Target |
|------------|--------|
| `skills.yml` — declarative policy manifest per path/type/blast radius | Q3 2026 |
| `SkillRouter` — diff → SkillPlan (risk score, blast radius, required gates) | Q3 2026 |
| `SkillComposer` — DAG-aware skill execution (lint → type_check → security_scan) | Q3 2026 |
| `SkillVerifierLoop` — block agent until required skills pass | Q3 2026 |
| `BlastRadiusEnforcer` — hard cap with auto-decomposition suggestions | Q3 2026 |
| `ReasoningCheckpoint` — validate agent's stated understanding vs graph | Q3 2026 |
| `EvidenceBundle` — per-action audit record (skills run, context used, result) | Q3 2026 |
| Built-in skills: `lint`, `type_check`, `security_scan`, `docs_link_check` | Q3 2026 |
| MCP tools: `get_skill_plan`, `run_skill_gate`, `get_evidence_bundle` | Q3 2026 |
| CLI: `context skills plan`, `context skills run`, `context skills history` | Q3 2026 |
| `beforeFileWrite` hook — checks edit token before allowing write | Q3 2026 |

---

## Phase 7 — Semantic Contract Layer ⬡ Planned

**Goal:** The harness understands what code *promises*, not just what it is.

> Full spec: [docs/product/PLAN_NEXT_PHASES.md](product/PLAN_NEXT_PHASES.md#phase-7--semantic-contract-layer)

| Capability | Target |
|------------|--------|
| `ContractExtractor` — docstring + type + test → contract per symbol | Q4 2026 |
| `ContractRegistry` — SQLite-backed store, queryable per symbol | Q4 2026 |
| `InvariantGuard` — `invariants.yml` + counterfactual graph checker | Q4 2026 |
| `NegativeContextIndex` — anti-pattern registry with context + remediation | Q4 2026 |
| `IntentPreserver` — behavioral invariants from tests, verified post-patch | Q4 2026 |
| MCP tools: `get_contracts`, `check_invariants`, `get_anti_patterns` | Q4 2026 |
| CLI: `context contracts show <symbol>`, `context invariants check` | Q4 2026 |

---

## Phase 8 — Context Governance & Trust ⬡ Planned

**Goal:** Context is a governed artifact with provenance, trust tiers, and lifecycle.

> Full spec: [docs/product/PLAN_NEXT_PHASES.md](product/PLAN_NEXT_PHASES.md#phase-8--context-governance--trust)

| Capability | Target |
|------------|--------|
| `TrustScorer` — 5-tier trust scoring per context chunk | Q4 2026 |
| `ContextDebtTracker` — per-module staleness and debt scoring | Q4 2026 |
| `ProvenanceChain` — chain of custody per chunk, stored in SQLite | Q4 2026 |
| `BudgetRiskSignal` — budget as safety gate, not just truncation | Q4 2026 |
| `AgentLockTable` — dependency lock for multi-agent conflict detection | Q4 2026 |
| Trust-aware `ContextCompiler` — risk-gated source selection | Q4 2026 |
| MCP tools: `get_context_debt`, `get_provenance`, `check_agent_conflicts` | Q4 2026 |
| CLI: `context debt`, `context provenance <chunk_id>`, `context locks` | Q4 2026 |

---

## Phase 9 — Adaptive Intelligence ⬡ Planned

**Goal:** The system gets smarter from every agent run, without labeled supervision.

> Full spec: [docs/product/PLAN_NEXT_PHASES.md](product/PLAN_NEXT_PHASES.md#phase-9--adaptive-intelligence)

| Capability | Target |
|------------|--------|
| `FailurePatternStore` — classify, store, retrieve failure patterns by type | Q1 2027 |
| `ProactivePatternBriefing` — surface relevant patterns before agent acts | Q1 2027 |
| `PlaybookLearner` — propose `skills.yml` updates from observed successful runs | Q1 2027 |
| `ContextSnapshotEngine` — snapshot + diff context state across agent runs | Q1 2027 |
| `CouplingMonitor` — track coupling trends, detect decay, surface hotspots | Q1 2027 |
| MCP tools: `get_failure_patterns`, `get_coupling_trend`, `diff_context_snapshots` | Q1 2027 |
| CLI: `context patterns`, `context coupling`, `context snapshots diff` | Q1 2027 |

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
