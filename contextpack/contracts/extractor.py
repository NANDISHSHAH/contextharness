"""Contract extractor — preconditions, postconditions, invariants from Python source."""
from __future__ import annotations

import ast
import re
import time
from pathlib import Path

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class Contract(BaseModel):
    symbol_id: str              # e.g. "src/auth/tokens.py:validate_token"
    file_path: str
    symbol_name: str
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)
    test_coverage: list[str] = Field(default_factory=list)
    trust_score: float = 0.8
    last_verified: float = Field(default_factory=time.time)

    @property
    def has_contracts(self) -> bool:
        return bool(self.preconditions or self.postconditions or self.invariants)

    def to_context_block(self) -> str:
        lines = [f"**{self.symbol_name}** `{self.file_path}` (trust: {self.trust_score:.2f})"]
        if self.preconditions:
            lines.append("  Preconditions: " + " | ".join(self.preconditions[:4]))
        if self.postconditions:
            lines.append("  Returns/Ensures: " + " | ".join(self.postconditions[:4]))
        if self.invariants:
            lines.append("  Raises/Invariants: " + " | ".join(self.invariants[:4]))
        if self.test_coverage:
            lines.append(f"  Tests: {', '.join(self.test_coverage[:5])}")
        return "\n".join(lines)


_TEST_RE = re.compile(r"def (test_\w+)\(", re.MULTILINE)


class ContractExtractor:
    """Extract contracts from Python source files using AST analysis."""

    def extract_from_file(self, file_path: Path, content: str) -> list[Contract]:
        contracts: list[Contract] = []
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            return contracts

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                c = self._extract_fn(node, file_path)
                if c:
                    contracts.append(c)
            elif isinstance(node, ast.ClassDef):
                c = self._extract_cls(node, file_path)
                if c:
                    contracts.append(c)
        return contracts

    def _extract_fn(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: Path,
    ) -> Contract | None:
        pre: list[str] = []
        post: list[str] = []
        inv: list[str] = []
        doc = ast.get_docstring(node) or ""

        if doc:
            pre += _section(doc, ["Args:", "Parameters:", "Requires:", "requires:"])
            post += _section(doc, ["Returns:", "Yields:", "Ensures:", "ensures:"])
            inv += _section(doc, ["Raises:", "Invariant:", "Note:"])

        # Type hints → contracts
        if node.returns:
            try:
                post.append(f"returns {ast.unparse(node.returns)}")
            except Exception:
                pass
        for arg in node.args.args:
            if arg.annotation:
                try:
                    pre.append(f"{arg.arg}: {ast.unparse(arg.annotation)}")
                except Exception:
                    pass

        # Assert / raise in body
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                try:
                    pre.append(f"assert {ast.unparse(child.test)}")
                except Exception:
                    pass
            elif isinstance(child, ast.Raise) and child.exc:
                try:
                    inv.append(f"raises {ast.unparse(child.exc).split('(')[0]}")
                except Exception:
                    pass

        if not (pre or post or inv):
            return None

        return Contract(
            symbol_id=f"{file_path}:{node.name}",
            file_path=str(file_path),
            symbol_name=node.name,
            preconditions=_dedup(pre)[:8],
            postconditions=_dedup(post)[:8],
            invariants=_dedup(inv)[:8],
            trust_score=0.92 if doc else 0.72,
        )

    def _extract_cls(self, node: ast.ClassDef, file_path: Path) -> Contract | None:
        doc = ast.get_docstring(node) or ""
        post: list[str] = []
        inv: list[str] = []

        if doc:
            post += _section(doc, ["Attributes:", "Properties:"])
            inv += _section(doc, ["Invariant:", "Note:"])

        if not (post or inv):
            return None

        return Contract(
            symbol_id=f"{file_path}:{node.name}",
            file_path=str(file_path),
            symbol_name=node.name,
            postconditions=_dedup(post)[:6],
            invariants=_dedup(inv)[:6],
            trust_score=0.75,
        )

    def extract_test_coverage(self, test_files: list[Path]) -> dict[str, list[str]]:
        """Map target symbol name → list of test function names that cover it."""
        coverage: dict[str, list[str]] = {}
        for tf in test_files:
            try:
                content = tf.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in _TEST_RE.finditer(content):
                test_name = m.group(1)
                # test_validate_token_success → "validate_token"
                body = test_name[5:]  # strip "test_"
                parts = body.split("_")
                for length in range(len(parts), 0, -1):
                    candidate = "_".join(parts[:length])
                    if len(candidate) > 3:
                        coverage.setdefault(candidate, []).append(test_name)
                        break
        return coverage


# ── helpers ───────────────────────────────────────────────────────────────────

def _section(doc: str, markers: list[str]) -> list[str]:
    """Extract bullet-point lines after any of the given section markers."""
    results: list[str] = []
    lines = doc.splitlines()
    active = False
    for line in lines:
        stripped = line.strip()
        if any(stripped.startswith(m) for m in markers):
            active = True
            continue
        if active:
            if stripped and not stripped[0].isspace() and stripped.endswith(":"):
                active = False
            elif stripped:
                results.append(stripped.lstrip("- "))
    return results


def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
