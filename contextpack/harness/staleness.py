"""Detect when .contextpack index is missing or out of date."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from contextpack.core.config import get_settings


@dataclass(frozen=True)
class StalenessReport:
    is_stale: bool
    reason: str
    git_head: str | None = None
    indexed_head: str | None = None


def _git_head(repo: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if out.returncode == 0:
            return out.stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def check_staleness(repo: Path) -> StalenessReport:
    """Return whether the agent should run `context build`."""
    root = repo.resolve()
    ctx = get_settings().context_dir(root)
    map_path = ctx / "project_map.json"
    config_path = ctx / "config.json"

    if not map_path.is_file():
        return StalenessReport(
            is_stale=True,
            reason="No project index. Run: context build",
        )

    head = _git_head(root)
    indexed: str | None = None
    if config_path.is_file():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            indexed = data.get("git_head")
        except json.JSONDecodeError:
            indexed = None

    if head and indexed and head != indexed:
        return StalenessReport(
            is_stale=True,
            reason="Git HEAD changed since last build.",
            git_head=head,
            indexed_head=indexed,
        )

    if head and not indexed:
        return StalenessReport(
            is_stale=True,
            reason="Index has no git_head stamp. Rebuild recommended.",
            git_head=head,
        )

    return StalenessReport(
        is_stale=False,
        reason="Index present.",
        git_head=head,
        indexed_head=indexed,
    )


def stamp_build(repo: Path) -> None:
    """Record current git HEAD in .contextpack/config.json after build."""
    root = repo.resolve()
    ctx = get_settings().context_dir(root)
    config_path = ctx / "config.json"
    data: dict[str, str] = {}
    if config_path.is_file():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    head = _git_head(root)
    if head:
        data["git_head"] = head
    data["root"] = str(root)
    data["version"] = data.get("version", "0.1.0")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
