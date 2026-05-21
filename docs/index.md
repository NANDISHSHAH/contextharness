# ContextPack + Context Harness

**ContextPack** is the context runtime (graph, harvest, compile). **Context Harness** is the agent workflow layer (hooks, MCP, skills) wired into that runtime. See [HARNESS.md](../HARNESS.md).

---

## Who this documentation is for

| Audience | Start here |
|----------|------------|
| Product / engineering leaders | [Vision & benefits](product/vision-and-benefits.md) · [Why not RAG?](product/comparison.md) |
| Architects | [System overview](architecture/overview.md) · [Design principles](architecture/design-principles.md) |
| Agent / platform engineers | [Getting started](guides/getting-started.md) · [Agent integration](guides/agent-integration.md) |
| Azure / enterprise teams | [Azure AI Foundry](guides/azure-foundry.md) |

---

## What ContextPack is

```text
Repository  →  Understanding  →  Compressed context  →  Agent reasoning
```

Traditional RAG answers: *"Which documents look similar to this query?"*

ContextPack answers: *"What in this system matters for this task, how do parts relate, and what constraints apply?"*

---

## Core capabilities (MVP)

1. **Repository intelligence** — scan, parse (Python/TS/JS), dependency graphs
2. **Semantic memory** — chunking, embeddings, hybrid retrieval
3. **Context compilation** — token-budgeted packs ranked for the query
4. **Multi-source harvesting** — code + guidelines + tests + product intent (Jira)
5. **Agent adapters** — Claude, OpenAI, Cursor, LangGraph, Azure Foundry
6. **CLI & SDK** — `context build`, `context ask`, `Project` API
7. **Context Harness** — hooks, MCP, skills, `context harness validate`

---

## Documentation map

### Product

- [Vision & benefits](product/vision-and-benefits.md)
- [Problem statement](product/problem-statement.md)
- [Context Harness vision](product/context-harness-vision.md)
- [ContextPack vs alternatives](product/comparison.md)
- [Use cases](product/use-cases.md)

### Architecture

- [System overview](architecture/overview.md)
- [Design principles](architecture/design-principles.md)
- [Context harvester & aggregator](architecture/context-harvester.md)
- [Build & query data flows](architecture/data-flow.md)
- [Module reference](reference/modules.md)

### Guides

- [Getting started](guides/getting-started.md)
- [Package usage (SDK)](guides/package-usage.md)
- [Azure AI Foundry integration](guides/azure-foundry.md)
- [Agent integration patterns](guides/agent-integration.md)
- [Context Harness setup](guides/context-harness.md)
- [Configuration reference](reference/configuration.md)

### Planning

- [Roadmap](roadmap.md)

---

## Quick commands

```bash
uv sync && uv pip install -e .
context init ./my-repo
context build ./my-repo
context harvest "review auth changes" ./my-repo
context ask "How does authentication work?" ./my-repo --llm
```

See the [README](../README.md) for install notes and performance tips (SQLite vectors vs Chroma).
