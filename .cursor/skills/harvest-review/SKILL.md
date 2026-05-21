---
name: harvest-review
description: Domain-aware review using ContextPack harvest (code + guidelines + tests + Jira).
---

# Harvest review

Use when reviewing a feature, PR, or architectural change.

## Steps

1. Ensure index exists: `context build .` (or confirm `.contextpack/project_map.json`).
2. Harvest task context:

```bash
context harvest "functional review of <area>" . --branch <branch-if-any>
```

Or MCP: `harvest_context` with the same query.

3. Read `extra_instructions` / harvest output before judging the diff.
4. Cross-check: acceptance criteria (Jira), team guidelines (`AGENTS.md`), test behaviour names.
5. Run `context harness validate` if you updated harness docs.

## Output format

- AC / intent gaps
- Behaviour vs tests
- Dependency / graph risks (use `graph_neighbours` MCP for hotspots)
- Concrete file-level findings
