"""Skill manifest — declarative policy definitions from skills.yml."""
from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


class MatchCriteria(BaseModel):
    """Conditions that trigger this policy."""

    paths: list[str] = Field(default_factory=list, description="Glob patterns for file paths")
    extensions_only: list[str] = Field(default_factory=list, description="Only trigger on these extensions")
    graph_roles: list[str] = Field(default_factory=list, description="hub, entrypoint, etc.")
    graph_hub_threshold: float = Field(default=0.7, description="Centrality threshold for hub detection")
    blast_radius_min: int = Field(default=0, description="Min blast radius to trigger this policy")


class RequireSpec(BaseModel):
    """What this policy mandates."""

    skills: list[str] = Field(default_factory=list)
    max_blast_radius: int | None = None
    human_review: bool = False


class SkillPolicy(BaseModel):
    name: str
    description: str = ""
    match: MatchCriteria = Field(default_factory=MatchCriteria)
    require: RequireSpec = Field(default_factory=RequireSpec)


class SkillManifest(BaseModel):
    version: int = 1
    policies: list[SkillPolicy] = Field(default_factory=list)

    @classmethod
    def load(cls, repo_path: Path) -> "SkillManifest":
        """Load skills.yml from repo. Returns default manifest if not found."""
        candidates = [
            repo_path / "skills.yml",
            repo_path / ".contextpack" / "skills.yml",
            repo_path / ".contextpack" / "skills.yaml",
        ]
        for candidate in candidates:
            if candidate.exists():
                if yaml is None:
                    break
                data = yaml.safe_load(candidate.read_text())
                if data:
                    return cls.model_validate(data)
        return cls.default()

    def policies_matching(
        self,
        file_path: str,
        blast_radius: int = 0,
        hub_centrality: float = 0.0,
    ) -> list[SkillPolicy]:
        """Return all policies that match the given file path + metrics."""
        matched: list[SkillPolicy] = []
        for policy in self.policies:
            m = policy.match
            # path check — empty paths means match all
            if m.paths:
                if not any(fnmatch.fnmatch(file_path, pat) for pat in m.paths):
                    continue
            # extension check
            if m.extensions_only:
                ext = Path(file_path).suffix
                if ext not in m.extensions_only:
                    continue
            # blast radius check
            if blast_radius < m.blast_radius_min:
                continue
            # hub role check
            if "hub" in m.graph_roles and hub_centrality < m.graph_hub_threshold:
                continue
            matched.append(policy)
        return matched

    @classmethod
    def default(cls) -> "SkillManifest":
        """Sensible defaults for repos without a skills.yml."""
        return cls(
            policies=[
                SkillPolicy(
                    name="default",
                    description="Default: lint everything",
                    match=MatchCriteria(),
                    require=RequireSpec(skills=["lint"]),
                ),
                SkillPolicy(
                    name="hub_node_changes",
                    description="Hub nodes always get type-checked",
                    match=MatchCriteria(graph_roles=["hub"], graph_hub_threshold=0.7),
                    require=RequireSpec(skills=["lint", "type_check"], max_blast_radius=50),
                ),
            ]
        )

    def to_yaml(self) -> str:
        """Export manifest as YAML string."""
        if yaml is None:
            return str(self.model_dump())
        return yaml.dump(self.model_dump(), default_flow_style=False)
