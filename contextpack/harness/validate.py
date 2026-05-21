"""Validate AGENTS.md / CLAUDE.md claims against the dependency graph."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from contextpack.core.config import get_settings
from contextpack.core.models import EntityType, ProjectMap
from contextpack.graph.engine import ContextGraph

DOC_PATHS = ("AGENTS.md", "CLAUDE.md", ".contextpack/guidelines.md")
BACKTICK_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_.]*)`")
CAMEL_RE = re.compile(r"\b([A-Z][a-z]+(?:[A-Z][a-z0-9]+)+)\b")

STOPWORDS = frozenset(
    {
        "AGENTS",
        "API",
        "CLI",
        "Context",
        "Harness",
        "Markdown",
        "Python",
        "Run",
        "The",
        "Use",
        "When",
        "Your",
    }
)

CODE_ENTITY_TYPES = frozenset(
    {
        EntityType.CLASS,
        EntityType.FUNCTION,
        EntityType.METHOD,
        EntityType.MODULE,
        EntityType.API,
        EntityType.ROUTE,
        EntityType.SERVICE,
        "class",
        "function",
        "method",
        "module",
        "api",
        "route",
        "service",
    }
)


@dataclass
class HarnessValidation:
    ok: bool
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = ["## Context Harness validation"]
        if self.ok and not self.warnings:
            lines.append("No doc/graph drift detected.")
        for w in self.warnings:
            lines.append(f"- **Warning:** {w}")
        for s in self.suggestions:
            lines.append(f"- **Suggestion:** {s}")
        return "\n".join(lines)


def _load_docs(root: Path) -> str:
    chunks: list[str] = []
    for rel in DOC_PATHS:
        p = root / rel
        if p.is_file():
            chunks.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def _doc_symbols(text: str) -> set[str]:
    """PascalCase symbols explicitly marked in docs (likely types/modules)."""
    found: set[str] = set()
    for m in BACKTICK_RE.finditer(text):
        sym = m.group(1).split(".")[-1]
        if re.fullmatch(r"[A-Z][a-zA-Z0-9]+", sym) and sym not in STOPWORDS:
            found.add(sym)
    for m in CAMEL_RE.finditer(text):
        sym = m.group(1)
        if sym not in STOPWORDS and re.fullmatch(r"[A-Z][a-zA-Z0-9]+", sym):
            found.add(sym)
    return found


def _code_entity_names(project_map: ProjectMap) -> set[str]:
    names: set[str] = set()
    for ent in project_map.entities:
        if ent.type in CODE_ENTITY_TYPES:
            names.add(ent.name)
    return names


def _public_hub_names(project_map: ProjectMap, graph: ContextGraph, limit: int = 8) -> set[str]:
    type_by_name = {e.name: e.type for e in project_map.entities}
    hubs = graph.hub_entities(40)
    out: set[str] = set()
    for name, _fpath, _deg in hubs:
        if name.startswith("_") or name in {"Project", "main", "app"}:
            continue
        et = type_by_name.get(name)
        if et not in (EntityType.CLASS, EntityType.MODULE, EntityType.SERVICE, "class", "module", "service"):
            continue
        out.add(name)
        if len(out) >= limit:
            break
    return out


def validate_harness_docs(repo: Path) -> HarnessValidation:
    root = repo.resolve()
    ctx = get_settings().context_dir(root)
    map_path = ctx / "project_map.json"
    result = HarnessValidation(ok=True)

    if not map_path.is_file():
        result.ok = False
        result.warnings.append("No built index — run `context build` before validating harness docs.")
        return result

    project_map = ProjectMap.model_validate_json(map_path.read_text(encoding="utf-8"))
    graph = ContextGraph.from_project_map(project_map)
    code_names = _code_entity_names(project_map)
    hub_names = _public_hub_names(project_map, graph)

    docs = _load_docs(root)
    if not docs.strip():
        result.warnings.append(
            "No AGENTS.md / CLAUDE.md found. Add AGENTS.md describing critical modules."
        )
        result.suggestions.append(
            f"Document graph hubs: {', '.join(sorted(hub_names)[:8])}"
        )
        result.ok = False
        return result

    mentioned = _doc_symbols(docs)
    unknown = sorted(s for s in mentioned if s not in code_names)[:8]
    if unknown:
        result.warnings.append(
            f"Docs reference symbols not in code index: {', '.join(unknown)}"
        )

    undocumented_hubs = sorted(hub_names - mentioned)[:6]
    if undocumented_hubs:
        result.suggestions.append(
            f"Consider documenting high-connectivity modules: {', '.join(undocumented_hubs)}"
        )

    if result.warnings:
        result.ok = False
    return result
