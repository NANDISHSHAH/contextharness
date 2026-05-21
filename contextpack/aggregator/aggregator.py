"""Context Aggregator — structured <extra_instructions> for agents."""

from __future__ import annotations

from contextpack.core.models import AggregatedAgentContext, ContextPack, HarvestedContext


class ContextAggregator:
    """
    Merges parallel fetcher outputs into one agent prompt block.

    Matches meetup pattern: distinct headings under extra_instructions,
    graceful skips when a source is missing.
    """

    SECTION_ORDER = [
        "product_intent",
        "product_guidelines",
        "product_behaviour",
        "code",
        "docs",
        "git",
    ]

    def aggregate(
        self,
        query: str,
        sections: list[HarvestedContext],
        *,
        compiled_pack: ContextPack | None = None,
    ) -> AggregatedAgentContext:
        ordered = sorted(
            sections,
            key=lambda s: (
                self.SECTION_ORDER.index(s.source.value)
                if s.source.value in self.SECTION_ORDER
                else 99
            ),
        )
        guardrails = _build_guardrails(ordered)
        block = self._format_extra_instructions(query, ordered, compiled_pack)

        return AggregatedAgentContext(
            query=query,
            sections=ordered,
            extra_instructions=block,
            compiled_pack=compiled_pack,
            guardrails=guardrails,
        )

    def _format_extra_instructions(
        self,
        query: str,
        sections: list[HarvestedContext],
        compiled_pack: ContextPack | None,
    ) -> str:
        parts = [
            "<extra_instructions>",
            f"# Agent Context Pack",
            f"**User query:** {query}",
            "",
        ]
        for section in sections:
            if not section.available:
                parts.append(f"## {section.title}")
                parts.append(f"_Skipped: {section.skip_reason}_")
                parts.append("")
                continue
            parts.append(f"## {section.title}")
            parts.append(section.content.strip())
            parts.append("")

        if compiled_pack and compiled_pack.summaries:
            parts.append("## Compiled Code Memory")
            for s in compiled_pack.summaries[:20]:
                parts.append(f"- {s}")
            if compiled_pack.graph_excerpt:
                parts.append("")
                parts.append(compiled_pack.graph_excerpt)

        parts.append("</extra_instructions>")
        return "\n".join(parts)


def _build_guardrails(sections: list[HarvestedContext]) -> list[str]:
    """Surface mismatches / missing data (meetup: example guardrails)."""
    notes: list[str] = []
    intent = next((s for s in sections if s.source.value == "product_intent"), None)
    guidelines = next((s for s in sections if s.source.value == "product_guidelines"), None)
    behaviour = next((s for s in sections if s.source.value == "product_behaviour"), None)

    if intent and not intent.available:
        notes.append("Product intent unavailable — verify branch links to a Jira ticket.")
    if guidelines and not guidelines.available:
        notes.append("Team guidelines missing — domain convention checks skipped.")
    if behaviour and not behaviour.available:
        notes.append("Test suite behaviour not loaded — behavioural consistency checks limited.")
    return notes
