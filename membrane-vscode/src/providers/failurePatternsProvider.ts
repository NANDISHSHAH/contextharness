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
        return Promise.resolve([
          new vscode.TreeItem('No failure patterns detected'),
        ]);
      }

      return Promise.resolve(
        this.data.map((item) => {
          const item_obj = new vscode.TreeItem(
            `${item.category || 'Unknown'} (${item.count || 0}x)`,
            vscode.TreeItemCollapsibleState.None,
          );
          item_obj.tooltip = `Pattern: ${item.pattern_id || 'Unknown'}\nGlob: ${item.glob || 'N/A'}`;
          item_obj.iconPath = new vscode.ThemeIcon('alert');
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
