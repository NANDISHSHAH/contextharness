import pytest

from contextpack.aggregator.aggregator import ContextAggregator
from contextpack.core.models import ContextSourceType, HarvestedContext, ProjectMap
from contextpack.harvester.harvester import ContextHarvester


@pytest.mark.asyncio
async def test_aggregator_formats_extra_instructions():
    sections = [
        HarvestedContext(
            source=ContextSourceType.CODE,
            title="Code Context",
            content="class Foo: pass",
        ),
        HarvestedContext(
            source=ContextSourceType.PRODUCT_GUIDELINES,
            title="Guidelines",
            content="",
            available=False,
            skip_reason="missing",
        ),
    ]
    agg = ContextAggregator().aggregate("auth flow", sections)
    assert "<extra_instructions>" in agg.extra_instructions
    assert "Code Context" in agg.extra_instructions
    assert any("guideline" in g.lower() for g in agg.guardrails)


@pytest.mark.asyncio
async def test_harvester_runs_fetchers(tmp_path):
    (tmp_path / "app.py").write_text("class AuthService:\n    def login(self): pass\n")
    guidelines = tmp_path / ".pr-review"
    guidelines.mkdir()
    (guidelines / "guidelines.md").write_text("# Auth\nUse OAuth2 for all login flows.")

    from contextpack.scanner.scanner import RepositoryScanner
    from contextpack.parsers.base import parse_project_files

    pmap = RepositoryScanner(tmp_path).scan()
    triples = []
    for f in pmap.files:
        if f.language:
            triples.append((f.path, f.language, (tmp_path / f.path).read_text()))
    pmap.entities = parse_project_files(str(tmp_path), triples)

    result = await ContextHarvester().harvest("authentication", pmap)
    assert len(result) >= 3
    code = next(s for s in result if s.source == ContextSourceType.CODE)
    assert code.available
    assert "AuthService" in code.content or "authentication" in code.content.lower()
