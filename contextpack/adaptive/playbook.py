"""Playbook learner — propose skills.yml additions from observed successful runs."""
from __future__ import annotations

import time
from pathlib import Path

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class PlaybookProposal(BaseModel):
    """A proposed addition to skills.yml."""
    policy_name: str
    description: str
    file_pattern: str
    skills_to_add: list[str]
    confidence: float  # 0-1
    evidence: str      # human-readable explanation
    timestamp: float = Field(default_factory=time.time)

    def to_yaml_block(self) -> str:
        skills_str = "\n".join(f"        - {s}" for s in self.skills_to_add)
        return f"""
  - name: {self.policy_name}
    description: "{self.description}"
    match:
      paths: ["{self.file_pattern}"]
    require:
      skills:
{skills_str}
"""

    def to_text(self) -> str:
        return (
            f"PLAYBOOK PROPOSAL: Add policy `{self.policy_name}`\n"
            f"  Evidence: {self.evidence}\n"
            f"  Skills to add: {', '.join(self.skills_to_add)}\n"
            f"  Confidence: {self.confidence:.0%}\n"
            f"  Add to skills.yml:\n{self.to_yaml_block()}"
        )


class PlaybookLearner:
    """
    Analyse evidence bundles to propose skills.yml policy additions.

    Learning rule: if skill X was present in ≥N consecutive successful runs
    on file pattern P, but was absent in failed runs on the same pattern,
    propose adding X as a required skill for P.
    """

    MIN_SUCCESSFUL_RUNS = 3
    MIN_CONFIDENCE = 0.65

    def propose(self, evidence_records: list[dict]) -> list[PlaybookProposal]:
        """
        Analyse a list of evidence bundle dicts and propose playbook updates.
        """
        if not evidence_records:
            return []

        # Group by file pattern → {skill: [passed_bools]}
        pattern_skill_outcomes: dict[str, dict[str, list[bool]]] = {}

        for record in evidence_records:
            files = record.get("files_modified", [])
            skill_results = record.get("skill_results", [])
            for f in files:
                pattern = _file_to_pattern(f)
                if pattern not in pattern_skill_outcomes:
                    pattern_skill_outcomes[pattern] = {}
                for sr in skill_results:
                    skill = sr.get("skill", "")
                    passed = sr.get("passed", False)
                    if skill:
                        pattern_skill_outcomes[pattern].setdefault(skill, []).append(passed)

        proposals: list[PlaybookProposal] = []
        for pattern, skills in pattern_skill_outcomes.items():
            skills_to_add: list[str] = []
            for skill, outcomes in skills.items():
                if len(outcomes) < self.MIN_SUCCESSFUL_RUNS:
                    continue
                success_rate = sum(outcomes) / len(outcomes)
                if success_rate >= self.MIN_CONFIDENCE:
                    skills_to_add.append(skill)

            if skills_to_add:
                confidence = min(1.0, len(evidence_records) / 10.0)
                proposals.append(
                    PlaybookProposal(
                        policy_name=_pattern_to_policy_name(pattern),
                        description=(
                            f"Auto-learned: {', '.join(skills_to_add)} required for {pattern}"
                        ),
                        file_pattern=pattern,
                        skills_to_add=skills_to_add,
                        confidence=round(confidence, 2),
                        evidence=(
                            f"Observed {len(evidence_records)} runs; "
                            f"skills {', '.join(skills_to_add)} passed ≥{self.MIN_CONFIDENCE:.0%} "
                            f"of the time on `{pattern}` files"
                        ),
                    )
                )

        return proposals

    def format_proposals(self, proposals: list[PlaybookProposal]) -> str:
        if not proposals:
            return "No playbook updates proposed yet — accumulate more evidence runs."
        lines = [
            f"## Playbook Learner — {len(proposals)} proposal(s)",
            "",
            "The following policies were observed in successful runs and are "
            "proposed for addition to skills.yml:",
        ]
        for p in proposals:
            lines.extend(["", p.to_text()])
        lines.append(
            "\nReview each proposal and add accepted policies to .contextpack/skills.yml"
        )
        return "\n".join(lines)


def _file_to_pattern(file_path: str) -> str:
    parts = Path(file_path).parts
    if len(parts) >= 2:
        return str(Path(*parts[:2]) / "**")
    return "**"


def _pattern_to_policy_name(pattern: str) -> str:
    return pattern.replace("/", "_").replace("**", "").strip("_").lower() + "_policy"
