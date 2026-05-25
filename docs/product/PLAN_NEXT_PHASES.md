# ContextPack + Context Harness — Next Phases Plan

**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-05-24  
**Author:** Engineering  

---

## Executive Summary

Phases 1–5 solved the **context delivery** problem: scan, parse, graph, embed, retrieve, compile, harvest, adapt, watch, remember. That is a strong foundation.

The next evolution is a different problem class: **context governance**.

The distinction matters:
- **Context delivery** answers "what does the agent need to know?"
- **Context governance** answers "what must the agent verify before it is allowed to act?"

The research consensus points here. *Agentless* (arXiv 2407.01489) showed a three-stage localize → repair → verify loop beats more complex agent setups on SWE-bench Lite. *SWT-Bench* showed generated tests can filter proposed fixes before human review. *AOCI* (arXiv 2605.02421) showed symbolic-semantic repository blueprints updated incrementally outperform naïve RAG on repository-scale understanding. *ACE* (arXiv 2510.04618) showed contexts that evolve as playbooks produce self-improving agents without labeled supervision.

The signal is consistent: **deterministic verification + governed context + evolving memory** is the moat, not more retrieval.

This document defines four new phases:

| Phase | Theme | Core Bet |
|-------|-------|----------|
| 6 | Pre-Skill Engine | Harness decides what agent must do before touching code |
| 7 | Semantic Contract Layer | Harness understands what code *promises*, not just what it *is* |
| 8 | Context Governance & Trust | Context itself becomes a governed, auditable artifact |
| 9 | Adaptive Intelligence | System gets smarter from every agent run, without supervision |

---

## Current State (Phases 1–5 Complete)

```
Scanner → Parsers → ContextGraph → Embeddings → SQLite
                         │
                   HybridRetriever → ContextCompiler
                         │
               ContextHarvester (code + guidelines + tests + Jira)
                         │
                   ContextAggregator → AggregatedAgentContext
                         │
              Adapters (Claude / OpenAI / Cursor / LangGraph / Azure)
                         │
            Harness (hooks · MCP · skills · validate · watch)
                         │
          Live Memory (incremental builds · workflows · agent memory)
```

Everything from scan to adapt is done. What is missing is the **policy and verification layer** that sits between the agent's intent and its first file write.

---

## Phase 6 — Pre-Skill Engine

**Theme:** The harness becomes a gatekeeper, not just a briefer.

### 6.1 The Core Problem

Today the harness *briefs* the agent at session start and *validates* docs at session stop. Nothing happens in between. An agent can:
- Touch a hub node without knowing it is a hub
- Edit an auth module without triggering a security check
- Modify a module with 40 downstream dependents without knowing the blast radius

The gap is an enforcement layer that runs *before* the first edit.

### 6.2 Skill Manifest (`skills.yml`)

A declarative policy file committed to the repo:

```yaml
# .contextpack/skills.yml

version: 1

policies:
  - name: auth_changes
    description: Any change touching the auth subgraph
    match:
      paths: ["src/auth/**", "src/middleware/auth*"]
      graph_roles: ["hub"]                         # any hub node in matched paths
    require:
      skills: [lint, type_check, security_scan, auth_tests]
      human_review: false

  - name: payment_changes
    description: Payment module — zero tolerance
    match:
      paths: ["src/payment/**", "src/billing/**"]
      blast_radius_min: 1                          # any blast radius triggers this
    require:
      skills: [lint, type_check, security_scan, integration_tests, contract_check]
      human_review: true                           # always requires human

  - name: hub_node_changes
    description: Any file that is a graph hub (degree centrality > 0.8)
    match:
      graph_hub_threshold: 0.8
    require:
      skills: [lint, type_check, full_test_suite]
      max_blast_radius: 20                         # refuse if blast radius > 20

  - name: doc_only_changes
    description: Markdown / docs only — lightweight checks
    match:
      paths: ["**/*.md", "docs/**"]
      extensions_only: [".md", ".rst", ".txt"]
    require:
      skills: [docs_link_check, spelling]

  - name: default
    description: Everything else
    require:
      skills: [lint]
```

