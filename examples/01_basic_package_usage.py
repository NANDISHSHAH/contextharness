#!/usr/bin/env python3
"""
Basic ContextPack usage as an installed package.

Install:
  cd /path/to/contextharness
  uv sync && uv pip install -e .

Run:
  python examples/01_basic_package_usage.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Sample repo ships with the project
REPO = Path(__file__).resolve().parent / "sample_repo"


async def main() -> None:
    from contextpack import Project
    from contextpack.adapters import CursorAdapter

    project = Project(REPO)

    print("1) Initialize workspace (.contextpack/)")
    await project.init()

    print("2) Build index (scan → parse → graph → embed)")
    pmap, stats = await project.build()
    print(f"   Files: {len(pmap.files)}, entities: {len(pmap.entities)}, skipped: {pmap.files_skipped}")
    print(f"   Embedded: {stats.embed_count}  store-only: {stats.store_only_count}  total: {stats.total_time:.2f}s")

    print("3) Harvest complete agent context (code + guidelines + tests)")
    agent_ctx = await project.harvest("How does authentication work?")
    print(f"   Sections: {len(agent_ctx.sections)}")
    print(f"   Guardrails: {agent_ctx.guardrails}")

    print("4) Inject into Cursor / any agent runtime")
    payload = CursorAdapter().inject(agent_ctx)
    print(f"   Payload keys: {list(payload.keys())}")
    print(f"   Context preview ({min(400, len(payload['extra_instructions']))} chars)...")
    print(payload["extra_instructions"][:400], "...\n")

    print("5) Offline answer (no API key)")
    answer = await project.ask("How does authentication work?")
    print(answer[:800])
    print("\nDone.")


if __name__ == "__main__":
    if not REPO.exists():
        print(f"Missing sample repo: {REPO}", file=sys.stderr)
        sys.exit(1)
    asyncio.run(main())
