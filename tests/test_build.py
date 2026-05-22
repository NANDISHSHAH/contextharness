import pytest

from contextpack import Project


@pytest.mark.asyncio
async def test_project_build_and_ask(tmp_path):
    (tmp_path / "auth.py").write_text(
        '''
"""Authentication module."""

class AuthMiddleware:
    def authenticate(self, token: str) -> bool:
        return bool(token)
'''
    )
    project = Project(tmp_path)
    await project.init()
    await project.build()
    answer = await project.ask("How authentication works?")
    assert "authentication" in answer.lower() or "AuthMiddleware" in answer


@pytest.mark.asyncio
async def test_buildstats_fields_are_consistent(tmp_path):
    """BuildStats file and embed counts must be self-consistent after build."""
    (tmp_path / "auth.py").write_text(
        "class Auth:\n    def login(self):\n        pass\n"
    )
    project = Project(tmp_path)
    await project.init()
    _, stats = await project.build()

    assert stats.files_scanned == stats.files_indexed + stats.files_skipped
    assert stats.embed_count + stats.store_only_count == stats.entities
    assert {"scan", "parse", "chunk", "embed", "store"}.issubset(stats.phase_times.keys())


@pytest.mark.asyncio
async def test_embed_cap_is_enforced(tmp_path):
    """embed_count must not exceed max_embed_entities when embed_hubs_first is False."""
    for i in range(5):
        (tmp_path / f"module{i}.py").write_text(
            f"class Cls{i}:\n    def run(self):\n        pass\n"
        )
    project = Project(tmp_path)
    await project.init()
    project._settings.embed_hubs_first = False
    project._settings.max_embed_entities = 2

    _, stats = await project.build()

    assert stats.embed_count <= 2


@pytest.mark.asyncio
async def test_hubs_always_embedded_when_enabled(tmp_path):
    """When embed_hubs_first is True, hub entities are always part of the embedded set."""
    for i in range(5):
        (tmp_path / f"module{i}.py").write_text(
            f"import os\nclass Cls{i}:\n    def run(self):\n        pass\n"
        )
    project = Project(tmp_path)
    await project.init()
    project._settings.embed_hubs_first = True
    project._settings.max_embed_entities = 2

    _, stats = await project.build()

    assert stats.hub_entities > 0
    # All detected hub entities must be present in the embedded set
    assert stats.embed_count >= stats.hub_entities
