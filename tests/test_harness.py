"""Context Harness unit tests."""

from pathlib import Path

import pytest

from contextpack.core.models import EntityType, ParsedEntity
from contextpack.graph.engine import ContextGraph
from contextpack.harness.orientation import build_orientation
from contextpack.harness.staleness import check_staleness, stamp_build
from contextpack.harness.validate import validate_harness_docs


def test_hub_entities():
    entities = [
        ParsedEntity(type=EntityType.CLASS, name="Hub", file_path="hub.py", imports=["dep"]),
        ParsedEntity(type=EntityType.FUNCTION, name="leaf", file_path="leaf.py"),
    ]
    g = ContextGraph.from_entities(entities)
    hubs = g.hub_entities(5)
    assert hubs
    assert hubs[0][0] == "Hub"


def test_find_symbol():
    entities = [
        ParsedEntity(type=EntityType.CLASS, name="AuthService", file_path="auth.py"),
    ]
    g = ContextGraph.from_entities(entities)
    hits = g.find_symbol("auth")
    assert hits
    assert hits[0]["name"] == "AuthService"


def test_staleness_missing_index(tmp_path: Path):
    report = check_staleness(tmp_path)
    assert report.is_stale
    assert "build" in report.reason.lower()


def test_validate_without_index(tmp_path: Path):
    result = validate_harness_docs(tmp_path)
    assert not result.ok


def test_orientation_without_build(tmp_path: Path):
    text = build_orientation(tmp_path)
    assert "Context Harness" in text
    assert "build" in text.lower()


def test_stamp_build(tmp_path: Path):
    ctx = tmp_path / ".contextpack"
    ctx.mkdir(parents=True)
    (ctx / "project_map.json").write_text('{"root": ".", "files": [], "entities": []}')
    stamp_build(tmp_path)
    assert (ctx / "config.json").is_file()


def test_agents_md_validate_on_repo():
    root = Path(__file__).resolve().parents[1]
    if not (root / ".contextpack" / "project_map.json").is_file():
        pytest.skip("run context build first for full validate test")
    result = validate_harness_docs(root)
    assert result.warnings is not None
