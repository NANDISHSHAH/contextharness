"""SQLite persistence for project memory."""

from __future__ import annotations

import json
from pathlib import Path

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    path TEXT PRIMARY KEY,
    language TEXT,
    size_bytes INTEGER,
    metadata TEXT
);
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    type TEXT,
    name TEXT,
    file_path TEXT,
    data TEXT
);
CREATE TABLE IF NOT EXISTS relationships (
    source TEXT,
    target TEXT,
    relation TEXT,
    weight REAL DEFAULT 1.0,
    PRIMARY KEY (source, target, relation)
);
CREATE TABLE IF NOT EXISTS summaries (
    entity_id TEXT PRIMARY KEY,
    summary TEXT
);
CREATE TABLE IF NOT EXISTS embeddings (
    chunk_id TEXT PRIMARY KEY,
    vector TEXT,
    metadata TEXT
);
CREATE TABLE IF NOT EXISTS workflows (
    name TEXT PRIMARY KEY,
    data TEXT
);
CREATE TABLE IF NOT EXISTS file_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    build_id TEXT,
    path TEXT,
    change_type TEXT,
    old_hash TEXT,
    new_hash TEXT,
    timestamp REAL,
    git_commit TEXT,
    data TEXT
);
CREATE TABLE IF NOT EXISTS agent_memory (
    fact_id TEXT PRIMARY KEY,
    agent_id TEXT,
    fact_type TEXT,
    content TEXT,
    entity_ids TEXT,
    timestamp REAL,
    confidence REAL,
    metadata TEXT
);
"""


class SQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    async def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA)
            await db.commit()

    async def upsert_entities_batch(
        self,
        rows: list[tuple[str, str, str, str, dict]],
    ) -> None:
        """Insert many entities in one connection (fast path for context build)."""
        if not rows:
            return
        payload = [
            (eid, etype, name, fpath, json.dumps(data))
            for eid, etype, name, fpath, data in rows
        ]
        async with aiosqlite.connect(self.db_path) as db:
            await db.executemany(
                (
                    "INSERT OR REPLACE INTO entities "
                    "(id, type, name, file_path, data) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                payload,
            )
            await db.commit()

    async def upsert_entity(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        file_path: str,
        data: dict,
    ) -> None:
        await self.upsert_entities_batch(
            [(entity_id, entity_type, name, file_path, data)]
        )

    async def upsert_embeddings_batch(
        self,
        rows: list[tuple[str, list[float], dict]],
    ) -> None:
        if not rows:
            return
        payload = [(cid, json.dumps(vec), json.dumps(meta)) for cid, vec, meta in rows]
        async with aiosqlite.connect(self.db_path) as db:
            await db.executemany(
                "INSERT OR REPLACE INTO embeddings (chunk_id, vector, metadata) VALUES (?, ?, ?)",
                payload,
            )
            await db.commit()

    async def upsert_embedding(self, chunk_id: str, vector: list[float], metadata: dict) -> None:
        await self.upsert_embeddings_batch([(chunk_id, vector, metadata)])

    async def list_entities(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM entities") as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def insert_file_changes(self, build_id: str, changes: list[dict]) -> None:
        if not changes:
            return
        rows = [
            (
                build_id,
                c["path"],
                c["change_type"],
                c.get("old_hash", ""),
                c.get("new_hash", ""),
                c.get("timestamp", 0.0),
                c.get("git_commit", ""),
                json.dumps(c),
            )
            for c in changes
        ]
        async with aiosqlite.connect(self.db_path) as db:
            await db.executemany(
                """INSERT INTO file_changes
                   (build_id, path, change_type, old_hash, new_hash, timestamp, git_commit, data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
            await db.commit()

    async def get_recent_changes(self, limit: int = 50) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM file_changes ORDER BY timestamp DESC LIMIT ?", (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def upsert_agent_fact(self, fact: dict) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                (
                    "INSERT OR REPLACE INTO agent_memory "
                    "(fact_id, agent_id, fact_type, content, "
                    "entity_ids, timestamp, confidence, metadata) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    fact["fact_id"],
                    fact.get("agent_id", "default"),
                    fact["fact_type"],
                    fact["content"],
                    json.dumps(fact.get("entity_ids", [])),
                    fact.get("timestamp", 0.0),
                    fact.get("confidence", 1.0),
                    json.dumps(fact.get("metadata", {})),
                ),
            )
            await db.commit()

    async def recall_agent_facts(
        self, query: str = "", agent_id: str = "", limit: int = 20
    ) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if agent_id:
                async with db.execute(
                    "SELECT * FROM agent_memory WHERE agent_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (agent_id, limit),
                ) as cursor:
                    rows = await cursor.fetchall()
            else:
                async with db.execute(
                    "SELECT * FROM agent_memory ORDER BY timestamp DESC LIMIT ?", (limit,)
                ) as cursor:
                    rows = await cursor.fetchall()
            results = [dict(r) for r in rows]
            if query:
                q = query.lower()
                results = [r for r in results if q in r.get("content", "").lower()]
            return results

    async def upsert_workflow(self, name: str, data: dict) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO workflows (name, data) VALUES (?, ?)",
                (name, json.dumps(data)),
            )
            await db.commit()

    async def list_workflows(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT name, data FROM workflows") as cursor:
                rows = await cursor.fetchall()
                return [{"name": r["name"], **json.loads(r["data"])} for r in rows]
