# Membrane VSCode — Full Implementation Solution Plan

_Date: 2026-05-30 | Based on deep codebase audit_

---

## Executive Summary

The Python backend (Phases 1–9) is largely complete. The VS Code extension layer has 7 skeleton providers (4 are stubs), 3 disconnected WebViews, a broken installer lifecycle, and no Diagnostics integration. This plan fixes all of it across 3 phases, with graphify integrated for the dependency graph view.

---

## Architecture Overview (Current vs. Target)

### Current (broken)
```
extension.ts
  └─ activate() ──► [11-step init with silent failures]
       ├─ installer.ts ──► [uv detection, silent wheel errors]
       ├─ 7 tree providers ──► [4 return placeholder text]
       ├─ 3 webviews ──► [HTML exists, no postMessage handlers]
       └─ commands ──► [most write to Output Channel only]
```

### Target (working)
```
extension.ts
  └─ activate()
       ├─ StatusBarManager ──► [Initializing → Ready / Error(click)]
       ├─ installer.ts (fixed) ──► [retry, rollback, platform wheels]
       ├─ LifecycleWizard ──► [6-step guided setup on first run]
       ├─ 7 tree providers ──► [all wired to MCP runner]
       │    ├─ symbolExplorer ──► find_symbol + project_outline
       │    ├─ contextDebt ──► get_context_debt
       │    ├─ skillGates ──► run_skill_gate + get_evidence_bundles
       │    ├─ agentLocks ──► check_agent_conflicts
       │    ├─ failurePatterns ──► get_failure_patterns
       │    ├─ trustScores ──► [ALREADY WORKS]
       │    └─ playbook ──► [ALREADY WORKS]
       ├─ 3 webviews (connected)
       │    ├─ GraphView ──► graphify HTML embedded in WebView
       │    ├─ HarvestView ──► query → harvest_context → display
       │    └─ WizardView ──► step-by-step backend execution
       ├─ DiagnosticsEngine ──► skill gate failures → Problems panel
       └─ FileWatcher ──► auto-refresh on save + conflict detection
```

---

## Phase 1 — Reliability Foundation (Week 1–2)

### 1.1 StatusBarManager (new file: `src/statusBar.ts`)

The single most impactful change. Users need to know what state the extension is in.

```typescript
// src/statusBar.ts
export type MembraneState = 'initializing' | 'building' | 'ready' | 'error' | 'disabled';

export class StatusBarManager {
  private item: vscode.StatusBarItem;
  private _state: MembraneState = 'initializing';

  constructor() {
    this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 10);
    this.item.command = 'membrane.showStatus';
    this.setState('initializing');
    this.item.show();
  }

  setState(state: MembraneState, detail?: string) {
    this._state = state;
    const icons = { initializing: '$(sync~spin)', building: '$(sync~spin)', ready: '$(check)', error: '$(error)', disabled: '$(circle-slash)' };
    const labels = { initializing: 'Membrane: Starting...', building: 'Membrane: Building...', ready: 'Membrane: Ready', error: `Membrane: Error${detail ? ` — ${detail}` : ''}`, disabled: 'Membrane: Disabled' };
    this.item.text = `${icons[state]} ${labels[state]}`;
    this.item.backgroundColor = state === 'error' ? new vscode.ThemeColor('statusBarItem.errorBackground') : undefined;
  }

  get state() { return this._state; }
  dispose() { this.item.dispose(); }
}
```

Wire into `extension.ts` `activate()` — set `initializing` at start, `ready` when MCP confirms, `error` on any lifecycle failure.

Add `membrane.showStatus` command that opens the Output Channel and shows a QuickPick with "Retry Setup", "Open Settings", "View Logs".

---

### 1.2 Fix installer.ts

**Problems to fix:**
1. Silent failure when wheel not found — wrap in try/catch with explicit `throw new Error(...)`
2. No platform-specific wheel variant logic
3. No rollback on partial venv creation

