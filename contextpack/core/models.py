"""Pydantic domain models."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    MODULE = "module"
    API = "api"
    ROUTE = "route"
    WORKFLOW = "workflow"
    FILE = "file"
    SERVICE = "service"


class ContextSourceType(str, Enum):
    """Multi-source context types (meetup: domain-aware agent architecture)."""

    CODE = "code"
    PRODUCT_INTENT = "product_intent"
    PRODUCT_BEHAVIOUR = "product_behaviour"
    PRODUCT_GUIDELINES = "product_guidelines"
    GIT = "git"
    DOCS = "docs"


class ParsedEntity(BaseModel):
    type: EntityType | str
    name: str
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    dependencies: list[str] = Field(default_factory=list)
    imports: list[str] = Field(default_factory=list)
    summary: str = ""
    docstring: str = ""
    language: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class SymbolReference(BaseModel):
    name: str
    file_path: str
    line: int = 0
    kind: str = ""


class Relationship(BaseModel):
    source: str
    target: str
    relation: str
    weight: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class Workflow(BaseModel):
    name: str
    steps: list[str] = Field(default_factory=list)
    summary: str = ""
    entities: list[str] = Field(default_factory=list)


class FileRecord(BaseModel):
    path: str
    language: str = ""
    size_bytes: int = 0
    framework_hints: list[str] = Field(default_factory=list)


class ProjectMap(BaseModel):
    root: str
    files: list[FileRecord] = Field(default_factory=list)
    languages: dict[str, int] = Field(default_factory=dict)
    frameworks: list[str] = Field(default_factory=list)
    entities: list[ParsedEntity] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SemanticChunk(BaseModel):
    type: str
    name: str
    file_path: str = ""
    summary: str = ""
    content: str = ""
    dependencies: list[str] = Field(default_factory=list)
    token_estimate: int = 0


class ContextPack(BaseModel):
    """Compiled, token-budgeted context for an LLM."""

    query: str = ""
    summaries: list[str] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    workflows: list[Workflow] = Field(default_factory=list)
    chunks: list[SemanticChunk] = Field(default_factory=list)
    graph_excerpt: str = ""
    token_estimate: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class HarvestedContext(BaseModel):
    """Single fetcher output — one slice of complete agent context."""

    source: ContextSourceType
    title: str
    content: str
    structured: dict[str, Any] = Field(default_factory=dict)
    available: bool = True
    skip_reason: str | None = None


class AggregatedAgentContext(BaseModel):
    """
    Complete agent-ready context (meetup: Context Aggregator).

    Merges code, product intent, behaviour, and guidelines into
    structured sections suitable for <extra_instructions> injection.
    """

    query: str = ""
    sections: list[HarvestedContext] = Field(default_factory=list)
    extra_instructions: str = ""
    compiled_pack: ContextPack | None = None
    guardrails: list[str] = Field(default_factory=list)

    def to_agent_prompt_block(self) -> str:
        return self.extra_instructions or self._build_default_block()

    def _build_default_block(self) -> str:
        parts: list[str] = ["<extra_instructions>"]
        for section in self.sections:
            if not section.available:
                continue
            parts.append(f"## {section.title}")
            parts.append(section.content)
        parts.append("</extra_instructions>")
        return "\n\n".join(parts)
