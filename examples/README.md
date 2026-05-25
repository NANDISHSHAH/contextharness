# ContextPack — Runnable Examples

All examples work with **no cloud API key** unless noted. They run against the bundled `sample_repo/`.

```bash
cd /path/to/contextharness
uv sync
uv pip install -e .
```

---

## 01 — Basic package usage

```bash
python examples/01_basic_package_usage.py
```

**What it shows:**
- `Project.init()` + `Project.build()` → `(ProjectMap, BuildStats)`
- `Project.harvest()` → `AggregatedAgentContext`
- Adapter injection: Claude, OpenAI, LangGraph
- `Project.ask()` — offline answer, no API key needed

---

## 02 — Azure AI Foundry agent

**Requires Azure Foundry credentials.**

1. Open [Azure AI Foundry](https://ai.azure.com) → **Deployments**
2. Copy endpoint, key, deployment name into `.env`:

```env
CONTEXTPACK_LLM_PROVIDER=azure_foundry
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_DEPLOYMENT=<deployment-name>

# Optional: same resource for embeddings
CONTEXTPACK_EMBEDDING_PROVIDER=azure_foundry
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
```

```bash
python examples/02_azure_foundry_agent.py
# or via CLI:
context build examples/sample_repo
context ask "How does authentication work?" examples/sample_repo --llm
```

---

## 03 — Incremental builds & change tracking (Phase 3)

```bash
python examples/03_incremental_watch.py
```

**What it shows:**
- Full build → `incremental_build()` with no changes (fast path)
- Touch a file → incremental build records the delta
- Query the SQLite change log: `project.recent_changes()`
- Low-level helpers: `load_hashes`, `diff_hashes`, `build_changeset`

---

## 04 — Workflows & multi-agent memory (Phase 5)

```bash
python examples/04_workflows_agent_memory.py
```

**What it shows:**
- `WorkflowExtractor` detecting API surfaces, call chains, class lifecycles
- `project.workflows()` — query extracted workflows
- `AgentMemory.store_decision()` / `store_constraint()` / `store_observation()`
- `SharedMemory.recall_all()` — cross-agent fact retrieval
- `format_for_prompt()` — inject shared memory into LLM prompt

---

## 05 — Pre-Skill Engine (Phase 6)

```bash
python examples/05_skill_engine.py
```

**What it shows:**
- Load a `SkillManifest` (skills.yml or default policies)
- `SkillRouter.route()` → `SkillPlan` with risk score, blast radius, required gates
- `SkillComposer.execution_order()` — topological sort of the skill DAG
- `SkillVerifierLoop.verify()` — full gate: route → enforce → run → record evidence
- `BlastRadiusEnforcer.check()` — decomposition plan when blast radius too high
- `EvidenceStore.list_recent()` — audit trail of all gate results

---

## 06 — Semantic Contracts (Phase 7)

```bash
python examples/06_contracts.py
```

**What it shows:**
- `ContractExtractor.extract_from_file()` — AST-based preconditions, postconditions, raises
- `ContractRegistry.upsert_batch()` / `search()` — SQLite-backed contract store
- `InvariantConfig.load()` + `InvariantGuard.check()` — architectural rule validation
- `NegativeContextIndex.add()` / `scan_code()` — anti-pattern detection
- `IntentPreserver.extract_invariants()` + `check_preserved()` — behavioral invariant check

---

## 07 — Context Governance (Phase 8)

```bash
python examples/07_governance.py
```

**What it shows:**
- `TrustScorer.score_chunk()` — 5-tier trust scoring per context source
- `TrustScorer.filter_for_risk()` — exclude low-trust chunks on high-risk tasks
- `ContextDebtTracker.compute_debt()` + `format_report()` — staleness × churn × centrality
- `ProvenanceChain.record()` — chain of custody per context chunk
- `BudgetRiskAnalyser.analyse()` — budget as risk signal with option menu
- `AgentLockTable.acquire()` + `check_conflicts()` — multi-agent conflict detection

---

## 08 — Adaptive Intelligence (Phase 9)

```bash
python examples/08_adaptive.py
```

**What it shows:**
- `FailurePatternStore.record()` — classify and store skill failures
- `FailurePatternStore.list_proactive()` — surface patterns before an agent edits a file
- `CouplingMonitor.snapshot_from_graph()` + `trend()` — architectural decay detection
- `ContextSnapshotEngine.capture()` + `diff()` — semantic state diff across agent runs
- `PlaybookLearner.propose()` — auto-propose `skills.yml` additions from evidence bundles

---

## Sample repo

`examples/sample_repo/` — minimal Python auth + payment module with guidelines. Used by all examples.

```
sample_repo/
  src/
    auth/
      middleware.py      # hub node (high centrality)
      tokens.py
    payment/
      processor.py
    api/
      routes.py
  tests/
    test_auth.py
    test_payment.py
  .pr-review/
    guidelines.md
```
