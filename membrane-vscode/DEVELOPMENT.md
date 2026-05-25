# Membrane VSCode Extension — Development Guide

## Project Structure

```
membrane-vscode/
├── src/                          TypeScript source code
│   ├── extension.ts              Extension activation/deactivation entry point
│   ├── constants.ts              Brand strings, command IDs, settings keys
│   ├── python/
│   │   ├── detector.ts           uv executable detection + platform handling
│   │   ├── installer.ts          contextpack wheel installation into ~/.membrane/venv/
│   │   └── runner.ts             ContextRunner class for executing context CLI
│   ├── mcp/
│   │   ├── manager.ts            MCP server subprocess lifecycle
│   │   └── mcpConfig.ts          .mcp.json reading/writing
│   ├── build/
│   │   ├── buildService.ts       Full/incremental build orchestration
│   │   └── statusBar.ts          3 status bar items (build, staleness, agents)
│   ├── watcher/
│   │   └── fileWatcher.ts        Debounced file system watcher
│   ├── providers/
│   │   ├── symbolExplorerProvider.ts
│   │   ├── contextDebtProvider.ts
│   │   ├── skillGatesProvider.ts
│   │   ├── agentLocksProvider.ts
│   │   └── failurePatternsProvider.ts
│   ├── commands/
│   │   ├── buildCommands.ts
│   │   ├── harvestCommands.ts
│   │   ├── skillCommands.ts
│   │   ├── governanceCommands.ts
│   │   └── setupCommands.ts
│   └── utils/
│       ├── output.ts             Wraps VSCode output channel
│       ├── workspace.ts          Workspace path helpers
│       └── config.ts             Settings → env var mapping
├── webview-src/                  Webview TypeScript source
│   ├── graph/
│   │   └── graph.ts              Cytoscape.js dependency graph
│   ├── harvest/
│   │   └── harvest.ts            Context harvest query panel
│   └── wizard/
│       └── wizard.ts             Setup wizard multi-step flow
├── media/
│   ├── membrane.svg              Activity bar icon
│   └── membrane-logo.svg         Marketplace logo
├── resources/                    Runtime assets (built by CI)
│   ├── wheels/contextpack-*.whl
│   ├── uv-linux-x64, uv-darwin-*, uv-win32-x64.exe
│   └── cytoscape.min.js
├── package.json                  VSCode extension manifest + npm scripts
├── tsconfig.json                 TypeScript compiler config
├── esbuild.mjs                   Build bundler config
├── .vscodeignore                 Files to exclude from VSIX
├── README.md                     Marketplace listing
├── CHANGELOG.md                  Release notes
└── DEVELOPMENT.md                This file
```

## Setup & Development

### Prerequisites

- Node.js 18+
- npm/yarn
- VSCode 1.85.0+

### Installation

```bash
cd membrane-vscode
npm install
npm run compile
npm run compile:webviews
```

### Development Loop

1. **Watch mode**: Continuously rebuild TypeScript as you edit
   ```bash
   npm run watch
   npm run watch:webviews  # in another terminal
   ```

2. **Launch extension**: Press `F5` in VSCode (if `run` extension config exists), or manually:
   - Open the membrane-vscode folder in VSCode
   - Press `F5` → "Extension Development Host"

3. **Live reload**: Changes to `.ts` files are auto-compiled; reload the extension host window (`Ctrl+R`)

### Key Files to Edit

| File | Purpose | Edit when... |
|------|---------|-------------|
| `src/extension.ts` | Extension lifecycle | Changing activation logic or initialization order |
| `src/constants.ts` | All brand/config strings | Rebranding, adding commands, changing settings |
| `src/commands/*.ts` | Command handlers | Adding/modifying commands |
| `src/providers/*.ts` | Tree view data sources | Changing sidebar view contents |
| `src/python/runner.ts` | CLI execution | Changing how Python commands are invoked |
| `src/mcp/manager.ts` | MCP server lifecycle | Changing server startup/shutdown behavior |
| `package.json` | VSCode manifest | Adding views, commands, keybindings, settings |

## Compilation

### TypeScript → JavaScript

The extension uses esbuild for fast bundling:

```bash
npm run compile              # Main extension code
npm run compile:webviews    # Webview panels
npm run prepackage          # Both (used before packaging)
```

Output files land in `out/`:
- `extension.js` — Main extension
- `webview-graph.js` — Graph visualization
- `webview-harvest.js` — Harvest panel
- `webview-wizard.js` — Setup wizard

### Bundling Options

- **External `vscode`**: Don't bundle the VSCode API (it's provided by the host)
- **Platform `node`**: Generate Node.js-compatible code
- **Format `cjs`**: CommonJS (required for Node.js)
- **Target `node18`**: Use ES2022 features that node18+ understands

## Testing

### Unit Tests
Not yet implemented. Placeholder for future test suite.

### Manual Testing Checklist

1. **Activation**:
   - [ ] uv detection works
   - [ ] contextpack installation (if not present)
   - [ ] MCP server starts
   - [ ] Status bar items appear
   - [ ] Symbol Explorer populates

