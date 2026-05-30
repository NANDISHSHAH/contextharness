"""Install portable harness artifacts into a target repository."""

from __future__ import annotations

import shutil
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent
_TEMPLATES = _PKG_ROOT / "templates"


def install_harness(target: Path, *, force: bool = False) -> list[str]:
    """Copy .cursor harness + .mcp.json templates. Returns paths written."""
    root = target.resolve()
    written: list[str] = []

    cursor_dst = root / ".cursor"
    cursor_dst.mkdir(parents=True, exist_ok=True)

    for name in ("hooks.json",):
        src = _TEMPLATES / "cursor" / name
        dst = cursor_dst / name
        if dst.exists() and not force:
            continue
        if src.is_file():
            shutil.copy2(src, dst)
            written.append(str(dst))

    hooks_src = _TEMPLATES / "cursor" / "hooks"
    hooks_dst = cursor_dst / "hooks"
    if hooks_src.is_dir():
        if hooks_dst.exists() and force:
            shutil.rmtree(hooks_dst)
        if not hooks_dst.exists():
            shutil.copytree(hooks_src, hooks_dst)
            written.append(str(hooks_dst))

    for sub in ("skills", "agents"):
        src_dir = _TEMPLATES / "cursor" / sub
        if not src_dir.is_dir():
            continue
        dst_dir = cursor_dst / sub
        dst_dir.mkdir(parents=True, exist_ok=True)
        for item in src_dir.rglob("*"):
            if item.is_dir():
                continue
            rel = item.relative_to(src_dir)
            out = dst_dir / rel
            if out.exists() and not force:
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, out)
            written.append(str(out))

    mcp_src = _TEMPLATES / "mcp.json"
    mcp_dst = root / ".mcp.json"
    if mcp_src.is_file() and (not mcp_dst.exists() or force):
        shutil.copy2(mcp_src, mcp_dst)
        written.append(str(mcp_dst))

    agents_src = _TEMPLATES / "AGENTS.md"
    agents_dst = root / "AGENTS.md"
    if agents_src.is_file() and (not agents_dst.exists() or force):
        shutil.copy2(agents_src, agents_dst)
        written.append(str(agents_dst))

    return written
