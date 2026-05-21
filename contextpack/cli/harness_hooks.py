"""Cursor hook entrypoints (stdin JSON → stdout JSON)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from contextpack.harness.orientation import build_orientation
from contextpack.harness.validate import validate_harness_docs


def _read_input() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload))
    sys.stdout.flush()


def session_start(repo: Path | None = None) -> int:
    root = (repo or Path.cwd()).resolve()
    hook_in = _read_input()
    query = str(hook_in.get("user_message", "") or hook_in.get("prompt", "") or "architecture")[:200]
    context = build_orientation(root, query=query or "architecture")
    _emit({"additional_context": context})
    return 0


def stop_validate(repo: Path | None = None) -> int:
    root = (repo or Path.cwd()).resolve()
    validation = validate_harness_docs(root)
    if validation.ok and not validation.suggestions:
        _emit({})
        return 0
    msg = validation.to_markdown()
    if validation.suggestions:
        msg += "\n\nUpdate AGENTS.md if these hubs are business-critical."
    _emit({"followup_message": msg})
    return 0


def main() -> None:
    if len(sys.argv) < 2:
        sys.stderr.write("usage: harness_hooks <session-start|stop-validate> [repo]\n")
        sys.exit(1)
    cmd = sys.argv[1]
    repo = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path.cwd()
    if cmd == "session-start":
        sys.exit(session_start(repo))
    if cmd == "stop-validate":
        sys.exit(stop_validate(repo))
    sys.stderr.write(f"unknown command: {cmd}\n")
    sys.exit(1)


if __name__ == "__main__":
    main()
