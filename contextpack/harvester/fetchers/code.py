"""Code context fetcher — graph, symbols, dependencies (meetup: Graphify)."""

from __future__ import annotations

from contextpack.core.models import ContextSourceType, HarvestedContext, ProjectMap
from contextpack.graph.engine import ContextGraph


class CodeContextFetcher:
    source_type = ContextSourceType.CODE

    def __init__(self, graph: ContextGraph | None = None) -> None:
        self._graph = graph

    async def fetch(self, query: str, project_map: ProjectMap) -> HarvestedContext:
        graph = self._graph or ContextGraph.from_project_map(project_map)
        excerpt = graph.describe_neighborhood(query, max_nodes=24)
        top_entities = [
            e for e in project_map.entities if query.lower() in (e.name + e.summary).lower()
        ][:12]
        if not top_entities:
            top_entities = project_map.entities[:15]

        lines = [
            f"Repository: {project_map.root}",
            f"Languages: {project_map.languages}",
            f"Frameworks: {project_map.frameworks}",
            "",
            "### Call graph & dependencies",
            excerpt,
            "",
            "### Relevant symbols",
        ]
        for ent in top_entities:
            deps = ", ".join(ent.dependencies[:6]) if ent.dependencies else "—"
            lines.append(f"- **{ent.name}** ({ent.type}) — {ent.summary or ent.file_path} [deps: {deps}]")

        return HarvestedContext(
            source=ContextSourceType.CODE,
            title="Code Context",
            content="\n".join(lines),
            structured={
                "entity_count": len(project_map.entities),
                "file_count": len(project_map.files),
                "frameworks": project_map.frameworks,
            },
        )
