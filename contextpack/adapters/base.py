"""Agent runtime adapters."""

from __future__ import annotations

from typing import Protocol

from contextpack.core.models import AggregatedAgentContext, ContextPack


class AgentAdapter(Protocol):
    def inject(self, context: ContextPack | AggregatedAgentContext) -> dict: ...
