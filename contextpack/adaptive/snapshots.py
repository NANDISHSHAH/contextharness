"""Context snapshot engine — snapshot and diff semantic state across agent runs."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

import aiosqlite
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS context_snapshots (
    snapshot_id   TEXT PRIMARY KEY,
    agent_id      TEXT,
    task          TEXT,
    timestamp     REAL,
    graph_state   TEXT,
    context_used  TEXT,
    trust_summary TEXT,
    git_commit    TEXT
);
"""


class ContextSnapshot(BaseModel):
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    agent_id: str = "default"
    task: str = ""
    timestamp: float = Field(default_factory=time.time)
    graph_state: dict = Field(default_factory=dict)   # {nodes, edges, hubs, centralities}
    context_used: dict = Field(default_factory=dict)  # {chunks, tokens, trust_avg, sources}
    trust_summary: dict = Field(default_factory=dict) # {tier_counts, avg_trust}
    git_commit: str = ""


class SnapshotDiff(BaseModel):
    before_id: str
    after_id: str
    graph_changes: dict = Field(default_factory=dict)
    context_changes: dict = Field(default_factory=dict)
    trust_changes: dict = Field(default_factory=dict)
    summary_lines: list[str] = Field(default_factory=list)

    def to_text(self) -> str:
        lines = [
            f"## Context Snapshot Diff",
            f"Before: `{self.before_id}`  →  After: `{self.after_id}`",
            "",
        ]
        if self.graph_changes:
            lines.append("### Graph changes")
            for k, v in self.graph_changes.items():
                lines.append(f"  · {k}: {v}")
        if self.context_changes:
            lines.append("")
            lines.append("### Context used")
            for k, v in self.context_changes.items():
                lines.append(f"  · {k}: {v}")
        if self.trust_changes:
            lines.append("")
            lines.append("### Trust changes")
            for k, v in self.trust_changes.items():
                lines.append(f"  · {k}: {v}")
        for s in self.summary_lines:
            lines.append(s)
        return "\n".join(lines)


class ContextSnapshotEngine:
    """Snapshot and diff the semantic state of the codebase across agent runs."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    async def _init(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()

    def capture(
        self,
        agent_id: str,
        task: str,
        graph,
        context_pack: dict | None = None,
        git_commit: str = "",
    ) -> ContextSnapshot:
        """Capture a snapshot from a ContextGraph + optional context pack."""
        g = graph.graph
        node_count = g.number_of_nodes()
        edge_count = g.number_of_edges()

        # Hub detection
        degrees = sorted(
            [(n, g.degree(n)) for n in g.nodes()], key=lambda x: x[1], reverse=True
        )
        hubs = [n for n, d in degrees[:10] if d > 2]

        graph_state = {
            "nodes": node_count,
            "edges": edge_count,
            "hub_count": len(hubs),
            "top_hubs": hubs[:5],
        }

        ctx = context_pack or {}
        context_used = {
            "chunks": ctx.get("chunk_count", 0),
            "tokens": ctx.get("token_estimate", 0),
            "trust_avg": ctx.get("trust_avg", 0.0),
            "sources": ctx.get("sources", []),
        }

        return ContextSnapshot(
            agent_id=agent_id,
            task=task,
            graph_state=graph_state,
            context_used=context_used,
            git_commit=git_commit,
        )

    async def save(self, snapshot: ContextSnapshot) -> str:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO context_snapshots
                   (snapshot_id, agent_id, task, timestamp,
                    graph_state, context_used, trust_summary, git_commit)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    snapshot.snapshot_id,
                    snapshot.agent_id,
                    snapshot.task,
                    snapshot.timestamp,
                    json.dumps(snapshot.graph_state),
                    json.dumps(snapshot.context_used),
                    json.dumps(snapshot.trust_summary),
                    snapshot.git_commit,
                ),
            )
            await db.commit()
        logger.debug("snapshot_saved", snapshot_id=snapshot.snapshot_id)
        return snapshot.snapshot_id

    async def get(self, snapshot_id: str) -> ContextSnapshot | None:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM context_snapshots WHERE snapshot_id = ?", (snapshot_id,)
            ) as cur:
                row = await cur.fetchone()
        return _row(dict(row)) if row else None

    async def list_recent(self, limit: int = 20) -> list[ContextSnapshot]:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM context_snapshots ORDER BY timestamp DESC LIMIT ?", (limit,)
            ) as cur:
                rows = await cur.fetchall()
        return [_row(dict(r)) for r in rows]

    def diff(self, before: ContextSnapshot, after: ContextSnapshot) -> SnapshotDiff:
        """Compute a semantic diff between two snapshots."""
        graph_changes: dict = {}
        b_g, a_g = before.graph_state, after.graph_state
        for key in ("nodes", "edges", "hub_count"):
            if key in b_g and key in a_g:
                delta = a_g[key] - b_g[key]
                if delta != 0:
                    graph_changes[key] = f"{b_g[key]} → {a_g[key]} ({delta:+d})"

        new_hubs = set(a_g.get("top_hubs", [])) - set(b_g.get("top_hubs", []))
        if new_hubs:
            graph_changes["new_hubs"] = ", ".join(list(new_hubs)[:3])

        context_changes: dict = {}
        b_c, a_c = before.context_used, after.context_used
        for key in ("chunks", "tokens"):
            if key in b_c and key in a_c and b_c[key] != a_c[key]:
                context_changes[key] = f"{b_c[key]} → {a_c[key]}"

        summary: list[str] = []
        if graph_changes:
            summary.append(f"Graph: {len(graph_changes)} changes")
        if context_changes:
            summary.append(f"Context: {len(context_changes)} changes")

        return SnapshotDiff(
            before_id=before.snapshot_id,
            after_id=after.snapshot_id,
            graph_changes=graph_changes,
            context_changes=context_changes,
            summary_lines=summary,
        )


def _row(d: dict) -> ContextSnapshot:
    return ContextSnapshot(
        snapshot_id=d["snapshot_id"],
        agent_id=d["agent_id"],
        task=d["task"],
        timestamp=d["timestamp"],
        graph_state=json.loads(d["graph_state"]),
        context_used=json.loads(d["context_used"]),
        trust_summary=json.loads(d["trust_summary"]),
        git_commit=d["git_commit"],
    )
