"""Orchestrates parallel context fetchers into complete agent context."""

from __future__ import annotations

import asyncio

import structlog

from contextpack.aggregator.aggregator import ContextAggregator
from contextpack.core.models import AggregatedAgentContext, HarvestedContext, ProjectMap
from contextpack.core.protocols import ContextFetcher
from contextpack.harvester.fetchers.behaviour import TestBehaviourFetcher
from contextpack.harvester.fetchers.code import CodeContextFetcher
from contextpack.harvester.fetchers.guidelines import ProductGuidelinesFetcher
from contextpack.harvester.fetchers.jira import JiraIntentFetcher

logger = structlog.get_logger(__name__)


class ContextHarvester:
    """
    Domain-aware context harvester.

    Inspired by meetup PR-review architecture: run fetchers in parallel,
    tolerate missing sources, and aggregate into agent-ready memory.
    """

    def __init__(
        self,
        fetchers: list[ContextFetcher] | None = None,
        aggregator: ContextAggregator | None = None,
    ) -> None:
        self._fetchers: list[ContextFetcher] = fetchers or [
            CodeContextFetcher(),
            ProductGuidelinesFetcher(),
            TestBehaviourFetcher(),
            JiraIntentFetcher(),
        ]
        self._aggregator = aggregator or ContextAggregator()

    async def harvest(
        self,
        query: str,
        project_map: ProjectMap,
        *,
        branch_name: str | None = None,
    ) -> list[HarvestedContext]:
        if branch_name:
            project_map.metadata["branch_name"] = branch_name

        async def _run(f: ContextFetcher) -> HarvestedContext:
            try:
                return await f.fetch(query, project_map)
            except Exception as exc:  # noqa: BLE001 — graceful degradation per meetup
                logger.warning("fetcher_failed", source=f.source_type, error=str(exc))
                from contextpack.core.models import ContextSourceType

                src = (
                    f.source_type
                    if isinstance(f.source_type, ContextSourceType)
                    else ContextSourceType.CODE
                )
                return HarvestedContext(
                    source=src,
                    title=f"Unavailable: {getattr(f, 'source_type', 'unknown')}",
                    content="",
                    available=False,
                    skip_reason=str(exc),
                )

        return await asyncio.gather(*[_run(f) for f in self._fetchers])

    async def harvest_and_aggregate(
        self,
        query: str,
        project_map: ProjectMap,
        *,
        branch_name: str | None = None,
        compiled_pack=None,
    ) -> AggregatedAgentContext:
        sections = await self.harvest(query, project_map, branch_name=branch_name)
        return self._aggregator.aggregate(
            query=query,
            sections=sections,
            compiled_pack=compiled_pack,
        )
