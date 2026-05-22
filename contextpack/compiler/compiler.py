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
    """Lightweight workflow inference from compiled chunks (no graph required).

    The full WorkflowExtractor runs during build and persists results to SQLite.
    This fallback produces a quick summary for the compiled pack only.
    """
    routes = [c for c in chunks if c.type in ("route", "api")]
    workflows: list[Workflow] = []
    if routes:
        workflows.append(
            Workflow(
                name="api_surface",
                steps=[r.name for r in routes[:10]],
                summary=f"API routes relevant to query ({len(routes)} endpoints)",
                entities=list({r.file_path for r in routes}),
            )
        )
    # Detect sequential patterns: chunks whose names suggest an ordered flow
    _FLOW_HINTS = ("parse", "validate", "process", "save", "send", "emit", "publish")
    flow_chunks = [
        c for c in chunks
        if any(h in c.name.lower() for h in _FLOW_HINTS)
    ]
    if len(flow_chunks) >= 2:
        workflows.append(
            Workflow(
                name="processing_flow",
                steps=[c.name for c in flow_chunks[:8]],
                summary="Detected processing/pipeline steps",
                entities=list({c.file_path for c in flow_chunks}),
            )
        )
    return workflows
