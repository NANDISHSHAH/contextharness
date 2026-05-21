"""Vector stores — SQLite default (fast), Chroma optional (lazy import)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Protocol

from contextpack.core.models import SemanticChunk


class VectorStore(Protocol):
    def upsert_chunks(self, chunks: list[SemanticChunk], embeddings: list[list[float]]) -> None: ...

    def query(self, embedding: list[float], n: int = 10) -> list[SemanticChunk]: ...


class SQLiteVectorStore:
    """Fast local store — no Chroma/onnx cold start."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._chunks: list[SemanticChunk] = []
        self._vectors: list[list[float]] = []
        self._load()

    def _load(self) -> None:
        if not self._db_path.exists():
            return
        data = json.loads(self._db_path.read_text())
        self._chunks = [SemanticChunk.model_validate(c) for c in data.get("chunks", [])]
        self._vectors = data.get("vectors", [])

    def _save(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db_path.write_text(
            json.dumps(
                {
                    "chunks": [c.model_dump() for c in self._chunks],
                    "vectors": self._vectors,
                }
            )
        )

    def upsert_chunks(self, chunks: list[SemanticChunk], embeddings: list[list[float]]) -> None:
        self._chunks = chunks
        self._vectors = embeddings
        self._save()

    def query(self, embedding: list[float], n: int = 10) -> list[SemanticChunk]:
        if not self._vectors:
            return []
        scored = sorted(
            zip(self._chunks, (_cosine(embedding, v) for v in self._vectors)),
            key=lambda x: x[1],
            reverse=True,
        )
        return [c for c, _ in scored[:n]]


class ChromaVectorStore:
    """ChromaDB — loaded only when explicitly selected (slow first import)."""

    def __init__(self, persist_dir: Path, collection_name: str = "contextpack") -> None:
        import chromadb  # noqa: PLC0415 — intentional lazy import

        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(self, chunks: list[SemanticChunk], embeddings: list[list[float]]) -> None:
        ids = [f"{c.file_path}::{c.name}::{c.type}" for c in chunks]
        documents = [c.content or c.summary for c in chunks]
        metadatas: list[dict[str, Any]] = [
            {
                "type": c.type,
                "name": c.name,
                "file_path": c.file_path,
                "summary": (c.summary or "")[:500],
            }
            for c in chunks
        ]
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(self, embedding: list[float], n: int = 10) -> list[SemanticChunk]:
        result = self._collection.query(query_embeddings=[embedding], n_results=n)
        chunks: list[SemanticChunk] = []
        if not result["ids"] or not result["ids"][0]:
            return chunks
        for i, chunk_id in enumerate(result["ids"][0]):
            meta = (result.get("metadatas") or [[]])[0][i] or {}
            doc = (result.get("documents") or [[]])[0][i] or ""
            chunks.append(
                SemanticChunk(
                    type=meta.get("type", ""),
                    name=meta.get("name", chunk_id),
                    file_path=meta.get("file_path", ""),
                    summary=meta.get("summary", ""),
                    content=doc,
                )
            )
        return chunks


def get_vector_store(ctx_dir: Path, backend: str) -> VectorStore:
    if backend == "chroma":
        return ChromaVectorStore(ctx_dir / "chroma")
    return SQLiteVectorStore(ctx_dir / "vectors.json")


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)
