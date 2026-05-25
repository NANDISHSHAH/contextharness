"""Budget risk signal — token budget as a safety gate, not just truncation."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class BudgetRiskLevel(str, Enum):
    SAFE     = "safe"
    WARNING  = "warning"
    CRITICAL = "critical"


class BudgetRiskSignal(BaseModel):
    """Result of checking whether the context budget is sufficient for a task."""

    budget: int
    minimum_safe_tokens: int
    actual_tokens: int
    risk_score: float
    risk_level: BudgetRiskLevel
    message: str
    options: list[str] = Field(default_factory=list)
    forced_truncation: bool = False

    @property
    def is_safe(self) -> bool:
        return self.risk_level == BudgetRiskLevel.SAFE


class BudgetRiskAnalyser:
    """Analyse token budget adequacy for a given task risk profile."""

    def analyse(
        self,
        budget: int,
        actual_tokens: int,
        risk_score: float,
        task_description: str = "",
    ) -> BudgetRiskSignal:
        """
        Determine if the token budget is adequate.

        High risk + insufficient budget → CRITICAL (agent should not auto-proceed).
        Medium risk + small overage → WARNING.
        Low risk → SAFE even with minor truncation.
        """
        coverage_ratio = actual_tokens / max(budget, 1)
        # How much of the minimum safe context is covered
        # For high-risk tasks, minimum_safe = actual (can't reduce safely)
        # For low-risk, minimum_safe = ~60% of actual
        if risk_score > 0.7:
            min_safe = actual_tokens  # cannot truncate safely
        elif risk_score > 0.4:
            min_safe = int(actual_tokens * 0.8)
        else:
            min_safe = int(actual_tokens * 0.6)

        if budget >= actual_tokens:
            level = BudgetRiskLevel.SAFE
            msg = f"Budget adequate: {actual_tokens:,} tokens fit within {budget:,} budget"
            options: list[str] = []
            forced = False
        elif budget >= min_safe:
            level = BudgetRiskLevel.WARNING
            msg = (
                f"Budget tight: {actual_tokens:,} tokens → truncating to {budget:,}. "
                f"Risk score: {risk_score:.2f} — proceeding with reduced context."
            )
            options = [
                f"Increase budget to {actual_tokens:,} (recommended)",
                "Narrow task scope to reduce required context",
                f"Proceed with {budget:,}-token context (current)",
            ]
            forced = True
        else:
            level = BudgetRiskLevel.CRITICAL
            msg = (
                f"RISK: Minimum safe context ({min_safe:,} tokens) exceeds budget "
                f"({budget:,} tokens). Risk score: {risk_score:.2f}."
            )
            options = [
                f"Increase budget to {min_safe:,} tokens (recommended)",
                "Decompose task to reduce required context",
                "Request human review before proceeding",
                f"Proceed with {budget:,}-token context (not recommended — high risk)",
            ]
            forced = True

        return BudgetRiskSignal(
            budget=budget,
            minimum_safe_tokens=min_safe,
            actual_tokens=actual_tokens,
            risk_score=risk_score,
            risk_level=level,
            message=msg,
            options=options,
            forced_truncation=forced,
        )

    def format_signal(self, signal: BudgetRiskSignal) -> str:
        if signal.is_safe:
            return f"✅ {signal.message}"
        icon = "⚠️" if signal.risk_level == BudgetRiskLevel.WARNING else "🚨"
        lines = [f"{icon} BUDGET RISK SIGNAL", "", signal.message]
        if signal.options:
            lines.extend(["", "Options:"])
            for i, opt in enumerate(signal.options, 1):
                lines.append(f"  {i}. {opt}")
        return "\n".join(lines)
