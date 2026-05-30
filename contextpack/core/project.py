"""High-level Project SDK."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from contextpack.adapters.azure_foundry import AzureFoundryAdapter
from contextpack.compiler.chunking.engine import ChunkingEngine
from contextpack.compiler.compiler import ContextCompiler
from contextpack.core.config import get_settings
from contextpack.core.models import AggregatedAgentContext, ChangeSet, ContextPack, ProjectMap
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


@dataclass
class BuildStats:
    """Per-phase timing and counts for a single `project.build()` run."""

    files_scanned: int = 0
    files_indexed: int = 0
    files_skipped: int = 0
    entities: int = 0
    hub_entities: int = 0
    chunks: int = 0
    estimated_tokens: int = 0
    embed_count: int = 0
    store_only_count: int = 0
    phase_times: dict[str, float] = field(default_factory=dict)

    @property
    def total_time(self) -> float:
        return sum(self.phase_times.values())


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

    async def build(
        self,
        on_phase: Callable[[str, str, str], None] | None = None,
    ) -> tuple[ProjectMap, BuildStats]:
        """Build the index.

        Args:
            on_phase: Optional callback invoked at phase boundaries.
                      Signature: ``on_phase(phase, event, detail)``
                      where *event* is ``"start"`` or ``"done"``.
        """
        stats = BuildStats()

        def _start(phase: str) -> None:
            if on_phase:
                on_phase(phase, "start", "")

        def _done(phase: str, detail: str = "") -> None:
            if on_phase:
                on_phase(phase, "done", detail)

        # ── scan ────────────────────────────────────────────────────────────
        _start("scan")
        t = time.perf_counter()
        scanner = RepositoryScanner(self.root)
        project_map = scanner.scan()
        stats.phase_times["scan"] = time.perf_counter() - t
        stats.files_scanned = len(project_map.files) + project_map.files_skipped
        stats.files_indexed = len(project_map.files)
        stats.files_skipped = project_map.files_skipped
        _done(
            "scan",
            (
                f"[cyan]{stats.files_scanned:,}[/cyan] files  "
                f"[yellow]{stats.files_skipped:,} skipped[/yellow]"
            ),
        )

        # ── parse ────────────────────────────────────────────────────────────
        _start("parse")
        t = time.perf_counter()
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
        stats.phase_times["parse"] = time.perf_counter() - t
        stats.entities = len(entities)
        _done(
            "parse",
            (
                f"[blue]{stats.entities:,}[/blue] entities from "
                f"[dim]{stats.files_indexed:,}[/dim] files"
            ),
        )

        # ── graph ────────────────────────────────────────────────────────────
        _start("graph")
        t = time.perf_counter()
        graph = ContextGraph.from_entities(entities)
        self._graph = graph
        stats.phase_times["graph"] = time.perf_counter() - t

        # ── tiered embedding selection ───────────────────────────────────────
        # Tier 1: hub nodes (high graph degree) — always embed regardless of budget
        # Tier 2: remaining entities up to max_embed_entities cap
        # Tier 3 (store-only): entities beyond cap — kept in DB for symbol lookup
        hub_names: set[str] = set()
        if self._settings.embed_hubs_first and entities:
            hub_names = {name for name, _, _ in graph.hub_entities(limit=50)}

        tier1 = [e for e in entities if e.name in hub_names]
        tier2 = [e for e in entities if e.name not in hub_names]
        budget_remaining = max(0, self._settings.max_embed_entities - len(tier1))
        to_embed = tier1 + tier2[:budget_remaining]
        to_store_only = tier2[budget_remaining:]

        stats.hub_entities = len(hub_names)
        stats.embed_count = len(to_embed)
        stats.store_only_count = len(to_store_only)
        _done(
            "graph",
            (
                f"[magenta]{len(entities):,}[/magenta] nodes  "
                f"[bright_magenta]{stats.hub_entities}[/bright_magenta] hubs"
            ),
        )

        # ── chunk ────────────────────────────────────────────────────────────
        _start("chunk")
        t = time.perf_counter()
        chunker = ChunkingEngine()
        chunks = chunker.chunk_entities(to_embed)
        stats.chunks = len(chunks)
        stats.estimated_tokens = sum(c.token_estimate for c in chunks)
        stats.phase_times["chunk"] = time.perf_counter() - t
        _done(
            "chunk",
            (
                f"[yellow]{stats.chunks:,}[/yellow] chunks  "
                f"[dim]~{stats.estimated_tokens:,} tokens[/dim]"
            ),
        )

        # ── embed ────────────────────────────────────────────────────────────
        _start("embed")
        t = time.perf_counter()
        embedder = get_embedding_provider()
        texts = [c.summary or c.content for c in chunks]
        embeddings = await embedder.embed_batch(texts)
        vector_store = get_vector_store(self._ctx_dir, self._settings.vector_store)
        vector_store.upsert_chunks(chunks, embeddings)
        stats.phase_times["embed"] = time.perf_counter() - t
        _done(
            "embed",
            (
                f"[bright_green]{stats.embed_count:,}[/bright_green] "
                f"embedded  [dim]{stats.store_only_count:,} store-only[/dim]"
            ),
        )

        # ── store ────────────────────────────────────────────────────────────
        _start("store")
        t = time.perf_counter()
        db_store = SQLiteStore(self._ctx_dir / "memory.db")
        await db_store.initialize()
        entity_rows = [
            (
                f"{ent.file_path}::{ent.name}",
                str(ent.type),
                ent.name,
                ent.file_path,
                ent.model_dump(),
            )
            for ent in entities  # store ALL entities (including store-only tier)
        ]
        await db_store.upsert_entities_batch(entity_rows)
        stats.phase_times["store"] = time.perf_counter() - t
        _done("store", f"[green]{stats.entities:,}[/green] entities → memory.db")

        retriever = HybridRetriever(vector_store, graph, embedder)
        self._compiler = ContextCompiler(retriever, graph)
        self._project_map = project_map

        # ── workflow extraction (Phase 5) ────────────────────────────────────
        from contextpack.memory.store import compute_hashes, save_hashes
        from contextpack.workflows.extractor import extract_and_store

        t = time.perf_counter()
        try:
            workflows = await extract_and_store(
                graph, entities, self._ctx_dir / "memory.db"
            )
            stats.phase_times["workflows"] = time.perf_counter() - t
            logger.info("workflows_extracted", count=len(workflows))
        except Exception:
            stats.phase_times["workflows"] = 0.0

        # ── save file hashes for incremental builds ──────────────────────────
        all_paths = [r.path for r in project_map.files]
        new_hashes = compute_hashes(self.root, all_paths)
        save_hashes(self._ctx_dir, new_hashes)

        map_path = self._ctx_dir / "project_map.json"
        map_path.write_text(project_map.model_dump_json(indent=2))
        from contextpack.harness.staleness import stamp_build

        stamp_build(self.root)
        logger.info(
            "build_complete",
            files=stats.files_indexed,
            files_skipped=stats.files_skipped,
            entities=stats.entities,
            embed_count=stats.embed_count,
            store_only=stats.store_only_count,
            total_s=round(stats.total_time, 2),
        )
        return project_map, stats

    async def incremental_build(self) -> tuple[ProjectMap, BuildStats, ChangeSet]:
        """Re-parse only files that changed since the last build.

        Falls back to a full build when no prior hash snapshot exists.
        Always records a ChangeSet in the change log.
        """
        from contextpack.memory.store import (
            build_changeset,
            compute_hashes,
            diff_hashes,
            load_hashes,
            save_hashes,
        )

        if not self.is_built():
            project_map, stats = await self.build()
            empty_cs = ChangeSet(summary="initial build (no prior snapshot)")
            return project_map, stats, empty_cs

        # ── detect changed files ─────────────────────────────────────────────
        old_hashes = load_hashes(self._ctx_dir)
        scanner = RepositoryScanner(self.root)
        project_map = scanner.scan()
        all_paths = [r.path for r in project_map.files]
        new_hashes = compute_hashes(self.root, all_paths)
        added, modified, deleted = diff_hashes(old_hashes, new_hashes)
        changed = set(added) | set(modified)

        if not changed and not deleted:
            existing = self._load_project_map()
            cs = ChangeSet(summary="no changes detected")
            return existing, BuildStats(), cs

        # ── load existing project map and patch it ───────────────────────────
        existing_map = self._load_project_map()
        kept_entities = [
            e for e in existing_map.entities
            if e.file_path not in (changed | set(deleted))
        ]

        # ── re-parse only changed files ──────────────────────────────────────
        stats = BuildStats()
        t = time.perf_counter()
        file_triples: list[tuple[str, str, str]] = []
        lang_map = {r.path: r.language for r in project_map.files}
        for path in changed:
            lang = lang_map.get(path, "")
            if not lang:
                continue
            full = self.root / path
            try:
                content = full.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if len(content) > 300_000:
                continue
            file_triples.append((path, lang, content))

        new_entities = parse_project_files(str(self.root), file_triples)
        for ent in new_entities:
            ent.summary = ent.docstring or f"{ent.type} {ent.name}"
        stats.phase_times["parse"] = time.perf_counter() - t

        # Build entity delta for the change log
        old_entity_names: dict[str, set[str]] = {}
        for ent in existing_map.entities:
            old_entity_names.setdefault(ent.file_path, set()).add(ent.name)
        new_entity_names: dict[str, set[str]] = {}
        for ent in new_entities:
            new_entity_names.setdefault(ent.file_path, set()).add(ent.name)

        entity_delta: dict[str, tuple[list[str], list[str], list[str]]] = {}
        for path in changed:
            old_names = old_entity_names.get(path, set())
            cur_names = new_entity_names.get(path, set())
            entity_delta[path] = (
                sorted(cur_names - old_names),
                sorted(old_names - cur_names),
                sorted(old_names & cur_names),
            )

        # ── merge and rebuild graph ──────────────────────────────────────────
        all_entities = kept_entities + new_entities
        project_map.entities = all_entities
        stats.entities = len(all_entities)

        t = time.perf_counter()
        graph = ContextGraph.from_entities(all_entities)
        self._graph = graph
        stats.phase_times["graph"] = time.perf_counter() - t

        # ── embed only new/changed chunks ────────────────────────────────────
        t = time.perf_counter()
        chunker = ChunkingEngine()
        chunks = chunker.chunk_entities(new_entities)
        stats.chunks = len(chunks)
        stats.phase_times["chunk"] = time.perf_counter() - t

        t = time.perf_counter()
        embedder = get_embedding_provider()
        texts = [c.summary or c.content for c in chunks]
        vector_store = get_vector_store(self._ctx_dir, self._settings.vector_store)
        if texts:
            embeddings = await embedder.embed_batch(texts)
            vector_store.upsert_chunks(chunks, embeddings)
        stats.embed_count = len(chunks)
        stats.phase_times["embed"] = time.perf_counter() - t

        # ── store updated entities ───────────────────────────────────────────
        t = time.perf_counter()
        db_store = SQLiteStore(self._ctx_dir / "memory.db")
        await db_store.initialize()
        entity_rows = [
            (f"{e.file_path}::{e.name}", str(e.type), e.name, e.file_path, e.model_dump())
            for e in new_entities
        ]
        if entity_rows:
            await db_store.upsert_entities_batch(entity_rows)
        stats.phase_times["store"] = time.perf_counter() - t

        # ── build change set and persist ─────────────────────────────────────
        changeset = build_changeset(
            self.root, self._ctx_dir, old_hashes, new_hashes, entity_delta
        )
        await db_store.insert_file_changes(
            changeset.build_id, [fc.model_dump() for fc in changeset.files_changed]
        )

        # ── save updated hashes and project map ─────────────────────────────
        save_hashes(self._ctx_dir, new_hashes)
        map_path = self._ctx_dir / "project_map.json"
        map_path.write_text(project_map.model_dump_json(indent=2))

        retriever = HybridRetriever(vector_store, graph, embedder)
        self._compiler = ContextCompiler(retriever, graph)
        self._project_map = project_map

        from contextpack.harness.staleness import stamp_build
        stamp_build(self.root)

        logger.info(
            "incremental_build_complete",
            changed=len(changed),
            deleted=len(deleted),
            new_entities=len(new_entities),
            summary=changeset.summary,
        )
        return project_map, stats, changeset

    async def recent_changes(self, limit: int = 50) -> list[dict]:
        """Return the most recent file changes from the change log."""
        db_store = SQLiteStore(self._ctx_dir / "memory.db")
        await db_store.initialize()
        return await db_store.get_recent_changes(limit=limit)

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

    async def harvest(
        self, query: str, *, branch_name: str | None = None
    ) -> AggregatedAgentContext:
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

    async def workflows(self) -> list[dict]:
        """Return all extracted workflows from the SQLite store."""
        db_store = SQLiteStore(self._ctx_dir / "memory.db")
        await db_store.initialize()
        return await db_store.list_workflows()

    def agent_memory(self, agent_id: str = "default") -> AgentMemory:  # type: ignore[name-defined]
        """Return an AgentMemory scoped to agent_id, backed by this project's DB."""
        from contextpack.skills import AgentMemory
        return AgentMemory(agent_id, self._ctx_dir / "memory.db")

    def shared_memory(self) -> SharedMemory:  # type: ignore[name-defined]
        """Return a SharedMemory view across all agents for this project."""
        from contextpack.skills import SharedMemory
        return SharedMemory(self._ctx_dir / "memory.db")


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
