import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';
import { log } from '../utils/output';

interface PlaybookProposal {
  policy_name: string;
  description: string;
  file_pattern: string;
  skills_to_add: string[];
  confidence: number;
  evidence: string;
  yaml_block: string;
}

export class PlaybookProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<vscode.TreeItem | undefined | null | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private data: PlaybookProposal[] = [];

  constructor(private runner?: ContextRunner) {}

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: vscode.TreeItem): Thenable<vscode.TreeItem[]> {
    if (!element) {
      if (this.data.length === 0) {
        const empty = new vscode.TreeItem('No proposals yet — accumulate skill gate runs');
        empty.iconPath = new vscode.ThemeIcon('lightbulb');
        return Promise.resolve([empty]);
      }

      return Promise.resolve(
        this.data.map((proposal) => {
          const confidencePct = Math.round(proposal.confidence * 100);
          const item = new vscode.TreeItem(
            `${proposal.policy_name}  (${confidencePct}% confidence)`,
            vscode.TreeItemCollapsibleState.None,
          );
          item.iconPath = new vscode.ThemeIcon('lightbulb');
          item.tooltip = new vscode.MarkdownString(
            `**${proposal.policy_name}**\n\n${proposal.description}\n\n` +
              `**Pattern:** \`${proposal.file_pattern}\`  \n` +
              `**Skills:** ${proposal.skills_to_add.join(', ')}  \n\n` +
              `_${proposal.evidence}_\n\n` +
              `\`\`\`yaml\n${proposal.yaml_block}\n\`\`\``,
          );
          item.description = proposal.file_pattern;
          return item;
        }),
      );
    }
    return Promise.resolve([]);
  }

  setData(data: PlaybookProposal[]): void {
    this.data = data;
    this._onDidChangeTreeData.fire();
  }

  async refresh(): Promise<void> {
    if (!this.runner) {
      this._onDidChangeTreeData.fire();
      return;
    }
    try {
      const result = await this.runner.runJson(['playbook', '--json']);
      if (Array.isArray(result)) {
        this.data = result as PlaybookProposal[];
      }
    } catch (error) {
      log(`Failed to load playbook proposals: ${error}`);
    }
    this._onDidChangeTreeData.fire();
  }
}
