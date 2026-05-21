"""Product guidelines fetcher (meetup: Product Skill / team rules)."""

from __future__ import annotations

from pathlib import Path

from contextpack.core.config import get_settings
from contextpack.core.models import ContextSourceType, HarvestedContext, ProjectMap

GUIDELINE_PATHS = [
    ".pr-review/guidelines.md",
    ".contextpack/guidelines.md",
    "docs/CONTRIBUTING.md",
    "AGENTS.md",
    "CLAUDE.md",
]


class ProductGuidelinesFetcher:
    source_type = ContextSourceType.PRODUCT_GUIDELINES

    async def fetch(self, query: str, project_map: ProjectMap) -> HarvestedContext:
        root = Path(project_map.root)
        settings = get_settings()
        max_chars = settings.guidelines_max_chars

        for rel in GUIDELINE_PATHS:
            path = root / rel
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")[:max_chars]
            return HarvestedContext(
                source=ContextSourceType.PRODUCT_GUIDELINES,
                title="Product Context (Team Guidelines)",
                content=text,
                structured={"path": str(path), "chars": len(text)},
            )

        return HarvestedContext(
            source=ContextSourceType.PRODUCT_GUIDELINES,
            title="Product Context (Team Guidelines)",
            content="",
            available=False,
            skip_reason="No guideline files found; checks using team rules are skipped.",
        )
