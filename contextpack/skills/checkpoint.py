"""Reasoning checkpoint — validate agent understanding before hub-node edits."""
from __future__ import annotations

from pathlib import Path

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class CheckpointResult(BaseModel):
    passed: bool
    symbol: str
    question: str
    agent_answer: str | None = None
    graph_validated: bool = False
    correction: str | None = None


class ReasoningCheckpoint:
    """Generates and heuristically validates reasoning checkpoints for hub nodes."""

    def generate(self, symbol: str, graph_summary: dict) -> str:
        """Return a checkpoint prompt text for the agent."""
        centrality = graph_summary.get("centrality", 0.0)
        importers: list[str] = graph_summary.get("importers", [])
        role = graph_summary.get("role", "")
        critical_paths: list[str] = graph_summary.get("critical_paths", [])

        lines = [
            f"── CHECKPOINT: before editing {symbol} ──",
            "",
            "Based on the dependency graph, this module:",
            f"  • Is a hub node  (centrality: {centrality:.2f})",
            f"  • Has {len(importers)} direct importers",
        ]
        if role:
            lines.append(f"  • Role: {role}")
        if critical_paths:
            lines.append(
                f"  • Critical path of: {', '.join(critical_paths[:4])}"
            )
        lines.extend([
            "",
            "Before proceeding, confirm your understanding:",
            f"  Q1: What is the primary responsibility of {Path(symbol).stem}?",
            f"  Q2: Which downstream modules will be affected by a signature change here?",
            "",
            "Your answer is validated against the graph. "
            "Mismatches trigger a re-briefing, not a block.",
        ])
        return "\n".join(lines)

    def validate_answer(
        self,
        symbol: str,
        answer: str,
        graph_summary: dict,
    ) -> CheckpointResult:
        """
        Heuristic validation: check if the answer mentions expected concepts.
        Passes if ≥ half the role_keywords appear in the answer.
        """
        role_keywords: list[str] = graph_summary.get("role_keywords", [])
        importers: list[str] = graph_summary.get("importers", [])
        answer_lower = answer.lower()

        if not role_keywords:
            # No keywords to check — assume pass
            return CheckpointResult(
                passed=True,
                symbol=symbol,
                question=f"What is the primary responsibility of {Path(symbol).stem}?",
                agent_answer=answer,
                graph_validated=False,
            )

        mentioned = [kw for kw in role_keywords if kw.lower() in answer_lower]
        threshold = max(1, len(role_keywords) // 2)
        passed = len(mentioned) >= threshold

        correction: str | None = None
        if not passed:
            missing = [kw for kw in role_keywords if kw.lower() not in answer_lower]
            correction = (
                f"Your answer may be missing context about: {', '.join(missing[:3])}. "
                + (
                    f"Key importers include: {', '.join(importers[:5])}."
                    if importers
                    else ""
                )
            )

        return CheckpointResult(
            passed=passed,
            symbol=symbol,
            question=f"What is the primary responsibility of {Path(symbol).stem}?",
            agent_answer=answer,
            graph_validated=True,
            correction=correction,
        )
