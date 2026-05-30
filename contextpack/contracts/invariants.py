"""Architecture invariant guard — declarative architectural rules from invariants.yml."""
from __future__ import annotations

import fnmatch
import time
from pathlib import Path

import aiosqlite
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS invariant_violations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    invariant_name  TEXT,
    file_path       TEXT,
    violation_type  TEXT,
    description     TEXT,
    severity        TEXT,
    timestamp       REAL,
    diff_hash       TEXT
);
"""


class ArchInvariant(BaseModel):
    name: str
    description: str = ""
    rule: str  # "no_direct_import" | "no_cycles" | "max_import_growth"
    from_patterns: list[str] = Field(default_factory=list)
    to_patterns: list[str] = Field(default_factory=list)
    scope: str = "**"
    max_growth: int | None = None
    severity: str = "error"

    model_config = {"populate_by_name": True}


class InvariantViolation(BaseModel):
    invariant_name: str
    file_path: str
    violation_type: str
    description: str
    severity: str = "error"
    timestamp: float = Field(default_factory=time.time)
    diff_hash: str = ""

    def to_text(self) -> str:
        icon = "❌" if self.severity == "error" else "⚠️"
        return f"{icon} [{self.invariant_name}] {self.description}"


class InvariantConfig(BaseModel):
    invariants: list[ArchInvariant] = Field(default_factory=list)

    @classmethod
    def load(cls, repo_path: Path) -> InvariantConfig:
        candidates = [
            repo_path / "invariants.yml",
            repo_path / ".contextpack" / "invariants.yml",
        ]
        for c in candidates:
            if c.exists():
                if yaml is None:
                    break
                data = yaml.safe_load(c.read_text())
                if data:
                    return cls.model_validate(data)
        return cls()


class InvariantGuard:
    """Check architectural invariants against import edges extracted from the graph."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    async def _init(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()

    def check(
        self,
        config: InvariantConfig,
        import_edges: list[tuple[str, str]],
        has_cycles: bool = False,
    ) -> list[InvariantViolation]:
        """Check all invariants. Returns list of violations (empty = all clear)."""
        violations: list[InvariantViolation] = []
        for inv in config.invariants:
            if inv.rule == "no_direct_import":
                violations += self._check_no_import(inv, import_edges)
            elif inv.rule == "no_cycles" and has_cycles:
                violations.append(
                    InvariantViolation(
                        invariant_name=inv.name,
                        file_path="(graph-wide)",
                        violation_type="no_cycles",
                        description=(
                            f"Circular dependency detected — "
                            f"violates '{inv.name}': {inv.description}"
                        ),
                        severity=inv.severity,
                    )
                )
        return violations

    def _check_no_import(
        self,
        inv: ArchInvariant,
        edges: list[tuple[str, str]],
    ) -> list[InvariantViolation]:
        violations: list[InvariantViolation] = []
        for src, tgt in edges:
            src_ok = any(fnmatch.fnmatch(src, pat) for pat in inv.from_patterns)
            tgt_ok = any(fnmatch.fnmatch(tgt, pat) for pat in inv.to_patterns)
            if src_ok and tgt_ok:
                violations.append(
                    InvariantViolation(
                        invariant_name=inv.name,
                        file_path=src,
                        violation_type="no_direct_import",
                        description=(
                            f"{src} directly imports {tgt} — "
                            f"violates '{inv.name}': {inv.description}"
                        ),
                        severity=inv.severity,
                    )
                )
        return violations

    async def save_violations(
        self,
        violations: list[InvariantViolation],
        diff_hash: str = "",
    ) -> None:
        if not violations:
            return
        await self._init()
        rows = [
            (
                v.invariant_name,
                v.file_path,
                v.violation_type,
                v.description,
                v.severity,
                v.timestamp,
                diff_hash,
            )
            for v in violations
        ]
        async with aiosqlite.connect(self._db_path) as db:
            await db.executemany(
                (
                    "INSERT INTO invariant_violations "
                    "(invariant_name, file_path, violation_type, "
                    "description, severity, timestamp, diff_hash) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)"
                ),
                rows,
            )
            await db.commit()

    async def recent_violations(self, limit: int = 30) -> list[dict]:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM invariant_violations ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ) as cur:
                rows = await cur.fetchall()
        return [dict(r) for r in rows]
