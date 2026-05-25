"""Example 07 — Context Governance & Trust (Phase 8).

Demonstrates:
- TrustScorer: 5-tier scoring, risk-gated filtering
- ContextDebtTracker: per-module staleness scoring
- ProvenanceChain: chain of custody per chunk
- BudgetRiskAnalyser: budget as risk signal
- AgentLockTable: multi-agent conflict detection

Run:
    python examples/07_governance.py
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

DB = Path("/tmp/contextharness_demo/memory.db")
DB.parent.mkdir(parents=True, exist_ok=True)


async def main() -> None:
    from contextpack.governance import (
        TrustScorer,
        ContextDebtTracker,
        DebtRecord,
        ProvenanceChain,
        ProvenanceRecord,
        BudgetRiskAnalyser,
        AgentLockTable,
    )

    # ── 1. Trust scoring ──────────────────────────────────────────────────────
    print("=" * 60)
    print("1.  TrustScorer — 5-tier trust per source type")
    print("=" * 60)
    scorer = TrustScorer()

    examples = [
        ("type_signature", "src/auth/tokens.py",  0,   True,  0.95),
        ("test",           "tests/test_auth.py",   2,   True,  0.92),
        ("docstring",      "src/auth/tokens.py",  15,   False, 0.0),
        ("docs",           "docs/auth.md",         90,  False, 0.0),
        ("jira",           "PROJ-123",             0,   False, 0.0),
    ]
    chunks = []
    for source_type, file_path, days, ci, coverage in examples:
        score = scorer.score_chunk(source_type, file_path, days, ci, coverage)
        print(f"  {score.label:<20s}  {score.score:.3f}  {score.rationale}")
        chunks.append({
            "chunk_id": f"chunk_{source_type[:4]}",
            "content": f"from {file_path}",
            "trust_tier": score.tier,
            "trust_score": score.score,
            "source_type": source_type,
        })

    # High-risk task: only Tier 1-2 allowed
    print()
    included, excluded = scorer.filter_for_risk(chunks, risk_score=0.82)
    print(f"  High-risk task (score=0.82): included={len(included)}, excluded={len(excluded)}")
    for c in excluded:
        print(f"    excluded [{c['source_type']}] trust_tier={c['trust_tier']}")

    # ── 2. Context debt ───────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("2.  ContextDebtTracker — per-module staleness report")
    print("=" * 60)
    tracker = ContextDebtTracker(DB)

    now = time.time()
    records = [
        tracker.compute_debt("src/auth/middleware.py",  now - 3 * 86400,   churn_count=18, hub_centrality=0.91),
        tracker.compute_debt("src/payment/processor.py", now - 1 * 86400,  churn_count=4,  hub_centrality=0.30),
        tracker.compute_debt("src/db/models.py",         now - 21 * 86400, churn_count=22, hub_centrality=0.60),
        tracker.compute_debt("src/api/routes.py",        now - 12 * 86400, churn_count=8,  hub_centrality=0.20),
    ]
    await tracker.upsert_batch(records)
    all_records = await tracker.list_all()
    print(tracker.format_report(all_records))

    # ── 3. Provenance chains ──────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("3.  ProvenanceChain — chain of custody per chunk")
    print("=" * 60)
    chain = ProvenanceChain(DB)
    prov = ProvenanceRecord(
        chunk_id="chunk_validate_token_001",
        source="src/auth/tokens.py",
        source_type="code",
        trust_tier=2,
        trust_score=0.88,
        file_hash="sha256:a3f2b1...",
        git_commit="abc1234",
        git_author="dev@company.com",
        last_modified=now - 3 * 86400,
        test_coverage=0.94,
        ci_verified=True,
        last_ci_run=now - 86400,
    )
    await chain.record(prov)
    retrieved = await chain.get("chunk_validate_token_001")
    if retrieved:
        print(f"  chunk_id:     {retrieved.chunk_id}")
        print(f"  source:       {retrieved.source}")
        print(f"  trust_tier:   T{retrieved.trust_tier}")
        print(f"  trust_score:  {retrieved.trust_score}")
        print(f"  ci_verified:  {retrieved.ci_verified}")
        print(f"  inline tag:   {retrieved.to_inline_tag()}")

    # ── 4. Budget risk signal ─────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("4.  BudgetRiskAnalyser — budget as safety gate")
    print("=" * 60)
    analyser = BudgetRiskAnalyser()

    for budget, actual, risk in [(16000, 8000, 0.3), (8000, 9200, 0.5), (8000, 13500, 0.82)]:
        signal = analyser.analyse(budget=budget, actual_tokens=actual, risk_score=risk)
        print(f"\n  Budget={budget:,}  Actual={actual:,}  Risk={risk}")
        print(f"  " + analyser.format_signal(signal).replace("\n", "\n  "))

    # ── 5. Multi-agent conflict detection ─────────────────────────────────────
    print()
    print("=" * 60)
    print("5.  AgentLockTable — multi-agent conflict detection")
    print("=" * 60)
    locks = AgentLockTable(DB)

    # Agent A acquires a lock
    lock_a = await locks.acquire(
        "agent_cursor_1",
        files=["src/auth/tokens.py", "src/auth/middleware.py"],
        ttl=3600,
    )
    print(f"  Agent A acquired: {lock_a.lock_id if hasattr(lock_a, 'lock_id') else lock_a}")

    # Agent B tries the same file — should conflict
    conflict = await locks.check_conflicts(
        "agent_cursor_2",
        files=["src/auth/tokens.py", "src/api/routes.py"],
        symbols=[],
    )
    print()
    print(conflict.to_text())

    # Release lock
    if hasattr(lock_a, "lock_id"):
        await locks.release(lock_a.lock_id)
        print(f"\n  Lock {lock_a.lock_id} released")


if __name__ == "__main__":
    asyncio.run(main())
