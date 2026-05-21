"""Product intent from Jira (meetup: ticket AC, descriptions)."""

from __future__ import annotations

import re

import httpx
import structlog

from contextpack.core.config import get_settings
from contextpack.core.models import ContextSourceType, HarvestedContext, ProjectMap

logger = structlog.get_logger(__name__)

TICKET_RE = re.compile(r"([A-Z][A-Z0-9]+-\d+)")


class JiraIntentFetcher:
    source_type = ContextSourceType.PRODUCT_INTENT

    async def fetch(self, query: str, project_map: ProjectMap) -> HarvestedContext:
        settings = get_settings()
        if not all([settings.jira_base_url, settings.jira_email, settings.jira_api_token]):
            return HarvestedContext(
                source=ContextSourceType.PRODUCT_INTENT,
                title="Product Intent (Jira)",
                content="",
                available=False,
                skip_reason="Jira credentials not configured.",
            )

        ticket = _extract_ticket(project_map.metadata.get("branch_name", ""), query)
        if not ticket:
            return HarvestedContext(
                source=ContextSourceType.PRODUCT_INTENT,
                title="Product Intent (Jira)",
                content="",
                available=False,
                skip_reason="No Jira ticket id in branch name or query.",
            )

        try:
            issue = await _fetch_issue(
                settings.jira_base_url or "",
                settings.jira_email or "",
                settings.jira_api_token or "",
                ticket,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("jira_fetch_failed", ticket=ticket, error=str(exc))
            return HarvestedContext(
                source=ContextSourceType.PRODUCT_INTENT,
                title="Product Intent (Jira)",
                content="",
                available=False,
                skip_reason=f"Jira fetch failed: {exc}",
            )

        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        description = fields.get("description") or ""
        if isinstance(description, dict):
            description = str(description)

        ac = fields.get("customfield_acceptance_criteria") or fields.get("acceptanceCriteria") or ""
        content = "\n".join(
            [
                f"**Ticket:** {ticket}",
                f"**Summary:** {summary}",
                "",
                "**Description:**",
                str(description)[:4000],
                "",
                "**Acceptance Criteria:**",
                str(ac)[:4000] if ac else "_Not provided in ticket_",
            ]
        )
        return HarvestedContext(
            source=ContextSourceType.PRODUCT_INTENT,
            title="Product Intent (Jira)",
            content=content,
            structured={"ticket": ticket, "key": issue.get("key")},
        )


def _extract_ticket(branch: str, query: str) -> str | None:
    for text in (branch, query):
        m = TICKET_RE.search(text)
        if m:
            return m.group(1)
    return None


async def _fetch_issue(base_url: str, email: str, token: str, ticket: str) -> dict:
    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{ticket}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, auth=(email, token))
        resp.raise_for_status()
        return resp.json()
