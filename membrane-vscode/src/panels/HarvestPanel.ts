import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { ContextRunner } from '../python/runner';
import { log } from '../utils/output';

export class HarvestPanel {
  static currentPanel: HarvestPanel | undefined;
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
    if (HarvestPanel.currentPanel) {
      HarvestPanel.currentPanel.panel.reveal(vscode.ViewColumn.Two);
      return;
    }

    const panel = vscode.window.createWebviewPanel(
      'membrane.harvest',
      'Membrane: Harvest Context',
      vscode.ViewColumn.Two,
      {
        enableScripts: true,
        localResourceRoots: [vscode.Uri.joinPath(context.extensionUri, 'out')],
        retainContextWhenHidden: true,
      },
    );

    const instance = new HarvestPanel(panel, context, runner);
    instance.panel.webview.html = instance.buildHtml();
    HarvestPanel.currentPanel = instance;
  }

  private buildHtml(): string {
    const htmlPath = path.join(
      this.context.extensionPath,
      'webview-src',
      'harvest',
      'index.html',
    );
    const scriptUri = this.panel.webview.asWebviewUri(
      vscode.Uri.joinPath(this.context.extensionUri, 'out', 'webview-harvest.js'),
    );

    let html = fs.readFileSync(htmlPath, 'utf-8');
    html = html.replace(/<script src="\.\.\/harvest\.js"><\/script>/, `<script src="${scriptUri}"></script>`);
    return html;
  }

  private send(msg: object): void {
    this.panel.webview.postMessage(msg);
  }

  private async handleMessage(msg: any): Promise<void> {
    switch (msg.type) {
      case 'harvest': {
        const query: string = msg.query ?? '';
        const branch: string = msg.branch ?? '';
        if (!query.trim()) {
          this.send({ type: 'error', message: 'Please enter a query' });
          return;
        }
        log(`Harvesting context for: "${query}"`);
        this.send({ type: 'loading' });

        try {
          const args = branch ? ['harvest', query, '--branch', branch] : ['harvest', query];
          const result = await this.runner.run(args, { timeout: 120_000 });
          if (result.exitCode === 0) {
            this.send({ type: 'harvestResult', content: result.stdout || '(no context returned)' });
          } else {
            this.send({ type: 'harvestError', error: result.stderr || 'Harvest failed' });
          }
        } catch (err: any) {
          this.send({ type: 'harvestError', error: err.message });
        }
        break;
      }

      case 'openInEditor': {
        const content: string = msg.content ?? '';
        const doc = await vscode.workspace.openTextDocument({
          content: `# Harvested Context\n\n${content}`,
          language: 'markdown',
        });
        vscode.window.showTextDocument(doc, { preview: true, viewColumn: vscode.ViewColumn.One });
        break;
      }
    }
  }

  private dispose(): void {
    HarvestPanel.currentPanel = undefined;
    this.panel.dispose();
    this.disposables.forEach(d => d.dispose());
    this.disposables = [];
  }
}