2. **Build**:
   - [ ] `Ctrl+Shift+M B` triggers build
   - [ ] Output channel shows build progress
   - [ ] Status bar changes from "Building..." → "Ready"
   - [ ] `.contextpack/` directory created

3. **File Watcher**:
   - [ ] Toggle watch: `Ctrl+Shift+M W`
   - [ ] Save a file → incremental build triggered (after 1.5s debounce)

4. **Commands**:
   - [ ] `Harvest Context` opens dialog, executes `context harvest`
   - [ ] `View Dependency Graph` opens webview
   - [ ] `Show Context Debt` runs and outputs

5. **Tree Views**:
   - [ ] Symbol Explorer shows files/entities
   - [ ] Clicking entity opens file at correct line
   - [ ] Refresh buttons work

6. **Settings**:
   - [ ] All settings under `membrane.*` appear in settings UI
   - [ ] Secret settings stored securely (API keys not in plaintext)
   - [ ] Env vars passed to Python commands correctly

## Python Integration

The extension shells out to the Python `context` CLI via `ContextRunner.run()`.

### Commands Used

| Command | Purpose |
|---------|---------|
| `context init .` | Initialize `.contextpack/` |
| `context build .` | Full build (scan → graph → embed → store) |
| `context harvest "<query>"` | Harvest context |
| `context ask "<question>"` | Ask LLM |
| `context debt` | Show context debt (--json flag needed) |
| `context locks` | Show agent locks (--json flag needed) |
| `context patterns` | Show failure patterns (--json flag needed) |
| `context-harness-mcp` | Start MCP server |
| `context harness install` | Install harness (hooks, .mcp.json, etc.) |

### Adding CLI Support

If you need a new Python command:

1. Check that it's defined in `contextpack/cli/main.py`
2. In `ContextRunner`, call:
   ```typescript
   const result = await runner.run(['subcommand', 'args']);
   ```
3. For JSON output, add `--json` flag to the Python command:
   ```python
   json_output: bool = typer.Option(False, "--json")
   ```
4. In TypeScript:
   ```typescript
   const data = await runner.runJson(['command', '--json']);
   ```

## MCP Server Integration

The MCP server (`context-harness-mcp`) is started as a subprocess on extension activation.

**Configuration**: `.mcp.json` is auto-written by `mcpConfig.ts`:

```json
{
  "mcpServers": {
    "context-harness": {
      "command": "/absolute/path/to/uv",
      "args": ["run", "--extra", "harness", "context-harness-mcp"],
      "env": { "CONTEXTPACK_ROOT": "/workspace/path" }
    }
  }
}
```

Claude Code reads this and connects to the MCP server automatically.

### MCP Tools Available

All 15 tools from `contextpack/mcp/server.py`:
- `harvest_context` — Multi-source context for a query
- `find_symbol` — Symbol lookup
- `agent_memory_store` / `agent_memory_recall` — Shared memory
- `get_skill_plan` — Skill gate plan
- `run_skill_gate` — Execute skills
- ... and 10 more

## Packaging & Distribution

### Create VSIX

```bash
npm run prepackage
npm run package
```

Produces: `membrane-vscode-0.1.0.vsix` (ready to install or publish)

### Publish to Marketplace

```bash
# Set PAT in environment or vsce config
npm run publish --pat <your-vsce-pat>
```

See `.github/workflows/membrane-vscode-publish.yml` for CI/CD setup.

## Debugging

### VSCode Extension Debugger

1. Press `F5` to launch Extension Development Host
2. Breakpoints in `src/*.ts` are hit directly
3. Use `Debug Console` for evaluating expressions

### Output Channel

All logs go to "Membrane" output channel via `log()` function.

### Python Subprocess Output

Spawned Python processes stream output to the Membrane output channel.

## Common Issues

### "uv not found"
The bundled uv binary may not exist for your platform. Ensure:
- VSIX was built on a multi-platform CI (GitHub Actions)
- Or manually download uv binaries and place in `resources/`

### "contextpack not installed"
The installer runs automatically on first activation. Check:
- `~/.membrane/venv/` exists
- `~/.membrane/venv/bin/python` (or Scripts/ on Windows) is executable

### ".mcp.json not found"
Extension auto-creates it. Check:
- `membrane.autoMcpConfigure` is true
- Workspace root is writable

### "MCP server won't start"
Check:
- `.mcp.json` has valid JSON syntax
- `CONTEXTPACK_ROOT` env var is set
- Python backend is accessible via `uv run context --version`

## Roadmap

### Phase 2 (Planned)
- [ ] Webview panels styled + functional (graph, harvest, wizard)
- [ ] --json flags on all CLI commands
- [ ] CodeLens on hub entities
- [ ] Inline diagnostics (debt, patterns)

### Phase 3 (Planned)
- [ ] Multi-root workspace support
- [ ] Remote/WSL extension host detection
- [ ] GitHub Actions CI/CD verified
- [ ] Marketplace submission

### Phase 4+ (Future)
- [ ] Source control integration
- [ ] Activity feed
- [ ] Export/share context bundles
- [ ] Performance profiler

## Resources

- [VSCode Extension API](https://code.visualstudio.com/api)
- [WebView API](https://code.visualstudio.com/api/extension-guides/webview)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [contextpack Python docs](../README.md)