**Key design decisions:**
- Policies are additive — a single file can match multiple policies (all requirements merge)
- `graph_roles` lets the graph itself drive policy, not just paths
- `blast_radius_min` triggers on impact, not on what the file is named
- `human_review: true` is a hard stop the harness enforces via CLI exit code

### 6.3 Skill Router

The router analyses the incoming diff or task description and returns the union of all matching policy requirements:

```
Input:
  - diff: list of changed files
  - task: natural language description (optional)
  - graph: current ContextGraph

Output:
  - SkillPlan
      required_skills: [lint, type_check, security_scan, auth_tests]
      risk_score: 0.73
      blast_radius: 12
      hub_nodes_touched: ["src/auth/middleware.py:AuthMiddleware"]
      human_review_required: false
      decomposition_required: false
      reasoning: "Matched policies: auth_changes, hub_node_changes"
```

The router computes risk score as:

```
risk_score = (
    0.35 * hub_centrality_max          # highest centrality node touched
  + 0.30 * blast_radius_normalised     # downstream impact / total nodes
  + 0.20 * policy_count_normalised     # how many policies triggered
  + 0.15 * cross_module_flag           # touches > 1 top-level module
)
```

### 6.4 Skill Composition Trees

Skills have dependencies. Running type-check before lint is waste. A full DAG ensures correct execution order:

```
lint
  └── type_check
        ├── security_scan
        └── contract_check
              └── integration_tests
                    └── full_test_suite
```

The runner executes the minimal DAG that satisfies all required skills. If `lint` fails, the tree halts — no point running type-check on code that doesn't parse.

### 6.5 Verifier Loop

The loop blocks the agent until all required skills pass:

```
1. Agent declares intent (edit, create, delete)
2. SkillRouter computes SkillPlan
3. If decomposition_required: refuse, return decomposition suggestion
4. If human_review_required: pause, notify, await approval
5. Execute skill DAG in dependency order
6. If any skill fails: return failure report, block edit
7. If all pass: issue an edit token valid for N minutes
8. Agent proceeds with edit
9. Post-edit: re-run affected skills (fast re-verification)
10. Log result to EvidenceBundle
```

### 6.6 Blast Radius Enforcement (Original Idea)

The most important enforcement that no existing tool does:

If a task's blast radius exceeds the policy threshold, the harness **refuses to proceed** and instead returns a decomposition plan:

```
BLOCKED: blast radius 34 exceeds policy max_blast_radius 20

This task touches UserService which has 34 downstream dependents.
Suggested decomposition:
  Task A: Update UserService.get_user() signature  [blast_radius: 8]
  Task B: Update auth layer callers               [blast_radius: 6]
  Task C: Update API layer callers                [blast_radius: 9]
  Task D: Update test fixtures                    [blast_radius: 4]
  Task E: Integration test + release              [blast_radius: 0]

Run each task in sequence with full skill gates between.
```

This enforces smaller, safer edits — not as a suggestion, but as a hard gate.

### 6.7 Observable Reasoning Checkpoints (Original Idea)

Before the agent touches a critical file (hub node or high-risk policy match), the harness presents a checkpoint:

```
CHECKPOINT before editing src/auth/middleware.py

Based on the dependency graph, this module:
  - Is a hub node (centrality: 0.91)
  - Has 28 direct importers
  - Is in the critical path of: login_flow, token_refresh, session_management
  - Last modified: 3 days ago by 2 different agents

Before proceeding, confirm your understanding:
  Q: What is the primary responsibility of AuthMiddleware?
  Q: Which downstream modules will be affected by a signature change to validate_token()?

Your answer is validated against the graph. Mismatches trigger a re-briefing, not a block.
```

The checkpoint does not block on wrong answers — it corrects misunderstandings before they become bugs. This is inspired by how code review works: the reviewer does not refuse the PR, they ask the author to explain their reasoning.

### 6.8 Evidence Bundle

Every agent action produces an auditable bundle:

