"""Multi-agent memory and coordination."""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any


class AgentMemory:
    """Per-agent local memory backed by SQLite.

    Each agent has its own ``agent_id`` and can store/recall facts.
    Facts are also visible to SharedMemory for cross-agent queries.
    """

    def __init__(self, agent_id: str, db_path: Path) -> None:
        self.agent_id = agent_id
        self._db_path = db_path

    async def store(
        self,
        content: str,
        fact_type: str = "observation",
        entity_ids: list[str] | None = None,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a fact. Returns the generated fact_id."""
        from contextpack.storage.sqlite import SQLiteStore

        fact_id = str(uuid.uuid4())[:12]
        store = SQLiteStore(self._db_path)
        await store.initialize()
        await store.upsert_agent_fact(
            {
                "fact_id": fact_id,
                "agent_id": self.agent_id,
                "fact_type": fact_type,
                "content": content,
                "entity_ids": entity_ids or [],
                "timestamp": time.time(),
                "confidence": confidence,
                "metadata": metadata or {},
            }
        )
        return fact_id

    async def recall(self, query: str = "", limit: int = 20) -> list[dict]:
        """Recall facts for this agent, optionally filtered by query text."""
        from contextpack.storage.sqlite import SQLiteStore

        store = SQLiteStore(self._db_path)
        await store.initialize()
        return await store.recall_agent_facts(query=query, agent_id=self.agent_id, limit=limit)

    async def store_decision(
        self,
        content: str,
        entity_ids: list[str] | None = None,
        confidence: float = 1.0,
    ) -> str:
        return await self.store(
            content, fact_type="decision", entity_ids=entity_ids, confidence=confidence
        )

    async def store_observation(
        self,
        content: str,
        entity_ids: list[str] | None = None,
        confidence: float = 1.0,
    ) -> str:
        return await self.store(
            content, fact_type="observation", entity_ids=entity_ids, confidence=confidence
        )

    async def store_constraint(self, content: str) -> str:
        return await self.store(content, fact_type="constraint")

    async def store_task_state(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        return await self.store(content, fact_type="task_state", metadata=metadata)


class SharedMemory:
    """Cross-agent shared fact store — readable by all agents.

    All agent facts land in the same SQLite table; SharedMemory queries
    across all agents rather than filtering by agent_id.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def for_agent(self, agent_id: str) -> AgentMemory:
        return AgentMemory(agent_id, self._db_path)

    async def recall_all(self, query: str = "", limit: int = 40) -> list[dict]:
        """Recall facts across all agents, optionally filtered by query text."""
        from contextpack.storage.sqlite import SQLiteStore

        store = SQLiteStore(self._db_path)
        await store.initialize()
        return await store.recall_agent_facts(query=query, limit=limit)

    async def recall_decisions(self, limit: int = 20) -> list[dict]:
        return await self.recall_all(query="", limit=limit * 3)

    async def format_for_prompt(self, query: str = "", limit: int = 10) -> str:
        """Return a markdown block suitable for injecting into an agent prompt."""
        facts = await self.recall_all(query=query, limit=limit)
        if not facts:
            return ""
        lines = ["## Shared agent memory"]
        for f in facts:
            agent = f.get("agent_id", "?")
            ftype = f.get("fact_type", "observation")
            content = f.get("content", "")
            lines.append(f"- [{agent}/{ftype}] {content}")
        return "\n".join(lines)


# ── Phase 6: Pre-Skill Engine ────────────────────────────────────────────────
from contextpack.skills.checkpoint import CheckpointResult, ReasoningCheckpoint
from contextpack.skills.composer import SKILL_DAG, SkillComposer, SkillResult
from contextpack.skills.enforcer import BlastRadiusEnforcer, DecompositionPlan, SubTask
from contextpack.skills.evidence import EvidenceBundle, EvidenceStore
from contextpack.skills.manifest import MatchCriteria, RequireSpec, SkillManifest, SkillPolicy
from contextpack.skills.router import SkillPlan, SkillRouter
from contextpack.skills.verifier import SkillVerifierLoop, VerifierResult

__all__ = [
    # Phase 5 (existing)
    "AgentMemory",
    "SharedMemory",
    # Phase 6 (new)
    "SkillManifest",
    "SkillPolicy",
    "MatchCriteria",
    "RequireSpec",
    "SkillRouter",
    "SkillPlan",
    "SkillComposer",
    "SkillResult",
    "SKILL_DAG",
    "BlastRadiusEnforcer",
    "DecompositionPlan",
    "SubTask",
    "ReasoningCheckpoint",
    "CheckpointResult",
    "EvidenceBundle",
    "EvidenceStore",
    "SkillVerifierLoop",
    "VerifierResult",
]
