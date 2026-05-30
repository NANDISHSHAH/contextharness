import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { ContextRunner } from '../python/runner';
import { log } from '../utils/output';
import { getWorkspaceRoot } from '../utils/workspace';

export class GraphPanel {
  static async show(context: vscode.ExtensionContext, runner: ContextRunner): Promise<void> {
    const panel = vscode.window.createWebviewPanel(
      'membrane.graph',
      'Membrane: Dependency Graph',
      vscode.ViewColumn.One,
      {
        enableScripts: true,
        // Allow loading from vis.js CDN (graphify uses it)
        enableExternalUris: true,
        retainContextWhenHidden: true,
      },
    );

    panel.webview.html = getLoadingHtml();

    const workspaceRoot = getWorkspaceRoot();
    if (!workspaceRoot) {
      panel.webview.html = getErrorHtml('No workspace folder open');
      return;
    }

    const outputPath = path.join(workspaceRoot, '.membrane', 'graph.html');

    try {
      // Ensure .membrane directory exists
      const membraneDir = path.join(workspaceRoot, '.membrane');
      if (!fs.existsSync(membraneDir)) {
        fs.mkdirSync(membraneDir, { recursive: true });
      }

      log(`Generating dependency graph to ${outputPath}...`);

      const result = await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: 'Membrane: Generating dependency graph...',
          cancellable: false,
        },
        async () => runner.run(['graphify', '--output', outputPath], { timeout: 300_000 }),
      );

      if (result.exitCode !== 0) {
        log(`graphify failed: ${result.stderr}`);
        // Fall back to built-in Cytoscape graph if graphify is unavailable
        panel.webview.html = await getBuiltinGraphHtml(context, panel.webview, runner);
        return;
      }

      if (!fs.existsSync(outputPath)) {
        panel.webview.html = getErrorHtml('graphify ran but did not produce output');
        return;
      }

      log(`Graph generated. Loading...`);
      const graphHtml = fs.readFileSync(outputPath, 'utf-8');
      panel.webview.html = graphHtml;

    } catch (err: any) {
      log(`GraphPanel error: ${err.message}`);
      // Fall back to built-in graph view
      panel.webview.html = await getBuiltinGraphHtml(context, panel.webview, runner);
    }
  }
}

async function getBuiltinGraphHtml(
  context: vscode.ExtensionContext,
  webview: vscode.Webview,
  runner: ContextRunner,
): Promise<string> {
  const scriptUri = webview.asWebviewUri(
    vscode.Uri.joinPath(context.extensionUri, 'out', 'webview-graph.js'),
  );

  let graphData = { nodes: [], edges: [] };
  try {
    const neighbours = await runner.runJson(['graph', 'neighbours', '--json']);
    if (neighbours) graphData = neighbours;
  } catch {
    // no graph data yet
  }

  const htmlPath = path.join(context.extensionPath, 'webview-src', 'graph', 'index.html');
  if (!fs.existsSync(htmlPath)) {
    return getErrorHtml('Graph view HTML not found');
  }
  let html = fs.readFileSync(htmlPath, 'utf-8');
  html = html.replace(/<script src="\.\.\/graph\.js"><\/script>/, `<script src="${scriptUri}"></script>`);
  // Inject initial data
  html = html.replace('</body>', `<script>window.__GRAPH_DATA__ = ${JSON.stringify(graphData)};</script></body>`);
  return html;
}

function getLoadingHtml(): string {
  return `<!DOCTYPE html><html><body style="background:#1e1e1e;color:#e0e0e0;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;">
    <div style="text-align:center">
      <div style="font-size:24px;margin-bottom:12px">⚡</div>
      <div>Generating dependency graph...</div>
    </div>
  </body></html>`;
}

function getErrorHtml(message: string): string {
  return `<!DOCTYPE html><html><body style="background:#1e1e1e;color:#e0e0e0;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;">
    <div style="text-align:center">
      <div style="font-size:24px;margin-bottom:12px;color:#f44">✗</div>
      <div>${message}</div>
      <div style="margin-top:12px;font-size:12px;color:#888">Run "Build Index" first, then try again</div>
    </div>
  </body></html>`;
}
