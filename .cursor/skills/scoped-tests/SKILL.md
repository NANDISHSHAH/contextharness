---
name: scoped-tests
description: Run tests scoped to the area being changed. Use when editing or reviewing code.
---

# Scoped tests

After changes, run the smallest relevant test set.

## Python (this repo)

```bash
uv sync --extra dev
pytest tests/ -q
```

For a single module:

```bash
pytest tests/test_harness.py -q
```

## Before testing

If you changed parsers, graph, or harvest logic:

```bash
context build .
context harness validate
```

## Context Harness

Use `context harvest` for the feature area first so failures are interpreted against real dependencies and guidelines.
