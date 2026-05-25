"""Intent preserver — extract behavioral invariants from tests and verify patches."""
from __future__ import annotations

import ast
import re
from pathlib import Path

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

_RETURNS_RE = re.compile(r"test_(\w+?)_(returns?|gives?|yields?)_(\w+)", re.IGNORECASE)
_RAISES_RE  = re.compile(r"test_(\w+?)_(raises?|throws?|fails?_on?)_(\w+)", re.IGNORECASE)
_SUCCESS_RE = re.compile(r"test_(\w+?)_success", re.IGNORECASE)
_FAIL_RE    = re.compile(r"test_(\w+?)_(fail|failure|error)(?:_|$)", re.IGNORECASE)


class BehaviorInvariant(BaseModel):
    test_name: str
    target_symbol: str
    description: str
    expected_behavior: str  # "returns X", "raises Y on Z"
    confidence: float = 0.8


class InvariantCheckResult(BaseModel):
    symbol: str
    invariants_checked: int
    passed: int
    failed: int
    violations: list[str] = Field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.failed == 0


class IntentPreserver:
    """Extract behavioral invariants from test names; heuristically verify patches."""

    def extract_invariants(self, test_files: list[Path]) -> list[BehaviorInvariant]:
        invariants: list[BehaviorInvariant] = []
        for tf in test_files:
            try:
                content = tf.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content, filename=str(tf))
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("test_"):
                        inv = self._infer(node.name)
                        if inv:
                            invariants.append(inv)
        return invariants

    def _infer(self, test_name: str) -> BehaviorInvariant | None:
        m = _RETURNS_RE.match(test_name)
        if m:
            return BehaviorInvariant(
                test_name=test_name,
                target_symbol=m.group(1),
                description=f"{m.group(1)} returns {m.group(3)}",
                expected_behavior=f"returns {m.group(3)} (not None, not empty)",
                confidence=0.85,
            )
        m = _RAISES_RE.match(test_name)
        if m:
            return BehaviorInvariant(
                test_name=test_name,
                target_symbol=m.group(1),
                description=f"{m.group(1)} raises error on {m.group(3)}",
                expected_behavior=f"raises exception when given {m.group(3)}",
                confidence=0.90,
            )
        m = _SUCCESS_RE.match(test_name)
        if m:
            return BehaviorInvariant(
                test_name=test_name,
                target_symbol=m.group(1),
                description=f"{m.group(1)} succeeds in happy path",
                expected_behavior="completes without raising",
                confidence=0.75,
            )
        m = _FAIL_RE.match(test_name)
        if m:
            return BehaviorInvariant(
                test_name=test_name,
                target_symbol=m.group(1),
                description=f"{m.group(1)} fails gracefully",
                expected_behavior="raises or returns error indicator",
                confidence=0.70,
            )
        return None

    def check_preserved(
        self,
        invariants: list[BehaviorInvariant],
        proposed_code: str,
        symbol_name: str,
    ) -> InvariantCheckResult:
        """Heuristic: verify proposed code still plausibly honors test-derived invariants."""
        relevant = [inv for inv in invariants if inv.target_symbol == symbol_name]
        if not relevant:
            return InvariantCheckResult(
                symbol=symbol_name, invariants_checked=0, passed=0, failed=0
            )

        passed = 0
        failed = 0
        violations: list[str] = []
        code_lower = proposed_code.lower()

        for inv in relevant:
            if "returns" in inv.expected_behavior:
                if "return " in code_lower:
                    passed += 1
                else:
                    failed += 1
                    violations.append(
                        f"'{inv.test_name}' expects a return value, "
                        "but no `return` statement found"
                    )
            elif "raises" in inv.expected_behavior:
                if "raise " in code_lower:
                    passed += 1
                else:
                    failed += 1
                    violations.append(
                        f"'{inv.test_name}' expects an exception to be raised, "
                        "but no `raise` statement found"
                    )
            else:
                passed += 1  # Cannot determine — optimistic pass

        return InvariantCheckResult(
            symbol=symbol_name,
            invariants_checked=len(relevant),
            passed=passed,
            failed=failed,
            violations=violations,
        )

    def format_report(self, results: list[InvariantCheckResult]) -> str:
        if not results:
            return ""
        lines = ["## Intent Preservation Report"]
        for r in results:
            icon = "✅" if r.ok else "❌"
            lines.append(
                f"\n{icon} **{r.symbol}**: "
                f"{r.passed}/{r.invariants_checked} invariants preserved"
            )
            for v in r.violations:
                lines.append(f"  · {v}")
        return "\n".join(lines)
