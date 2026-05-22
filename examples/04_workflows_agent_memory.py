#!/usr/bin/env python3
"""
Phase 5 — Workflow extraction & multi-agent memory.

Shows:
  - WorkflowExtractor detecting flows from entity graph
  - project.workflows() retrieving persisted workflows
  - AgentMemory storing decisions, constraints, observations
  - SharedMemory recalling facts across agents
  - SharedMemory.format_for_prompt() injecting memory into a prompt

Install:
  cd /path/to/contextharness
  uv sync && uv pip install -e .

Run:
  python examples/04_workflows_agent_memory.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent / "sample_repo"


async def main() -> None:
    from contextpack import Project, WorkflowExtractor

    project = Project(REPO)

    # ── Step 1: build (runs workflow extraction automatically) ───────────────
    print("=" * 60)
    print("Step 1: Build — workflow extraction runs automatically")
    print("=" * 60)
    await project.init()
    pmap, stats = await project.build()
    print(f"  Entities     : {len(pmap.entities)}")
    print(f"  Build time   : {stats.total_time:.2f}s")
    print(f"  Workflows phase: {stats.phase_times.get('workflows', 0):.3f}s")
    print()

    # ── Step 2: list workflows persisted by the build ────────────────────────
    print("=" * 60)
    print("Step 2: Workflows detected in the codebase")
    print("=" * 60)
    workflows = await project.workflows()
    if workflows:
        for wf in workflows:
            print(f"  [{wf['name']}]")
            print(f"    {wf.get('summary', '')}")
            steps = wf.get("steps", [])
            if steps:
                print(f"    Steps: {' → '.join(steps[:6])}")
            print()
    else:
        print("  No workflows detected (repo may be too small for pattern recognition)")
        print()

    # ── Step 3: use WorkflowExtractor directly (no DB) ──────────────────────
    print("=" * 60)
    print("Step 3: WorkflowExtractor used directly (in-memory)")
    print("=" * 60)
    from contextpack.graph.engine import ContextGraph

    graph = ContextGraph.from_entities(pmap.entities)
    extractor = WorkflowExtractor(graph, pmap.entities)
    live_workflows = extractor.extract()
    print(f"  Extracted {len(live_workflows)} workflow(s) in-memory:")
    for wf in live_workflows[:5]:
        print(f"  - {wf.name}: {wf.summary}")
    print()

    # ── Step 4: AgentMemory — write facts as the reviewer agent ─────────────
    print("=" * 60)
    print("Step 4: AgentMemory — reviewer agent stores findings")
    print("=" * 60)
    reviewer = project.agent_memory("reviewer")

    fact1 = await reviewer.store_decision(
        "Auth flow uses token-based validation — avoid session cookies",
        entity_ids=["auth.py::authenticate"],
        confidence=0.95,
    )
    fact2 = await reviewer.store_constraint(
        "Never expose raw user IDs in API responses — always use opaque tokens"
    )
    fact3 = await reviewer.store_observation(
        "Billing module is isolated — no direct DB calls from the API layer"
    )
    await reviewer.store(
        "In progress: reviewing the upload pipeline",
        fact_type="task_state",
        metadata={"phase": "code_review", "priority": "high"},
    )

    print(f"  Stored fact ids: {fact1}, {fact2}, {fact3}")
    print()

    # ── Step 5: AgentMemory — recall for the reviewer agent ─────────────────
    print("=" * 60)
    print("Step 5: Recall reviewer agent's own memory")
    print("=" * 60)
    own_facts = await reviewer.recall(query="auth")
    print(f"  Facts matching 'auth': {len(own_facts)}")
    for f in own_facts:
        print(f"  [{f['fact_type']}] {f['content'][:80]}")
    print()

    # ── Step 6: SharedMemory — a second agent reads all facts ────────────────
    print("=" * 60)
    print("Step 6: SharedMemory — fixer agent reads across all agents")
    print("=" * 60)
    fixer = project.agent_memory("fixer")
    await fixer.store_decision(
        "Decided to add rate-limiting middleware before token validation",
        entity_ids=["auth.py"],
    )

    shared = project.shared_memory()
    all_facts = await shared.recall_all(limit=20)
    print(f"  Total facts across all agents: {len(all_facts)}")
    for f in all_facts:
        print(f"  [{f['agent_id']:12} / {f['fact_type']:12}] {f['content'][:70]}")
    print()

    # ── Step 7: format_for_prompt — inject shared memory into a prompt ───────
    print("=" * 60)
    print("Step 7: format_for_prompt — ready to inject into an LLM call")
    print("=" * 60)
    memory_block = await shared.format_for_prompt(query="auth", limit=5)
    print(memory_block or "(no facts matched 'auth')")
    print()

    # ── Step 8: combine memory + harvest for a complete prompt ───────────────
    print("=" * 60)
    print("Step 8: Combined prompt = harvest context + agent memory")
    print("=" * 60)
    harvested = await project.harvest("review authentication")
    memory_block = await shared.format_for_prompt()
    full_prompt = harvested.to_agent_prompt_block() + "\n\n" + memory_block
    print(f"  Harvest block  : {len(harvested.to_agent_prompt_block())} chars")
    print(f"  Memory block   : {len(memory_block)} chars")
    print(f"  Combined total : {len(full_prompt)} chars")
    print()
    print("  Memory block preview:")
    print(memory_block[:500])
    print()

    print("Done.")
    print()
    print("Next steps:")
    print("  context workflows ./examples/sample_repo")
    print("  Use list_workflows in Cursor via MCP")
    print("  Use agent_memory_store / agent_memory_recall in Cursor via MCP")


if __name__ == "__main__":
    if not REPO.exists():
        print(f"Missing sample repo: {REPO}", file=sys.stderr)
        sys.exit(1)
    asyncio.run(main())
