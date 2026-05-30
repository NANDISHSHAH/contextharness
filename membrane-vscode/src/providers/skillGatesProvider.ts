import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';
import { log } from '../utils/output';

export class SkillGatesProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
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
        const item = new vscode.TreeItem('▶ Build Index to run skill gates', vscode.TreeItemCollapsibleState.None);
        item.command = { command: 'membrane.build', title: 'Build Index' };
        item.iconPath = new vscode.ThemeIcon('play');
        return Promise.resolve([item]);
      }

      return Promise.resolve(
        this.data.map((item) => {
          const passed = item.passed ?? (item.status === 'pass');
          const label = `${item.action_id || item.skill || 'Unknown'} — ${passed ? '✓ Passed' : '✗ Failed'}`;
          const treeItem = new vscode.TreeItem(label, vscode.TreeItemCollapsibleState.None);
          treeItem.tooltip = `Agent: ${item.agent_id || 'Unknown'}\nBlast radius: ${item.blast_radius ?? 'N/A'}`;
          treeItem.iconPath = new vscode.ThemeIcon(passed ? 'pass' : 'error');
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
      const result = await this.runner.runJson(['skills', 'history', '--json']);
      if (Array.isArray(result)) {
        this.data = result;
      }
    } catch (error) {
      log(`Failed to load skill gates: ${error}`);
    }

    this._onDidChangeTreeData.fire();
  }
}
