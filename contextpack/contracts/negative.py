"""Negative context index — anti-patterns the agent should never introduce."""
from __future__ import annotations

import fnmatch
import json
import re
import time
from pathlib import Path

import aiosqlite
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS negative_patterns (
    pattern_id  TEXT PRIMARY KEY,
    pattern     TEXT,
    reason      TEXT,
    severity    TEXT,
    scope       TEXT,
    remediation TEXT,
    refs        TEXT,
    is_regex    INTEGER,
    created_at  REAL
);
"""


class NegativePattern(BaseModel):
    pattern_id: str
    pattern: str          # substring or regex
    reason: str
    severity: str = "warning"   # "error" | "warning"
    scope: str = "**"           # file glob
    remediation: str = ""
    references: list[str] = Field(default_factory=list)
    is_regex: bool = False
    created_at: float = Field(default_factory=time.time)

    def matches(self, code: str, file_path: str) -> bool:
        if not fnmatch.fnmatch(file_path, self.scope):
            return False
        if self.is_regex:
            return bool(re.search(self.pattern, code))
        return self.pattern in code

    def to_context_block(self) -> str:
        icon = "❌" if self.severity == "error" else "⚠️"
        lines = [f"{icon} **Anti-pattern:** `{self.pattern}`", f"   **Why:** {self.reason}"]
        if self.remediation:
            lines.append(f"   **Instead use:** {self.remediation}")
        if self.references:
            lines.append(f"   **See:** {', '.join(self.references)}")
        return "\n".join(lines)


class NegativeContextIndex:
    """Store and query anti-patterns; surface relevant ones as agent context."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    async def _init(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()

    async def add(self, pattern: NegativePattern) -> None:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO negative_patterns
                   (pattern_id, pattern, reason, severity, scope, remediation,
                    refs, is_regex, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    pattern.pattern_id,
                    pattern.pattern,
                    pattern.reason,
                    pattern.severity,
                    pattern.scope,
                    pattern.remediation,
                    json.dumps(pattern.references),  # stored as refs
                    1 if pattern.is_regex else 0,
                    pattern.created_at,
                ),
            )
            await db.commit()

    async def list_all(self) -> list[NegativePattern]:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM negative_patterns") as cur:
                rows = await cur.fetchall()
        return [_row(dict(r)) for r in rows]

    async def scan_code(self, code: str, file_path: str) -> list[NegativePattern]:
        """Return all anti-patterns found in the given code snippet."""
        patterns = await self.list_all()
        return [p for p in patterns if p.matches(code, file_path)]

    def format_findings(self, patterns: list[NegativePattern]) -> str:
        if not patterns:
            return ""
        lines = ["## ⚠️ Anti-pattern Warnings — Review Before Proceeding"]
        for p in patterns:
            lines.append("")
            lines.append(p.to_context_block())
        return "\n".join(lines)


def _row(d: dict) -> NegativePattern:
    return NegativePattern(
        pattern_id=d["pattern_id"],
        pattern=d["pattern"],
        reason=d["reason"],
        severity=d["severity"],
        scope=d["scope"],
        remediation=d["remediation"],
        references=json.loads(d["refs"]),
        is_regex=bool(d["is_regex"]),
        created_at=d["created_at"],
    )