```json
{
  "action_id": "act_8f3k2",
  "timestamp": "2026-05-24T14:23:01Z",
  "agent_id": "cursor_agent_1",
  "files_modified": ["src/auth/middleware.py"],
  "diff_hash": "sha256:a3f...",
  "skill_plan": {
    "policies_matched": ["auth_changes", "hub_node_changes"],
    "required_skills": ["lint", "type_check", "security_scan", "auth_tests"],
    "risk_score": 0.73,
    "blast_radius": 12
  },
  "skill_results": {
    "lint": {"passed": true, "duration_ms": 340},
    "type_check": {"passed": true, "duration_ms": 890},
    "security_scan": {"passed": true, "duration_ms": 1200, "findings": []},
    "auth_tests": {"passed": true, "duration_ms": 4500, "tests_run": 34}
  },
  "reasoning_checkpoint": {
    "question": "What is the primary responsibility of AuthMiddleware?",
    "agent_answer": "Validates JWT tokens and attaches user context to requests",
    "graph_validated": true
  },
  "context_used": {
    "chunks": ["auth/middleware.py:45-89", "auth/tokens.py:12-45"],
    "trust_scores": [0.95, 0.87]
  }
}
```

This bundle is stored in SQLite and surfaced in the harness validator. PRs can require a valid bundle before merge.

### 6.9 Phase 6 Deliverables

| Deliverable | Description |
|-------------|-------------|
| `skills.yml` schema + parser | Declarative policy file format |
| `SkillRouter` | Diff → SkillPlan computation |
| `SkillComposer` | DAG-aware skill execution engine |
| `SkillVerifierLoop` | Block/approve/decompose logic |
| `BlastRadiusEnforcer` | Hard cap with decomposition suggestions |
| `ReasoningCheckpoint` | Pre-edit understanding validation |
| `EvidenceBundle` | Per-action audit record |
| Built-in skills | `lint`, `type_check`, `security_scan`, `docs_link_check` (pluggable shell runners) |
| MCP tools | `get_skill_plan`, `run_skill_gate`, `get_evidence_bundle` |
| CLI | `context skills plan <diff>`, `context skills run`, `context skills history` |
| Hook | `beforeFileWrite` — checks edit token before allowing write |

---

## Phase 7 — Semantic Contract Layer

**Theme:** The harness understands what code *promises*, not just what it is.

### 7.1 The Core Problem

Lint checks syntax. Type checks check types. Neither checks whether a function still does what it claims to do, or whether a module-level invariant ("payment never calls auth directly") has been violated. These are semantic contracts, and they live between the lines of code.

### 7.2 Contract Registry

Extract implicit contracts from code at build time:

**Input sources:**
- Docstrings → natural language contracts
- Type signatures → type contracts
- Test names → behavioural contracts (`test_payment_fails_on_invalid_card`)
- `assert` statements → runtime invariants
- `raise` / exception types → error contracts

**Output: `ContractRegistry`**

```python
{
  "src/payment/processor.py:PaymentProcessor.charge": {
    "preconditions": ["amount > 0", "card is not None", "user.is_verified"],
    "postconditions": ["returns TransactionResult", "raises PaymentError on decline"],
    "invariants": ["never_calls_auth_directly"],
    "test_coverage": ["test_charge_success", "test_charge_decline", "test_charge_invalid_amount"],
    "last_verified": "2026-05-23T10:00:00Z",
    "trust_score": 0.92
  }
}
```

### 7.3 Architecture Invariant Guard

Declarative architectural rules that the harness enforces at diff time:

```yaml
# .contextpack/invariants.yml

invariants:
  - name: payment_auth_isolation
    description: Payment module must never directly import auth module
    rule: "no_direct_import"
    from: "src/payment/**"
    to: "src/auth/**"
    severity: error

  - name: service_layer_boundary
    description: API routes must not call database directly
    rule: "no_direct_import"
    from: "src/api/routes/**"
    to: "src/db/**"
    severity: error

  - name: circular_dependency_ban
    description: No circular imports anywhere
    rule: "no_cycles"
    scope: "**"
    severity: error

  - name: hub_stability
    description: Hub nodes must not increase their import count by more than 3 per PR
    rule: "max_import_growth"
    scope: "graph_hubs"
    max_growth: 3
    severity: warning
```

These run on the *counterfactual graph* — the graph as it would look after the proposed change. This catches architectural violations before any code is committed.

### 7.4 Negative Context Index

Most context systems index what *exists*. This indexes what *should not exist*:

```python
NegativeContextEntry(
  pattern="from jwt import decode",  # direct JWT decode without wrapper
  reason="Use auth.tokens.validate_token() instead — handles expiry, rotation, revocation",
  severity="error",
  scope="**",
  references=["docs/security/jwt-policy.md"]
)
```

