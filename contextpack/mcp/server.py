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

    mcp.run()


if __name__ == "__main__":
    run_server()
