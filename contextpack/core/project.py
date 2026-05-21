"""High-level Project SDK."""

from __future__ import annotations

import json
from pathlib import Path

import structlog

from contextpack.aggregator.aggregator import ContextAggregator
from contextpack.compiler.chunking.engine import ChunkingEngine
from contextpack.compiler.compiler import ContextCompiler
from contextpack.adapters.azure_foundry import AzureFoundryAdapter
from contextpack.core.config import get_settings
from contextpack.core.models import AggregatedAgentContext, ContextPack, ProjectMap
from contextpack.core.protocols import LLMProvider
from contextpack.embeddings.provider import get_embedding_provider
from contextpack.embeddings.vector_store import get_vector_store
from contextpack.graph.engine import ContextGraph
from contextpack.harvester.harvester import ContextHarvester
from contextpack.parsers.base import parse_project_files
from contextpack.retrieval.engine import HybridRetriever
from contextpack.scanner.scanner import RepositoryScanner
from contextpack.storage.sqlite import SQLiteStore

logger = structlog.get_logger(__name__)


class Project:
    def __init__(self, path: str | Path) -> None:
        self.root = Path(path).resolve()
        self._settings = get_settings()
        self._ctx_dir = self._settings.context_dir(self.root)
        self._project_map: ProjectMap | None = None
        self._graph: ContextGraph | None = None
        self._compiler: ContextCompiler | None = None
        self._harvester = ContextHarvester()

    @property
    def context_dir(self) -> Path:
        return self._ctx_dir

    async def init(self) -> None:
        self._ctx_dir.mkdir(parents=True, exist_ok=True)
        store = SQLiteStore(self._ctx_dir / "memory.db")
        await store.initialize()
        (self._ctx_dir / "config.json").write_text(
            json.dumps({"root": str(self.root), "version": "0.1.0"}, indent=2)
        )

    async def build(self) -> ProjectMap:
        scanner = RepositoryScanner(self.root)
        project_map = scanner.scan()

        file_triples: list[tuple[str, str, str]] = []
        for record in project_map.files:
            if not record.language:
                continue
            full = self.root / record.path
            try:
                content = full.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if len(content) > 300_000:
                continue
            file_triples.append((record.path, record.language, content))

        entities = parse_project_files(str(self.root), file_triples)
        for ent in entities:
            ent.summary = ent.docstring or f"{ent.type} {ent.name}"
        project_map.entities = entities

        graph = ContextGraph.from_entities(entities)
        self._graph = graph

        chunker = ChunkingEngine()
        chunks = chunker.chunk_entities(entities)

        embedder = get_embedding_provider()
        texts = [c.summary or c.content for c in chunks]
        embeddings = await embedder.embed_batch(texts)

        vector_store = get_vector_store(self._ctx_dir, self._settings.vector_store)
        vector_store.upsert_chunks(chunks, embeddings)

        db_store = SQLiteStore(self._ctx_dir / "memory.db")
        await db_store.initialize()
        for ent in entities:
            eid = f"{ent.file_path}::{ent.name}"
            await db_store.upsert_entity(
                eid,
                str(ent.type),
                ent.name,
                ent.file_path,
                ent.model_dump(),
            )

        retriever = HybridRetriever(vector_store, graph, embedder)
        self._compiler = ContextCompiler(retriever, graph)
        self._project_map = project_map

        map_path = self._ctx_dir / "project_map.json"
        map_path.write_text(project_map.model_dump_json(indent=2))
        from contextpack.harness.staleness import stamp_build

        stamp_build(self.root)
        logger.info("build_complete", files=len(project_map.files), entities=len(entities))
        return project_map

    def is_built(self) -> bool:
        return (self._ctx_dir / "project_map.json").is_file()

    def project_map(self) -> ProjectMap:
        return self._load_project_map()

    def orientation(self, query: str = "architecture") -> str:
        from contextpack.harness.orientation import build_orientation

        return build_orientation(self.root, query=query)

    def _load_project_map(self) -> ProjectMap:
        if self._project_map:
            return self._project_map
        path = self._ctx_dir / "project_map.json"
        if path.exists():
            self._project_map = ProjectMap.model_validate_json(path.read_text())
            self._graph = ContextGraph.from_project_map(self._project_map)
            embedder = get_embedding_provider()
            store = get_vector_store(self._ctx_dir, self._settings.vector_store)
            self._compiler = ContextCompiler(
                HybridRetriever(store, self._graph, embedder), self._graph
            )
            return self._project_map
        raise RuntimeError("Project not built. Run project.build() or `context build` first.")

    async def compile(self, query: str, token_budget: int | None = None) -> ContextPack:
        self._load_project_map()
        assert self._compiler
        budget = token_budget or self._settings.default_token_budget
        return await self._compiler.compile(query, token_budget=budget)

    async def harvest(self, query: str, *, branch_name: str | None = None) -> AggregatedAgentContext:
        """Complete agent context (meetup: harvest + aggregate all sources)."""
        project_map = self._load_project_map()
        compiled = await self.compile(query) if self._compiler else None
        return await self._harvester.harvest_and_aggregate(
            query,
            project_map,
            branch_name=branch_name,
            compiled_pack=compiled,
        )

    async def ask(
        self,
        question: str,
        *,
        branch_name: str | None = None,
        use_llm: bool = False,
        llm: LLMProvider | None = None,
    ) -> str:
        aggregated = await self.harvest(question, branch_name=branch_name)
        if use_llm or llm is not None:
            return await self.ask_llm(question, aggregated=aggregated, llm=llm)
        return _synthesize_answer(question, aggregated)

    async def ask_llm(
        self,
        question: str,
        *,
        aggregated: AggregatedAgentContext | None = None,
        llm: LLMProvider | None = None,
        branch_name: str | None = None,
    ) -> str:
        """Answer using Azure Foundry / configured LLM + full harvested context."""
        ctx = aggregated or await self.harvest(question, branch_name=branch_name)
        adapter = AzureFoundryAdapter()
        system, user = adapter.build_prompt(ctx)
        provider = llm
        if provider is None:
            from contextpack.llm.factory import get_llm_provider

            provider = get_llm_provider()
        user_block = f"{user}\n\n---\n\n**Question:** {question}"
        return await provider.complete(system, user_block)

    def graph_summary(self, query: str = "architecture") -> str:
        project_map = self._load_project_map()
        graph = self._graph or ContextGraph.from_project_map(project_map)
        return graph.describe_neighborhood(query, max_nodes=40)

    def hub_entities(self, limit: int = 12) -> list[tuple[str, str, int]]:
        project_map = self._load_project_map()
        graph = self._graph or ContextGraph.from_project_map(project_map)
        return graph.hub_entities(limit)


def _synthesize_answer(question: str, ctx: AggregatedAgentContext) -> str:
    """MVP answer synthesis from harvested context (no LLM required)."""
    lines = [
        f"# Answer: {question}",
        "",
        ctx.to_agent_prompt_block()[:6000],
        "",
    ]
    if ctx.guardrails:
        lines.append("## Guardrails")
        for g in ctx.guardrails:
            lines.append(f"- {g}")
    if ctx.compiled_pack:
        lines.append("")
        lines.append("## Key architectural signals")
        for s in ctx.compiled_pack.summaries[:8]:
            lines.append(f"- {s}")
    lines.append("")
    lines.append(
        "_Tip: pipe `AggregatedAgentContext.extra_instructions` into your LLM "
        "via adapters (Claude, OpenAI, Cursor) for full reasoning._"
    )
    return "\n".join(lines)
