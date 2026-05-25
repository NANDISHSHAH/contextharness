"""Blast radius enforcer — hard cap + decomposition suggestions."""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from contextpack.skills.manifest import SkillManifest
from contextpack.skills.router import SkillPlan


class SubTask(BaseModel):
    label: str
    files: list[str] = Field(default_factory=list)
    blast_radius: int = 0
    description: str = ""


class DecompositionPlan(BaseModel):
    blocked: bool = True
    blocked_reason: str = ""
    blast_radius: int = 0
    max_allowed: int = 0
    subtasks: list[SubTask] = Field(default_factory=list)

    def to_text(self) -> str:
        lines = [
            f"⛔ BLOCKED: blast radius {self.blast_radius} exceeds policy max {self.max_allowed}",
            "",
            self.blocked_reason,
            "",
            "Suggested decomposition:",
        ]
        for i, sub in enumerate(self.subtasks, 1):
            label = chr(64 + i)
            lines.append(
                f"  Task {label}: {sub.label}  [blast_radius: {sub.blast_radius}]"
            )
            if sub.description:
                lines.append(f"            {sub.description}")
        lines.extend([
            "",
            "Run each task in sequence with full skill gates between steps.",
        ])
        return "\n".join(lines)


class BlastRadiusEnforcer:
    """Checks a SkillPlan against policy max_blast_radius; proposes decompositions."""

    def check(
        self,
        plan: SkillPlan,
        manifest: SkillManifest,
    ) -> DecompositionPlan | None:
        """Return a DecompositionPlan if blast radius exceeds policy; else None."""
        max_br: int | None = None
        for policy in manifest.policies:
            if policy.name in plan.policies_matched:
                if policy.require.max_blast_radius is not None:
                    max_br = (
                        policy.require.max_blast_radius
                        if max_br is None
                        else min(max_br, policy.require.max_blast_radius)
                    )

        if max_br is None or plan.blast_radius <= max_br:
            return None

        subtasks = self._suggest_subtasks(plan, max_br)
        hub_str = (
            f" (hub nodes: {', '.join(plan.hub_nodes_touched)})"
            if plan.hub_nodes_touched
            else ""
        )
        return DecompositionPlan(
            blocked=True,
            blocked_reason=(
                f"This task touches {plan.blast_radius} downstream modules{hub_str}. "
                f"The matched policy caps blast radius at {max_br}."
            ),
            blast_radius=plan.blast_radius,
            max_allowed=max_br,
            subtasks=subtasks,
        )

    def _suggest_subtasks(self, plan: SkillPlan, max_br: int) -> list[SubTask]:
        """Produce a naive decomposition: one task per hub node + remainder."""
        subtasks: list[SubTask] = []
        n_hubs = max(len(plan.hub_nodes_touched), 1)

        for hub in plan.hub_nodes_touched:
            br = max(1, plan.blast_radius // n_hubs)
            subtasks.append(
                SubTask(
                    label=f"Update {Path(hub).name}",
                    files=[hub],
                    blast_radius=br,
                    description=f"Isolate changes to hub node {hub}",
                )
            )

        remainder_br = max(
            0, plan.blast_radius - sum(s.blast_radius for s in subtasks)
        )
        subtasks.append(
            SubTask(
                label="Update downstream callers + integration tests",
                files=[],
                blast_radius=remainder_br,
                description="Apply follow-up changes after hub updates are stable",
            )
        )
        return subtasks
