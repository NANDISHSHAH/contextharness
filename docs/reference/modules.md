# Module reference

## `contextpack.scanner`

| Class | Responsibility |
|-------|----------------|
| `RepositoryScanner` | Walk repo, detect languages/frameworks, ignore `node_modules`, `.venv`, etc. |

**Output:** `ProjectMap` (files, languages, frameworks)

---

## `contextpack.parsers`

| Class | Languages |
|-------|-----------|
| `PythonParser` | `.py` — tree-sitter + AST fallback |
| `TypeScriptParser` | `.ts`, `.tsx` |
| `JSParser` | `.js`, `.jsx` |

**Output:** `ParsedEntity` (class, function, route, imports, docstring)

---

## `contextpack.graph`

| Class | Responsibility |
|-------|----------------|
| `ContextGraph` | NetworkX `DiGraph`; `add_entity`, `add_relationship`, `describe_neighborhood` |

**Edge types:** `defines`, `imports`, `depends_on`

---

## `contextpack.compiler`

| Component | Responsibility |
|-----------|----------------|
| `ChunkingEngine` | Entities → `SemanticChunk` (module + symbol chunks) |
| `ContextCompiler` | Query + budget → `ContextPack` |

---

## `contextpack.embeddings`

| Component | Responsibility |
|-----------|----------------|
| `HashEmbeddingProvider` | Local deterministic vectors (default) |
| `OpenAIEmbeddingProvider` | `api.openai.com` embeddings |
| `AzureFoundryEmbeddingProvider` | Azure deployment embeddings |
| `get_vector_store()` | SQLite (fast) or Chroma (optional) |

---

## `contextpack.retrieval`

| Class | Responsibility |
|-------|----------------|
| `HybridRetriever` | 65% semantic + 35% graph boost |

---

## `contextpack.harvester`

| Class | Responsibility |
|-------|----------------|
| `ContextHarvester` | Parallel `asyncio.gather` over fetchers |

| Fetcher | `ContextSourceType` |
|---------|---------------------|
| `CodeContextFetcher` | `code` |
| `ProductGuidelinesFetcher` | `product_guidelines` |
| `TestBehaviourFetcher` | `product_behaviour` |
| `JiraIntentFetcher` | `product_intent` |

---

## `contextpack.aggregator`

| Class | Responsibility |
|-------|----------------|
| `ContextAggregator` | Merge → `extra_instructions` + guardrails |

---

## `contextpack.adapters`

| Adapter | Output shape |
|---------|--------------|
| `ClaudeAdapter` | system + messages |
| `OpenAIAdapter` | OpenAI chat JSON |
| `CursorAdapter` | `extra_instructions` block |
| `LangGraphAdapter` | state dict |
| `AzureFoundryAdapter` | `(system, user)` tuple via `build_prompt()` |

---

## `contextpack.llm`

| Class | Endpoint |
|-------|----------|
| `AzureFoundryLLM` | Azure deployment / inference URL |
| `OpenAIDirectLLM` | `api.openai.com` |
| `get_llm_provider()` | Factory from `CONTEXTPACK_LLM_PROVIDER` |

---

## `contextpack.core`

| Module | Contents |
|--------|----------|
| `models.py` | Pydantic domain models |
| `config.py` | `Settings` from environment |
| `protocols.py` | Provider protocols |
| `project.py` | `Project` orchestration |

---

## `contextpack.storage`

| Class | Responsibility |
|-------|----------------|
| `SQLiteStore` | Persist entities, embeddings metadata |

---

## `contextpack.watch`

| Function | Responsibility |
|----------|----------------|
| `run_watch()` | watchdog → debounced `build()` |

---

## `contextpack.cli`

Entry: `context` → `contextpack.cli.main:app`

Commands: `init`, `build`, `ask`, `harvest`, `graph`, `watch`
