"""Graph-native dependency and service relationships."""

from __future__ import annotations

import networkx as nx

from contextpack.core.models import ParsedEntity, ProjectMap, Relationship


class ContextGraph:
    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()

    def add_entity(self, entity_id: str, **attrs) -> None:
        self.graph.add_node(entity_id, **attrs)

    def add_relationship(
        self,
        source: str,
        target: str,
        relation: str = "depends_on",
        **attrs
    ) -> None:
        self.graph.add_edge(source, target, relation=relation, **attrs)

    @classmethod
    def from_entities(cls, entities: list[ParsedEntity]) -> ContextGraph:
        g = cls()
        for ent in entities:
            node_id = f"{ent.file_path}::{ent.name}"
            g.add_entity(
                node_id,
                name=ent.name,
                type=str(ent.type),
                file=ent.file_path,
                summary=ent.summary,
            )
            for imp in ent.imports:
                imp_id = f"import::{imp[:80]}"
                g.add_entity(imp_id, name=imp[:80], type="import")
                g.add_relationship(node_id, imp_id, "imports")
            for dep in ent.dependencies:
                dep_id = f"dep::{dep}"
                g.add_entity(dep_id, name=dep, type="dependency")
                g.add_relationship(node_id, dep_id, "depends_on")
            # file module link
            mod_id = f"file::{ent.file_path}"
            g.add_entity(mod_id, name=ent.file_path, type="file")
            g.add_relationship(mod_id, node_id, "defines")
        return g

    @classmethod
    def from_project_map(cls, project_map: ProjectMap) -> ContextGraph:
        return cls.from_entities(project_map.entities)

    def get_relationships(self) -> list[Relationship]:
        rels: list[Relationship] = []
        for u, v, data in self.graph.edges(data=True):
            rels.append(
                Relationship(
                    source=u,
                    target=v,
                    relation=data.get("relation", "related"),
                )
            )
        return rels

    def neighbors(self, node_id: str, depth: int = 2) -> set[str]:
        found: set[str] = {node_id}
        frontier = {node_id}
        for _ in range(depth):
            nxt: set[str] = set()
            for n in frontier:
                nxt.update(self.graph.successors(n))
                nxt.update(self.graph.predecessors(n))
            found.update(nxt)
            frontier = nxt - found
        return found

    def describe_neighborhood(self, query: str, max_nodes: int = 20) -> str:
        q = query.lower()
        seeds = [
            n
            for n, d in self.graph.nodes(data=True)
            if q in str(d.get("name", "")).lower() or q in n.lower()
        ]
        if not seeds:
            seeds = list(self.graph.nodes())[:5]

        lines: list[str] = []
        seen: set[str] = set()
        for seed in seeds[:3]:
            hood = self.neighbors(seed, depth=1)
            for node in list(hood)[:max_nodes]:
                if node in seen:
                    continue
                seen.add(node)
                data = self.graph.nodes.get(node, {})
                lines.append(
                    f"- {data.get('name', node)} ({data.get('type', '?')})"
                )
                for _, tgt, edata in self.graph.out_edges(node, data=True):
                    tgt_name = self.graph.nodes.get(tgt, {}).get('name', tgt)
                    relation = edata.get('relation')
                    lines.append(f"    → {tgt_name} [{relation}]")
        return "\n".join(lines) if lines else "_No graph nodes matched query._"

    def hub_entities(self, limit: int = 15) -> list[tuple[str, str, int]]:
        """Top entity nodes by total degree (name, file_path, degree)."""
        scored: list[tuple[str, str, int]] = []
        for node, data in self.graph.nodes(data=True):
            ntype = str(data.get("type", ""))
            if ntype in ("import", "dependency", "file"):
                continue
            name = str(data.get("name", ""))
            if not name or name.startswith("import::") or name.startswith("dep::"):
                continue
            deg = self.graph.in_degree(node) + self.graph.out_degree(node)
            if deg < 1:
                continue
            scored.append((name, str(data.get("file", "")), deg))
        scored.sort(key=lambda x: x[2], reverse=True)
        seen: set[str] = set()
        out: list[tuple[str, str, int]] = []
        for name, fpath, deg in scored:
            if name in seen:
                continue
            seen.add(name)
            out.append((name, fpath, deg))
            if len(out) >= limit:
                break
        return out

    def find_symbol(self, symbol: str, limit: int = 10) -> list[dict[str, str]]:
        """Match entities by name (case-insensitive substring)."""
        q = symbol.lower()
        hits: list[dict[str, str]] = []
        for node, data in self.graph.nodes(data=True):
            name = str(data.get("name", ""))
            if q not in name.lower() and q not in node.lower():
                continue
            ntype = str(data.get("type", ""))
            if ntype in ("import", "dependency"):
                continue
            hits.append(
                {
                    "node_id": node,
                    "name": name,
                    "type": ntype,
                    "file": str(data.get("file", "")),
                }
            )
            if len(hits) >= limit:
                break
        return hits

    def rank_by_graph_distance(self, query: str, candidates: list[str]) -> list[tuple[str, float]]:
        q = query.lower()
        seeds = [n for n in self.graph.nodes if q in n.lower()]
        if not seeds:
            return [(c, 0.0) for c in candidates]

        scores: dict[str, float] = {}
        seed = seeds[0]
        lengths = nx.single_source_shortest_path_length(
            self.graph.to_undirected(), seed, cutoff=4
        )
        for cand in candidates:
            best = min(
                (
                    1.0 / (1 + lengths.get(c, 99))
                    for c in self.graph.nodes
                    if cand in c
                ),
                default=0.0,
            )
            scores[cand] = best
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
