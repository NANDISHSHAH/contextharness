"""Context debt tracker — per-module staleness scoring."""
from __future__ import annotations

import time
from pathlib import Path

import aiosqlite
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS context_debt (
    file_path       TEXT PRIMARY KEY,
    days_stale      REAL,
    churn_rate      REAL,
    hub_centrality  REAL,
    debt_score      REAL,
    last_computed   REAL,
    action          TEXT
);
"""

_ACTION_THRESHOLDS = {
    "CRITICAL": 0.85,
    "HIGH":     0.65,
    "MED":      0.40,
    "LOW":      0.00,
}


class DebtRecord(BaseModel):
    file_path: str
    days_stale: float = 0.0
    churn_rate: float = 0.0
    hub_centrality: float = 0.0
    debt_score: float = 0.0
    last_computed: float = Field(default_factory=time.time)
    action: str = "OK"

    def is_critical(self) -> bool:
        return self.debt_score >= _ACTION_THRESHOLDS["CRITICAL"]

    def to_row(self) -> str:
        bar = "█" * int(self.debt_score * 10)
        return (
            f"{self.file_path:<50s}  "
            f"{self.days_stale:>5.0f}d  "
            f"{self.debt_score:.2f}  "
            f"[{bar:<10}]  "
            f"{self.action}"
        )


class ContextDebtTracker:
    """Compute and store per-module context debt scores."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    async def _init(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()

    def compute_debt(
        self,
        file_path: str,
        last_indexed_ts: float,
        churn_count: int = 0,
        total_commits: int = 100,
        hub_centrality: float = 0.0,
    ) -> DebtRecord:
        """Compute debt score for one file.

        debt = 0.5 * days_stale_norm + 0.3 * churn_norm + 0.2 * hub_centrality
        """
        now = time.time()
        days_stale = max(0.0, (now - last_indexed_ts) / 86_400)
        # Normalise: 60 days → 1.0
        days_norm = min(1.0, days_stale / 60.0)
        churn_norm = min(1.0, churn_count / max(total_commits, 1))

        debt = (
            0.50 * days_norm
            + 0.30 * churn_norm
            + 0.20 * hub_centrality
        )
        debt = round(min(1.0, debt), 3)

        action = "OK"
        if debt >= _ACTION_THRESHOLDS["CRITICAL"]:
            action = "URGENT — re-index immediately"
        elif debt >= _ACTION_THRESHOLDS["HIGH"]:
            action = "Re-index"
        elif debt >= _ACTION_THRESHOLDS["MED"]:
            action = "Watch"

        return DebtRecord(
            file_path=file_path,
            days_stale=round(days_stale, 1),
            churn_rate=round(churn_norm, 3),
            hub_centrality=round(hub_centrality, 3),
            debt_score=debt,
            action=action,
        )

    async def upsert_batch(self, records: list[DebtRecord]) -> None:
        if not records:
            return
        await self._init()
        rows = [
            (
                r.file_path,
                r.days_stale,
                r.churn_rate,
                r.hub_centrality,
                r.debt_score,
                r.last_computed,
                r.action,
            )
            for r in records
        ]
        async with aiosqlite.connect(self._db_path) as db:
            await db.executemany(
                """INSERT OR REPLACE INTO context_debt
                   (file_path, days_stale, churn_rate, hub_centrality,
                    debt_score, last_computed, action)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
            await db.commit()

    async def list_all(self, limit: int = 200) -> list[DebtRecord]:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM context_debt ORDER BY debt_score DESC LIMIT ?", (limit,)
            ) as cur:
                rows = await cur.fetchall()
        return [_row(dict(r)) for r in rows]

    async def critical_modules(self) -> list[DebtRecord]:
        all_records = await self.list_all()
        return [r for r in all_records if r.is_critical()]

    def format_report(self, records: list[DebtRecord]) -> str:
        if not records:
            return "No debt records yet — run `context build` first."
        lines = [
            "## Context Debt Report",
            "",
            f"{'Module':<50s}  {'Stale':>5}  {'Debt':>4}  {'Bar':<12}  Action",
            "─" * 90,
        ]
        for r in records[:30]:
            lines.append(r.to_row())
        critical = [r for r in records if r.is_critical()]
        if critical:
            msg = (
                f"🚨 {len(critical)} module(s) at CRITICAL debt — "
                "re-index before using as context"
            )
            lines.extend(["", msg])
        return "\n".join(lines)


def _row(d: dict) -> DebtRecord:
    return DebtRecord(
        file_path=d["file_path"],
        days_stale=d["days_stale"],
        churn_rate=d["churn_rate"],
        hub_centrality=d["hub_centrality"],
        debt_score=d["debt_score"],
        last_computed=d["last_computed"],
        action=d["action"],
    )
