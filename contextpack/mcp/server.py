"""MCP tools: project_outline, find_symbol, graph_neighbours, harvest_context."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from contextpack.core.project import Project
from contextpack.graph.engine import ContextGraph


def _repo_root() -> Path:
    env = os.environ.get("CONTEXTPACK_ROOT") or os.environ.get("CONTEXT_HARNESS_ROOT")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


def _project() -> Project:
    return Project(_repo_root())


def run_server() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as e:
        raise SystemExit(
            "MCP server requires the harness extra: uv sync --extra harness"
        ) from e

    mcp = FastMCP(
        "context-harness",
        instructions=(
            "Context Harness MCP — graph-native codebase understanding. "
            "Run `context build` if tools report a missing index."
        ),
    )

    @mcp.tool()
    def project_outline() -> str:
        """Summarize indexed repo: languages, entity count, graph hubs, staleness."""
        root = _repo_root()
        from contextpack.harness.orientation import build_orientation
        from contextpack.harness.staleness import check_staleness

        stale = check_staleness(root)
        header = f"Stale index: {stale.is_stale} — {stale.reason}\n\n"
        if not Project(root).is_built():
            return header + "Run: context build " + str(root)
        return header + build_orientation(root)

    @mcp.tool()
    def find_symbol(symbol: str) -> str:
        """Find entities matching a symbol name in the dependency graph."""
        p = _project()
        if not p.is_built():
            return "Index missing. Run `context build` first."
        graph = ContextGraph.from_project_map(p.project_map())
        hits = graph.find_symbol(symbol)
        if not hits:
            return f"No matches for `{symbol}`."
        lines = [f"Matches for `{symbol}`:"]
        for h in hits:
            lines.append(f"- {h['name']} ({h['type']}) @ {h['file']}")
        return "\n".join(lines)

    @mcp.tool()
    def graph_neighbours(symbol: str, depth: int = 2) -> str:
        """Return dependency neighbourhood for a symbol (graph traversal)."""
        p = _project()
        if not p.is_built():
            return "Index missing. Run `context build` first."
        from contextpack.graph.engine import ContextGraph

        graph = ContextGraph.from_project_map(p.project_map())
        hits = graph.find_symbol(symbol, limit=1)
        if not hits:
            return f"Symbol `{symbol}` not found in graph."
        node_id = hits[0]["node_id"]
        hood = graph.neighbors(node_id, depth=min(max(depth, 1), 4))
        lines = [f"Neighbourhood of `{symbol}` (depth={depth}):"]
        for node in sorted(hood)[:40]:
            data = graph.graph.nodes.get(node, {})
            lines.append(f"- {data.get('name', node)} ({data.get('type', '?')})")
        return "\n".join(lines)

    @mcp.tool()
    def harvest_context(query: str, branch: str = "") -> str:
        """Harvest multi-source agent context (code + guidelines + tests + optional Jira)."""
        p = _project()
        if not p.is_built():
            return "Index missing. Run `context build` first."

        async def _run() -> str:
            agg = await p.harvest(query, branch_name=branch or None)
            return agg.to_agent_prompt_block()

        return asyncio.run(_run())

    @mcp.tool()
    def compile_context(query: str, token_budget: int = 8000) -> str:
        """Token-budgeted code context pack for a query (no external fetchers)."""
        p = _project()
        if not p.is_built():
            return "Index missing. Run `context build` first."

        async def _run() -> str:
            pack = await p.compile(query, token_budget=token_budget)
            parts = [f"# Context pack: {query}", ""]
            for s in pack.summaries[:20]:
                parts.append(f"- {s}")
            if pack.chunks:
                parts.append("")
                parts.append("## Chunks")
                for c in pack.chunks[:8]:
                    parts.append(f"### {c.file_path}")
                    parts.append((c.summary or c.content)[:1200])
            return "\n".join(parts)

        return asyncio.run(_run())

    @mcp.tool()
    def get_recent_changes(limit: int = 20) -> str:
        """List file changes recorded by the last incremental build (Phase 3)."""
        p = _project()
        if not p.is_built():
            return "Index missing. Run `context build` first."

        async def _run() -> str:
            rows = await p.recent_changes(limit=limit)
            if not rows:
                return "No change log yet. Run `context watch` or `context build` to populate."
            from contextpack.memory.store import format_changeset
            from contextpack.core.models import ChangeSet, FileChange

            # Group by build_id, show most recent build's changes
            by_build: dict[str, list[dict]] = {}
            for r in rows:
                by_build.setdefault(r.get("build_id", "?"), []).append(r)
            lines = []
            for build_id, changes in list(by_build.items())[:3]:
                lines.append(f"Build {build_id}:")
                for c in changes[:10]:
                    prefix = {"added": "+", "modified": "~", "deleted": "-"}.get(
                        c.get("change_type", "?"), "?"
                    )
                    lines.append(f"  {prefix} {c.get('path', '?')}")
            return "\n".join(lines)

        return asyncio.run(_run())

    @mcp.tool()
    def list_workflows() -> str:
        """List all workflows extracted from the codebase (Phase 5)."""
        p = _project()
        if not p.is_built():
            return "Index missing. Run `context build` first."

        async def _run() -> str:
            wfs = await p.workflows()
            if not wfs:
                return "No workflows extracted yet. Run `context build` to populate."
            lines = [f"Extracted workflows ({len(wfs)}):"]
            for wf in wfs[:20]:
                name = wf.get("name", "?")
                summary = wf.get("summary", "")
                steps = wf.get("steps", [])
                lines.append(f"\n## {name}")
                if summary:
                    lines.append(summary)
                if steps:
                    lines.append("Steps: " + " → ".join(steps[:8]))
            return "\n".join(lines)

        return asyncio.run(_run())

    @mcp.tool()
    def agent_memory_store(
        content: str,
        agent_id: str = "default",
        fact_type: str = "observation",
    ) -> str:
        """Store a fact in multi-agent shared memory (Phase 5).

        fact_type: one of decision | observation | constraint | task_state
        """
        p = _project()
        mem = p.agent_memory(agent_id)

        async def _run() -> str:
            fact_id = await mem.store(content, fact_type=fact_type)
            return f"Stored fact {fact_id} for agent '{agent_id}' (type: {fact_type})"

        return asyncio.run(_run())

    @mcp.tool()
    def agent_memory_recall(query: str = "", agent_id: str = "", limit: int = 10) -> str:
        """Recall facts from multi-agent shared memory (Phase 5).

        Leave agent_id empty to query across all agents.
        """
        p = _project()

        async def _run() -> str:
            mem = p.shared_memory()
            if agent_id:
                facts = await p.agent_memory(agent_id).recall(query=query, limit=limit)
            else:
                facts = await mem.recall_all(query=query, limit=limit)
            if not facts:
                return "No matching facts found."
            lines = [f"Agent memory ({len(facts)} facts):"]
            for f in facts:
                aid = f.get("agent_id", "?")
                ftype = f.get("fact_type", "?")
                content = f.get("content", "")
                lines.append(f"- [{aid}/{ftype}] {content}")
            return "\n".join(lines)

        return asyncio.run(_run())

    # ── Phase 6: Pre-Skill Engine ─────────────────────────────────────────────

    @mcp.tool()
    def get_skill_plan(files: str, blast_radius: int = 0) -> str:
        """Compute a SkillPlan for a comma-separated list of changed files (Phase 6)."""
        root = _repo_root()
        changed = [f.strip() for f in files.split(",") if f.strip()]
        from contextpack.skills.manifest import SkillManifest
        from contextpack.skills.router import SkillRouter
        manifest = SkillManifest.load(root)
        plan = SkillRouter(manifest).route(changed, blast_radius=blast_radius)
        return plan.summary()

    @mcp.tool()
    def run_skill_gate(files: str, blast_radius: int = 0) -> str:
        """Run the full skill verification gate on changed files (Phase 6)."""
        root = _repo_root()
        changed = [f.strip() for f in files.split(",") if f.strip()]

        async def _run() -> str:
            from contextpack.skills.manifest import SkillManifest
            from contextpack.skills.verifier import SkillVerifierLoop
            manifest = SkillManifest.load(root)
            db = root / ".contextpack" / "memory.db"
            loop = SkillVerifierLoop(db)
            result = await loop.verify(changed, root, manifest, blast_radius=blast_radius)
            return result.to_text()

        return asyncio.run(_run())

    @mcp.tool()
    def get_evidence_bundles(limit: int = 10) -> str:
        """List recent evidence bundles (per-action skill gate audit trail) (Phase 6)."""
        root = _repo_root()

        async def _run() -> str:
            from contextpack.skills.evidence import EvidenceStore
            db = root / ".contextpack" / "memory.db"
            store = EvidenceStore(db)
            bundles = await store.list_recent(limit=limit)
            if not bundles:
                return "No evidence bundles yet. Run `context skills run` first."
            lines = [f"Evidence bundles ({len(bundles)}):"]
            for b in bundles:
                icon = "✅" if b.passed else "❌"
                lines.append(f"\n{icon} `{b.action_id}` — {', '.join(b.files_modified[:3])}")
                for r in b.skill_results[:4]:
                    ri = "✅" if r.get("passed") else "❌"
                    lines.append(f"   {ri} {r['skill']} ({r.get('duration_ms', 0):.0f}ms)")
            return "\n".join(lines)

        return asyncio.run(_run())

    # ── Phase 7: Semantic Contracts ───────────────────────────────────────────

    @mcp.tool()
    def get_contracts(symbol: str = "", limit: int = 20) -> str:
        """Look up extracted contracts for a symbol or list all contracts (Phase 7)."""
        root = _repo_root()

        async def _run() -> str:
            from contextpack.contracts.registry import ContractRegistry
            db = root / ".contextpack" / "memory.db"
            reg = ContractRegistry(db)
            if symbol:
                results = await reg.search(symbol, limit=limit)
            else:
                results = await reg.list_all(limit=limit)
            if not results:
                return "No contracts indexed. Run `context build` first."
            return reg.format_for_context(results)

        return asyncio.run(_run())

    @mcp.tool()
    def check_invariants(files: str) -> str:
        """Check architectural invariants for a comma-separated list of files (Phase 7)."""
        root = _repo_root()
        changed = [f.strip() for f in files.split(",") if f.strip()]

        async def _run() -> str:
            from contextpack.contracts.invariants import InvariantConfig, InvariantGuard
            config = InvariantConfig.load(root)
            if not config.invariants:
                return "No invariants.yml found. Create .contextpack/invariants.yml to define rules."
            db = root / ".contextpack" / "memory.db"
            guard = InvariantGuard(db)
            # Build edges from changed files (simplified: just check imports in file)
            edges: list[tuple[str, str]] = []
            for f in changed:
                fp = root / f
                if fp.exists() and fp.suffix == ".py":
                    content = fp.read_text(errors="replace")
                    import re
                    for imp in re.findall(r"^(?:from|import)\s+(\S+)", content, re.MULTILINE):
                        edges.append((f, imp.replace(".", "/")))
            violations = guard.check(config, edges)
            if not violations:
                return f"✅ No invariant violations found for {len(changed)} file(s)."
            lines = [f"❌ {len(violations)} invariant violation(s):"]
            for v in violations:
                lines.append(v.to_text())
            return "\n".join(lines)

        return asyncio.run(_run())

    # ── Phase 8: Context Governance ───────────────────────────────────────────

    @mcp.tool()
    def get_context_debt(limit: int = 20) -> str:
        """Show per-module context debt scores (Phase 8)."""
        root = _repo_root()

        async def _run() -> str:
            from contextpack.governance.debt import ContextDebtTracker
            db = root / ".contextpack" / "memory.db"
            tracker = ContextDebtTracker(db)
            records = await tracker.list_all(limit=limit)
            if not records:
                return "No debt records yet. Run `context build` to populate."
            return tracker.format_report(records)

        return asyncio.run(_run())

    @mcp.tool()
    def check_agent_conflicts(agent_id: str, files: str) -> str:
        """Check for multi-agent file conflicts before editing (Phase 8)."""
        root = _repo_root()
        file_list = [f.strip() for f in files.split(",") if f.strip()]

        async def _run() -> str:
            from contextpack.governance.locks import AgentLockTable
            db = root / ".contextpack" / "memory.db"
            locks = AgentLockTable(db)
            conflict = await locks.check_conflicts(agent_id, file_list, [])
            return conflict.to_text()

        return asyncio.run(_run())

    # ── Phase 9: Adaptive Intelligence ───────────────────────────────────────

    @mcp.tool()
    def get_failure_patterns(file_path: str = "") -> str:
        """Get proactive failure pattern warnings for a file (Phase 9)."""
        root = _repo_root()

        async def _run() -> str:
            from contextpack.adaptive.patterns import FailurePatternStore
            db = root / ".contextpack" / "memory.db"
            store = FailurePatternStore(db)
            if file_path:
                patterns = await store.list_proactive(file_path)
            else:
                patterns = await store.list_all(limit=20)
            if not patterns:
                return "No failure patterns recorded yet."
            lines = [f"Failure patterns ({len(patterns)}):"]
            for p in patterns:
                lines.append(p.to_briefing())
            return "\n".join(lines)

        return asyncio.run(_run())

    @mcp.tool()
    def get_coupling_trend() -> str:
        """Show architectural coupling trend over the last 30 days (Phase 9)."""
        root = _repo_root()

        async def _run() -> str:
            from contextpack.adaptive.coupling import CouplingMonitor
            db = root / ".contextpack" / "memory.db"
            monitor = CouplingMonitor(db)
            trend = await monitor.trend(days=30)
            return trend.to_text()

        return asyncio.run(_run())

    mcp.run()


if __name__ == "__main__":
    run_server()
