"""Agent lock table — dependency-level locks for multi-agent conflict detection."""
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
CREATE TABLE IF NOT EXISTS agent_locks (
    lock_id      TEXT PRIMARY KEY,
    agent_id     TEXT,
    files        TEXT,
    symbols      TEXT,
    acquired_at  REAL,
    expires_at   REAL,
    status       TEXT
);
"""

_DEFAULT_TTL = 3600  # 1 hour


class AgentLock(BaseModel):
    lock_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    agent_id: str
    files: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    acquired_at: float = Field(default_factory=time.time)
    expires_at: float = 0.0
    status: str = "active"  # "active" | "released" | "expired"

    def is_active(self) -> bool:
        return self.status == "active" and time.time() < self.expires_at


class ConflictReport(BaseModel):
    has_conflict: bool
    conflicting_files: list[str] = Field(default_factory=list)
    conflicting_symbols: list[str] = Field(default_factory=list)
    blocking_agent: str = ""
    blocking_lock_id: str = ""
    message: str = ""

    def to_text(self) -> str:
        if not self.has_conflict:
            return "✅ No conflicts — safe to proceed"
        lines = [
            "⚡ CONFLICT DETECTED",
            "",
            f"Agent `{self.blocking_agent}` (lock `{self.blocking_lock_id}`) holds:",
        ]
        for f in self.conflicting_files[:5]:
            lines.append(f"  · {f}")
        if self.conflicting_symbols:
            lines.append("Overlapping symbols:")
            for s in self.conflicting_symbols[:5]:
                lines.append(f"  · {s}")
        lines.extend([
            "",
            "Options:",
            "  A. Wait for the other agent to release its lock",
            "  B. Coordinate — split files between agents",
            "  C. Override (requires human approval)",
        ])
        return "\n".join(lines)


class AgentLockTable:
    """Manage per-agent dependency locks to prevent multi-agent conflicts."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    async def _init(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()

    async def acquire(
        self,
        agent_id: str,
        files: list[str],
        symbols: list[str] | None = None,
        ttl: int = _DEFAULT_TTL,
    ) -> AgentLock | ConflictReport:
        """Try to acquire a lock. Returns AgentLock on success, ConflictReport on conflict."""
        conflict = await self.check_conflicts(agent_id, files, symbols or [])
        if conflict.has_conflict:
            return conflict

        lock = AgentLock(
            agent_id=agent_id,
            files=files,
            symbols=symbols or [],
            acquired_at=time.time(),
            expires_at=time.time() + ttl,
        )
        await self._save(lock)
        logger.info("lock_acquired", agent=agent_id, lock_id=lock.lock_id)
        return lock

    async def release(self, lock_id: str) -> None:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "UPDATE agent_locks SET status = 'released' WHERE lock_id = ?",
                (lock_id,),
            )
            await db.commit()
        logger.debug("lock_released", lock_id=lock_id)

    async def check_conflicts(
        self,
        requesting_agent: str,
        files: list[str],
        symbols: list[str],
    ) -> ConflictReport:
        """Check if any active lock conflicts with the requested files/symbols."""
        active = await self._list_active()
        files_set = set(files)
        symbols_set = set(symbols)

        for lock in active:
            if lock.agent_id == requesting_agent:
                continue  # own lock
            conflict_files = files_set & set(lock.files)
            conflict_symbols = symbols_set & set(lock.symbols)
            if conflict_files or conflict_symbols:
                return ConflictReport(
                    has_conflict=True,
                    conflicting_files=sorted(conflict_files),
                    conflicting_symbols=sorted(conflict_symbols),
                    blocking_agent=lock.agent_id,
                    blocking_lock_id=lock.lock_id,
                    message=(
                        f"Agent {lock.agent_id} has an active lock on "
                        f"{len(conflict_files)} of the requested files"
                    ),
                )
        return ConflictReport(has_conflict=False)

    async def list_active(self) -> list[AgentLock]:
        return await self._list_active()

    async def _list_active(self) -> list[AgentLock]:
        await self._init()
        now = time.time()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM agent_locks WHERE status = 'active' AND expires_at > ?",
                (now,),
            ) as cur:
                rows = await cur.fetchall()
        return [_row(dict(r)) for r in rows]

    async def _save(self, lock: AgentLock) -> None:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO agent_locks
                   (lock_id, agent_id, files, symbols, acquired_at, expires_at, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    lock.lock_id,
                    lock.agent_id,
                    json.dumps(lock.files),
                    json.dumps(lock.symbols),
                    lock.acquired_at,
                    lock.expires_at,
                    lock.status,
                ),
            )
            await db.commit()


def _row(d: dict) -> AgentLock:
    return AgentLock(
        lock_id=d["lock_id"],
        agent_id=d["agent_id"],
        files=json.loads(d["files"]),
        symbols=json.loads(d["symbols"]),
        acquired_at=d["acquired_at"],
        expires_at=d["expires_at"],
        status=d["status"],
    )
