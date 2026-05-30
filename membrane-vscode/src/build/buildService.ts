import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';
import { log } from '../utils/output';
import { BRAND } from '../constants';

export class BuildService implements vscode.Disposable {
  constructor(
    private workspaceRoot: string,
    private runner: ContextRunner,
  ) {}

  async build(): Promise<boolean> {
    log('Starting full build...');
    const result = await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: `${BRAND.name}: Building index...`,
        cancellable: false,
      },
      async (progress) => {
        progress.report({ message: 'Scanning codebase...' });
        return this.runner.run(['build'], { timeout: 300_000 });
      },
    );
    if (result.exitCode === 0) {
      log('Build complete');
      return true;
    }
    log(`Build failed: ${result.stderr}`);
    return false;
  }

  async incrementalBuild(): Promise<boolean> {
    log('Starting incremental build...');
    const result = await this.runner.run(['build', '--incremental'], { timeout: 120_000 });
    if (result.exitCode === 0) {
      log('Incremental build complete');
      return true;
    }
    log(`Incremental build failed: ${result.stderr}`);
    return false;
  }

  dispose(): void {}
}
