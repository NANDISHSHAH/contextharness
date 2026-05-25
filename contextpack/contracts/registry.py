"""Contract registry — SQLite-backed store for extracted contracts."""
from __future__ import annotations

import json
from pathlib import Path

import aiosqlite
import structlog

from contextpack.contracts.extractor import Contract

logger = structlog.get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS contracts (
    symbol_id    TEXT PRIMARY KEY,
    file_path    TEXT,
    symbol_name  TEXT,
    preconditions  TEXT,
    postconditions TEXT,
    invariants     TEXT,
    test_coverage  TEXT,
    last_verified  REAL,
    trust_score    REAL
);
"""


class ContractRegistry:
    """Persists and retrieves per-symbol contracts from SQLite."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    async def _init(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()

    async def upsert(self, contract: Contract) -> None:
        await self.upsert_batch([contract])

    async def upsert_batch(self, contracts: list[Contract]) -> None:
        if not contracts:
            return
        await self._init()
        rows = [
            (
                c.symbol_id,
                c.file_path,
                c.symbol_name,
                json.dumps(c.preconditions),
                json.dumps(c.postconditions),
                json.dumps(c.invariants),
                json.dumps(c.test_coverage),
                c.last_verified,
                c.trust_score,
            )
            for c in contracts
        ]
        async with aiosqlite.connect(self._db_path) as db:
            await db.executemany(
                """INSERT OR REPLACE INTO contracts
                   (symbol_id, file_path, symbol_name, preconditions, postconditions,
                    invariants, test_coverage, last_verified, trust_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
            await db.commit()
        logger.debug("contracts_upserted", count=len(contracts))

    async def get(self, symbol_id: str) -> Contract | None:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM contracts WHERE symbol_id = ?", (symbol_id,)
            ) as cur:
                row = await cur.fetchone()
        return _row(dict(row)) if row else None

    async def list_for_file(self, file_path: str) -> list[Contract]:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM contracts WHERE file_path = ?", (file_path,)
            ) as cur:
                rows = await cur.fetchall()
        return [_row(dict(r)) for r in rows]

    async def search(self, query: str, limit: int = 20) -> list[Contract]:
        await self._init()
        q = f"%{query}%"
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM contracts WHERE symbol_name LIKE ? OR file_path LIKE ? LIMIT ?",
                (q, q, limit),
            ) as cur:
                rows = await cur.fetchall()
        return [_row(dict(r)) for r in rows]

    async def list_all(self, limit: int = 500) -> list[Contract]:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM contracts ORDER BY trust_score DESC LIMIT ?", (limit,)
            ) as cur:
                rows = await cur.fetchall()
        return [_row(dict(r)) for r in rows]

    def format_for_context(self, contracts: list[Contract]) -> str:
        if not contracts:
            return ""
        lines = ["## Symbol Contracts (trust-verified)"]
        for c in contracts:
            lines.append("")
            lines.append(c.to_context_block())
        return "\n".join(lines)


def _row(d: dict) -> Contract:
    return Contract(
        symbol_id=d["symbol_id"],
        file_path=d["file_path"],
        symbol_name=d["symbol_name"],
        preconditions=json.loads(d["preconditions"]),
        postconditions=json.loads(d["postconditions"]),
        invariants=json.loads(d["invariants"]),
        test_coverage=json.loads(d["test_coverage"]),
        last_verified=d["last_verified"],
        trust_score=d["trust_score"],
    )
