"""WorkflowExtractor — detect multi-step flows from entity graph and source code."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contextpack.core.models import ParsedEntity, Workflow
    from contextpack.graph.engine import ContextGraph


# Patterns that indicate a workflow entry point by entity name / file name
_ENTRY_PATTERNS = [
    "route", "endpoint", "handler", "controller", "command",
    "main", "run", "execute", "process", "handle", "dispatch",
]

# Framework prefixes that tag routes
_ROUTE_TYPES = {"route", "api"}

# Min chain length to be considered a meaningful workflow
_MIN_CHAIN = 2


class WorkflowExtractor:
    """Extract workflows from a ContextGraph + entity list."""

    def __init__(self, graph: ContextGraph, entities: list[ParsedEntity]) -> None:
        self._graph = graph
        self._entities = entities
        self._entity_map = {e.name: e for e in entities}

    def extract(self) -> list[Workflow]:

        workflows: list[Workflow] = []

        # 1. API / route surface
        api_wf = self._extract_api_workflows()
        workflows.extend(api_wf)

        # 2. Call chains originating from entry-point functions
        chain_wf = self._extract_call_chains()
        workflows.extend(chain_wf)

        # 3. Class hierarchy flows
        class_wf = self._extract_class_flows()
        workflows.extend(class_wf)

        # Deduplicate by name
        seen: set[str] = set()
        unique: list[Workflow] = []
        for wf in workflows:
            if wf.name not in seen:
                seen.add(wf.name)
                unique.append(wf)
        return unique

    def _extract_api_workflows(self) -> list[Workflow]:
        from contextpack.core.models import Workflow

        routes = [e for e in self._entities if str(e.type) in _ROUTE_TYPES]
        if not routes:
            routes = [
                e for e in self._entities
                if any(p in e.name.lower() for p in ("route", "endpoint", "handler"))
            ]
        if not routes:
            return []

        # Group routes by file (one workflow per service file)
        by_file: dict[str, list[ParsedEntity]] = {}
        for r in routes:
            by_file.setdefault(r.file_path, []).append(r)

        workflows: list[Workflow] = []
        for file_path, file_routes in by_file.items():
            svc_name = Path(file_path).stem
            steps = [r.name for r in file_routes[:12]]
            workflows.append(
                Workflow(
                    name=f"api_surface::{svc_name}",
                    steps=steps,
                    summary=f"API routes in {svc_name} ({len(steps)} endpoints)",
                    entities=[r.file_path for r in file_routes],
                )
            )
        return workflows

    def _extract_call_chains(self) -> list[Workflow]:
        """Walk dependency edges to find chains of length >= _MIN_CHAIN."""
        from contextpack.core.models import Workflow

        # Find entry points: functions / methods matching _ENTRY_PATTERNS
        entry_nodes = []
        for node, data in self._graph.graph.nodes(data=True):
            ntype = str(data.get("type", ""))
            if ntype in ("import", "dependency", "file"):
                continue
            name = str(data.get("name", "")).lower()
            if any(p in name for p in _ENTRY_PATTERNS):
                entry_nodes.append(node)

        workflows: list[Workflow] = []
        for entry in entry_nodes[:20]:
            chain = self._walk_chain(entry, max_depth=5)
            if len(chain) < _MIN_CHAIN:
                continue
            data = self._graph.graph.nodes.get(entry, {})
            label = str(data.get("name", entry))
            steps = [
                str(self._graph.graph.nodes.get(n, {}).get("name", n))
                for n in chain
            ]
            entities = list(
                {
                    str(self._graph.graph.nodes.get(n, {}).get("file", ""))
                    for n in chain
                }
            )
            workflows.append(
                Workflow(
                    name=f"call_chain::{label}",
                    steps=steps,
                    summary=f"Call chain from {label} ({len(chain)} steps)",
                    entities=entities,
                )
            )
        return workflows

    def _walk_chain(self, start: str, max_depth: int) -> list[str]:
        chain = [start]
        visited = {start}
        current = start
        for _ in range(max_depth):
            successors = [
                n
                for n in self._graph.graph.successors(current)
                if n not in visited
                and str(self._graph.graph.nodes.get(n, {}).get("type", ""))
                not in ("import", "dependency")
            ]
            if not successors:
                break
            # prefer the node with the highest in-degree (most connected)
            nxt = max(
                successors,
                key=lambda n: self._graph.graph.in_degree(n) + self._graph.graph.out_degree(n),
            )
            chain.append(nxt)
            visited.add(nxt)
            current = nxt
        return chain

    def _extract_class_flows(self) -> list[Workflow]:
        """Detect class → method hierarchies as lifecycle workflows."""
        from contextpack.core.models import Workflow

        classes = [e for e in self._entities if str(e.type) == "class"]
        workflows: list[Workflow] = []
        for cls in classes[:10]:
            node_id = f"{cls.file_path}::{cls.name}"
            # Find methods defined in the same file with this class's name in their path
            methods = [
                e for e in self._entities
                if str(e.type) == "method"
                and e.file_path == cls.file_path
            ]
            if len(methods) < 2:
                continue
            steps = [m.name for m in methods[:10]]
            workflows.append(
                Workflow(
                    name=f"class_lifecycle::{cls.name}",
                    steps=steps,
                    summary=f"{cls.name} class with {len(steps)} methods",
                    entities=[cls.file_path],
                )
            )
        return workflows


async def extract_and_store(
    graph: ContextGraph,
    entities: list[ParsedEntity],
    db_path: Path,
) -> list[Workflow]:
    """Extract workflows and persist them to the SQLite store."""
    from contextpack.storage.sqlite import SQLiteStore

    extractor = WorkflowExtractor(graph, entities)
    workflows = extractor.extract()

    store = SQLiteStore(db_path)
    await store.initialize()
    for wf in workflows:
        await store.upsert_workflow(wf.name, wf.model_dump())

    return workflows
