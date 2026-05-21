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
