# Build performance & `.contextpack/memory.db`

## What `context build` actually does

Build is **not** only creating `memory.db`. It runs a layered pipeline:

```text
SmartIgnore (.gitignore + built-in patterns)
    │
    ▼
scan → parse → graph → hub scoring
                              │
                    tiered embed selection
                              │
              chunk → embed → vectors.json
                              ↘
                        memory.db (all entities)
                              ↘
                        project_map.json
```

After every build, a summary table is printed automatically — no flags needed:

```
  scan      0.3s    1,234 files scanned  |  778 skipped
  parse     1.2s    789 entities  (from 456 files)
  graph     0.1s    912 nodes  1,456 edges  12 hubs
  chunk     0.2s    2,100 chunks  ~84K tokens estimated
  embed     0.8s    2,100 embedded  |  340 store-only
  store     0.4s    789 entities → memory.db
  total     3.0s
```

Use `--timing` for additional verbose output (e.g. language breakdown).

Add `--vibe` for an animated Pac-Man display with live phase progress and a token/cost summary:

```bash
context build ./my-repo --vibe
```

```
╭──────────────── ContextPack  ᗧ·····◉  nom nom nom ─────────────────╮
│  ●  SCAN    0.30s    1,234 files  778 skipped                       │
│  ●  PARSE   1.20s    789 entities from 456 files                    │
│  ●  GRAPH   0.10s    912 nodes  12 hubs                             │
│  ●  CHUNK   0.20s    2,100 chunks  ~84K tokens                      │
│  ●  EMBED   0.80s    2,100 embedded  340 store-only                 │
│  ●  STORE   0.40s    789 entities → memory.db                       │
╰─────────────────────────────────────────────────────────────────────╯
╭──────────────────── ᗧ◉  build stats ───────────────────────────────╮
│  files scanned       1,234    778 skipped                           │
│  entities embedded   2,100    340 store-only                        │
│  tokens indexed       ~84K    estimated                             │
│  embed cost          $0.00    hash                                  │
│  total time          3.00s                                          │
╰─────────────────────────────────────────────────────────────────────╯
```

Each phase row shows a live animation while running, then locks to a colored `●` when done.

## Smart ignore — what gets skipped

The scanner applies three layers of filtering before a file is indexed:

**1. Directory ignore** — built-in set of 35+ dirs:
`node_modules`, `.venv`, `dist`, `build`, `out`, `target`, `coverage`,
`.next`, `.nuxt`, `.turbo`, `.svelte-kit`, `vendor`, `generated`, and more.

**2. File pattern ignore** — generated/binary files with no semantic value:
| Pattern | Reason |
|---------|--------|
| `*.d.ts` | TypeScript declarations — generated from `.ts` source |
| `*.min.js`, `*.min.css` | Minified — no readable symbols |
| `*.map` | Source maps |
| `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` | Dependency lock files |
| `*_pb2.py`, `*.pb.go` | Protobuf generated code |

**3. `.gitignore` + `.contextpackignore`** — any pattern your project already tells git to ignore is also ignored by the scanner. Add a `.contextpackignore` file at repo root for project-specific overrides using the same syntax.

The "skipped" count in the build summary tells you exactly how many files were filtered.

## Tiered embedding — why not everything gets embedded

After the dependency graph is built, entities are ranked by graph degree (how many other modules import or depend on them). This produces three tiers:

| Tier | What | Treatment |
|------|------|-----------|
| 1 | Hub nodes (top 50 by degree) | Always embedded |
| 2 | All other entities, up to `CONTEXTPACK_MAX_EMBED_ENTITIES` | Embedded if budget allows |
| 3 | Entities beyond budget | Stored in SQLite only — available for symbol lookup and graph traversal, not vector search |

**Result:** On large repos, 60–80% of entities fall into Tier 3, dramatically cutting embedding time and vector store size while preserving retrieval quality for the most important queries.

The build summary shows `embedded | store-only` counts so you can see the split.

## What is stored where

| File | Contents |
|------|----------|
| `memory.db` | All entity rows (Tier 1 + 2 + 3) |
| `vectors.json` | Chunk text + embedding vectors for Tier 1 + 2 only |
| `project_map.json` | Full scan result — reload without re-parse |
| `config.json` | `git_head` for harness staleness checks |

`memory.db` size grows with entity count; for tiny-api it stays under ~100KB.

## Why `memory.db` used to feel slow

Earlier versions called `upsert_entity()` **once per symbol**, each opening a new SQLite connection and commit. On ~240 entities that meant hundreds of round-trips.

**Fix (current):** `upsert_entities_batch()` — one connection, one transaction.

## Slow builds — checklist

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| 2–5 min first run | Chroma + ONNX import | Use default `CONTEXTPACK_VECTOR_STORE=sqlite` |
| High "files scanned" despite ignore rules | Custom build dirs not in `.gitignore` | Add them to `.contextpackignore` |
| High "embedded" count | Large repo, many entities | Lower `CONTEXTPACK_MAX_EMBED_ENTITIES` |
| API latency during embed | `embedding_provider=openai` | Use `hash` locally for dev |
| Slow `memory.db` only | Old ContextPack | Pull latest (batched SQLite) |

## Environment variables

```bash
CONTEXTPACK_VECTOR_STORE=sqlite       # default, fast
CONTEXTPACK_EMBEDDING_PROVIDER=hash   # default, no API key required
CONTEXTPACK_MAX_EMBED_ENTITIES=2000   # max entities to embed (default 2000)
CONTEXTPACK_EMBED_HUBS_FIRST=true     # always embed hub nodes first (default true)
```

## Ask vibe mode

The `--vibe` flag also works on `context ask` — it shows a Pac-Man thinking spinner while the context is compiled, then prints a token trace panel after the answer:

```bash
context ask "How does billing integrate with auth?" ./my-repo --vibe
```

```
╭──────────────────── ᗧ◉  token trace ──────────────────────────────╮
│  question           ~12    tokens (estimated)                      │
│  context          ~8.0K    tokens (compiled pack)                  │
│  response          ~850    tokens (estimated)                      │
│  total            ~8.9K                                            │
│                                                                    │
│  provider          hash                                            │
│  est. cost        $0.00                                            │
│  elapsed           0.42s                                           │
╰────────────────────────────────────────────────────────────────────╯
```

When using `--llm` with OpenAI or Azure Foundry, the cost estimate reflects real API pricing (~$0.005/1K input, ~$0.015/1K output).

## Accessing build stats programmatically

`project.build()` returns `(ProjectMap, BuildStats)`:

```python
pmap, stats = await project.build()
print(f"Scanned: {stats.files_scanned}, Skipped: {stats.files_skipped}")
print(f"Embedded: {stats.embed_count}, Store-only: {stats.store_only_count}")
print(f"Estimated tokens: {stats.estimated_tokens:,}")
print(f"Total time: {stats.total_time:.2f}s")
print(f"Phase breakdown: {stats.phase_times}")
```

## Related

- [Configuration reference](../reference/configuration.md)
- [User journey](../../demo/USER-JOURNEY.md)
- [Getting started](getting-started.md)
