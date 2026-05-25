# Membrane — Context Intelligence & Agent Governance

**Graph-native codebase understanding, skill gates, and agent governance for your workspace.**

A biological membrane stores context boundaries, controls information flow, enforces rules, filters actions, and coordinates systems. Membrane does exactly that for AI agents and your codebase.

## What is Membrane?

Membrane is a VSCode extension that brings graph-native code intelligence to your workspace. It automatically:

- **Scans** your entire codebase and builds a semantic graph of dependencies
- **Embeds** key entities for AI agent understanding
- **Governs** agent actions with skill gates and trust scoring
- **Monitors** coupling and failure patterns across phases
- **Coordinates** multi-agent work with context intelligence

## Features

### 🔍 Code Intelligence

- Dependency graph visualization with hub detection
- Symbol explorer with cross-file navigation
- Semantic chunking for AI context
- Multi-language support (Python, TypeScript, JavaScript)

### 🛡️ Agent Governance

- **Skill Gates**: Verify code changes meet requirements before execution
- **Trust Scoring**: 5-tier trust levels for context chunks (GroundTruth → Unverified)
- **Context Debt**: Track module staleness and technical debt
- **Failure Patterns**: Detect and learn from agent mistakes

### 📊 Adaptive Intelligence

- Coupling trend monitoring over 30 days
- Failure pattern memory with remediation hints
- Snapshot diffing for agent task analysis
- Playbook learning from evidence bundles

### 🔗 MCP Integration

Built-in MCP server for Claude Code and other agents. Get context via:

```
mem brane.harvest_context("Query about your code")
membrane.find_symbol("FunctionName")
membrane.agent_memory_recall(agent_id="...")
```

## Getting Started

1. **Install** from VSCode Marketplace
2. **Open a folder** with Python/TypeScript code
3. **Click "Build Membrane Index"** — the extension handles the rest:
   - Initializes `.contextpack/` directory
   - Scans and parses your codebase
   - Builds the dependency graph
   - Configures MCP server for Claude Code

## Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| Build Membrane Index | `Ctrl+Shift+M B` | Full index build |
| Harvest Context | `Ctrl+Shift+M H` | Query codebase intelligence |
| View Dependency Graph | `Ctrl+Shift+M G` | Interactive graph visualization |
| Get Skill Plan | Right-click file | Check skill gates for file |
| Show Context Debt | `Ctrl+Shift+M D` | View module staleness |

## Settings

Configure in **Preferences → Extensions → Membrane**:

- **Embedding Provider**: `hash` (local), `openai`, or `azure_foundry`
- **LLM Provider**: For `ask` and `harvest` with LLM synthesis
- **Auto Watch**: Trigger incremental builds on file save
- **Auto MCP**: Automatically configure `.mcp.json`

## Architecture

```
Membrane (VSCode Extension)
├── Python Backend (contextpack)
│   ├── Repository Scanner (languages, entities)
│   ├── Semantic Graph (dependencies, hubs)
│   ├── Vector Store (embeddings)
│   └── SQLite Storage (memory.db)
├── Skills System (policy gates, verification)
├── Governance (trust, debt, locks)
├── Adaptive (patterns, coupling, playbooks)
└── MCP Server (15+ tools for agents)
```

## FAQ

### Does Membrane require Python?

No — Python and all dependencies are bundled in the VSIX. Zero prerequisites. Just install and use.

### Can it handle large codebases?

Yes. Membrane uses a tiered embedding strategy:
- **Hub nodes** (high-degree dependencies): Always embedded
- **Remaining entities**: Embedded up to configurable limit (default 2000)
- **Rest**: Stored-only (searchable but not embedded)

### How do I use it with Claude Code?

After building the index, the MCP server starts automatically. In Claude Code, run:

```
@membrane harvest "How does authentication work?"
```

The MCP tools (`harvest_context`, `find_symbol`, `agent_memory_recall`) are available in your agent context.

### What happens to my code?

Your code stays local. All processing is in `.contextpack/` (SQLite + embeddings). No data leaves your machine unless you configure an LLM provider.

## Troubleshooting

**"uv not found"**  
→ Bundled uv is included. If it fails, manually install: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**"Build times out"**  
→ Large repos may take a while (first build). Watch the output channel for progress.

**"MCP server won't start"**  
→ Check that `.mcp.json` is valid JSON and `CONTEXTPACK_ROOT` is set. Run `Membrane: Configure MCP Server`.

## Contributing

Found a bug or have a feature request? Open an issue on [GitHub](https://github.com/NANDISHSHAH/contextharness).

## License

MIT — See LICENSE in the repository.

---

**Made by [Nandish Shah](https://github.com/NANDISHSHAH)**  
*Bringing context intelligence to your agents.*
