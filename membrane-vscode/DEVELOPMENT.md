# Membrane VSCode Extension — Development Guide

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VS Code Extension Host                        │
│                                                                 │
│  ┌─────────────┐  ┌──────────────────────────────────────────┐  │
│  │ StatusBar   │  │            extension.ts                  │  │
│  │ Manager     │  │  activate() → uv → install → runner →   │  │
│  │ (state +    │  │  providers → commands → diagnostics →    │  │
│  │  conflicts) │  │  wizard (first-run)                      │  │
│  └─────────────┘  └──────────────────────────────────────────┘  │
│                                                                 │
│  ┌── 7 Tree View Providers ──────────────────────────────────┐  │
│  │  symbolExplorer  contextDebt   skillGates   agentLocks    │  │
│  │  failurePatterns  trustScores  playbook                   │  │
│  │  (all call runner.runJson([cmd, '--json']))                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌── 3 WebView Panels ────┐  ┌── Diagnostics ───────────────┐  │
│  │  WizardPanel           │  │  SkillGateDiagnosticProvider │  │
│  │  GraphPanel (graphify) │  │  → Problems panel red squig. │  │
│  │  HarvestPanel          │  │  → onDidSaveTextDocument     │  │
│  └────────────────────────┘  └──────────────────────────────┘  │
│                                                                 │
│  ┌── ContextRunner ───────────────────────────────────────────┐  │
│  │  spawn: ~/.membrane/venv/bin/python -m contextpack.cli.main│  │
│  │  fallback: uv run --extra harness context                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────┘
                                 │ subprocess
┌────────────────────────────────▼────────────────────────────────┐
│               Python contextpack backend                        │
│  contextpack/cli/main.py → Phases 1-9:                         │
│  build · harvest · ask · debt · locks · patterns · coupling    │
│  trust · playbook · contracts · graphify · harness             │
│                                                                 │
│  MCP Server (context-harness-mcp) ← Claude Code reads .mcp.json│
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
membrane-vscode/
├── src/
│   ├── extension.ts              Entry point — fault-tolerant lifecycle with status bar
│   ├── constants.ts              Brand strings, command IDs, settings keys
│   ├── statusBar.ts              StatusBarManager (state + conflict counter)
│   ├── python/
│   │   ├── detector.ts           uv detection + venv path resolution
│   │   ├── installer.ts          contextpack install (local → wheel → PyPI) + rollback
│   │   └── runner.ts             ContextRunner — spawn Python CLI, parse JSON
│   ├── mcp/
│   │   ├── manager.ts            MCP server subprocess lifecycle
│   │   └── mcpConfig.ts          .mcp.json read/write
│   ├── build/
│   │   ├── buildService.ts       Full/incremental build orchestration
│   │   └── statusBar.ts          Build-specific 3-item status bar
│   ├── watcher/
│   │   └── fileWatcher.ts        Debounced file system watcher
│   ├── diagnostics/
│   │   └── skillGateDiagnostics.ts  Skill gate failures → VS Code Problems panel
│   ├── panels/
│   │   ├── WizardPanel.ts        Setup wizard WebView controller
│   │   ├── GraphPanel.ts         Dependency graph (graphify or Cytoscape fallback)
│   │   └── HarvestPanel.ts       Context harvest WebView controller
│   ├── providers/
│   │   ├── symbolExplorerProvider.ts   File → symbols tree (from project map JSON)
│   │   ├── contextDebtProvider.ts      context debt --json
│   │   ├── skillGatesProvider.ts       context skills history --json
│   │   ├── agentLocksProvider.ts       context locks --json
│   │   ├── failurePatternsProvider.ts  context patterns --json
│   │   ├── trustScoresProvider.ts      context trust --json  ✅ complete
│   │   └── playbookProvider.ts         context playbook --json  ✅ complete
│   ├── commands/
│   │   ├── buildCommands.ts      build, incrementalBuild, watch
│   │   ├── harvestCommands.ts    harvest (→ HarvestPanel), ask
│   │   ├── skillCommands.ts      skillsPlan, skillsRun, skillsHistory
│   │   ├── governanceCommands.ts debtReport, locksShow, patternsShow, contractsShow, couplingTrend
│   │   └── setupCommands.ts      harnessInstall, harnessValidate, setup, mcpConfigure
│   └── utils/
│       ├── output.ts             Output channel wrapper
│       ├── workspace.ts          Workspace path helpers
│       └── config.ts             Settings → env var mapping
├── webview-src/
│   ├── graph/
│   │   ├── index.html            Dependency graph HTML
│   │   └── graph.ts              Cytoscape.js fallback
│   ├── harvest/
│   │   ├── index.html            Harvest query panel HTML
│   │   └── harvest.ts            Query → postMessage → HarvestPanel.ts
│   └── wizard/
│       ├── index.html            6-step setup wizard HTML
│       └── wizard.ts             Step navigation → postMessage → WizardPanel.ts
├── package.json                  Extension manifest
├── esbuild.mjs                   Build config (extension.js + 3 webview bundles)
└── DEVELOPMENT.md                This file
```

## Setup & Development

### Prerequisites

- Node.js 18+
- VS Code 1.85.0+
- Python 3.10+ with [uv](https://docs.astral.sh/uv/installation/) (`brew install uv`)

### Installation

```bash
cd membrane-vscode
npm install
npm run compile          # builds out/extension.js
npm run compile:webviews # builds out/webview-*.js
```

### Development Loop

```bash
# Terminal 1 — watch extension code
npm run watch

