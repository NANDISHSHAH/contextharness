import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { ContextRunner } from '../python/runner';
import { log } from '../utils/output';
import { getWorkspaceRoot } from '../utils/workspace';
import { COMMANDS } from '../constants';

interface GraphNode {
  id: string;
  label: string;
  isHub?: boolean;
  type?: string;
  filePath?: string;
  connections?: number;
}

interface GraphEdge {
  from: string;
  to: string;
  id?: string;
}

export class GraphPanel {
  static currentPanel: GraphPanel | undefined;
  private readonly panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];

  private constructor(
    panel: vscode.WebviewPanel,
    private context: vscode.ExtensionContext,
    private runner: ContextRunner,
  ) {
    this.panel = panel;
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
    this.panel.webview.onDidReceiveMessage(
      msg => this.handleMessage(msg),
      null,
      this.disposables,
    );
  }

  static show(context: vscode.ExtensionContext, runner: ContextRunner): void {
    if (GraphPanel.currentPanel) {
      GraphPanel.currentPanel.panel.reveal(vscode.ViewColumn.One);
      GraphPanel.currentPanel.loadGraphData();
      return;
    }

    const panel = vscode.window.createWebviewPanel(
      'membrane.graph',
      'Membrane — Dependency Graph',
      vscode.ViewColumn.One,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
        localResourceRoots: [
          vscode.Uri.joinPath(context.extensionUri, 'media'),
          vscode.Uri.joinPath(context.extensionUri, 'webview-src'),
        ],
      },
    );

    const instance = new GraphPanel(panel, context, runner);
    instance.panel.webview.html = instance.buildHtml();
    GraphPanel.currentPanel = instance;

    // Load data after panel is ready (small delay for webview init)
    setTimeout(() => instance.loadGraphData(), 800);
  }

  private buildHtml(): string {
    const htmlPath = path.join(
      this.context.extensionPath,
      'webview-src',
      'graph',
      'index.html',
    );

    let html = fs.readFileSync(htmlPath, 'utf-8');

    const nonce = getNonce();
    html = html.replace(/nonce="NONCE"/g, `nonce="${nonce}"`);
    html = html.replace(/nonce-NONCE/g, `nonce-${nonce}`);

    // Inject local vis.js URI (avoids CDN dependency)
    const visUri = this.panel.webview.asWebviewUri(
      vscode.Uri.joinPath(this.context.extensionUri, 'media', 'vis-network.min.js'),
    );
    html = html.replace('VIS_JS_URI', visUri.toString());

    // Inject WebView CSP source for local resources
    html = html.replace('WEBVIEW_CSP_SOURCE', this.panel.webview.cspSource);

    return html;
  }

  private async loadGraphData(): Promise<void> {
    try {
      log('GraphPanel: loading graph data...');

      // Try outline first (always available after build)
      const outline = await this.runner.runJson<any>(['outline', '--json']);
      if (outline) {
        const { nodes, edges } = buildGraphFromOutline(outline);
        this.send({ type: 'graphData', nodes, edges });
        return;
      }

      // Fallback: neighbours
      const neighbours = await this.runner.runJson<any>(['graph', 'neighbours', '--json']);
      if (neighbours) {
        const { nodes, edges } = buildGraphFromNeighbours(neighbours);
        this.send({ type: 'graphData', nodes, edges });
        return;
      }

      // No data — show empty state
      this.send({ type: 'graphData', nodes: [], edges: [] });
    } catch (err: any) {
      log(`GraphPanel data error: ${err.message}`);
      this.send({ type: 'graphData', nodes: [], edges: [] });
    }
  }

  private send(msg: object): void {
    this.panel.webview.postMessage(msg);
  }

  private async handleMessage(msg: any): Promise<void> {
    switch (msg.type) {
      case 'requestGraphData':
        await this.loadGraphData();
        break;

      case 'buildIndex':
        vscode.commands.executeCommand(COMMANDS.build);
        break;

      case 'nodeSelected':
        if (msg.filePath) {
          const workspaceRoot = getWorkspaceRoot() ?? '';
          const absPath = msg.filePath.startsWith('/')
            ? msg.filePath
            : path.join(workspaceRoot, msg.filePath);
          const uri = vscode.Uri.file(absPath);
          try {
            await vscode.window.showTextDocument(uri, {
              preview: true,
              viewColumn: vscode.ViewColumn.Beside,
            });
          } catch {
            // file may not exist locally
          }
        }
        break;
    }
  }

  private dispose(): void {
    GraphPanel.currentPanel = undefined;
    this.panel.dispose();
    this.disposables.forEach(d => d.dispose());
    this.disposables = [];
  }
}

// ── data transformers ──

function buildGraphFromOutline(outline: any): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  const connectionCount: Record<string, number> = {};

  const entities: any[] = outline.entities ?? outline.symbols ?? [];
  const files: any[] = outline.files ?? [];

  // Count connections per entity from imports/deps
  for (const e of entities) {
    const deps: string[] = e.deps ?? e.imports ?? [];
    for (const dep of deps) {
      connectionCount[e.id ?? e.name] = (connectionCount[e.id ?? e.name] ?? 0) + 1;
      connectionCount[dep] = (connectionCount[dep] ?? 0) + 1;
      edges.push({ from: e.id ?? e.name, to: dep });
    }
  }

  // File nodes
  for (const f of files) {
    const id = f.path ?? f.id;
    const conns = connectionCount[id] ?? 0;
    nodes.push({
      id,
      label: path.basename(id),
      isHub: conns >= 5,
      type: 'file',
      filePath: id,
      connections: conns,
    });
  }

  // Entity nodes
  for (const e of entities) {
    const id = e.id ?? e.name;
    if (nodes.find(n => n.id === id)) continue;
    const conns = connectionCount[id] ?? 0;
    nodes.push({
      id,
      label: e.name ?? id,
      isHub: conns >= 5,
      type: e.type ?? e.kind ?? 'function',
      filePath: e.file_path ?? e.file ?? undefined,
      connections: conns,
    });
  }

  return { nodes, edges };
}

function buildGraphFromNeighbours(data: any): { nodes: GraphNode[]; edges: GraphEdge[] } {
  if (Array.isArray(data)) {
    // Array of {node, neighbours} objects
    const nodes: GraphNode[] = [];
    const edges: GraphEdge[] = [];
    const seen = new Set<string>();

    for (const entry of data) {
      const id = entry.node ?? entry.id;
      if (!seen.has(id)) {
        seen.add(id);
        const conns = (entry.neighbours ?? []).length;
        nodes.push({ id, label: path.basename(id), isHub: conns >= 5, type: 'module', filePath: id, connections: conns });
      }
      for (const n of entry.neighbours ?? []) {
        if (!seen.has(n)) {
          seen.add(n);
          nodes.push({ id: n, label: path.basename(n), isHub: false, type: 'module', filePath: n, connections: 1 });
        }
        edges.push({ from: id, to: n });
      }
    }
    return { nodes, edges };
  }

  // Object with nodes/edges arrays
  return {
    nodes: (data.nodes ?? []).map((n: any) => ({
      id: n.id, label: n.label ?? n.id,
      isHub: n.isHub ?? false, type: n.type, filePath: n.filePath, connections: n.connections ?? 0,
    })),
    edges: (data.edges ?? []).map((e: any, i: number) => ({
      id: String(i), from: e.source ?? e.from, to: e.target ?? e.to,
    })),
  };
}

function getNonce(): string {
  let text = '';
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for (let i = 0; i < 32; i++) text += possible.charAt(Math.floor(Math.random() * possible.length));
  return text;
}
