"""Protocols for swappable providers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from contextpack.core.models import (
    HarvestedContext,
    ParsedEntity,
    ProjectMap,
    SemanticChunk,
)


@runtime_checkable
class ContextFetcher(Protocol):
    """Parallel context source (meetup: Context Harvester fetchers)."""

    source_type: str

    async def fetch(self, query: str, project_map: ProjectMap) -> HarvestedContext: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    async def embed(self, text: str) -> list[float]: ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


@runtime_checkable
class Parser(Protocol):
    language: str

    def parse_file(self, path: str, content: str) -> list[ParsedEntity]: ...


@runtime_checkable
class Retriever(Protocol):
    async def retrieve(self, query: str, limit: int = 10) -> list[SemanticChunk]: ...


@runtime_checkable
class LLMProvider(Protocol):
    async def complete(self, system: str, user: str) -> str: ...
