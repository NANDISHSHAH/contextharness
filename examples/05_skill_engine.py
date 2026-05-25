"""Example 05 — Pre-Skill Engine (Phase 6).

Demonstrates:
- SkillManifest: load or use defaults
- SkillRouter.route() → SkillPlan
- BlastRadiusEnforcer: decomposition when blast radius too high
- SkillComposer: DAG-ordered execution
- SkillVerifierLoop.verify(): full gate (no API key needed)
- EvidenceStore: audit trail

Run:
    python examples/05_skill_engine.py
"""
from __future__ import annotations

import asyncio
from pathlib import Path

# ── paths ─────────────────────────────────────────────────────────────────────
REPO = Path(__file__).parent / "sample_repo"
DB   = Path("/tmp/contextharness_demo/memory.db")
DB.parent.mkdir(parents=True, exist_ok=True)


async def main() -> None:
    from contextpack.skills.manifest import SkillManifest, SkillPolicy, MatchCriteria, RequireSpec
    from contextpack.skills.router import SkillRouter
    from contextpack.skills.composer import SkillComposer, SKILL_DAG
    from contextpack.skills.enforcer import BlastRadiusEnforcer
    from contextpack.skills.verifier import SkillVerifierLoop
    from contextpack.skills.evidence import EvidenceStore

    # ── 1. Build a manifest (inline, no skills.yml file needed) ───────────────
    print("=" * 60)
    print("1.  Skill Manifest")
    print("=" * 60)
    manifest = SkillManifest(
        policies=[
            SkillPolicy(
                name="auth_changes",
                description="Auth subgraph — security gates required",
                match=MatchCriteria(paths=["src/auth/**"]),
                require=RequireSpec(
                    skills=["lint", "type_check", "security_scan"],
                    max_blast_radius=20,
                ),
            ),
            SkillPolicy(
                name="default",
                description="Lint everything else",
                match=MatchCriteria(),
                require=RequireSpec(skills=["lint"]),
            ),
        ]
    )
    print(f"Policies: {[p.name for p in manifest.policies]}")

    # ── 2. Route changed files to a SkillPlan ────────────────────────────────
    print()
    print("=" * 60)
    print("2.  SkillRouter — compute SkillPlan")
    print("=" * 60)
    router = SkillRouter(manifest)
    plan = router.route(
        changed_files=["src/auth/middleware.py", "src/auth/tokens.py"],
        blast_radius=12,
        hub_centralities={"src/auth/middleware.py": 0.91},
        total_nodes=200,
    )
    print(plan.summary())

    # ── 3. Skill DAG — topological order ─────────────────────────────────────
    print()
    print("=" * 60)
    print("3.  Skill DAG — execution order")
    print("=" * 60)
    composer = SkillComposer()
    order = composer.execution_order(plan.required_skills)
    print("Execution order:", " → ".join(order))

    # ── 4. Blast radius enforcement ───────────────────────────────────────────
    print()
    print("=" * 60)
    print("4.  BlastRadiusEnforcer — blast radius = 30 (over limit)")
    print("=" * 60)
    high_blast_plan = router.route(
        changed_files=["src/auth/middleware.py"],
        blast_radius=30,     # over the max_blast_radius=20 in policy
        hub_centralities={"src/auth/middleware.py": 0.91},
    )
    enforcer = BlastRadiusEnforcer()
    decomp = enforcer.check(high_blast_plan, manifest)
    if decomp:
        print(decomp.to_text())
    else:
        print("No decomposition needed")

    # ── 5. Full verifier loop ─────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("5.  SkillVerifierLoop — full gate on real repo")
    print("=" * 60)
    loop = SkillVerifierLoop(DB)
    result = await loop.verify(
        changed_files=["src/auth/middleware.py"],
        repo_path=REPO,
        manifest=manifest,
        blast_radius=8,
        hub_centralities={"src/auth/middleware.py": 0.91},
        agent_id="demo_agent",
    )
    print(result.to_text())

    # ── 6. Evidence audit trail ───────────────────────────────────────────────
    print()
    print("=" * 60)
    print("6.  EvidenceStore — audit trail")
    print("=" * 60)
    store = EvidenceStore(DB)
    bundles = await store.list_recent(limit=5)
    for b in bundles:
        icon = "✅" if b.passed else "❌"
        print(f"  {icon} {b.action_id}  agent={b.agent_id}  files={b.files_modified}")


if __name__ == "__main__":
    asyncio.run(main())
