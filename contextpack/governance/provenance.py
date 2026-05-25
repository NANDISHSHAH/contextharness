"""Context provenance chains — chain of custody per context chunk."""
from __future__ import annotations

import json
import time
from pathlib import Path

import aiosqlite
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS context_provenance (
    chunk_id        TEXT PRIMARY KEY,
    source          TEXT,
    source_type     TEXT,
    trust_tier      INTEGER,
    trust_score     REAL,
    file_hash       TEXT,
    git_commit      TEXT,
    git_author      TEXT,
    last_modified   REAL,
    test_coverage   REAL,
    ci_verified     INTEGER,
    last_ci_run     REAL
);
"""


class ProvenanceRecord(BaseModel):
    chunk_id: str
    source: str          # file path or URL
    source_type: str     # "code", "test", "docs", "jira", etc.
    trust_tier: int = 3
    trust_score: float = 0.7
    file_hash: str = ""
    git_commit: str = ""
    git_author: str = ""
    last_modified: float = Field(default_factory=time.time)
    test_coverage: float = 0.0
    ci_verified: bool = False
    last_ci_run: float = 0.0

    def to_inline_tag(self) -> str:
        """Compact provenance tag for inline display in context output."""
        import datetime
        mod_dt = datetime.datetime.fromtimestamp(self.last_modified).strftime("%Y-%m-%d")
        ci = "✓CI" if self.ci_verified else ""
        return f"[T{self.trust_tier}|{self.source_type}|{mod_dt}{ci}]"

    def days_since_modified(self) -> float:
        return (time.time() - self.last_modified) / 86_400


class ProvenanceChain:
    """Store and retrieve provenance records per context chunk."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    async def _init(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()

    async def record(self, prov: ProvenanceRecord) -> None:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO context_provenance
                   (chunk_id, source, source_type, trust_tier, trust_score,
                    file_hash, git_commit, git_author, last_modified,
                    test_coverage, ci_verified, last_ci_run)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    prov.chunk_id,
                    prov.source,
                    prov.source_type,
                    prov.trust_tier,
                    prov.trust_score,
                    prov.file_hash,
                    prov.git_commit,
                    prov.git_author,
                    prov.last_modified,
                    prov.test_coverage,
                    1 if prov.ci_verified else 0,
                    prov.last_ci_run,
                ),
            )
            await db.commit()

    async def record_batch(self, records: list[ProvenanceRecord]) -> None:
        if not records:
            return
        await self._init()
        rows = [
            (
                p.chunk_id, p.source, p.source_type, p.trust_tier, p.trust_score,
                p.file_hash, p.git_commit, p.git_author, p.last_modified,
                p.test_coverage, 1 if p.ci_verified else 0, p.last_ci_run,
            )
            for p in records
        ]
        async with aiosqlite.connect(self._db_path) as db:
            await db.executemany(
                """INSERT OR REPLACE INTO context_provenance
                   (chunk_id, source, source_type, trust_tier, trust_score,
                    file_hash, git_commit, git_author, last_modified,
                    test_coverage, ci_verified, last_ci_run)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
            await db.commit()

    async def get(self, chunk_id: str) -> ProvenanceRecord | None:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM context_provenance WHERE chunk_id = ?", (chunk_id,)
            ) as cur:
                row = await cur.fetchone()
        return _row(dict(row)) if row else None

    async def list_low_trust(self, max_tier: int = 4, limit: int = 50) -> list[ProvenanceRecord]:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM context_provenance WHERE trust_tier >= ? ORDER BY trust_score ASC LIMIT ?",
                (max_tier, limit),
            ) as cur:
                rows = await cur.fetchall()
        return [_row(dict(r)) for r in rows]


def _row(d: dict) -> ProvenanceRecord:
    return ProvenanceRecord(
        chunk_id=d["chunk_id"],
        source=d["source"],
        source_type=d["source_type"],
        trust_tier=d["trust_tier"],
        trust_score=d["trust_score"],
        file_hash=d["file_hash"],
        git_commit=d["git_commit"],
        git_author=d["git_author"],
        last_modified=d["last_modified"],
        test_coverage=d["test_coverage"],
        ci_verified=bool(d["ci_verified"]),
        last_ci_run=d["last_ci_run"],
    )
