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
      log('GraphPanel: loading graph data via graphify --stdout...');

      const data = await this.runner.runJson<{ nodes: GraphNode[]; edges: GraphEdge[] }>(
        ['graphify', '--stdout'],
        { timeout: 30_000 },
      );

      if (data && Array.isArray(data.nodes) && data.nodes.length > 0) {
        this.send({ type: 'graphData', nodes: data.nodes, edges: data.edges ?? [] });
        return;
      }

      // Empty — show empty state (index not built)
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


function getNonce(): string {
  let text = '';
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for (let i = 0; i < 32; i++) text += possible.charAt(Math.floor(Math.random() * possible.length));
  return text;
}
