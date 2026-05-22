#!/usr/bin/env python3
"""
Phase 3 — Incremental builds & change tracking.

Shows:
  - incremental_build() re-parsing only changed files
  - ChangeSet with per-file entity deltas
  - recent_changes() querying the SQLite change log
  - memory module helpers used directly

Install:
  cd /path/to/contextharness
  uv sync && uv pip install -e .

Run:
  python examples/03_incremental_watch.py
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent / "sample_repo"


async def main() -> None:
    from contextpack import Project
    from contextpack.memory import format_changeset

    project = Project(REPO)

    # ── Step 1: full build (creates baseline hashes) ─────────────────────────
    print("=" * 60)
    print("Step 1: Full build — establishes file-hash baseline")
    print("=" * 60)
    await project.init()
    pmap, stats = await project.build()
    print(f"  Files indexed : {len(pmap.files)}")
    print(f"  Entities      : {len(pmap.entities)}")
    print(f"  Build time    : {stats.total_time:.2f}s")
    print()

    # ── Step 2: incremental build immediately after (no changes) ────────────
    print("=" * 60)
    print("Step 2: Incremental build — no files changed")
    print("=" * 60)
    t0 = time.perf_counter()
    pmap2, stats2, changeset = await project.incremental_build()
    elapsed = time.perf_counter() - t0
    print(f"  Summary       : {changeset.summary}")
    print(f"  Files changed : {changeset.total_changes}")
    print(f"  Elapsed       : {elapsed:.3f}s  (should be near-instant)")
    print()

    # ── Step 3: simulate a file change ──────────────────────────────────────
    print("=" * 60)
    print("Step 3: Simulate editing a source file, then incremental build")
    print("=" * 60)
    # Touch a file to change its hash
    target = REPO / "auth.py"
    if not target.exists():
        # Fallback to any .py file in sample_repo
        py_files = list(REPO.glob("**/*.py"))
        target = py_files[0] if py_files else None

    if target:
        original = target.read_text()
        target.write_text(original + "\n# incremental-build-test\n")
        print(f"  Touched: {target.relative_to(REPO)}")

        pmap3, stats3, changeset3 = await project.incremental_build()
        print(f"  Summary       : {changeset3.summary}")
        print(f"  Files changed : {changeset3.total_changes}")
        print()
        print(format_changeset(changeset3))
        print()

        for fc in changeset3.files_changed:
            print(f"  File : {fc.path}")
            print(f"  Type : {fc.change_type}")
            print(f"  Git  : {fc.git_commit or '(not a git repo)'}")
            if fc.entities_modified:
                print(f"  Modified entities : {fc.entities_modified}")
            if fc.entities_added:
                print(f"  Added entities    : {fc.entities_added}")
            if fc.entities_removed:
                print(f"  Removed entities  : {fc.entities_removed}")

        # Restore original
        target.write_text(original)
    else:
        print("  No .py files found in sample_repo — skipping touch simulation")
    print()

    # ── Step 4: query the change log ────────────────────────────────────────
    print("=" * 60)
    print("Step 4: Query the SQLite change log")
    print("=" * 60)
    recent = await project.recent_changes(limit=10)
    if recent:
        print(f"  {len(recent)} change record(s) in the log:")
        for row in recent[:5]:
            print(f"  [{row.get('build_id','?')}] {row.get('change_type','?'):10} {row.get('path','?')}")
    else:
        print("  No change log entries yet (run watch mode to populate).")
    print()

    # ── Step 5: memory module helpers directly ───────────────────────────────
    print("=" * 60)
    print("Step 5: Memory module helpers (low-level API)")
    print("=" * 60)
    from contextpack.memory import (
        compute_hashes,
        diff_hashes,
        load_hashes,
    )

    ctx_dir = project.context_dir
    stored = load_hashes(ctx_dir)
    current = compute_hashes(REPO, [r.path for r in pmap.files])
    added, modified, deleted = diff_hashes(stored, current)
    print(f"  Stored hash entries : {len(stored)}")
    print(f"  Current files       : {len(current)}")
    print(f"  Added               : {len(added)}")
    print(f"  Modified            : {len(modified)}")
    print(f"  Deleted             : {len(deleted)}")
    print()

    print("Done. Run `context watch <path>` to see incremental builds live.")


if __name__ == "__main__":
    if not REPO.exists():
        print(f"Missing sample repo: {REPO}", file=sys.stderr)
        sys.exit(1)
    asyncio.run(main())
