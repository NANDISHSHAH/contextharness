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

    mcp.run()


if __name__ == "__main__":
    run_server()
