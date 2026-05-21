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
"""


class SQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    async def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA)
            await db.commit()

    async def upsert_entity(self, entity_id: str, entity_type: str, name: str, file_path: str, data: dict) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO entities (id, type, name, file_path, data) VALUES (?, ?, ?, ?, ?)",
                (entity_id, entity_type, name, file_path, json.dumps(data)),
            )
            await db.commit()

    async def upsert_embedding(self, chunk_id: str, vector: list[float], metadata: dict) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO embeddings (chunk_id, vector, metadata) VALUES (?, ?, ?)",
                (chunk_id, json.dumps(vector), json.dumps(metadata)),
            )
            await db.commit()

    async def list_entities(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM entities") as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
