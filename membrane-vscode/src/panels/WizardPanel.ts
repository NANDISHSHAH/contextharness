import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { ContextRunner } from '../python/runner';
import { detectUvPath } from '../python/detector';
import { installContextpack, isContextpackInstalled } from '../python/installer';
import { log } from '../utils/output';

export class WizardPanel {
  static currentPanel: WizardPanel | undefined;
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
    if (WizardPanel.currentPanel) {
      WizardPanel.currentPanel.panel.reveal(vscode.ViewColumn.One);
      return;
    }

    const panel = vscode.window.createWebviewPanel(
      'membrane.wizard',
      'Membrane: Setup Wizard',
      vscode.ViewColumn.One,
      {
        enableScripts: true,
        localResourceRoots: [vscode.Uri.joinPath(context.extensionUri, 'out')],
        retainContextWhenHidden: true,
      },
    );

    const instance = new WizardPanel(panel, context, runner);
    instance.panel.webview.html = instance.buildHtml();
    WizardPanel.currentPanel = instance;
  }

  private buildHtml(): string {
    const htmlPath = path.join(
      this.context.extensionPath,
      'webview-src',
      'wizard',
      'index.html',
    );
    const scriptUri = this.panel.webview.asWebviewUri(
      vscode.Uri.joinPath(this.context.extensionUri, 'out', 'webview-wizard.js'),
    );

    let html = fs.readFileSync(htmlPath, 'utf-8');
    // Replace the relative script reference with the compiled WebView URI
    html = html.replace(/<script src="\.\.\/wizard\.js"><\/script>/, `<script src="${scriptUri}"></script>`);
    return html;
  }

  private send(msg: object): void {
    this.panel.webview.postMessage(msg);
  }

  private log(text: string): void {
    log(`[Wizard] ${text}`);
    this.send({ type: 'wizardProgress', message: text });
  }

  private async handleMessage(msg: any): Promise<void> {
    switch (msg.type) {

      case 'wizardStep': {
        const step: number = msg.step ?? 0;
        // Step transitions trigger backend work
        if (step === 1) await this.runStep1CheckUv();
        if (step === 2) await this.runStep2Install();
        if (step === 3) await this.runStep3Init();
        if (step === 4) await this.runStep4Build();
        if (step === 5) await this.runStep5Mcp();
        break;
      }

      case 'wizardSkip':
        this.context.globalState.update('membrane.initialized', true);
        this.dispose();
        break;

      case 'wizardFinish':
        this.context.globalState.update('membrane.initialized', true);
        vscode.window.showInformationMessage('Membrane: Setup complete! Your codebase is indexed and ready.');
        this.dispose();
        break;
    }
  }

  private async runStep1CheckUv(): Promise<void> {
    this.log('Checking uv executable...');
    const uvPath = detectUvPath(this.context.extensionPath);
    if (uvPath) {
      this.log(`✓ uv found at: ${uvPath}`);
    } else {
      this.log('✗ uv not found. Install from https://docs.astral.sh/uv/installation/');
    }
  }

  private async runStep2Install(): Promise<void> {
    if (isContextpackInstalled()) {
      this.log('✓ contextpack already installed');
      return;
    }
    this.log('Installing contextpack...');
    const uvPath = detectUvPath(this.context.extensionPath);
    if (!uvPath) { this.log('✗ uv not found — cannot install'); return; }
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? '';
    const ok = await installContextpack(uvPath, this.context.extensionPath, workspaceRoot, {
      report: ({ message }) => { if (message) this.log(message); },
    });
    this.log(ok ? '✓ contextpack installed' : '✗ Installation failed — check Membrane output channel');
  }

  private async runStep3Init(): Promise<void> {
    this.log('Initializing workspace...');
    try {
      const res = await this.runner.run(['init']);
      this.log(res.exitCode === 0 ? '✓ Workspace initialized' : `✗ Init failed: ${res.stderr}`);
    } catch (err: any) {
      this.log(`✗ Init error: ${err.message}`);
    }
  }

  private async runStep4Build(): Promise<void> {
    this.log('Building index (this may take a minute)...');
    try {
      const res = await this.runner.run(['build'], { timeout: 300_000 });
      this.log(res.exitCode === 0 ? '✓ Index built successfully' : `✗ Build failed: ${res.stderr}`);
    } catch (err: any) {
      this.log(`✗ Build error: ${err.message}`);
    }
  }

  private async runStep5Mcp(): Promise<void> {
    this.log('Configuring MCP server...');
    try {
      const res = await this.runner.run(['harness', 'install']);
      this.log(res.exitCode === 0 ? '✓ MCP server configured' : `✗ MCP config failed: ${res.stderr}`);
    } catch (err: any) {
      this.log(`✗ MCP error: ${err.message}`);
    }
  }

  private dispose(): void {
    WizardPanel.currentPanel = undefined;
    this.panel.dispose();
    this.disposables.forEach(d => d.dispose());
    this.disposables = [];
  }
}