```typescript
// Key changes in installer.ts

// BEFORE (line ~95):
const wheels = await vscode.workspace.findFiles('**/*.whl', null, 1);

// AFTER:
const platform = process.platform; // 'darwin' | 'win32' | 'linux'
const arch = process.arch;         // 'x64' | 'arm64'
const pattern = `**/*${arch === 'arm64' && platform === 'darwin' ? 'arm64' : 'x86_64'}*.whl`;
const wheels = await vscode.workspace.findFiles(pattern, null, 1);
if (wheels.length === 0) {
  outputChannel.appendLine('[installer] No bundled wheel found, falling back to PyPI...');
  // continue to PyPI — NOT a hard failure
}

// Add rollback wrapper:
async function withRollback<T>(action: () => Promise<T>, rollback: () => Promise<void>): Promise<T> {
  try {
    return await action();
  } catch (err) {
    await rollback();
    throw err;
  }
}
```

---

### 1.3 Fix Extension Lifecycle in extension.ts

Replace the current linear 11-step activation with a fault-tolerant flow:

```typescript
// src/extension.ts — new activate() structure

export async function activate(context: vscode.ExtensionContext) {
  const statusBar = new StatusBarManager();
  const outputChannel = vscode.window.createOutputChannel('Membrane');
  context.subscriptions.push(statusBar, outputChannel);

  try {
    // Step 1: Check uv
    statusBar.setState('initializing', 'checking uv...');
    const uvOk = await detectUv(outputChannel);
    if (!uvOk) {
      statusBar.setState('error', 'uv not found');
      showInstallUvPrompt(); // QuickPick with install instructions
      return;
    }

    // Step 2: Install/verify contextpack
    statusBar.setState('initializing', 'installing contextpack...');
    await ensureContextpack(context, outputChannel);  // throws on hard failure

    // Step 3: Build service init (non-blocking — don't fail activation)
    const runner = new ContextRunner(outputChannel);
    const mcpReady = await runner.ping().catch(() => false);
    
    if (!mcpReady) {
      outputChannel.appendLine('[activate] MCP server not responding — prompting build');
      showBuildPrompt(); // "Build Index now?" notification
    }

    // Step 4: Register everything (always, even if MCP not ready)
    registerAllProviders(context, runner, statusBar);
    registerAllCommands(context, runner, statusBar);

    statusBar.setState(mcpReady ? 'ready' : 'error', mcpReady ? undefined : 'run Build Index');

    // Step 5: First-run wizard
    const isFirstRun = !context.globalState.get('membrane.initialized');
    if (isFirstRun) {
      WizardPanel.show(context, runner);
    }

  } catch (err: any) {
    statusBar.setState('error', err.message?.slice(0, 40));
    outputChannel.appendLine(`[activate] Fatal: ${err.message}`);
    outputChannel.show();
  }
}
```

Key changes:
- `try/catch` wrapping entire activation
- Steps are labeled in status bar so user sees progress
- Registration always happens (providers show "Build Index" prompt, not permanent placeholders)
- First-run wizard auto-opens

---

### 1.4 Fix the 4 Stub Tree Providers

Each follows the same pattern. Here's the template, with specifics per provider:

```typescript
// TEMPLATE for stub providers
async getChildren(element?: TreeItem): Promise<TreeItem[]> {
  if (element) return [];
  
  try {
    const result = await this.runner.runJson(['COMMAND', '--json']);
    if (!result || result.length === 0) {
      return [new TreeItem('No data found — run Build Index', TreeItemCollapsibleState.None)];
    }
    return result.map(item => this.mapToTreeItem(item));
  } catch {
    return [buildIndexPromptItem()]; // clickable item that runs membrane.build
  }
}

// buildIndexPromptItem() — shared utility
function buildIndexPromptItem(): TreeItem {
  const item = new TreeItem('▶ Build Index to populate this view', TreeItemCollapsibleState.None);
  item.command = { command: 'membrane.build', title: 'Build Index' };
  item.iconPath = new ThemeIcon('play');
  return item;
}
```

**contextDebtProvider.ts:**
```typescript
// Command: context debt --json
// Expected JSON: [{module: string, score: number, hotspots: string[], trend: 'rising'|'stable'|'falling'}]
// Icon: score >= 70 → error, >= 40 → warning, else → check
```

**skillGatesProvider.ts:**
```typescript
// Command: context skills history --json  (get_evidence_bundles via runner)
// Expected JSON: [{skill: string, file: string, status: 'pass'|'fail', blast_radius: number, timestamp: string}]
// Icon: pass → check, fail → error
// Tooltip: show blast_radius + timestamp
```

**agentLocksProvider.ts:**
```typescript
// Command: context locks --json
// Expected JSON: [{agent: string, file: string, acquired_at: string, ttl_seconds: number}]
// Show: "agent → file (Xm ago)"
// Context menu: "Release Lock" command
```

**failurePatternsProvider.ts:**
```typescript
// Command: context patterns --json
// Expected JSON: [{pattern: string, affected_files: string[], frequency: number, last_seen: string}]
// Group by severity (frequency > 5 → high, 2-5 → medium, 1 → low)
```

**symbolExplorerProvider.ts:**
```typescript
// Currently loads nothing — fix by calling: context outline --json
// Expected: [{file: string, symbols: [{name, kind, line}]}]
// Tree: File node → collapsible → Symbol children
// Click → vscode.window.showTextDocument(uri, {selection: range})
```

---

### 1.5 Connect the Wizard WebView

The wizard HTML/TS is built. The extension side is missing step handlers.

Add a `WizardPanel` class in `src/panels/WizardPanel.ts`:

```typescript
export class WizardPanel {
  static currentPanel?: WizardPanel;

  static show(context: vscode.ExtensionContext, runner: ContextRunner) {
    // Create WebView panel
    // Set HTML from wizard/index.html (read from extensionUri)
    // Handle messages:
    panel.webview.onDidReceiveMessage(async (msg) => {
      switch (msg.type) {
        case 'step-1-check': // check uv
          const uvOk = await detectUv();
          panel.webview.postMessage({ type: 'step-result', step: 1, ok: uvOk });
          break;
        case 'step-2-install':
          await ensureContextpack(context, outputChannel);
          panel.webview.postMessage({ type: 'step-result', step: 2, ok: true });
          break;
        case 'step-3-init':
          await runner.run(['init']);
          panel.webview.postMessage({ type: 'step-result', step: 3, ok: true });
          break;
        case 'step-4-build':
          await runner.run(['build']);
          panel.webview.postMessage({ type: 'step-result', step: 4, ok: true });
          break;
        case 'step-5-mcp':
          await configureMcp(context);
          panel.webview.postMessage({ type: 'step-result', step: 5, ok: true });
          break;
        case 'complete':
          context.globalState.update('membrane.initialized', true);
          panel.dispose();
          break;
      }
    });
  }
}
```

---

## Phase 2 — Surface Killer Features (Week 2–3)

### 2.1 Skill Gates as VS Code Diagnostics (THE most important feature)

This is what makes Membrane genuinely different. Failed skill gates appear as red squiggles in the editor and in the Problems panel — just like TypeScript errors.

**New file: `src/diagnostics/skillGateDiagnostics.ts`**

```typescript
import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';

export class SkillGateDiagnosticProvider {
  private collection: vscode.DiagnosticCollection;

  constructor(private runner: ContextRunner) {
    this.collection = vscode.languages.createDiagnosticCollection('membrane-skill-gates');
  }

  async runForFiles(uris: vscode.Uri[]) {
    this.collection.clear();
    const filePaths = uris.map(u => u.fsPath).join(',');
    
    const result = await this.runner.runJson(['skills', 'run', '--files', filePaths, '--json']);
    // result: [{file, line, col, message, severity: 'error'|'warning', skill, blast_radius}]
    
    const diagnosticMap = new Map<string, vscode.Diagnostic[]>();
    
    for (const violation of result ?? []) {
      const uri = vscode.Uri.file(violation.file);
      const range = new vscode.Range(
        violation.line - 1, violation.col ?? 0,
        violation.line - 1, violation.col_end ?? 999
      );
      const diag = new vscode.Diagnostic(
        range,
        `[Membrane] ${violation.message} (blast radius: ${violation.blast_radius})`,
        violation.severity === 'error' ? vscode.DiagnosticSeverity.Error : vscode.DiagnosticSeverity.Warning
      );
      diag.source = `membrane/${violation.skill}`;
      diag.code = { value: violation.skill, target: vscode.Uri.parse('https://contextharness.dev/skills') };
      
      const key = uri.toString();
      if (!diagnosticMap.has(key)) diagnosticMap.set(key, []);
      diagnosticMap.get(key)!.push(diag);
    }

    diagnosticMap.forEach((diags, key) => this.collection.set(vscode.Uri.parse(key), diags));
  }

  // Hook into file save
  hookFileSave(context: vscode.ExtensionContext) {
    context.subscriptions.push(
      vscode.workspace.onDidSaveTextDocument(doc => {
        this.runForFiles([doc.uri]);
      })
    );
  }

  // Hook into git pre-commit equivalent: run on all changed files
  async runForChangedFiles() {
    const changedFiles = await this.getGitChangedFiles();
    if (changedFiles.length > 0) {
      await this.runForFiles(changedFiles);
    }
  }

  dispose() { this.collection.dispose(); }
}
```

Register in `extension.ts`:
```typescript
const diagProvider = new SkillGateDiagnosticProvider(runner);
diagProvider.hookFileSave(context);
context.subscriptions.push(diagProvider);
// Run on activation for currently open files
const openDocs = vscode.workspace.textDocuments.map(d => d.uri);
if (openDocs.length) diagProvider.runForFiles(openDocs);
```

Add a `membrane.runSkillGates` command that runs for all git-changed files and shows the Problems panel:
```typescript
vscode.commands.executeCommand('workbench.action.problems.focus');
```

---

### 2.2 Agent Conflict Detection in Status Bar

Conflicts should be visible without opening any panel.

In `StatusBarManager`, add a secondary status bar item:

```typescript
// Add to StatusBarManager
private conflictItem: vscode.StatusBarItem;

async updateConflicts(runner: ContextRunner) {
  const conflicts = await runner.runJson(['locks', '--json']).catch(() => []);
  const count = (conflicts ?? []).length;
  if (count === 0) {
    this.conflictItem.hide();
  } else {
    this.conflictItem.text = `$(warning) ${count} Agent Conflict${count > 1 ? 's' : ''}`;
    this.conflictItem.tooltip = `${count} agent lock conflict(s) detected — click to review`;
    this.conflictItem.command = 'membrane.showLocks';
    this.conflictItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
    this.conflictItem.show();
  }
}
```

Poll every 30 seconds via `setInterval` (dispose on deactivate).

---

### 2.3 Connect the Graph WebView with Graphify

**Replace** the current Cytoscape.js skeleton with graphify's generated vis.js HTML.

Integration strategy:
1. When user runs `membrane.graphView`, execute: `context graphify --output .membrane/graph.html`
2. Read the generated HTML file
3. Embed it in a WebView panel using `webview.html = graphHtml`

```typescript
// src/panels/GraphPanel.ts

export class GraphPanel {
  static async show(context: vscode.ExtensionContext, runner: ContextRunner) {
    const panel = vscode.window.createWebviewPanel(
      'membrane.graph',
      'Membrane: Dependency Graph',
      vscode.ViewColumn.One,
      { enableScripts: true, localResourceRoots: [context.extensionUri] }
    );

    panel.webview.html = getLoadingHtml();

    // Run graphify via contextpack runner
    const outputPath = path.join(vscode.workspace.rootPath!, '.membrane', 'graph.html');
    const result = await runner.run(['graphify', '--output', outputPath]);
    
    if (result.exitCode !== 0) {
      panel.webview.html = getErrorHtml(result.stderr);
      return;
    }

    // Read generated HTML and inject CSP nonce for VS Code WebView security
    let graphHtml = await fs.readFile(outputPath, 'utf-8');
    // vis.js CDN references work fine in WebViews with allowExternalContent
    panel.webview.options = { enableScripts: true, enableExternalUris: true };
    panel.webview.html = graphHtml;
  }
}
```

**Add to contextpack Python side** (if `context graphify` CLI doesn't exist):
```python
# contextpack/cli/main.py — add graphify subcommand
@app.command()
def graphify(output: str = ".membrane/graph.html"):
    """Generate interactive dependency graph using graphify."""
    from graphify import extract, build_graph, cluster, analyze, export
    extractions = extract(os.getcwd())
    graph = build_graph(extractions)
    analysis = analyze(graph)
    export(graph, analysis, output_path=output)
    print(f"Graph written to {output}")
```

---

### 2.4 Connect the Harvest WebView

Currently `membrane.harvest` shows an input dialog and dumps to Output Channel. Replace with the WebView.

```typescript
// In harvestCommands.ts — replace dialog approach

case 'membrane.harvest':
  HarvestPanel.show(context, runner);
  break;

// src/panels/HarvestPanel.ts
export class HarvestPanel {
  static show(context: vscode.ExtensionContext, runner: ContextRunner) {
    const panel = vscode.window.createWebviewPanel(
      'membrane.harvest', 'Membrane: Harvest Context',
      vscode.ViewColumn.Two,
      { enableScripts: true }
    );
    panel.webview.html = getHarvestHtml(panel.webview, context.extensionUri);

    panel.webview.onDidReceiveMessage(async (msg) => {
      if (msg.type === 'harvest') {
        panel.webview.postMessage({ type: 'loading' });
        const result = await runner.run(['harvest', msg.query, '--branch', msg.branch || 'HEAD']);
        panel.webview.postMessage({ type: 'result', content: result.stdout, error: result.stderr });
      }
    });
  }
}
```

---

### 2.5 Failure Pattern Warnings on File Open

```typescript
// Register in extension.ts
context.subscriptions.push(
  vscode.window.onDidChangeActiveTextEditor(async editor => {
    if (!editor) return;
    const filePath = editor.document.uri.fsPath;
    const patterns = await runner.runJson(['patterns', '--file', filePath, '--json']).catch(() => []);
    if (patterns && patterns.length > 0) {
      const action = await vscode.window.showWarningMessage(
        `Membrane: ${patterns.length} known failure pattern(s) in this file`,
        'Review Patterns',
        'Dismiss'
      );
      if (action === 'Review Patterns') {
        vscode.commands.executeCommand('membrane.patternsShow');
      }
    }
  })
);
```

---

## Phase 3 — UI Upgrade & AI Coach Inspired Features (Week 3–4)

### 3.1 Context Debt WebView Dashboard

Replace the stub tree view with a proper WebView showing a bar chart built with VS Code-native styling (no external chart libraries).

**`src/panels/DebtDashboard.ts`** — render an HTML page using VS Code CSS variables:

```html
<!-- debt-dashboard.html template -->
<style>
  :root { color-scheme: dark light; }
  body { font-family: var(--vscode-font-family); color: var(--vscode-foreground); background: var(--vscode-editor-background); }
  .bar { background: var(--vscode-charts-orange); height: 20px; border-radius: 3px; }
  .critical .bar { background: var(--vscode-charts-red); }
</style>
<div id="modules"></div>
<script>
  const vscode = acquireVsCodeApi();
  window.addEventListener('message', e => {
    if (e.data.type === 'debt-data') renderBars(e.data.modules);
  });
  vscode.postMessage({ type: 'ready' });
  function renderBars(modules) {
    document.getElementById('modules').innerHTML = modules.map(m => `
      <div class="module ${m.score > 70 ? 'critical' : ''}">
        <span>${m.module}</span>
        <div class="bar" style="width:${m.score}%"></div>
        <span>${m.score}</span>
      </div>
    `).join('');
  }
</script>
```

---

### 3.2 Agent Rule Editor (Inspired by AI Coach's 45 rules)

AI Coach lets users edit anti-pattern rules for themselves. You can do the same for agent behavior.

**New file: `.contextpack/agent-rules.json`** (created by `context harness install`):
```json
{
  "rules": [
    { "id": "blast-radius-limit", "enabled": true, "threshold": 10, "description": "Block edits affecting more than N files" },
    { "id": "hub-file-protection", "enabled": true, "description": "Require skill plan before editing hub nodes" },
    { "id": "no-concurrent-agents", "enabled": true, "description": "Block simultaneous agent edits to the same module" },
    { "id": "harvest-before-edit", "enabled": false, "description": "Require context harvest before any edit command" }
  ]
}
```

**`membrane.editRules`** command opens a QuickPick multi-select where rules can be toggled, then writes back to the JSON file.

---

### 3.3 VS Code Chat Participant (`@membrane`)

Register a chat participant so users can type `@membrane what's the context debt?` in Copilot Chat.

```typescript
// src/chatParticipant.ts

export function registerChatParticipant(context: vscode.ExtensionContext, runner: ContextRunner) {
  const participant = vscode.chat.createChatParticipant('membrane', async (request, _ctx, stream, token) => {
    const q = request.prompt.toLowerCase();

    if (q.includes('debt')) {
      const debt = await runner.runJson(['debt', '--json']);
      stream.markdown(`## Context Debt\n${formatDebt(debt)}`);
    } else if (q.includes('conflict') || q.includes('lock')) {
      const locks = await runner.runJson(['locks', '--json']);
      stream.markdown(`## Agent Conflicts\n${formatLocks(locks)}`);
    } else if (q.includes('status') || q.includes('ready')) {
      const outline = await runner.runJson(['outline', '--json']);
      stream.markdown(`## Project Status\n${formatOutline(outline)}`);
    } else {
      // Fall back to harvest_context for open-ended questions
      const result = await runner.run(['harvest', request.prompt]);
      stream.markdown(result.stdout);
    }
  });

  participant.iconPath = vscode.Uri.joinPath(context.extensionUri, 'assets', 'membrane-icon.png');
  context.subscriptions.push(participant);
}
```

Requires `vscode.chat` API — add to `package.json` engines: `>=1.90.0` and `extensionDependencies: []`.

---

## Implementation Order (Priority Queue)

| # | File(s) to create/change | Why this order |
|---|---|---|
| 1 | `src/statusBar.ts` (new) + `extension.ts` | Unblocks debugging everything else |
| 2 | `installer.ts` (fix) + `extension.ts` lifecycle | Makes activation reliable |
| 3 | 4 stub providers: `contextDebt`, `skillGates`, `agentLocks`, `failurePatterns` | Removes all placeholder text |
| 4 | `symbolExplorerProvider.ts` (fix data source) | Core feature users see first |
| 5 | `src/diagnostics/skillGateDiagnostics.ts` (new) | Killer feature — Diagnostics integration |
| 6 | `src/panels/WizardPanel.ts` (new — connect wizard) | First-run UX |
| 7 | `src/panels/GraphPanel.ts` (new — graphify) | Visual wow factor |
| 8 | `src/panels/HarvestPanel.ts` (new — connect harvest WebView) | Replace dialog with real UI |
| 9 | Status bar conflict detector (add to StatusBarManager) | Always-visible governance |
| 10 | File open failure pattern warnings | Proactive UX |
| 11 | `src/panels/DebtDashboard.ts` (new) | Rich visualization |
| 12 | `src/chatParticipant.ts` (new) | @membrane in Copilot Chat |
| 13 | Agent rule editor | Power-user feature |

---

## Graphify Integration Details

Graphify (MIT, actively maintained, 56k stars) generates self-contained `graph.html` files using vis.js. Integration approach:

1. Add `graphify` as a Python dependency in contextpack's `pyproject.toml`
2. Add `context graphify` CLI subcommand (5 lines in `contextpack/cli/main.py`)
3. VS Code side: `GraphPanel.ts` runs the command, reads `.membrane/graph.html`, embeds in WebView
4. Enable `enableExternalUris: true` on the WebView (vis.js loads from CDN)
5. Optionally: parse `graph.json` generated alongside the HTML for the symbol explorer data source

This approach gives you a **production-quality interactive graph** (community detection, god node highlighting, hover tooltips) without any frontend JS to write.

---

## package.json Changes Required

```json
{
  "engines": { "vscode": "^1.90.0" },
  "contributes": {
    "chatParticipants": [{
      "id": "membrane",
      "name": "membrane",
      "description": "Membrane codebase intelligence — ask about debt, conflicts, and skill gates"
    }]
  }
}
```

Also add the `membrane.showStatus`, `membrane.editRules`, `membrane.graphView` (fix existing), `membrane.runSkillGatesAll` commands to the commands contributes array.

---

## Files to Create (New)

| File | Lines (est.) | Purpose |
|---|---|---|
| `src/statusBar.ts` | ~80 | State-aware status bar manager |
| `src/diagnostics/skillGateDiagnostics.ts` | ~120 | Skill gates → Problems panel |
| `src/panels/WizardPanel.ts` | ~150 | Connect wizard HTML to backend steps |
| `src/panels/GraphPanel.ts` | ~80 | Embed graphify output in WebView |
| `src/panels/HarvestPanel.ts` | ~100 | Harvest WebView controller |
| `src/panels/DebtDashboard.ts` | ~120 | Context debt bar chart |
| `src/chatParticipant.ts` | ~80 | @membrane chat participant |

## Files to Modify (Existing)

| File | What changes |
|---|---|
| `src/extension.ts` | Full lifecycle rewrite with try/catch, status bar, wizard |
| `src/python/installer.ts` | Platform wheel detection, rollback, better error messages |
| `src/providers/contextDebtProvider.ts` | Implement real data fetch from `context debt --json` |
| `src/providers/skillGatesProvider.ts` | Implement real data fetch from `context skills history --json` |
| `src/providers/agentLocksProvider.ts` | Implement real data fetch from `context locks --json` |
| `src/providers/failurePatternsProvider.ts` | Implement real data fetch from `context patterns --json` |
| `src/providers/symbolExplorerProvider.ts` | Fix data source: `context outline --json` |
| `src/commands/buildCommands.ts` | Add progress notification during build |
| `src/commands/harvestCommands.ts` | Replace dialog with HarvestPanel.show() |
| `contextpack/cli/main.py` | Add `graphify` subcommand |

---

## Definition of Done (Phase 1)

- [ ] Extension activates with no console errors on a fresh workspace
- [ ] Status bar shows correct state at each lifecycle stage
- [ ] All 7 tree view panels show real data (or "Build Index" CTA, not placeholder text)
- [ ] Wizard completes a full setup flow end-to-end

## Definition of Done (Phase 2)

- [ ] Saving a file triggers skill gate check → violations appear in Problems panel
- [ ] Agent conflicts visible in status bar within 30s of lock acquisition
- [ ] `membrane.graphView` opens an interactive dependency graph (graphify)
- [ ] `membrane.harvest` opens the WebView panel, not a dialog
- [ ] Opening a file with failure patterns shows a warning notification

## Definition of Done (Phase 3)

- [ ] `@membrane status` works in VS Code Chat
- [ ] Debt dashboard WebView shows real scores as bars
- [ ] Agent rules editable via `membrane.editRules` QuickPick
