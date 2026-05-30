"""Failure pattern memory — classify and store recurring skill failures."""
from __future__ import annotations

import time
from pathlib import Path

import aiosqlite
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS failure_patterns (
    pattern_id      TEXT PRIMARY KEY,
    skill           TEXT,
    file_pattern    TEXT,
    failure_class   TEXT,
    frequency       INTEGER DEFAULT 1,
    first_seen      REAL,
    last_seen       REAL,
    remediation_hint TEXT,
    auto_briefing   INTEGER DEFAULT 0,
    example_output  TEXT
);
"""

# Threshold: surface a pattern proactively after this many occurrences
_PROACTIVE_THRESHOLD = 3


class FailurePattern(BaseModel):
    pattern_id: str
    skill: str
    file_pattern: str       # glob pattern of files where this failure appears
    failure_class: str      # e.g. "missing_rate_limit", "unsafe_jwt_decode"
    frequency: int = 1
    first_seen: float = Field(default_factory=time.time)
    last_seen: float = Field(default_factory=time.time)
    remediation_hint: str = ""
    auto_briefing: bool = False
    example_output: str = ""

    def is_proactive(self) -> bool:
        return self.frequency >= _PROACTIVE_THRESHOLD

    def to_briefing(self) -> str:
        lines = [
            f"⚠️ PATTERN: `{self.failure_class}` (seen {self.frequency}× in last 30 days)",
            f"   Skill: `{self.skill}`  |  Files: `{self.file_pattern}`",
        ]
        if self.remediation_hint:
            lines.append(f"   Hint: {self.remediation_hint}")
        return "\n".join(lines)


class FailurePatternStore:
    """Persist and retrieve failure patterns from SQLite."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    async def _init(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()

    async def record(
        self,
        skill: str,
        file_path: str,
        failure_output: str,
        remediation_hint: str = "",
    ) -> FailurePattern:
        """Record a skill failure and update/create its pattern."""
        failure_class = _classify(skill, failure_output)
        file_pattern = _file_to_pattern(file_path)
        pattern_id = f"{skill}::{file_pattern}::{failure_class}"

        await self._init()
        existing = await self._get(pattern_id)

        if existing:
            updated = FailurePattern(
                **{
                    **existing.model_dump(),
                    "frequency": existing.frequency + 1,
                    "last_seen": time.time(),
                    "auto_briefing": (existing.frequency + 1) >= _PROACTIVE_THRESHOLD,
                    "example_output": failure_output[:500],
                }
            )
            await self._upsert(updated)
            return updated

        new_pattern = FailurePattern(
            pattern_id=pattern_id,
            skill=skill,
            file_pattern=file_pattern,
            failure_class=failure_class,
            frequency=1,
            remediation_hint=remediation_hint,
            example_output=failure_output[:500],
        )
        await self._upsert(new_pattern)
        return new_pattern

    async def list_proactive(self, file_path: str) -> list[FailurePattern]:
        """Return patterns that should be proactively shown for the given file."""
        import fnmatch

        all_patterns = await self._list_all()
        return [
            p
            for p in all_patterns
            if p.is_proactive() and fnmatch.fnmatch(file_path, p.file_pattern)
        ]

    async def list_all(self, limit: int = 100) -> list[FailurePattern]:
        return await self._list_all(limit=limit)

    async def _list_all(self, limit: int = 100) -> list[FailurePattern]:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM failure_patterns ORDER BY frequency DESC LIMIT ?", (limit,)
            ) as cur:
                rows = await cur.fetchall()
        return [_row(dict(r)) for r in rows]

    async def _get(self, pattern_id: str) -> FailurePattern | None:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM failure_patterns WHERE pattern_id = ?", (pattern_id,)
            ) as cur:
                row = await cur.fetchone()
        return _row(dict(row)) if row else None

    async def _upsert(self, p: FailurePattern) -> None:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO failure_patterns
                   (pattern_id, skill, file_pattern, failure_class, frequency,
                    first_seen, last_seen, remediation_hint, auto_briefing, example_output)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    p.pattern_id, p.skill, p.file_pattern, p.failure_class,
                    p.frequency, p.first_seen, p.last_seen,
                    p.remediation_hint, 1 if p.auto_briefing else 0,
                    p.example_output,
                ),
            )
            await db.commit()


def _classify(skill: str, output: str) -> str:
    """Heuristic failure classification from skill output."""
    out = output.lower()
    if skill == "security_scan":
        if "jwt" in out:
            return "unsafe_jwt_decode"
        if "sql" in out and "inject" in out:
            return "sql_injection_risk"
        if "rate" in out and "limit" in out:
            return "missing_rate_limit"
        if "password" in out:
            return "hardcoded_secret"
        return "security_violation"
    if skill == "type_check":
        if "missing" in out and "return" in out:
            return "missing_return_type"
        if "incompatible" in out:
            return "type_incompatibility"
        return "type_error"
    if skill == "lint":
        if "unused import" in out or "f401" in out:
            return "unused_import"
        if "line too long" in out or "e501" in out:
            return "line_too_long"
        return "lint_violation"
    if skill == "docs_link_check":
        return "broken_doc_link"
    return f"{skill}_failure"


def _file_to_pattern(file_path: str) -> str:
    """Convert a specific file path to a glob pattern for the module."""
    parts = Path(file_path).parts
    if len(parts) >= 2:
        return str(Path(*parts[:2]) / "**")
    return "**"


def _row(d: dict) -> FailurePattern:
    return FailurePattern(
        pattern_id=d["pattern_id"],
        skill=d["skill"],
        file_pattern=d["file_pattern"],
        failure_class=d["failure_class"],
        frequency=d["frequency"],
        first_seen=d["first_seen"],
        last_seen=d["last_seen"],
        remediation_hint=d["remediation_hint"],
        auto_briefing=bool(d["auto_briefing"]),
        example_output=d["example_output"],
    )
