"""Skill composer — DAG-ordered skill execution engine."""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

# Skill dependency DAG: skill → list of skills it must wait for
SKILL_DAG: dict[str, list[str]] = {
    "lint": [],
    "type_check": ["lint"],
    "security_scan": ["type_check"],
    "docs_link_check": [],
    "contract_check": ["type_check"],
    "integration_tests": ["contract_check"],
    "full_test_suite": ["integration_tests"],
    "new_test_required": ["lint"],
    "auth_tests": ["type_check"],
    "spelling": [],
}


class SkillResult(BaseModel):
    skill: str
    passed: bool
    duration_ms: float
    output: str = ""
    findings: list[str] = Field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""


def _topo_sort(required: list[str]) -> list[str]:
    """Return skills in dependency-first topological order, auto-including deps."""
    visited: set[str] = set()
    order: list[str] = []

    def visit(skill: str) -> None:
        if skill in visited:
            return
        visited.add(skill)
        for dep in SKILL_DAG.get(skill, []):
            visit(dep)
        order.append(skill)

    for s in required:
        visit(s)
    return order


class SkillComposer:
    """Executes skills in DAG-dependency order, halting the tree on failure."""

    def execution_order(self, required_skills: list[str]) -> list[str]:
        return _topo_sort(required_skills)

    async def run(
        self,
        required_skills: list[str],
        repo_path: Path,
    ) -> list[SkillResult]:
        """Execute skills in dependency order. Skips dependents of failed skills."""
        order = self.execution_order(required_skills)
        results: list[SkillResult] = []
        failed: set[str] = set()

        for skill in order:
            deps = SKILL_DAG.get(skill, [])
            blocked_by = [d for d in deps if d in failed]
            if blocked_by:
                results.append(
                    SkillResult(
                        skill=skill,
                        passed=False,
                        duration_ms=0,
                        skipped=True,
                        skip_reason=f"Dependency failed: {', '.join(blocked_by)}",
                    )
                )
                failed.add(skill)
                continue

            result = await self._run_one(skill, repo_path)
            results.append(result)
            logger.info(
                "skill_result",
                skill=skill,
                passed=result.passed,
                duration_ms=round(result.duration_ms),
            )
            if not result.passed and not result.skipped:
                failed.add(skill)

        return results

    async def _run_one(self, skill: str, repo_path: Path) -> SkillResult:
        from contextpack.skills import builtin

        runner = builtin.get_runner(skill)
        if runner is None:
            # Unknown / user-defined skill — treat as pass (no runner registered)
            return SkillResult(
                skill=skill,
                passed=True,
                duration_ms=0,
                output=f"[custom skill '{skill}' — no runner registered, assuming pass]",
            )
        t0 = time.perf_counter()
        try:
            return await runner.run(repo_path)
        except Exception as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            logger.warning("skill_error", skill=skill, error=str(exc))
            return SkillResult(
                skill=skill,
                passed=False,
                duration_ms=elapsed,
                output=str(exc),
            )
