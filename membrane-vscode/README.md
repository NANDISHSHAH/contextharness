# Membrane — Context Intelligence & Agent Governance

**Graph-native codebase understanding, skill gates, and agent governance for your workspace.**

A biological membrane controls information flow, enforces rules, filters actions, and coordinates systems. Membrane does exactly that for AI agents and your codebase.

> **Not another AI assistant.** Membrane governs how AI *agents* understand and safely modify your code — complementing tools like GitHub Copilot and Claude Code rather than replacing them.

---

## How It's Different

| Tool | Helps whom? | What it tracks |
|---|---|---|
| GitHub Copilot / Cursor | The human | Suggestions & autocomplete |
| Microsoft AI Engineering Coach | The human | Your AI usage habits |
| **Membrane** | **The AI agents** | **Codebase graph, agent conflicts, architectural contracts** |

---

## Features

### Always-On Status Bar

The Membrane status bar item shows your extension state at all times:

```
⚡ Membrane: Ready     ⚠ 2 Agent Conflicts
```

- Click the state item for quick actions: Retry Setup, View Logs, Build Index
- Conflicts update every 30 seconds automatically

### Skill Gates → VS Code Problems Panel

Skill gate violations appear as **red squiggles** in your editor — just like TypeScript errors:

```
[Membrane/blast-radius] This change affects 12 files (limit: 10) (blast radius: 12)
```

- Runs automatically on every file save
- "Run Skill Gates on Changed Files" command checks all git-modified files
- Results appear in the Problems panel (`Ctrl+Shift+M`)

### 7 Sidebar Views

| View | Data source | What it shows |
|---|---|---|
| Symbol Explorer | Project map JSON | Files → classes/functions, click to navigate |
| Context Debt | `context debt --json` | Module staleness scores with severity icons |
| Skill Gates | `context skills history --json` | Pass/fail audit log with blast radius |
| Agent Locks | `context locks --json` | Which agents hold locks on which files |
| Failure Patterns | `context patterns --json` | Recurring bugs grouped by severity |
| Trust Scores | `context trust --json` | Per-file trust tier (T1–T5) |
| Playbook Proposals | `context playbook --json` | AI-suggested governance rule additions |

All views show a clickable **▶ Build Index** prompt when no data exists — no dead placeholder text.

### Dependency Graph (powered by graphify)

`Membrane: View Dependency Graph` generates an interactive vis.js graph of your codebase:
- Nodes sized by connection count (hub detection)
- Color-coded by community cluster
- Hover for symbol details, click to navigate
- Falls back to Cytoscape.js view if graphify isn't installed

### Harvest Context (WebView)

`Membrane: Harvest Context` opens a dedicated panel:
- Query input + optional branch selector
- Results displayed in the panel with Copy / Open in Editor buttons
- Powered by multi-source context aggregation (code + guidelines + tests + Jira)

### Setup Wizard

First-time users get a guided 6-step setup wizard:
1. Verify Python environment (uv)
2. Install contextpack
3. Initialize workspace
4. Build index
5. Configure MCP server
6. Done

### Failure Pattern Warnings

Opening a file that has known failure patterns shows an immediate warning:
> `Membrane: 3 known failure pattern(s) in this file` → Review Patterns | Dismiss

### MCP Server for Claude Code

Built-in MCP server with 15 tools for Claude Code and other agents:

```
@membrane harvest_context("authentication flow")
@membrane find_symbol("UserService")
@membrane run_skill_gate(files=["src/auth.ts"])
@membrane check_agent_conflicts()
```

Add to `.mcp.json`:
```json
{
  "mcpServers": {
    "context-harness": {
      "command": "uv",
      "args": ["run", "--extra", "harness", "context-harness-mcp"],
      "env": { "CONTEXTPACK_ROOT": "${workspaceFolder}" }
    }
  }
}
```

---

## Getting Started

**Requirements**: [uv](https://docs.astral.sh/uv/installation/) (Python runtime manager)

1. Install Membrane from the VS Code Marketplace
2. Open a project folder
3. The setup wizard opens automatically on first run
4. Click **Build Index** — the extension indexes your codebase and configures everything

---

## Commands

| Command | Shortcut | Description |
|---|---|---|
| Build Membrane Index | `Ctrl+Shift+M B` | Full codebase index |
| Harvest Context | `Ctrl+Shift+M H` | Open harvest WebView |
| View Dependency Graph | `Ctrl+Shift+M G` | Interactive graph (graphify) |
| Run Skill Gates on Changed Files | — | Check git-modified files → Problems panel |
| Show Membrane Status | Click status bar | Recovery QuickPick |
| Get Skill Plan | Right-click file | Skill gate plan for this file |
| Show Context Debt | — | Module staleness report |
| Show Agent Locks | — | Active multi-agent locks |
| Show Failure Patterns | — | Learned failure patterns |

---

## Settings

Configure in **Preferences → Extensions → Membrane**:

| Setting | Default | Description |
|---|---|---|
| `membrane.embeddingProvider` | `hash` | `hash` (local), `openai`, `azure_foundry` |
| `membrane.llmProvider` | — | For AI-powered harvest and ask commands |
| `membrane.autoWatch` | `true` | Incremental rebuild on file save |
| `membrane.autoMcpConfigure` | `true` | Auto-write `.mcp.json` |
| `membrane.openaiApiKey` | — | OpenAI API key (stored securely) |
| `membrane.azureEndpoint` | — | Azure OpenAI endpoint |
| `membrane.jiraBaseUrl` | — | Jira instance URL for ticket-linked context |

---

## Architecture

```
VS Code Extension                    Python Backend
─────────────────                    ──────────────
StatusBarManager ──────────────────► context debt/locks
7 Tree Providers ──────────────────► context [cmd] --json
SkillGateDiagnostics ──────────────► context skills run --files
WizardPanel ───────────────────────► context init/build/harness
GraphPanel ─────────────────────────► context graphify
HarvestPanel ──────────────────────► context harvest
                                     │
                                     ▼
                                 MCP Server
                              (context-harness-mcp)
                                     │
                                     ▼
                             Claude Code / Agents
```

The Python backend (contextpack) implements Phases 1–9: graph building, context harvesting, skill gates, semantic contracts, agent trust scoring, failure pattern learning, and coupling trend monitoring.

---

## Requirements

- VS Code 1.85.0+
- [uv](https://docs.astral.sh/uv/installation/) — automatically detects and uses the bundled binary
- Internet connection for first install (downloads contextpack from PyPI)
- Optional: OpenAI or Azure OpenAI API key for LLM-powered features

---

## Contributing

See [DEVELOPMENT.md](DEVELOPMENT.md) for architecture details, development setup, and the manual testing checklist.

Issues and PRs: [github.com/NANDISHSHAH/contextharness](https://github.com/NANDISHSHAH/contextharness)

---

## License

MIT — © 2026 Nandish Shah
