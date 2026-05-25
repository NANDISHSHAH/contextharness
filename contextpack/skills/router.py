"""Skill router — maps a diff + graph state to a SkillPlan."""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from contextpack.skills.manifest import SkillManifest, SkillPolicy


class SkillPlan(BaseModel):
    policies_matched: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    risk_score: float = 0.0
    blast_radius: int = 0
    hub_nodes_touched: list[str] = Field(default_factory=list)
    human_review_required: bool = False
    decomposition_required: bool = False
    reasoning: str = ""

    def summary(self) -> str:
        lines = [
            f"Risk score: {self.risk_score:.2f}  |  Blast radius: {self.blast_radius}",
            f"Policies matched: {', '.join(self.policies_matched) or 'default'}",
            f"Required skills:  {', '.join(self.required_skills) or 'none'}",
        ]
        if self.hub_nodes_touched:
            lines.append(f"Hub nodes touched: {', '.join(self.hub_nodes_touched)}")
        if self.human_review_required:
            lines.append("⚠️  Human review required by policy")
        if self.decomposition_required:
            lines.append("⛔  Decomposition required — blast radius exceeds policy max")
        return "\n".join(lines)


class SkillRouter:
    """Routes a set of changed files to a SkillPlan."""

    def __init__(self, manifest: SkillManifest) -> None:
        self.manifest = manifest

    def route(
        self,
        changed_files: list[str],
        blast_radius: int = 0,
        hub_centralities: dict[str, float] | None = None,
        total_nodes: int = 1,
    ) -> SkillPlan:
        """Compute a SkillPlan for the given changed files."""
        hub_centralities = hub_centralities or {}

        matched_policies: list[SkillPolicy] = []
        hub_nodes_touched: list[str] = []

        for file_path in changed_files:
            centrality = hub_centralities.get(file_path, 0.0)
            if centrality >= 0.7:
                hub_nodes_touched.append(file_path)

            file_policies = self.manifest.policies_matching(
                file_path,
                blast_radius=blast_radius,
                hub_centrality=centrality,
            )
            for p in file_policies:
                if p not in matched_policies:
                    matched_policies.append(p)

        # Always apply default policy if nothing matched
        if not matched_policies:
            matched_policies = [
                p for p in self.manifest.policies if p.name == "default"
            ]
            if not matched_policies and self.manifest.policies:
                matched_policies = [self.manifest.policies[0]]

        # Merge requirements
        required_skills: set[str] = set()
        human_review = False
        max_br: int | None = None

        for p in matched_policies:
            required_skills.update(p.require.skills)
            if p.require.human_review:
                human_review = True
            if p.require.max_blast_radius is not None:
                max_br = (
                    p.require.max_blast_radius
                    if max_br is None
                    else min(max_br, p.require.max_blast_radius)
                )

        # ── Risk score ────────────────────────────────────────────────────────
        # 0.35 * hub_centrality_max
        # 0.30 * blast_radius_normalised
        # 0.20 * policy_count_normalised
        # 0.15 * cross_module_flag
        hub_max = (
            max(hub_centralities.get(f, 0.0) for f in changed_files)
            if changed_files
            else 0.0
        )
        br_norm = min(1.0, blast_radius / max(total_nodes, 1))
        policy_norm = min(1.0, len(matched_policies) / 5.0)
        top_modules = {Path(f).parts[0] for f in changed_files if Path(f).parts}
        cross_module = 1.0 if len(top_modules) > 1 else 0.0

        risk_score = min(
            1.0,
            0.35 * hub_max
            + 0.30 * br_norm
            + 0.20 * policy_norm
            + 0.15 * cross_module,
        )

        decomposition_required = max_br is not None and blast_radius > max_br

        reasoning_parts = [
            f"Matched: {', '.join(p.name for p in matched_policies)}"
        ]
        if hub_nodes_touched:
            reasoning_parts.append(f"Hubs: {', '.join(hub_nodes_touched)}")
        if decomposition_required:
            reasoning_parts.append(
                f"Blast radius {blast_radius} > max {max_br} — decompose"
            )

        return SkillPlan(
            policies_matched=[p.name for p in matched_policies],
            required_skills=sorted(required_skills),
            risk_score=round(risk_score, 3),
            blast_radius=blast_radius,
            hub_nodes_touched=hub_nodes_touched,
            human_review_required=human_review,
            decomposition_required=decomposition_required,
            reasoning="; ".join(reasoning_parts),
        )
