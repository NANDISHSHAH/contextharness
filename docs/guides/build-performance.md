# Build performance & `.contextpack/memory.db`

## What `context build` actually does

Build is **not** only creating `memory.db`. It runs a pipeline:

```text
scan → parse → graph → chunk → embed → vectors.json
                              ↘
                        memory.db (entities)
                              ↘
                        project_map.json
```

Most wall-clock time is usually **parsing** and **embedding**, not SQLite.

## Why `memory.db` used to feel slow

Earlier versions called `upsert_entity()` **once per symbol**, each opening a new SQLite connection and commit. On ~240 entities that meant hundreds of round-trips.

**Fix (current):** `upsert_entities_batch()` — one connection, one transaction.

After updating, compare:

```bash
context build . --timing
```

## What is stored where

| File | Contents |
|------|----------|
| `memory.db` | Entity rows (+ schema for future relationships/embeddings tables) |
| `vectors.json` | Chunk text + embedding vectors (default backend) |
| `project_map.json` | Full scan result — reload without re-parse |
| `config.json` | `git_head` for harness staleness checks |

`memory.db` size grows with entity count; for tiny-api it stays under ~100KB.

## Slow builds — checklist

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| 2–5 min first run | Chroma + ONNX import | Use default `CONTEXTPACK_VECTOR_STORE=sqlite` |
| Slow every build | Huge repo / many languages | Exclude paths in scanner ignore rules |
| Slow `memory.db` only | Old ContextPack | Pull latest (batched SQLite) |
| API latency | `embedding_provider=openai` | Use `hash` locally for dev |

## Environment variables

```bash
CONTEXTPACK_VECTOR_STORE=sqlite    # default, fast
CONTEXTPACK_EMBEDDING_PROVIDER=hash  # default, no API
```

## Measure

```bash
context build demo/tiny-api --timing
context build . --timing
```

## Related

- [User journey](../../demo/USER-JOURNEY.md)
- [Getting started](getting-started.md)
