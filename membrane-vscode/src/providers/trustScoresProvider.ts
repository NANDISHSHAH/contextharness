import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';
import { log } from '../utils/output';

interface TrustEntry {
  file: string;
  tier: number;
  score: number;
  label: string;
  source_type: string;
  rationale: string;
}

const TIER_ICONS: Record<number, string> = {
  1: 'verified',
  2: 'pass',
  3: 'circle-outline',
  4: 'warning',
  5: 'error',
};

const TIER_LABELS: Record<number, string> = {
  1: 'T1:GroundTruth',
  2: 'T2:High',
  3: 'T3:Medium',
  4: 'T4:Low',
  5: 'T5:Unverified',
};

export class TrustScoresProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<vscode.TreeItem | undefined | null | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private data: TrustEntry[] = [];

  constructor(private runner?: ContextRunner) {}

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: vscode.TreeItem): Thenable<vscode.TreeItem[]> {
    if (!element) {
      if (this.data.length === 0) {
        const empty = new vscode.TreeItem('No trust data — run Build Index first');
        empty.iconPath = new vscode.ThemeIcon('info');
        return Promise.resolve([empty]);
      }

      return Promise.resolve(
        this.data.slice(0, 50).map((entry) => {
          const label = `${entry.label}  ${entry.file}`;
          const item = new vscode.TreeItem(label, vscode.TreeItemCollapsibleState.None);
          const iconName = TIER_ICONS[entry.tier] ?? 'circle-outline';
          item.iconPath = new vscode.ThemeIcon(iconName);
          item.tooltip = new vscode.MarkdownString(
            `**${entry.file}**\n\nTier: ${TIER_LABELS[entry.tier] ?? entry.tier}  \nScore: ${entry.score.toFixed(3)}  \nType: ${entry.source_type}  \n\n_${entry.rationale}_`,
          );
          item.description = `${entry.score.toFixed(3)}`;
          return item;
        }),
      );
    }
    return Promise.resolve([]);
  }

  setData(data: TrustEntry[]): void {
    this.data = data;
    this._onDidChangeTreeData.fire();
  }

  async refresh(): Promise<void> {
    if (!this.runner) {
      this._onDidChangeTreeData.fire();
      return;
    }
    try {
      const result = await this.runner.runJson(['trust', '--json']);
      if (Array.isArray(result)) {
        this.data = result as TrustEntry[];
      }
    } catch (error) {
      log(`Failed to load trust scores: ${error}`);
    }
    this._onDidChangeTreeData.fire();
  }
}