When the agent's proposed edit contains a negative pattern, the harness surfaces the policy before the edit is applied — not as a lint warning, but as context that explains *why* and *what to do instead*.

### 7.5 Intent Preservation Verification

Inspired by SWT-Bench: before applying a patch, generate behavioral invariants from the existing test suite and verify they hold in the proposed change. This is different from running tests — it operates at the *intent* level:

```
Original:  test_validate_token_returns_user_id_on_success
           test_validate_token_raises_on_expired
           test_validate_token_raises_on_tampered

Invariants extracted:
  1. validate_token(valid_jwt) → user_id (not None, not empty)
  2. validate_token(expired_jwt) → raises TokenExpiredError
  3. validate_token(tampered_jwt) → raises TokenInvalidError

Post-patch verification:
  ✓ Invariant 1: passed
  ✓ Invariant 2: passed
  ✗ Invariant 3: failed — tampered token now returns None instead of raising
```

The harness catches semantic regressions that pass lint and type checks.

### 7.6 Phase 7 Deliverables

| Deliverable | Description |
|-------------|-------------|
| `ContractExtractor` | Docstring + type + test → contract registry |
| `ContractRegistry` | SQLite-backed store for contracts per symbol |
| `InvariantGuard` | invariants.yml parser + counterfactual graph checker |
| `NegativeContextIndex` | Anti-pattern registry with context + remediation |
| `IntentPreserver` | Behavioral invariant extraction from tests |
| MCP tools | `get_contracts`, `check_invariants`, `get_anti_patterns` |
| CLI | `context contracts show <symbol>`, `context invariants check` |

---

## Phase 8 — Context Governance & Trust

**Theme:** Context is a governed artifact with provenance, trust, and lifecycle.

### 8.1 The Core Problem

Every context chunk the agent sees today is treated equally. A fresh docstring from a file changed today is weighted the same as a stale docstring from a file last touched 18 months ago. A comment is weighted the same as a type signature. This is wrong.

### 8.2 Source Trust Tiers

Different context sources have different reliability:

| Tier | Sources | Trust Score | Rationale |
|------|---------|------------|-----------|
| 1 (Ground Truth) | Type signatures, `assert` statements, `raise` declarations | 0.95–1.0 | Machine-verifiable |
| 2 (High Trust) | Unit test names and bodies, CI-passing tests | 0.80–0.94 | Verified by CI |
| 3 (Medium Trust) | Docstrings, inline comments within 30 days | 0.60–0.79 | Human-written, may be stale |
| 4 (Low Trust) | README sections, docs/, wiki | 0.30–0.59 | Often lags code |
| 5 (Unverified) | Jira comments, Slack threads | 0.10–0.29 | Informal, unreviewed |

Context compiled for a high-risk task (risk_score > 0.7) only uses Tier 1–2 sources. Low-risk tasks may use Tier 3–4. The compiler makes this visible:

```
Context pack for: "Update payment flow"
  Risk score: 0.73 (high) — using Tier 1-2 sources only

  [T1] PaymentProcessor.charge: type signature, 3 assertions     trust: 0.97
  [T2] test_charge_success, test_charge_decline                  trust: 0.88
  [T1] TransactionResult: Pydantic model, 100% type coverage     trust: 0.95

  EXCLUDED (Tier 3-4):
  [T3] payment/processor.py docstring — 94 days stale            trust: 0.52
  [T4] docs/payment.md — 180 days stale                          trust: 0.31
```

### 8.3 Context Debt Scoring

Per-module staleness tracking:

```
Context Debt Report — 2026-05-24

Module                      Last Built    Churn    Debt Score    Action
─────────────────────────────────────────────────────────────────────────
src/auth/middleware.py       3 days ago    high     0.82 (HIGH)   Re-index
src/payment/processor.py     1 day ago     medium   0.34 (LOW)    OK
src/api/routes/users.py      12 days ago   low      0.45 (MED)    Watch
src/db/models.py             21 days ago   high     0.91 (CRIT)   URGENT

Debt formula:
  debt = 0.5 * days_stale_normalised + 0.3 * churn_rate + 0.2 * hub_centrality
```

