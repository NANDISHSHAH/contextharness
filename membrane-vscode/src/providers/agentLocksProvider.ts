import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';
import { log } from '../utils/output';

export class AgentLocksProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
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
        const item = new vscode.TreeItem('No active agent locks', vscode.TreeItemCollapsibleState.None);
        item.iconPath = new vscode.ThemeIcon('unlock');
        return Promise.resolve([item]);
      }

      return Promise.resolve(
        this.data.map((item) => {
          const fileCount = item.files?.length ?? 1;
          const label = `${item.agent_id || 'Unknown agent'} — ${fileCount} file${fileCount > 1 ? 's' : ''}`;
          const treeItem = new vscode.TreeItem(label, vscode.TreeItemCollapsibleState.None);
          treeItem.tooltip = `Acquired: ${item.acquired_at || 'Unknown'}\nTTL: ${item.ttl_seconds ? `${item.ttl_seconds}s` : 'N/A'}`;
          treeItem.iconPath = new vscode.ThemeIcon('lock');
          treeItem.description = item.acquired_at ? `${item.acquired_at}` : undefined;
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
      const result = await this.runner.runJson(['locks', '--json']);
      if (Array.isArray(result)) {
        this.data = result;
      }
    } catch (error) {
      log(`Failed to load agent locks: ${error}`);
    }

    this._onDidChangeTreeData.fire();
  }
}
