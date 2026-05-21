"""Product behaviour from tests (meetup: test descriptions as behavioural spec)."""

from __future__ import annotations

import re
from pathlib import Path

from contextpack.core.models import ContextSourceType, HarvestedContext, ProjectMap

TEST_PATTERNS = ("test_", "_test.py", ".spec.", ".test.")


class TestBehaviourFetcher:
    source_type = ContextSourceType.PRODUCT_BEHAVIOUR

    async def fetch(self, query: str, project_map: ProjectMap) -> HarvestedContext:
        root = Path(project_map.root)
        behaviours: list[str] = []

        for record in project_map.files:
            path = record.path
            if not any(p in path for p in TEST_PATTERNS):
                continue
            full = root / path
            if not full.is_file() or full.stat().st_size > 80_000:
                continue
            try:
                text = full.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            behaviours.extend(_extract_test_names(text, path))
            if len(behaviours) >= 80:
                break

        if not behaviours:
            return HarvestedContext(
                source=ContextSourceType.PRODUCT_BEHAVIOUR,
                title="Product Behaviour (Tests)",
                content="",
                available=False,
                skip_reason="No test files detected.",
            )

        content = "Expected product behaviour from test suite:\n\n" + "\n".join(
            f"- {b}" for b in behaviours[:60]
        )
        return HarvestedContext(
            source=ContextSourceType.PRODUCT_BEHAVIOUR,
            title="Product Behaviour (Tests)",
            content=content,
            structured={"test_count": len(behaviours)},
        )


def _extract_test_names(text: str, path: str) -> list[str]:
    names: list[str] = []
    for m in re.finditer(r"def\s+(test_\w+)", text):
        names.append(f"{path}::{m.group(1)}")
    for m in re.finditer(r"(?:it|test|describe)\s*\(\s*['\"]([^'\"]+)['\"]", text):
        names.append(f"{path}: {m.group(1)}")
    return names
