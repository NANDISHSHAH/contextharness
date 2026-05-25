"""Example 08 — Adaptive Intelligence (Phase 9).

Demonstrates:
- FailurePatternStore: classify recurring failures, proactive briefing
- CouplingMonitor: architectural decay detection from graph snapshots
- ContextSnapshotEngine: semantic state diff across agent runs
- PlaybookLearner: auto-propose skills.yml additions from evidence

Run:
    python examples/08_adaptive.py
"""
from __future__ import annotations

import asyncio
from pathlib import Path

DB = Path("/tmp/contextharness_demo/memory.db")
DB.parent.mkdir(parents=True, exist_ok=True)


async def main() -> None:
    from contextpack.adaptive import (
        FailurePatternStore,
        CouplingMonitor,
        CouplingSnapshot,
        ContextSnapshotEngine,
        ContextSnapshot,
        PlaybookLearner,
    )
    from contextpack.skills.evidence import EvidenceStore, EvidenceBundle

    # ── 1. Failure pattern memory ─────────────────────────────────────────────
    print("=" * 60)
    print("1.  FailurePatternStore — recurring failure classification")
    print("=" * 60)
    store = FailurePatternStore(DB)

    # Simulate 5 security_scan failures on auth files
    for i in range(5):
        pattern = await store.record(
            skill="security_scan",
            file_path="src/auth/middleware.py",
            failure_output="Issue: [B106] missing rate limiting on endpoint /api/auth/login  Severity: Medium",
            remediation_hint="Add @rate_limit from auth.decorators to all auth endpoints",
        )

    # Also record a type_check failure
    await store.record(
        skill="type_check",
        file_path="src/payment/processor.py",
        failure_output="error: Incompatible return value type (got None, expected TransactionResult)",
    )

    all_patterns = await store.list_all()
    print(f"  Recorded {len(all_patterns)} pattern(s):")
    for p in all_patterns:
        print(f"  · [{p.skill}] {p.failure_class:<30s} ×{p.frequency}  proactive={p.is_proactive()}")

    # Proactive briefing for next auth edit
    proactive = await store.list_proactive("src/auth/middleware.py")
    print(f"\n  Proactive warnings for src/auth/middleware.py: {len(proactive)}")
    for p in proactive:
        print(p.to_briefing())

    # ── 2. Coupling monitor ───────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("2.  CouplingMonitor — architectural decay trend")
    print("=" * 60)
    monitor = CouplingMonitor(DB)
    import time

    # Simulate coupling snapshots over 4 weeks
    base_time = time.time() - 30 * 86400
    snapshots_data = [
        (base_time + 0 * 7 * 86400,  0.23, 1456, 912, 10, 0),
        (base_time + 1 * 7 * 86400,  0.24, 1480, 920, 10, 0),
        (base_time + 2 * 7 * 86400,  0.27, 1530, 930, 11, 1),
        (base_time + 3 * 7 * 86400,  0.31, 1600, 940, 13, 1),
        (base_time + 4 * 7 * 86400,  0.33, 1671, 950, 14, 2),
    ]
    for ts, avg, edges, nodes, hubs, cycles in snapshots_data:
        snap = CouplingSnapshot(
            timestamp=ts,
            avg_coupling=avg,
            edge_count=edges,
            node_count=nodes,
            hub_count=hubs,
            cycle_count=cycles,
            hotspots=["src/api/routes/users.py", "src/auth/middleware.py"],
        )
        await monitor.record(snap)

    trend = await monitor.trend(days=35)
    print(trend.to_text())

    # ── 3. Context snapshots ──────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("3.  ContextSnapshotEngine — semantic state diff")
    print("=" * 60)
    engine = ContextSnapshotEngine(DB)

    # Simulate a graph-like object for the snapshot
    class FakeGraph:
        class graph:
            @staticmethod
            def number_of_nodes(): return 912
            @staticmethod
            def number_of_edges(): return 1456
            @staticmethod
            def nodes(): return range(912)
            @staticmethod
            def degree(n=None):
                if n is None:
                    return [(i, i % 5) for i in range(912)]
                return n % 5
            @staticmethod
            def out_degree(n): return n % 4

    snap_before = engine.capture(
        "demo_agent",
        "Refactor auth middleware",
        FakeGraph(),
        context_pack={"chunk_count": 24, "token_estimate": 7840, "trust_avg": 0.88},
    )
    # Simulate post-refactor: more edges and a new hub
    class FakeGraph2:
        class graph:
            @staticmethod
            def number_of_nodes(): return 915
            @staticmethod
            def number_of_edges(): return 1471
            @staticmethod
            def nodes(): return range(915)
            @staticmethod
            def degree(n=None):
                if n is None:
                    return [(i, i % 5) for i in range(915)]
                return n % 5
            @staticmethod
            def out_degree(n): return n % 4

    snap_after = engine.capture(
        "demo_agent",
        "Refactor auth middleware",
        FakeGraph2(),
        context_pack={"chunk_count": 26, "token_estimate": 8200, "trust_avg": 0.91},
    )

    before_id = await engine.save(snap_before)
    after_id  = await engine.save(snap_after)

    diff = engine.diff(snap_before, snap_after)
    print(diff.to_text())

    # ── 4. Playbook learner ───────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("4.  PlaybookLearner — auto-propose skills.yml additions")
    print("=" * 60)

    # Seed some evidence bundles showing security_scan always passes on auth files
    ev_store = EvidenceStore(DB)
    for i in range(4):
        bundle = EvidenceBundle(
            agent_id=f"agent_{i}",
            files_modified=["src/auth/middleware.py"],
            skill_plan={"risk_score": 0.7, "blast_radius": 8},
            skill_results=[
                {"skill": "lint",           "passed": True, "duration_ms": 320},
                {"skill": "security_scan",  "passed": True, "duration_ms": 1100},
            ],
        )
        await ev_store.store(bundle)

    # Also seed payment evidence
    for i in range(3):
        bundle = EvidenceBundle(
            agent_id=f"payment_agent_{i}",
            files_modified=["src/payment/processor.py"],
            skill_plan={"risk_score": 0.5, "blast_radius": 4},
            skill_results=[
                {"skill": "lint",       "passed": True, "duration_ms": 280},
                {"skill": "type_check", "passed": True, "duration_ms": 870},
            ],
        )
        await ev_store.store(bundle)

    bundles = await ev_store.list_recent(limit=20)
    learner = PlaybookLearner()
    proposals = learner.propose([b.model_dump() for b in bundles])
    print(learner.format_proposals(proposals))


if __name__ == "__main__":
    asyncio.run(main())
