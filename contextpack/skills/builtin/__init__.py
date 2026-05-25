"""Built-in skill runner registry."""
from __future__ import annotations

from contextpack.skills.builtin.lint import LintSkill
from contextpack.skills.builtin.type_check import TypeCheckSkill
from contextpack.skills.builtin.security_scan import SecurityScanSkill
from contextpack.skills.builtin.docs_link_check import DocsLinkCheckSkill

_REGISTRY: dict[str, object] = {}


def _register() -> None:
    for cls in [LintSkill, TypeCheckSkill, SecurityScanSkill, DocsLinkCheckSkill]:
        inst = cls()
        _REGISTRY[inst.name] = inst  # type: ignore[attr-defined]


_register()


def get_runner(skill_name: str):
    """Return a skill runner instance by name, or None if not registered."""
    return _REGISTRY.get(skill_name)


def list_runners() -> list[str]:
    """Return names of all registered built-in skills."""
    return list(_REGISTRY.keys())
