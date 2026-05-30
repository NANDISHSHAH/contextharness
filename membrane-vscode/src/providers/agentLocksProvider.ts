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
        return Promise.resolve([
          new vscode.TreeItem('No active agent locks'),
        ]);
      }

      return Promise.resolve(
        this.data.map((item) => {
          const item_obj = new vscode.TreeItem(
            `${item.agent_id || 'Unknown'} - ${item.files?.length || 0} files`,
            vscode.TreeItemCollapsibleState.None,
          );
          item_obj.tooltip = `Acquired: ${item.acquired_at || 'Unknown'}`;
          item_obj.iconPath = new vscode.ThemeIcon('lock');
          return item_obj;
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