Modules with critical debt are excluded from context compilation until rebuilt. The harness warns at session start if any hub node has critical debt.

### 8.4 Context Provenance Chains

Every context chunk carries a chain of custody:

```json
{
  "chunk_id": "chunk_a3f2",
  "content": "def validate_token(token: str) -> UserId: ...",
  "source": "src/auth/tokens.py",
  "source_type": "code",
  "trust_tier": 1,
  "trust_score": 0.97,
  "provenance": {
    "file_hash": "sha256:3f2a...",
    "git_commit": "abc1234",
    "git_author": "dev@company.com",
    "last_modified": "2026-05-21T09:14:00Z",
    "days_since_modified": 3,
    "test_coverage": 0.94,
    "ci_verified": true,
    "last_ci_run": "2026-05-23T22:00:00Z"
  }
}
```

This makes context auditable. A post-mortem can answer: "what context did the agent use when it made that change, and how trusted was it?"

### 8.5 Context Budget as Risk Signal (Original Idea)

The most underused signal in the system: the token budget itself.

Current behavior: if context exceeds budget, truncate.

Proposed behavior: if the *minimum safe context* for a task exceeds the budget, that is a **risk signal**, not a truncation problem:

```
RISK WARNING: Minimum safe context (12,400 tokens) exceeds budget (8,000 tokens)

This task requires context from 6 modules that are all highly coupled.
Options:
  A. Increase budget to 14,000 tokens for this task (recommended)
  B. Narrow task scope to reduce required context
  C. Proceed with truncated context (not recommended — high risk score: 0.81)
  D. Decompose task (blast radius enforcer will suggest breakdown)

Proceeding with truncated context on a high-risk task is not recommended.
The harness will log this as a FORCED_TRUNCATION event in the evidence bundle.
```

This makes "not enough context" a first-class safety concept.

### 8.6 Multi-Agent Conflict Detection (Original Idea)

When multiple agents work on the same codebase simultaneously, the harness detects overlapping dependency subgraphs *before* code is written:

```
CONFLICT DETECTED

Agent A (cursor_agent_1) has a pending edit plan touching:
  src/auth/middleware.py
  src/auth/tokens.py [hub, centrality: 0.91]

Agent B (cursor_agent_2) has a pending edit plan touching:
  src/api/routes/users.py
  src/auth/tokens.py [hub, centrality: 0.91]   ← OVERLAP

Both agents plan to modify src/auth/tokens.py.
Agent A has priority (earlier lock timestamp).

Options for Agent B:
  A. Wait for Agent A to complete and release lock
  B. Coordinate — Agent A takes tokens.py, Agent B takes routes/users.py only
  C. Override (requires human approval)
```

This requires agents to register their edit plans before executing. The harness holds a lightweight dependency lock table per repo.

### 8.7 Phase 8 Deliverables

| Deliverable | Description |
|-------------|-------------|
| `TrustScorer` | Assign trust tier + score per context chunk |
| `ContextDebtTracker` | Per-module staleness and debt scoring |
| `ProvenanceChain` | Chain of custody per chunk, stored in SQLite |
| `BudgetRiskSignal` | Budget as safety gate, not just truncation |
| `AgentLockTable` | Dependency lock for multi-agent conflict detection |
| Updated `ContextCompiler` | Trust-aware compilation, risk-gated source selection |
| MCP tools | `get_context_debt`, `get_provenance`, `check_agent_conflicts` |
| CLI | `context debt`, `context provenance <chunk_id>`, `context locks` |
| Updated harness hook | `sessionStart` warns on critical debt modules |

---

## Phase 9 — Adaptive Intelligence

**Theme:** The system gets smarter from every agent run, without labeled supervision.

### 9.1 The Core Problem

Today every build starts from the same place. The system does not remember that the last 4 times an agent edited `src/auth/middleware.py`, the security scan found an issue. It does not remember that a particular class of change always requires more context than the budget allows. The system is not learning.

### 9.2 Failure Pattern Memory

Classify and store every skill failure by type:

```
FailurePattern(
  pattern_id: "fp_a3k2",
  skill: "security_scan",
  file_pattern: "src/auth/**",
  failure_class: "missing_rate_limit",
  frequency: 7,              # seen 7 times in last 30 days
  last_seen: "2026-05-23",
  remediation_hint: "Add @rate_limit decorator from auth.decorators",
  auto_added_to_context: true  # proactively shown before next auth edit
)
```

