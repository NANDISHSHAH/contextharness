"""Evidence bundles — per-action auditable records of skill gates."""
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
CREATE TABLE IF NOT EXISTS evidence_bundles (
    action_id   TEXT PRIMARY KEY,
    agent_id    TEXT,
    timestamp   REAL,
    files_modified TEXT,
    skill_plan  TEXT,
    skill_results  TEXT,
    context_used   TEXT,
    diff_hash   TEXT,
    passed      INTEGER
);
"""


class EvidenceBundle(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: float = Field(default_factory=time.time)
    agent_id: str = "default"
    files_modified: list[str] = Field(default_factory=list)
    skill_plan: dict = Field(default_factory=dict)
    skill_results: list[dict] = Field(default_factory=list)
    context_used: dict = Field(default_factory=dict)
    diff_hash: str = ""

    @property
    def passed(self) -> bool:
        return all(r.get("passed", True) for r in self.skill_results)

    def to_markdown(self) -> str:
        import datetime

        dt = datetime.datetime.fromtimestamp(self.timestamp).isoformat(timespec="seconds")
        icon = "✅" if self.passed else "❌"
        lines = [
            f"## Evidence Bundle `{self.action_id}`  {icon}",
            f"**Agent:** `{self.agent_id}`  |  **Time:** {dt}",
            f"**Files:** {', '.join(self.files_modified) or '—'}",
            "",
            "### Skill Results",
        ]
        for r in self.skill_results:
            r_icon = "✅" if r.get("passed") else ("⏭ " if r.get("skipped") else "❌")
            ms = r.get("duration_ms", 0)
            lines.append(f"- {r_icon} `{r['skill']}` ({ms:.0f} ms)")
            for f in r.get("findings", [])[:3]:
                lines.append(f"  - {f}")
        if self.diff_hash:
            lines.append(f"\n**Diff hash:** `{self.diff_hash}`")
        return "\n".join(lines)


class EvidenceStore:
    """SQLite-backed store for evidence bundles."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    async def _init(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()

    async def store(self, bundle: EvidenceBundle) -> str:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO evidence_bundles
                   (action_id, agent_id, timestamp, files_modified, skill_plan,
                    skill_results, context_used, diff_hash, passed)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    bundle.action_id,
                    bundle.agent_id,
                    bundle.timestamp,
                    json.dumps(bundle.files_modified),
                    json.dumps(bundle.skill_plan),
                    json.dumps(bundle.skill_results),
                    json.dumps(bundle.context_used),
                    bundle.diff_hash,
                    1 if bundle.passed else 0,
                ),
            )
            await db.commit()
        logger.debug("evidence_stored", action_id=bundle.action_id)
        return bundle.action_id

    async def get(self, action_id: str) -> EvidenceBundle | None:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM evidence_bundles WHERE action_id = ?", (action_id,)
            ) as cur:
                row = await cur.fetchone()
        return self._row_to_bundle(dict(row)) if row else None

    async def list_recent(self, limit: int = 20) -> list[EvidenceBundle]:
        await self._init()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM evidence_bundles ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ) as cur:
                rows = await cur.fetchall()
        return [self._row_to_bundle(dict(r)) for r in rows]

    def _row_to_bundle(self, d: dict) -> EvidenceBundle:
        return EvidenceBundle(
            action_id=d["action_id"],
            agent_id=d["agent_id"],
            timestamp=d["timestamp"],
            files_modified=json.loads(d["files_modified"]),
            skill_plan=json.loads(d["skill_plan"]),
            skill_results=json.loads(d["skill_results"]),
            context_used=json.loads(d["context_used"]),
            diff_hash=d["diff_hash"],
        )
