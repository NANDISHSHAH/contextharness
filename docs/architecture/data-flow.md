# Data flows

## Flow 1 — `context build` (indexing)

**Goal:** Convert repository → durable project memory.

```mermaid
flowchart TD
    A[Repository root] --> B[RepositoryScanner.scan]
    B --> C[ProjectMap files + languages]
    C --> D[Read source files]
    D --> E[Parsers → ParsedEntity list]
    E --> F[ContextGraph.from_entities]
    E --> G[ChunkingEngine.chunk_entities]
    G --> H[EmbeddingProvider.embed_batch]
    H --> I[VectorStore.upsert_chunks]
    E --> J[SQLiteStore.upsert_entity]
    F --> K[Save project_map.json]
    I --> K
    J --> K
```

**Outputs:**

- `ProjectMap` with entities attached
- Vector index (default: `.contextpack/vectors.json`)
- SQLite entity rows
- In-memory graph used on subsequent loads

**Complexity drivers:** repository size, parser languages, embedding provider latency.

---

## Flow 2 — `context compile` (query-scoped pack)

**Goal:** Given a query, produce token-bounded `ContextPack`.

```mermaid
flowchart TD
    Q[User query] --> R[HybridRetriever.retrieve]
    R --> S[Semantic vector search]
    R --> T[Graph distance boost]
    S --> U[Merge scores 65/35]
    T --> U
    U --> V[ContextCompiler.compile]
    V --> W[Rank chunks by query overlap]
    W --> X[Fill summaries until token_budget]
    X --> Y[ContextPack]
```

**Hybrid scoring (MVP):**

- `0.65` — semantic rank position
- `0.35` — graph proximity to query-matched nodes

---

## Flow 3 — `context harvest` (complete agent context)

**Goal:** Code memory + product sources → `AggregatedAgentContext`.

```mermaid
flowchart TD
    Q[Query + optional branch] --> C[ContextCompiler]
    C --> P[ContextPack]
    Q --> H[ContextHarvester.harvest parallel]
    H --> S1[Code section]
    H --> S2[Guidelines section]
    H --> S3[Behaviour section]
    H --> S4[Jira section]
    S1 --> A[ContextAggregator]
    S2 --> A
    S3 --> A
    S4 --> A
    P --> A
    A --> O[AggregatedAgentContext]
```

---

## Flow 4 — `context ask` (answer)

### Offline mode (default)

```text
harvest → format extra_instructions → template answer + architectural bullets
```

No LLM credentials required. Useful for CI smoke tests and inspecting context quality.

### LLM mode (`--llm` / `use_llm=True`)

```mermaid
sequenceDiagram
    participant P as Project
    participant A as AzureFoundryAdapter
    participant L as AzureFoundryLLM

    P->>P: harvest()
    P->>A: build_prompt(ctx)
    A-->>P: system, user_context
    P->>L: complete(system, user + question)
    L-->>P: natural language answer
```

---

## Flow 5 — `context watch` (incremental)

```text
watchdog event → debounce 2s → Project.build() full rebuild
```

Phase 3 will introduce true incremental diff indexing; MVP rebuilds for correctness.

---

## State diagram: project readiness

```mermaid
stateDiagram-v2
    [*] --> Uninitialized
    Uninitialized --> Ready: init + build
    Ready --> Ready: build (refresh)
    Ready --> Queryable: project_map.json exists
    Queryable --> Queryable: harvest / ask / compile
```

Loading an existing repo: `Project` reads `project_map.json` and reconstructs graph + retriever without re-parse if map exists.

---

## Error & degradation paths

| Failure | Behaviour |
|---------|-----------|
| Parser error on file | Skip file; continue build |
| Fetcher exception | `available=false`, logged warning |
| Jira 401/404 | Skip intent section + guardrail |
| LLM misconfiguration | `ask_llm` raises clear ValueError |
| Missing build | RuntimeError: run build first |

---

## Related

- [System overview](overview.md)
- [Getting started](../guides/getting-started.md)
