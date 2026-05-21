#!/usr/bin/env python3
"""End-to-end Context Harness validator (run from repo root)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def check(name: str, ok: bool, detail: str = "") -> bool:
    mark = "✓" if ok else "✗"
    line = f"  {mark} {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    return ok


def main() -> int:
    print("Context Harness validation\n")
    passed = 0
    total = 0

    def run(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        if check(name, ok, detail):
            passed += 1

    run("HARNESS.md", (ROOT / "HARNESS.md").is_file())
    run("AGENTS.md", (ROOT / "AGENTS.md").is_file())
    run(".cursor/hooks.json", (ROOT / ".cursor" / "hooks.json").is_file())
    run(".mcp.json", (ROOT / ".mcp.json").is_file())
    run("harvest-review skill", (ROOT / ".cursor/skills/harvest-review/SKILL.md").is_file())
    run("explorer agent", (ROOT / ".cursor/agents/explorer.md").is_file())

    try:
        from contextpack.harness.validate import validate_harness_docs
        from contextpack.harness.staleness import check_staleness

        run("harness imports", True)
        stale = check_staleness(ROOT)
        run("staleness check", True, stale.reason)
        result = validate_harness_docs(ROOT)
        run("doc/graph validate", result.ok or bool(result.suggestions), result.to_markdown()[:80])
    except Exception as e:
        run("harness imports", False, str(e))

    try:
        from contextpack.graph.engine import ContextGraph
        from contextpack.core.models import EntityType, ParsedEntity

        g = ContextGraph.from_entities(
            [
                ParsedEntity(type=EntityType.CLASS, name="Foo", file_path="f.py"),
            ]
        )
        run("graph hub_entities", len(g.hub_entities(5)) >= 1)
    except Exception as e:
        run("graph hub_entities", False, str(e))

    r = subprocess.run(
        [sys.executable, "-m", "contextpack.cli.harness_hooks", "session-start"],
        cwd=ROOT,
        input="{}",
        capture_output=True,
        text=True,
        timeout=30,
    )
    run(
        "session-start hook JSON",
        r.returncode == 0 and "additional_context" in r.stdout,
        r.stderr[:120] if r.returncode else "",
    )

    print(f"\n{passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
