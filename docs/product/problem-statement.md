# Problem statement

## The failure mode of “smart chat on code”

Engineering organizations adopted LLMs quickly. The default integration pattern is:

1. Open an IDE or chat UI
2. Paste files or hope the tool indexed the repo
3. Ask a question
4. Receive a plausible but sometimes **structurally wrong** answer

This fails in predictable ways:

### 1. Similarity ≠ relevance

Vector search returns chunks that *look like* the query. It does not know that:

- `AuthMiddleware` is on the critical path for every upload request
- A changed file imports a deprecated internal API
- A Jira ticket requires OAuth2 but the diff implements API keys

**Symptom:** fluent answers that miss the actual dependency chain.

### 2. No shared “project memory”

Each chat session rebuilds context from scratch. There is no durable, structured representation of:

- Module boundaries
- Service relationships
- Documented team conventions
- Expected behaviour from tests

**Symptom:** inconsistent answers across engineers and agents.

### 3. Context window abuse

Teams compensate by dumping large folders into the model. That increases cost, latency, and noise — without guaranteeing the right symbols are included.

**Symptom:** high token bills and diluted attention on key files.

### 4. Product context is orphaned

Code intelligence tools rarely integrate:

- Acceptance criteria from issue trackers
- Team review guidelines in-repo
- Behaviour encoded in test names and descriptions

**Symptom:** agents that code well syntactically but fail product alignment (a pattern seen in domain-aware PR review systems).

### 5. Vendor lock-in at the context layer

Context is shaped for one IDE or one API shape. Moving to Azure Foundry, another model, or a headless agent pipeline requires re-building prompts.

**Symptom:** duplicate investment per platform.

---

## Root cause (architect view)

The missing layer is **not** another embedding index. It is a **context runtime**:

```text
┌─────────────────────────────────────────────────────────┐
│  Missing layer: Context Runtime                          │
│  - Understand structure (graph)                          │
│  - Select & compress (compiler)                        │
│  - Merge product + code sources (harvester)            │
│  - Emit provider-neutral packs (adapters)              │
└─────────────────────────────────────────────────────────┘
         ▲                              ▲
    Repository                    Agent / LLM
```

Without this layer, every agent re-implements partial solutions (grep, AST, RAG, custom prompts) — poorly integrated and unmaintainable.

---

## ContextPack hypothesis

If we treat **context as a first-class runtime artifact** — built, versioned, compressed, and retrieved like data in a query engine — then:

1. Agents become **grounded** in structure and policy, not just text
2. Teams can **audit** what the model saw (`extra_instructions`, graph excerpts)
3. Platforms can **swap models** without rebuilding understanding
4. Cost scales with **relevant** tokens, not repository size

---

## Success criteria

We consider ContextPack successful when a user can run:

```bash
context build ./repo
context ask "Explain the authentication architecture" ./repo
```

…and receive an answer that:

- Names real modules and relationships from the repo
- Reflects team guidelines when present
- Acknowledges missing product/test context when not configured
- Fits in a bounded token budget without manual file selection

Optional: same flow with `--llm` against **Azure AI Foundry** or OpenAI using the compiled pack — no manual paste.

---

## Related

- [Vision & benefits](vision-and-benefits.md)
- [Architecture overview](../architecture/overview.md)
