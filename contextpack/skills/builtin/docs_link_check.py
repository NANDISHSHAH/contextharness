"""Built-in docs link check — validate local markdown links exist."""
from __future__ import annotations

import re
import time
from pathlib import Path

from contextpack.skills.composer import SkillResult

_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)#\s]+)(?:#[^)]*)?\)")
_SKIP_DIRS = {"node_modules", ".git", ".contextpack", "dist", "build", "__pycache__"}


class DocsLinkCheckSkill:
    name = "docs_link_check"
    dependencies: list[str] = []

    async def run(self, repo_path: Path) -> SkillResult:
        t0 = time.perf_counter()
        broken: list[str] = []

        md_files = [
            f
            for f in repo_path.rglob("*.md")
            if not any(part in _SKIP_DIRS for part in f.parts)
        ]

        for md_file in md_files[:100]:
            try:
                content = md_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for _, link in _LINK_RE.findall(content):
                if link.startswith(("http://", "https://", "mailto:")):
                    continue  # skip external links
                target = (md_file.parent / link).resolve()
                if not target.exists():
                    rel = md_file.relative_to(repo_path)
                    broken.append(f"{rel}: broken link → {link}")

        elapsed = (time.perf_counter() - t0) * 1000
        passed = len(broken) == 0
        output = (
            "\n".join(broken[:20])
            if broken
            else f"All markdown links OK ({len(md_files)} files checked)"
        )
        return SkillResult(
            skill=self.name,
            passed=passed,
            duration_ms=elapsed,
            output=output,
            findings=broken[:10],
        )
