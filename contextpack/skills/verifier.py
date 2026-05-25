"""Skill verifier loop — orchestrates the full pre-skill gate flow."""
from __future__ import annotations

import hashlib
from pathlib import Path

import structlog
from pydantic import BaseModel, Field

from contextpack.skills.composer import SkillComposer, SkillResult
from contextpack.skills.enforcer import BlastRadiusEnforcer, DecompositionPlan
from contextpack.skills.evidence import EvidenceBundle, EvidenceStore
from contextpack.skills.manifest import SkillManifest
from contextpack.skills.router import SkillPlan, SkillRouter

logger = structlog.get_logger(__name__)


class VerifierResult(BaseModel):
    allowed: bool
    plan: SkillPlan
    skill_results: list[SkillResult] = Field(default_factory=list)
    decomposition: DecompositionPlan | None = None
    evidence_id: str = ""
    block_reason: str = ""

    def to_text(self) -> str:
        status = "✅ ALLOWED" if self.allowed else "❌ BLOCKED"
        lines = [status, "", self.plan.summary()]
        if self.block_reason:
            lines.extend(["", f"Block reason: {self.block_reason}"])
        if self.decomposition:
            lines.extend(["", self.decomposition.to_text()])
        if self.skill_results:
            lines.extend(["", "── Skill results ──"])
            for r in self.skill_results:
                if r.skipped:
                    icon = "⏭ "
                elif r.passed:
                    icon = "✅"
                else:
                    icon = "❌"
                lines.append(f"  {icon} {r.skill:20s} ({r.duration_ms:.0f} ms)")
                if r.skip_reason:
                    lines.append(f"     ↳ skipped: {r.skip_reason}")
                for finding in r.findings[:2]:
                    lines.append(f"     · {finding}")
        if self.evidence_id:
            lines.append(f"\nEvidence bundle: {self.evidence_id}")
        return "\n".join(lines)


class SkillVerifierLoop:
    """Orchestrates the full pre-skill gate: route → enforce → run → record."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._evidence = EvidenceStore(db_path)

    async def verify(
        self,
        changed_files: list[str],
        repo_path: Path,
        manifest: SkillManifest | None = None,
        blast_radius: int = 0,
        hub_centralities: dict[str, float] | None = None,
        total_nodes: int = 1,
        agent_id: str = "default",
    ) -> VerifierResult:
        """Run the full verification flow. Returns VerifierResult."""
        if manifest is None:
            manifest = SkillManifest.load(repo_path)

        hub_centralities = hub_centralities or {}

        # ── 1. Route ──────────────────────────────────────────────────────────
        router = SkillRouter(manifest)
        plan = router.route(
            changed_files=changed_files,
            blast_radius=blast_radius,
            hub_centralities=hub_centralities,
            total_nodes=total_nodes,
        )
        logger.info("skill_plan_computed", plan=plan.model_dump())

        # ── 2. Blast radius enforcement ───────────────────────────────────────
        enforcer = BlastRadiusEnforcer()
        decomp = enforcer.check(plan, manifest)
        if decomp and decomp.blocked:
            result = VerifierResult(
                allowed=False,
                plan=plan,
                decomposition=decomp,
                block_reason=(
                    f"Blast radius {blast_radius} exceeds policy max {decomp.max_allowed}"
                ),
            )
            result.evidence_id = await self._record(result, changed_files, agent_id)
            return result

        # ── 3. Human review gate ──────────────────────────────────────────────
        if plan.human_review_required:
            result = VerifierResult(
                allowed=False,
                plan=plan,
                block_reason="Human review required by policy — paused for approval",
            )
            result.evidence_id = await self._record(result, changed_files, agent_id)
            return result

        # ── 4. Execute skills ─────────────────────────────────────────────────
        composer = SkillComposer()
        # Run required + advisory together; advisory results never block
        all_to_run = list(plan.required_skills) + [
            s for s in plan.advisory_skills if s not in plan.required_skills
        ]
        skill_results = await composer.run(all_to_run, repo_path)

        advisory_set = set(plan.advisory_skills)
        required_results = [r for r in skill_results if r.skill not in advisory_set]
        # Allowed when all REQUIRED (non-advisory) skills passed
        all_passed = all(r.passed for r in required_results)
        failed = [r.skill for r in required_results if not r.passed and not r.skipped]
        advisory_failed = [
            r.skill
            for r in skill_results
            if r.skill in advisory_set and not r.passed and not r.skipped
        ]
        block_reason = (
            f"Skills failed: {', '.join(failed)}" if failed else ""
        )
        if advisory_failed and not failed:
            # Don't block; just note advisory warnings in reasoning
            plan.reasoning = (
                (plan.reasoning + "; " if plan.reasoning else "")
                + f"advisory warnings: {', '.join(advisory_failed)}"
            )

        result = VerifierResult(
            allowed=all_passed,
            plan=plan,
            skill_results=skill_results,
            block_reason=block_reason,
        )
        result.evidence_id = await self._record(result, changed_files, agent_id)
        return result

    async def _record(
        self,
        result: VerifierResult,
        changed_files: list[str],
        agent_id: str,
    ) -> str:
        diff_hash = hashlib.sha256(
            "|".join(sorted(changed_files)).encode()
        ).hexdigest()[:12]
        bundle = EvidenceBundle(
            agent_id=agent_id,
            files_modified=changed_files,
            skill_plan=result.plan.model_dump(),
            skill_results=[r.model_dump() for r in result.skill_results],
            diff_hash=diff_hash,
        )
        return await self._evidence.store(bundle)