# Terminal 2 — watch webview code
npm run watch:webviews

# VS Code — press F5 to launch Extension Development Host
# After changes: Ctrl+Shift+P → "Developer: Reload Window"
```

## New Features (Phase 1 + 2)

### StatusBarManager (`src/statusBar.ts`)

Two status bar items always visible in the lower-left:
- **State item**: `Membrane: Starting... / Building... / Ready / Error (click)`
  - Click → QuickPick with: Retry Setup / View Logs / Open Settings / Run Build Index
- **Conflict item**: `⚠ N Agent Conflicts` (hidden when 0)
  - Polls every 30s via `runner.runJson(['locks', '--json'])`
  - Click → `membrane.locksShow`

### Skill Gate Diagnostics (`src/diagnostics/skillGateDiagnostics.ts`)

Skill gate violations appear in the VS Code **Problems** panel as red squiggles — exactly like TypeScript errors.

- Runs automatically on every file save (`onDidSaveTextDocument`)
- `membrane.runSkillGatesAll` command runs gates on all git-changed files
- Diagnostic format: `[Membrane/skill-name] violation message (blast radius: N)`

### WebView Panels

| Panel | Class | Trigger |
|---|---|---|
| Setup Wizard | `WizardPanel.ts` | Auto on first run, or `membrane.setup` |
| Dependency Graph | `GraphPanel.ts` | `membrane.graphView` |
| Harvest Context | `HarvestPanel.ts` | `membrane.harvest` or `membrane.harvestPanel` |

**GraphPanel**: runs `context graphify --output .membrane/graph.html`, reads the self-contained vis.js HTML, and embeds it in a WebView. Falls back to the built-in Cytoscape view if graphify isn't available.

**WizardPanel**: executes backend steps (check uv → install → init → build → MCP config) when the user navigates through wizard steps.

**HarvestPanel**: replaces the previous input-dialog approach with a real WebView with query input, output area, and copy/open-in-editor buttons.

### Proactive File Warnings

When you open a file, Membrane checks `context patterns --file <path> --json`. If failure patterns are found, a warning notification appears: `"N known failure pattern(s) in this file"` with a "Review Patterns" button.

### All Empty States are Clickable

Every tree view that has no data shows a `▶ Build Index to populate this view` item that, when clicked, triggers `membrane.build`. No more dead placeholder text.

## Python Commands Reference

| Command | Flag | Used by |
|---------|------|---------|
| `context build` | — | BuildService |
| `context harvest "<query>"` | — | HarvestPanel, harvestCommands |
| `context ask "<q>"` | `--llm` | harvestCommands |
| `context debt` | `--json` | contextDebtProvider |
| `context locks` | `--json` | agentLocksProvider, StatusBar polling |
| `context patterns` | `--json`, `--file <path>` | failurePatternsProvider, file-open warnings |
| `context coupling` | `--json` | governanceCommands |
| `context trust` | `--json` | trustScoresProvider |
| `context playbook` | `--json` | playbookProvider |
| `context skills history` | `--json` | skillGatesProvider |
| `context skills run` | `--files <csv>`, `--json` | SkillGateDiagnosticProvider |
| `context graphify` | `--output <path>` | GraphPanel |
| `context harness install` | — | WizardPanel step 5, setupCommands |
| `context-harness-mcp` | — | McpServerManager |

## Manual Testing Checklist

### Phase 1 — Reliability

- [ ] Status bar shows `Membrane: Starting...` on activation
- [ ] Status bar transitions to `Membrane: Ready` when init completes
- [ ] Status bar shows `Membrane: Error — <reason>` if uv missing
- [ ] Clicking status bar item opens QuickPick with 4 options
- [ ] All 7 tree view panels show clickable `▶ Build Index` when index missing
- [ ] After `membrane.build`, panels refresh with real data
- [ ] Agent conflict item appears in status bar when locks exist

### Phase 2 — Features

- [ ] Saving a file triggers skill gate check (visible in Problems panel)
- [ ] `membrane.runSkillGatesAll` runs gates on git-changed files
- [ ] `membrane.graphView` generates and opens the graph WebView
- [ ] `membrane.harvest` opens HarvestPanel (not an input dialog)
- [ ] Opening a file with failure patterns shows warning notification
- [ ] First-run wizard opens on a fresh workspace
- [ ] Wizard step 4 (Build) runs and logs output in the wizard panel

### Settings

- [ ] All `membrane.*` settings appear in VS Code settings UI
- [ ] Changing embedding provider is reflected in next build
- [ ] Jira settings reach the Python CLI as env vars

## Common Issues

### "uv not found"
Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`  
Or on Mac: `brew install uv`

