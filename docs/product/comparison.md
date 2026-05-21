# ContextPack vs alternatives

## Positioning matrix

| Approach | Primary question | Strength | Weakness for code agents |
|----------|------------------|----------|---------------------------|
| **Copy-paste / @file** | “What did the human select?” | Simple | Incomplete, biased, not repeatable |
| **Vector RAG** | “What text is similar?” | Good for docs | Weak on structure & dependencies |
| **Prompt templates** | “How do we phrase the task?” | Cheap to start | No repo understanding |
| **IDE index (symbols)** | “Where is this symbol?” | Precise lookup | No compression or product context |
| **ContextPack** | “What matters for this task in this system?” | Graph + hybrid retrieval + multi-source harvest | Requires build step; MVP language scope |

---

## vs RAG frameworks

**Typical RAG pipeline**

```text
Documents → Chunk → Embed → Vector DB → Top-k → Prompt
```

**ContextPack pipeline**

```text
Repo → Parse → Graph → Chunk → Embed → Hybrid retrieve → Compile → Harvest → Aggregate → Agent
```

| Dimension | RAG | ContextPack |
|-----------|-----|-------------|
| Unit of retrieval | Text chunk | Chunk + graph distance + query ranking |
| Relationships | Often ignored | NetworkX dependency graph |
| Product rules | External / manual | Guidelines fetcher |
| Behavioural spec | Rare | Test behaviour fetcher |
| Output | Concatenated chunks | `ContextPack` + `AggregatedAgentContext` |
| Token control | Usually post-hoc truncation | `ContextCompiler` with budget |

ContextPack **may use** vectors; it is not **defined by** vectors.

---

## vs prompt engineering tools

Prompt libraries improve *wording*. They do not:

- Build a `ProjectMap` of your codebase
- Maintain embeddings and SQLite entity store under `.contextpack/`
- Traverse import/call relationships for hybrid scoring

Use both: ContextPack supplies **grounded content**; your prompts supply **task framing**.

---

## vs IDE-native AI

IDE tools optimize interactive coding. ContextPack optimizes:

- **Headless agents** (CI, PR bots, batch analysis)
- **Custom model endpoints** (Azure Foundry)
- **Explicit context artifacts** for logging and compliance

They are complementary: export ContextPack `extra_instructions` into Cursor via `CursorAdapter`.

---

## vs AI Layer / Helpline-style harness

[Helpline](https://github.com/coleam00/helpline) demonstrates an **AI Layer**: `CLAUDE.md` hierarchy, hooks, skills, MCP, subagents — workflow without a context runtime.

| Dimension | AI Layer only | ContextPack only | **Context Harness** |
|-----------|---------------|------------------|---------------------|
| Repo rules | ✓ static docs | reads guidelines | ✓ validated vs graph |
| Task context | agent search | harvest + compile | ✓ hook + MCP triggered |
| Structure | outline MCP | dependency graph | ✓ hubs in sessionStart |
| Drift | Stop hook prose | rebuild index | ✓ doc/graph validate |

Context Harness ships both: see [HARNESS.md](../../HARNESS.md) and [Context Harness guide](../guides/context-harness.md).

---

## vs static analysis only

Tools like linters and AST analyzers expose facts, not **LLM-ready, ranked, compressed** context packs. ContextPack bridges analysis → agent consumption.

---

## When RAG alone is enough

- Pure documentation site Q&A
- No need for dependency or product alignment
- Tiny repos where full-file context fits in the window

## When ContextPack is the better default

- Microservices, layered architectures, auth/data pipelines
- Agent workflows tied to Jira / guidelines / tests
- Enterprise Azure model deployments
- Repeated agent runs on the same repo (amortize `build`)

---

## Related

- [Design principles](../architecture/design-principles.md)
- [Context harvester](../architecture/context-harvester.md)
