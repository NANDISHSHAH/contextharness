import * as vscode from 'vscode';
import { BuildService } from '../build/buildService';
import { SETTINGS } from '../constants';
import { log } from '../utils/output';

export class FileWatcherManager {
  private watcher: vscode.FileSystemWatcher | null = null;
  private debounceTimer: NodeJS.Timeout | null = null;
  private debounceMs = 1500;
  private isWatching = false;

  constructor(
    private workspaceRoot: string,
    private buildService: BuildService,
  ) {}

  /**
   * Start watching for file changes.
   */
  start(): void {
    if (this.isWatching || this.watcher) {
      return;
    }

    const autoWatch = vscode.workspace.getConfiguration().get(SETTINGS.autoWatch, true);
    if (!autoWatch) {
      log('File watcher disabled in settings');
      return;
    }

    log('Starting file watcher (excluding .contextpack, node_modules, .git)');

    // Watch for changes to code files but exclude build artifacts
    const pattern = new vscode.RelativePattern(
      this.workspaceRoot,
      '**/*.{py,ts,tsx,js,jsx,md,yaml,yml,json}',
    );

    this.watcher = vscode.workspace.createFileSystemWatcher(pattern, true, false, true);

    // Debounce file change events
    this.watcher.onDidChange((uri) => {
      // Ignore changes in generated/config files
      if (uri.fsPath.includes('.contextpack') ||
          uri.fsPath.includes('.mcp.json') ||
          uri.fsPath.includes('node_modules') ||
          uri.fsPath.includes('.git')) {
        return;
      }
      this._onFileChange();
    });

    this.watcher.onDidCreate((uri) => {
      // Ignore changes in generated/config files
      if (uri.fsPath.includes('.contextpack') ||
          uri.fsPath.includes('.mcp.json') ||
          uri.fsPath.includes('node_modules') ||
          uri.fsPath.includes('.git')) {
        return;
      }
      this._onFileChange();
    });

    this.isWatching = true;
  }

  /**
   * Stop watching for file changes.
   */
  stop(): void {
    if (this.watcher) {
      this.watcher.dispose();
      this.watcher = null;
    }

    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }

    this.isWatching = false;
    log('Stopped file watcher');
  }

  /**
   * Toggle file watcher on/off.
   */
  toggle(): void {
    if (this.isWatching) {
      this.stop();
    } else {
      this.start();
    }
  }

  private _onFileChange(): void {
    // Debounce rapid file changes
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }

    this.debounceTimer = setTimeout(() => {
      log('Files changed, triggering incremental build');
      this.buildService.incrementalBuild();
      this.debounceTimer = null;
    }, this.debounceMs);
  }

  isActive(): boolean {
    return this.isWatching;
  }

  dispose(): void {
    this.stop();
  }
}
