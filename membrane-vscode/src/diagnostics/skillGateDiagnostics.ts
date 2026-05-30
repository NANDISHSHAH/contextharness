import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';
import { log } from '../utils/output';

interface GateViolation {
  file: string;
  line: number;
  col?: number;
  col_end?: number;
  message: string;
  severity: 'error' | 'warning';
  skill: string;
  blast_radius?: number;
}

export class SkillGateDiagnosticProvider implements vscode.Disposable {
  private collection: vscode.DiagnosticCollection;
  private running = false;

  constructor(private runner: ContextRunner) {
    this.collection = vscode.languages.createDiagnosticCollection('membrane-skill-gates');
  }

  async runForFiles(uris: vscode.Uri[]): Promise<void> {
    if (this.running || uris.length === 0) return;
    this.running = true;
    try {
      const filePaths = uris.map(u => u.fsPath).join(',');
      const violations = await this.runner.runJson<GateViolation[]>(
        ['skills', 'run', '--files', filePaths, '--json'],
      );
      this.applyViolations(violations ?? []);
    } catch (err) {
      log(`Skill gate diagnostics error: ${err}`);
    } finally {
      this.running = false;
    }
  }

  async runForChangedFiles(): Promise<void> {
    const changed = await this.getGitChangedFiles();
    if (changed.length > 0) await this.runForFiles(changed);
  }

  private applyViolations(violations: GateViolation[]): void {
    this.collection.clear();
    const byFile = new Map<string, vscode.Diagnostic[]>();

    for (const v of violations) {
      const uri = vscode.Uri.file(v.file);
      const startLine = Math.max(0, (v.line ?? 1) - 1);
      const range = new vscode.Range(startLine, v.col ?? 0, startLine, v.col_end ?? 999);
      const msg = v.blast_radius != null
        ? `[Membrane/${v.skill}] ${v.message} (blast radius: ${v.blast_radius})`
        : `[Membrane/${v.skill}] ${v.message}`;
      const diag = new vscode.Diagnostic(
        range,
        msg,
        v.severity === 'error' ? vscode.DiagnosticSeverity.Error : vscode.DiagnosticSeverity.Warning,
      );
      diag.source = `membrane`;
      diag.code = v.skill;

      const key = uri.toString();
      if (!byFile.has(key)) byFile.set(key, []);
      byFile.get(key)!.push(diag);
    }

    byFile.forEach((diags, key) => this.collection.set(vscode.Uri.parse(key), diags));
  }

  hookFileSave(context: vscode.ExtensionContext): void {
    context.subscriptions.push(
      vscode.workspace.onDidSaveTextDocument(doc => {
        if (doc.uri.scheme === 'file') {
          this.runForFiles([doc.uri]);
        }
      }),
    );

    // Register "run skill gates on all changed files" command
    context.subscriptions.push(
      vscode.commands.registerCommand('membrane.runSkillGatesAll', async () => {
        await vscode.window.withProgress(
          { location: vscode.ProgressLocation.Notification, title: 'Membrane: Running skill gates...' },
          async () => this.runForChangedFiles(),
        );
        vscode.commands.executeCommand('workbench.action.problems.focus');
      }),
    );
  }

  private async getGitChangedFiles(): Promise<vscode.Uri[]> {
    const { exec } = require('child_process');
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!workspaceRoot) return [];

    return new Promise(resolve => {
      exec('git diff --name-only HEAD', { cwd: workspaceRoot }, (err: any, stdout: string) => {
        if (err) { resolve([]); return; }
        const files = stdout.trim().split('\n').filter(Boolean);
        resolve(files.map(f => vscode.Uri.file(`${workspaceRoot}/${f}`)));
      });
    });
  }

  dispose(): void {
    this.collection.dispose();
  }
}
