"""Hybrid retrieval: semantic + graph + recency."""

from __future__ import annotations

from contextpack.core.models import SemanticChunk
from contextpack.core.protocols import EmbeddingProvider
from contextpack.embeddings.vector_store import VectorStore
from contextpack.graph.engine import ContextGraph


class HybridRetriever:
    def __init__(
        self,
        store: VectorStore,
        graph: ContextGraph,
        embedder: EmbeddingProvider,
    ) -> None:
        self._store = store
        self._graph = graph
        self._embedder = embedder

    async def retrieve(self, query: str, limit: int = 10) -> list[SemanticChunk]:
        vector = await self._embedder.embed(query)
        semantic = self._store.query(vector, n=limit * 2)

        scored: dict[str, tuple[SemanticChunk, float]] = {}
        for i, chunk in enumerate(semantic):
            key = f"{chunk.file_path}::{chunk.name}"
            semantic_score = 1.0 - (i / max(len(semantic), 1))
            graph_score = _graph_boost(self._graph, query, chunk)
            total = 0.65 * semantic_score + 0.35 * graph_score
            scored[key] = (chunk, total)

        ranked = sorted(scored.values(), key=lambda x: x[1], reverse=True)
        return [c for c, _ in ranked[:limit]]


def _graph_boost(graph: ContextGraph, query: str, chunk: SemanticChunk) -> float:
    node_hint = f"{chunk.file_path}::{chunk.name}"
    ranked = graph.rank_by_graph_distance(query, [node_hint, chunk.file_path, chunk.name])
    return ranked[0][1] if ranked else 0.0