When an agent is about to edit `src/auth/**`, the harness proactively surfaces:
```
PATTERN WARNING: Security scan has flagged "missing_rate_limit" 
on auth files 7 times in the last 30 days.

Before you proceed, ensure @rate_limit is applied to all new endpoints.
Reference: auth/decorators.py:rate_limit
```

This is a memory-driven pre-brief, not a post-hoc failure.

### 9.3 Auto-Playbook Learning (ACE-Inspired)

Inspired by ACE (arXiv 2510.04618): the skill pack is an evolving playbook that updates from successful runs:

```
PLAYBOOK UPDATE

After 5 successful auth changes in the last 7 days, the system observed:
  - All successful changes passed security_scan AND had a new test added
  - All failed changes had security_scan pass but NO new test

Proposed policy update for auth_changes:
  ADD: require skill "new_test_required" when modifying existing functions

Accept? [yes/no/review]
```

The system surfaces proposed policy updates. A human approves them. Over time the `skills.yml` becomes better without a human needing to think "what should I add?"

### 9.4 Temporal Context Snapshots

Like git, but for the *context state* — not the code state:

```
Context Snapshot  sha: ctx_8f3k2
  Date: 2026-05-24T14:00:00Z
  Agent: cursor_agent_1
  Task: "Refactor auth middleware to support OAuth2"

  Graph state:
    Nodes: 912  Edges: 1456  Hubs: 12
    Hub centralities: AuthMiddleware(0.91), UserService(0.87)...

  Context used:
    Chunks: 24  Tokens: 7,840  Trust avg: 0.88
    Sources: [code(18), tests(4), guidelines(2)]

  Contracts at time of edit:
    validate_token: preconditions[3], postconditions[2], trust: 0.97
```

After the agent run, a new snapshot is taken. The harness can diff:

```
context diff ctx_8f3k2 ctx_9a1m4

Graph changes:
  + Edge: AuthMiddleware → OAuthProvider (NEW DEPENDENCY)
  ~ Hub centrality: AuthMiddleware 0.91 → 0.94 (INCREASED)

Contract changes:
  ~ validate_token: postconditions changed (was: returns UserId, now: returns AuthToken)
  + new_contract: refresh_token added (2 preconditions, 1 postcondition)

Context debt:
  src/auth/middleware.py: debt 0.34 → 0.12 (IMPROVED — freshly indexed)
```

This gives a complete picture of how the codebase's *semantic model* changed, not just the code.

### 9.5 Graph-Temporal Coupling Monitor (Original Idea)

Track coupling metrics *over time*. If the dependency graph is getting more connected, that is a signal of architectural decay — before it becomes a problem:

```
COUPLING TREND — last 30 days

                    May 1   May 8   May 15  May 22  May 24
Average coupling:   0.23    0.24    0.27    0.31    0.33   ↑ TREND: +43%
Hub count:          10      10      11      13      14     ↑ TREND: +40%
Cycles detected:    0       0       1       1       2      ↑ TREND: NEW CYCLES

ALERT: Coupling has increased 43% in 30 days.
Hotspot: src/api/ modules now import src/auth/ 12 times (was 4 times 30 days ago)

Recommendation: Review PR #47, #51, #58 — these introduced direct cross-module imports
```

This is an architectural governance signal that no lint tool produces.

### 9.6 Phase 9 Deliverables

| Deliverable | Description |
|-------------|-------------|
| `FailurePatternStore` | Classify, store, and retrieve failure patterns |
| `ProactivePatternBriefing` | Surface relevant failure patterns before agent acts |
| `PlaybookLearner` | Propose skills.yml updates from observed successful patterns |
| `ContextSnapshotEngine` | Snapshot + diff context state across agent runs |
| `CouplingMonitor` | Track coupling trends, detect decay, surface hotspots |
| MCP tools | `get_failure_patterns`, `get_coupling_trend`, `diff_context_snapshots` |
| CLI | `context patterns`, `context coupling`, `context snapshots diff` |
| Hook | `sessionStart` injects proactive failure pattern warnings |

