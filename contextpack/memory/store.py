"""Temporal memory: file-hash tracking and git-diff change log."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contextpack.core.models import ChangeSet, FileChange


_HASH_FILE = "file_hashes.json"


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _git_head(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def load_hashes(ctx_dir: Path) -> dict[str, str]:
    p = ctx_dir / _HASH_FILE
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}
    return {}


def save_hashes(ctx_dir: Path, hashes: dict[str, str]) -> None:
    (ctx_dir / _HASH_FILE).write_text(json.dumps(hashes, indent=2))


def compute_hashes(root: Path, file_paths: list[str]) -> dict[str, str]:
    return {rel: _sha256(root / rel) for rel in file_paths}


def diff_hashes(
    old: dict[str, str], new: dict[str, str]
) -> tuple[list[str], list[str], list[str]]:
    """Return (added, modified, deleted) relative paths."""
    added = [p for p in new if p not in old]
    modified = [p for p in new if p in old and old[p] != new[p]]
    deleted = [p for p in old if p not in new]
    return added, modified, deleted


def build_changeset(
    root: Path,
    ctx_dir: Path,
    old_hashes: dict[str, str],
    new_hashes: dict[str, str],
    entity_delta: dict[str, tuple[list[str], list[str], list[str]]],
) -> "ChangeSet":
    from contextpack.core.models import ChangeSet, FileChange

    added, modified, deleted = diff_hashes(old_hashes, new_hashes)
    now = time.time()
    commit = _git_head(root)

    changes: list[FileChange] = []
    for path in added:
        ent = entity_delta.get(path, ([], [], []))
        changes.append(
            FileChange(
                path=path,
                change_type="added",
                new_hash=new_hashes.get(path, ""),
                timestamp=now,
                git_commit=commit,
                entities_added=ent[0],
                entities_removed=ent[1],
                entities_modified=ent[2],
            )
        )
    for path in modified:
        ent = entity_delta.get(path, ([], [], []))
        changes.append(
            FileChange(
                path=path,
                change_type="modified",
                old_hash=old_hashes.get(path, ""),
                new_hash=new_hashes.get(path, ""),
                timestamp=now,
                git_commit=commit,
                entities_added=ent[0],
                entities_removed=ent[1],
                entities_modified=ent[2],
            )
        )
    for path in deleted:
        changes.append(
            FileChange(
                path=path,
                change_type="deleted",
                old_hash=old_hashes.get(path, ""),
                timestamp=now,
                git_commit=commit,
            )
        )

    total = len(added) + len(modified) + len(deleted)
    summary_parts = []
    if added:
        summary_parts.append(f"{len(added)} added")
    if modified:
        summary_parts.append(f"{len(modified)} modified")
    if deleted:
        summary_parts.append(f"{len(deleted)} deleted")
    summary = ", ".join(summary_parts) if summary_parts else "no changes"
    if commit:
        summary = f"[{commit}] {summary}"

    return ChangeSet(
        build_id=str(uuid.uuid4())[:8],
        timestamp=now,
        git_commit=commit,
        files_changed=changes,
        summary=summary,
    )


def format_changeset(changeset: "ChangeSet") -> str:
    if not changeset.files_changed:
        return "No changes since last build."
    lines = [f"Changes ({changeset.summary}):"]
    for fc in changeset.files_changed:
        prefix = {"added": "+", "modified": "~", "deleted": "-"}.get(fc.change_type, "?")
        line = f"  {prefix} {fc.path}"
        details = []
        if fc.entities_added:
            details.append(f"+{len(fc.entities_added)} entities")
        if fc.entities_removed:
            details.append(f"-{len(fc.entities_removed)} entities")
        if fc.entities_modified:
            details.append(f"~{len(fc.entities_modified)} entities")
        if details:
            line += f"  [{', '.join(details)}]"
        lines.append(line)
    return "\n".join(lines)
