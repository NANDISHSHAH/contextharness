"""Session orientation text from project map + graph hubs."""

from __future__ import annotations

from pathlib import Path

from contextpack.core.project import Project
from contextpack.harness.staleness import check_staleness


def build_orientation(repo: Path, *, query: str = "architecture") -> str:
    """Compact briefing for sessionStart / AGENTS injection."""
    root = repo.resolve()
    stale = check_staleness(root)
    lines: list[str] = [
        "## Context Harness — session orientation",
        "",
    ]

    if stale.is_stale:
        lines.extend(
            [
                f"**Index status:** {stale.reason}",
                "",
                "Before deep refactors, run:",
                "```bash",
                "context build .",
                "```",
                "",
            ]
        )
    else:
        lines.append("**Index status:** ready (.contextpack/)")
        lines.append("")

    project = Project(root)
    if not project.is_built():
        lines.extend(
            [
                "_No graph yet. Use MCP `project_outline` after build, or ask the user to run `context build`._",
                "",
                "**Workflow:** For task-specific work, run `context harvest \"<task>\" .` or MCP `harvest_context`.",
            ]
        )
        return "\n".join(lines)

    pmap = project.project_map()
    lines.append(f"**Repository:** {pmap.root}")
    if pmap.languages:
        lang_summary = ", ".join(f"{k} ({v})" for k, v in sorted(pmap.languages.items()))
        lines.append(f"**Languages:** {lang_summary}")
    lines.append(f"**Entities indexed:** {len(pmap.entities)}")
    lines.append("")

    hubs = project.hub_entities(12)
    if hubs:
        lines.append("**Graph hubs (high connectivity):**")
        for name, fpath, degree in hubs[:10]:
            lines.append(f"- `{name}` ({fpath}) — degree {degree}")
        lines.append("")

    excerpt = project.graph_summary(query)
    if excerpt and excerpt != "_No graph nodes matched query._":
        lines.append(f"**Neighborhood for `{query}`:**")
        lines.append(excerpt[:2000])
        lines.append("")

    lines.extend(
        [
            "**Harness workflow:**",
            "1. MCP `harvest_context` or `context harvest \"<task>\"` for token-budgeted packs",
            "2. Skills under `.cursor/skills/` for path-scoped conventions",
            "3. `context harness validate` after sessions to catch doc/graph drift",
            "",
        ]
    )
    return "\n".join(lines)