### "contextpack not installed"
Check `~/.membrane/venv/bin/python -c "import contextpack"`. If it fails, run `membrane.setup` wizard.

### Skill gate diagnostics don't appear
The `context skills run --files <path> --json` command must return violations in the format:
```json
[{"file": "...", "line": 10, "message": "...", "severity": "error", "skill": "gate-name", "blast_radius": 3}]
```

### Graph WebView is blank
GraphPanel falls back to Cytoscape if graphify fails. Check the Membrane output channel for the error. Make sure `graphify` is installed: `pip install graphifyy`.

### MCP server won't start
Check `.mcp.json` syntax, then: `uv run --extra harness context-harness-mcp` in the terminal.

## Packaging

```bash
npm run prepackage   # compile extension + all 3 webviews
npm run package      # produce membrane-vscode-0.1.0.vsix
```

## Roadmap

### Done (Phase 1)
- [x] StatusBarManager with state + conflict counter
- [x] Fault-tolerant activation with try/catch and recovery QuickPick
- [x] Platform-specific wheel detection + venv rollback in installer
- [x] All tree providers: actionable "Build Index" CTA when empty
- [x] trustScoresProvider and playbookProvider (full implementations)
- [x] SkillGateDiagnosticProvider → VS Code Problems panel
- [x] WizardPanel connected to backend steps
- [x] GraphPanel with graphify integration (Cytoscape fallback)
- [x] HarvestPanel (WebView with query/result UI)
- [x] Failure pattern warnings on file open
- [x] 30s conflict polling on status bar

### In Progress (Phase 2)
- [ ] CodeLens on hub entities (click to run skill gate for that file)
- [ ] `@membrane` VS Code Chat participant
- [ ] Context Debt WebView dashboard with bar charts

### Phase 3 (Planned)
- [ ] Agent rule editor (editable `.contextpack/agent-rules.json`)
- [ ] Multi-root workspace support
- [ ] Remote/WSL extension host detection
- [ ] Marketplace submission

## Resources

- [VS Code Extension API](https://code.visualstudio.com/api)
- [WebView API](https://code.visualstudio.com/api/extension-guides/webview)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [graphify (vis.js graph generation)](https://github.com/safishamsi/graphify)
- [contextpack Python docs](../README.md)
