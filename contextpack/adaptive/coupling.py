"""Coupling monitor — track graph coupling trends over time, detect architectural decay."""
from __future__ import annotations

import json
import time
from pathlib import Path

import aiosqlite
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS coupling_metrics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       REAL,
    avg_coupling    REAL,
    edge_count      INTEGER,
    node_count      INTEGER,
    hub_count       INTEGER,
    cycle_count     INTEGER,
    hotspots        TEXT,
    git_commit      TEXT
);
"""

_DECAY_THRESHOLD = 0.15  # 15% increase in 30 days = alert


class CouplingSnapshot(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    avg_coupling: float = 0.0
    edge_count: int = 0
    node_count: int = 0
    hub_count: int = 0
    cycle_count: int = 0
    hotspots: list[str] = Field(default_factory=list)
    git_commit: str = ""


class CouplingTrend(BaseModel):
    snapshots: list[CouplingSnapshot]
    coupling_change_pct: float = 0.0
    hub_change: int = 0
    cycle_change: int = 0
    is_decaying: bool = False
    alert_message: str = ""
    hotspot_modules: list[str] = Field(default_factory=list)

    def to_text(self) -> str:
        if not self.snapshots:
            return "No coupling history yet — run builds to accumulate metrics."
        latest = self.snapshots[-1]
        lines = [
            "## Coupling Trend Report",
            f"Latest: {latest.edge_count} edges / {latest.node_count} nodes "
            f"| {latest.hub_count} hubs | {latest.cycle_count} cycles",
            f"Coupling change (30d): {self.coupling_change_pct:+.1f}%",
            f"Hub count change: {self.hub_change:+d}",
            f"Cycle count change: {self.cycle_change:+d}",
        ]
        if self.is_decaying:
            lines.extend([
                "",
                f"🚨 ALERT: {self.alert_message}",
            ])
        if self.hotspot_modules:
            lines.extend(["", "Hotspot modules (increasing imports):"])
            for m in self.hotspot_modules[:5]:
                lines.append(f"  · {m}")
        return "\n".join(lines)


class CouplingMonitor:
    """Record coupling snapshots and surface architectural decay trends."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    async def _init(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()

    def snapshot_from_graph(self, graph, git_commit: str = "") -> CouplingSnapshot:
        """Compute a coupling snapshot from a ContextGraph instance."""
        g = graph.graph
        node_count = g.number_of_nodes()
        edge_count = g.number_of_edges()
        avg_coupling = edge_count / max(node_count, 1)

        try:
            import networkx as nx
            cycle_count = len(list(nx.simple_cycles(g)))
        except Exception:
            cycle_count = 0

        # Hub nodes: degree > mean + 1 stddev
        degrees = [d for _, d in g.degree()]
        if degrees:
            mean_deg = sum(degrees) / len(degrees)
            hub_count = sum(1 for d in degrees if d > mean_deg * 2)
        else:
            hub_count = 0

        # Find hotspot nodes (high out-degree = many imports)
        hotspots = sorted(
            [(node, g.out_degree(node)) for node in g.nodes()],
            key=lambda x: x[1],
            reverse=True,
        )[:5]
        hotspot_names = [h[0] for h in hotspots if h[1] > 0]

        return CouplingSnapshot(
            avg_coupling=round(avg_coupling, 4),
            edge_count=edge_count,
            node_count=node_count,
            hub_count=hub_count,
            cycle_count=cycle_count,
            hotspots=hotspot_names,
            git_commit=git_commit,
        )

    async def record(self, snapshot: CouplingSnapshot) -> None:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT INTO coupling_metrics
                   (timestamp, avg_coupling, edge_count, node_count,
                    hub_count, cycle_count, hotspots, git_commit)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    snapshot.timestamp,
                    snapshot.avg_coupling,
                    snapshot.edge_count,
                    snapshot.node_count,
                    snapshot.hub_count,
                    snapshot.cycle_count,
                    json.dumps(snapshot.hotspots),
                    snapshot.git_commit,
                ),
            )
            await db.commit()

    async def trend(self, days: int = 30) -> CouplingTrend:
        """Compute coupling trend over the last N days."""
        cutoff = time.time() - days * 86_400
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM coupling_metrics WHERE timestamp > ? ORDER BY timestamp ASC",
                (cutoff,),
            ) as cur:
                rows = await cur.fetchall()

        snapshots = [_row(dict(r)) for r in rows]
        if len(snapshots) < 2:
            return CouplingTrend(snapshots=snapshots)

        first = snapshots[0]
        latest = snapshots[-1]

        coupling_change = (
            (latest.avg_coupling - first.avg_coupling) / max(first.avg_coupling, 0.001)
        ) * 100
        hub_change = latest.hub_count - first.hub_count
        cycle_change = latest.cycle_count - first.cycle_count
        is_decaying = coupling_change > _DECAY_THRESHOLD * 100

        alert = ""
        if is_decaying:
            alert = (
                f"Coupling increased {coupling_change:.1f}% in {days} days. "
                f"Hubs: {first.hub_count} → {latest.hub_count}. "
                f"Cycles: {first.cycle_count} → {latest.cycle_count}. "
                "Review recent PRs for excessive cross-module imports."
            )

        hotspots = list(dict.fromkeys(
            h for s in snapshots[-3:] for h in s.hotspots
        ))

        return CouplingTrend(
            snapshots=snapshots,
            coupling_change_pct=round(coupling_change, 1),
            hub_change=hub_change,
            cycle_change=cycle_change,
            is_decaying=is_decaying,
            alert_message=alert,
            hotspot_modules=hotspots[:10],
        )


def _row(d: dict) -> CouplingSnapshot:
    return CouplingSnapshot(
        timestamp=d["timestamp"],
        avg_coupling=d["avg_coupling"],
        edge_count=d["edge_count"],
        node_count=d["node_count"],
        hub_count=d["hub_count"],
        cycle_count=d["cycle_count"],
        hotspots=json.loads(d["hotspots"]),
        git_commit=d["git_commit"],
    )
