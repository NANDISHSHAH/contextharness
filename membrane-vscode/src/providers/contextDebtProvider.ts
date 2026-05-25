import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';
import { log } from '../utils/output';

class DebtTreeItem extends vscode.TreeItem {
  constructor(
    label: string,
    collapsibleState: vscode.TreeItemCollapsibleState,
    public score?: number,
    public tier?: string,
  ) {
    super(label, collapsibleState);

    if (tier) {
      this.tooltip = `Score: ${score?.toFixed(2) || 'N/A'} (${tier})`;

      if (tier === 'CRITICAL') {
        this.iconPath = new vscode.ThemeIcon('error', new vscode.Color([255, 0, 0]));
      } else if (tier === 'HIGH') {
        this.iconPath = new vscode.ThemeIcon('warning', new vscode.Color([255, 165, 0]));
      } else {
        this.iconPath = new vscode.ThemeIcon('check');
      }
    }
  }
}

export class ContextDebtProvider implements vscode.TreeDataProvider<DebtTreeItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<DebtTreeItem | undefined | null | void> =
    new vscode.EventEmitter<DebtTreeItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<DebtTreeItem | undefined | null | void> =
    this._onDidChangeTreeData.event;

  private data: any[] = [];

  constructor(private runner?: ContextRunner) {}

  getTreeItem(element: DebtTreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: DebtTreeItem): Thenable<DebtTreeItem[]> {
    if (!element) {
      if (this.data.length === 0) {
        return Promise.resolve([
          new DebtTreeItem('Run "Build Index" to analyze context debt', vscode.TreeItemCollapsibleState.None),
        ]);
      }

      return Promise.resolve(
        this.data.map(
          (item) =>
            new DebtTreeItem(
              item.module || 'Unknown',
              vscode.TreeItemCollapsibleState.None,
              item.score,
              item.tier,
            ),
        ),
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
      const result = await this.runner.runJson(['debt', '--json']);
      if (Array.isArray(result)) {
        this.data = result;
      }
    } catch (error) {
      log(`Failed to load context debt: ${error}`);
    }

    this._onDidChangeTreeData.fire();
  }
}
