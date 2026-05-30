import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';
import { log } from '../utils/output';

export class FailurePatternsProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<vscode.TreeItem | undefined | null | void> =
    new vscode.EventEmitter<vscode.TreeItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<vscode.TreeItem | undefined | null | void> =
    this._onDidChangeTreeData.event;

  private data: any[] = [];

  constructor(private runner?: ContextRunner) {}

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: vscode.TreeItem): Thenable<vscode.TreeItem[]> {
    if (!element) {
      if (this.data.length === 0) {
        const item = new vscode.TreeItem('No failure patterns detected', vscode.TreeItemCollapsibleState.None);
        item.iconPath = new vscode.ThemeIcon('check');
        return Promise.resolve([item]);
      }

      return Promise.resolve(
        this.data.map((item) => {
          const freq = item.count ?? item.frequency ?? 0;
          const severity = freq > 5 ? 'High' : freq > 1 ? 'Medium' : 'Low';
          const icon = freq > 5 ? 'error' : freq > 1 ? 'warning' : 'info';
          const label = `${item.category || item.pattern || 'Unknown'} (${freq}x · ${severity})`;
          const treeItem = new vscode.TreeItem(label, vscode.TreeItemCollapsibleState.None);
          treeItem.tooltip = [
            `Pattern: ${item.pattern_id || item.pattern || 'Unknown'}`,
            `Glob: ${item.glob || 'N/A'}`,
            `Last seen: ${item.last_seen || 'N/A'}`,
          ].join('\n');
          treeItem.iconPath = new vscode.ThemeIcon(icon);
          return treeItem;
        }),
      );
    }

    return Promise.resolve([]);
  }

  setData(data: any[]): void {
    this.data = data;
    this._onDidChangeTreeData.fire();
  }

  async refresh(): Promise<void> {
    if (!this.runner) {
      this._onDidChangeTreeData.fire();
      return;
    }

    try {
      const result = await this.runner.runJson(['patterns', '--json']);
      if (Array.isArray(result)) {
        this.data = result;
      }
    } catch (error) {
      log(`Failed to load failure patterns: ${error}`);
    }

    this._onDidChangeTreeData.fire();
  }
}
