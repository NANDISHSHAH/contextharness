# Changelog

All notable changes to the Membrane extension will be documented in this file.

## [0.1.0] - 2024-Present

### Added

#### Core Features
- **Full VSCode Extension**: Zero-config installation and activation
- **Bundled Backend**: contextpack Python package + uv binary included (no prerequisites)
- **Automatic Setup**: First-run wizard guides users through init → build → MCP config
- **MCP Server**: Built-in integration with Claude Code and other agents

#### Code Intelligence
- **Dependency Graph**: Interactive visualization with hub detection
- **Symbol Explorer**: Hierarchical file and entity browser
- **Semantic Chunking**: Automatic code slicing for AI context
- **Multi-language**: Python, TypeScript, JavaScript, YAML parsing

#### UI Components
- **Sidebar Views**: 5 tree views (Symbol Explorer, Context Debt, Skill Gates, Locks, Patterns)
- **Status Bar**: Build status, staleness indicator, active agents counter
- **Command Palette**: 20+ commands for all operations
- **File Watcher**: Debounced incremental builds on file save
- **Keybindings**: `Ctrl+Shift+M` + letter for common operations

#### Governance & Monitoring
- **Trust Scoring**: 5-tier context trust levels
- **Context Debt**: Module staleness and debt tracking
- **Skill Gates**: Pre-execution code verification
- **Agent Locks**: File-level locking for multi-agent coordination
- **Failure Patterns**: Detect and learn from agent mistakes
- **Coupling Monitor**: 30-day architectural coupling trends

#### Configuration
- **VSCode Settings**: Comprehensive configuration UI
- **Secret Storage**: Secure API key management
- **Environment Variables**: Full support for .env files
- **LLM Integration**: OpenAI and Azure OpenAI support
- **Jira Integration**: Optional ticket extraction

### Backend Integration

- Wraps `contextpack` Python package (unchanged)
- Exposes 15+ MCP tools to Claude Code
- Command-line interface for all operations
- SQLite storage for graphs, embeddings, metadata

### Known Limitations

- Webview panels (graph, harvest, wizard) are in prototype form
- Some tree providers use placeholder data pending CLI --json outputs
- CodeLens integration not yet implemented
- Inline diagnostics coming in Phase 2
- WSL2 remote paths fully supported
- Multi-root workspace support pending

### Technical

- Written in TypeScript for VSCode extension API
- esbuild bundler for compilation
- Native Node.js fs/child_process for Python integration
- No dependencies bundled (minimal VSIX footprint)

---

## Future Roadmap

### Phase 2 (Planned)
- Full graph WebView with Cytoscape.js
- Harvest context panel with markdown rendering
- Setup wizard UI with progress indicators
- Inline diagnostics (debt, patterns as editor diagnostics)
- CodeLens on hub functions
- Per-command --json output flag support

### Phase 3 (Planned)
- Multi-root workspace support
- Remote/WSL extension host verification
- Telemetry opt-in
- Marketplace polish and screenshots
- CI/CD for VSIX publishing

### Phase 4+ (Future)
- Source control integration (auto-build on checkout)
- Custom theme icons
- Activity feed for agent actions
- Performance profiler integration
- Export/share context bundles

---

## Contributing

Found a bug or want a feature? Open an issue on [GitHub](https://github.com/NANDISHSHAH/contextharness).

## License

MIT