---

## Implementation Priority

Phases are ordered by impact-to-effort ratio:

```
Phase 6: Pre-Skill Engine          ████████████  HIGH IMPACT, MEDIUM EFFORT
Phase 7: Semantic Contracts        ████████░░░░  HIGH IMPACT, HIGH EFFORT
Phase 8: Context Governance        ███████░░░░░  MEDIUM-HIGH IMPACT, MEDIUM EFFORT
Phase 9: Adaptive Intelligence     ██████░░░░░░  HIGH LONG-TERM IMPACT, HIGH EFFORT
```

**Recommended build order:**

1. Phase 6 first — delivers user-visible value immediately (gates before edits)
2. Phase 8 (trust + debt) second — improves existing context quality with low risk
3. Phase 7 (contracts + invariants) third — requires rich domain knowledge
4. Phase 9 (adaptive) last — needs data from Phases 6–8 to learn from

### Minimum Viable Phase 6

If bandwidth is limited, ship Phase 6 in two steps:

**Step 1 (2–3 weeks):**
- `skills.yml` parser
- `SkillRouter` (path-based + blast radius)
- `SkillComposer` (DAG execution)
- 4 built-in skills: `lint`, `type_check`, `security_scan`, `docs_link_check`
- CLI: `context skills plan`, `context skills run`

**Step 2 (2–3 weeks):**
- `BlastRadiusEnforcer` with decomposition suggestions
- `ReasoningCheckpoint`
- `EvidenceBundle`
- MCP tools: `get_skill_plan`, `run_skill_gate`
- `beforeFileWrite` hook

---

## New Success Metrics

| Metric | Target | Phase |
|--------|--------|-------|
| Skill gates triggered per PR | Measurable from Day 1 | 6 |
| Blast radius violations caught before write | > 90% of violating edits | 6 |
| Evidence bundles per agent session | 100% coverage | 6 |
| Architectural invariant violations caught | 100% before commit | 7 |
| Intent preservation test pass rate | > 95% before allow | 7 |
| Context trust score avg (high-risk tasks) | > 0.85 | 8 |
| Context debt reduction after re-index | > 60% debt reduction | 8 |
| Failure patterns learned per month | > 5 per active repo | 9 |
| Coupling trend alerts surfaced | 100% of degrading repos | 9 |
| Policy auto-updates proposed per quarter | > 3 human-approved | 9 |

---

## Research Backing

| Research | Insight | Applied In |
|----------|---------|-----------|
| Agentless (arXiv 2407.01489) | Localize → repair → verify beats complex agents | Phase 6: Verifier Loop |
| SWT-Bench | Generated tests filter proposed fixes | Phase 7: Intent Preservation |
| AOCI (arXiv 2605.02421) | Symbolic-semantic repo blueprints beat RAG | Phase 7: Contract Registry |
| Hierarchical Context Pruning (arXiv 2406.18294) | Topology preservation improves completion accuracy | Phase 8: Trust-Aware Compiler |
| ACE (arXiv 2510.04618) | Evolving context playbooks → self-improvement without supervision | Phase 9: Playbook Learner |
| Graphiti | Temporal context graphs with provenance | Phase 8: Provenance Chains |

---

## Open Questions for Each Phase

### Phase 6
1. Should `skills.yml` support custom shell commands as skill runners (e.g., `run: pytest src/auth/`) or only built-in skills?
2. What is the right blast radius threshold default — should it be repo-size relative?
3. Should the reasoning checkpoint be mandatory for all hub nodes, or configurable?

### Phase 7
1. How do we handle contracts that are intentionally removed (API deprecation)?
2. Can we auto-generate `invariants.yml` from the graph, or does it need to be human-authored?
3. Is intent preservation verification feasible without a running test environment in CI?

### Phase 8
1. How often should context debt be recomputed — on every build or on demand?
2. Should trust tiers be user-configurable or standardised?
3. Should the agent lock table be file-level or symbol-level?

### Phase 9
1. What failure count threshold triggers a pattern being surfaced (to avoid noise)?
2. Should playbook updates require human approval always, or auto-apply below a risk threshold?
3. How long should context snapshots be retained — by count, by age, or by event type?

---

*This plan is a living document. Update it as phases ship and research evolves.*
