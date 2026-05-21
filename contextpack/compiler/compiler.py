"""Context compiler — rank, compress, produce AI-ready packs."""

from __future__ import annotations

from contextpack.core.models import ContextPack, Relationship, SemanticChunk, Workflow
from contextpack.graph.engine import ContextGraph
from contextpack.retrieval.engine import HybridRetriever
from contextpack.utils.tokens import estimate_tokens


class ContextCompiler:
    def __init__(self, retriever: HybridRetriever, graph: ContextGraph) -> None:
        self._retriever = retriever
        self._graph = graph

    async def compile(self, query: str, token_budget: int = 8000) -> ContextPack:
        chunks = await self._retriever.retrieve(query, limit=24)
        ranked = _rank_chunks(query, chunks)

        summaries: list[str] = []
        files: set[str] = set()
        used_tokens = 0

        for chunk in ranked:
            line = f"[{chunk.type}] {chunk.name} ({chunk.file_path}): {chunk.summary or chunk.content[:200]}"
            cost = estimate_tokens(line)
            if used_tokens + cost > token_budget:
                break
            summaries.append(line)
            used_tokens += cost
            if chunk.file_path:
                files.add(chunk.file_path)

        relationships = self._graph.get_relationships()[:40]
        graph_excerpt = self._graph.describe_neighborhood(query, max_nodes=16)

        pack = ContextPack(
            query=query,
            summaries=summaries,
            relationships=relationships,
            files=sorted(files),
            workflows=_infer_workflows(ranked),
            chunks=ranked[:12],
            graph_excerpt=graph_excerpt,
            token_estimate=used_tokens,
        )
        return pack


def _rank_chunks(query: str, chunks: list[SemanticChunk]) -> list[SemanticChunk]:
    q = query.lower()

    def score(c: SemanticChunk) -> float:
        text = f"{c.name} {c.summary} {c.content}".lower()
        overlap = sum(1 for w in q.split() if len(w) > 2 and w in text)
        return overlap + (0.5 if c.type in ("class", "api", "route") else 0.0)

    return sorted(chunks, key=score, reverse=True)


def _infer_workflows(chunks: list[SemanticChunk]) -> list[Workflow]:
    routes = [c for c in chunks if c.type == "route" or c.type == "api"]
    if not routes:
        return []
    return [
        Workflow(
            name="detected_api_surface",
            steps=[r.name for r in routes[:10]],
            summary="API routes and handlers relevant to query",
            entities=[r.file_path for r in routes],
        )
    ]
