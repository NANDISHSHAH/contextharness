import * as vscode from 'vscode';
import { BRAND } from './constants';

export type MembraneState = 'initializing' | 'building' | 'ready' | 'error' | 'disabled';

const STATE_CONFIG: Record<MembraneState, { icon: string; label: string; bg?: string }> = {
  initializing: { icon: '$(sync~spin)', label: 'Starting...' },
  building:     { icon: '$(sync~spin)', label: 'Building...' },
  ready:        { icon: '$(check)',     label: 'Ready' },
  error:        { icon: '$(error)',     label: 'Error' },
  disabled:     { icon: '$(circle-slash)', label: 'Disabled' },
};

export class StatusBarManager implements vscode.Disposable {
  private stateItem: vscode.StatusBarItem;
  private conflictItem: vscode.StatusBarItem;
  private _state: MembraneState = 'initializing';
  private conflictInterval: NodeJS.Timeout | undefined;

  constructor() {
    this.stateItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      10,
    );
    this.stateItem.command = 'membrane.showStatus';

    this.conflictItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      9,
    );
    this.conflictItem.command = 'membrane.locksShow';

    this.setState('initializing');
    this.stateItem.show();
  }

  setState(state: MembraneState, detail?: string): void {
    this._state = state;
    const cfg = STATE_CONFIG[state];
    const suffix = detail ? ` — ${detail.slice(0, 35)}` : '';
    this.stateItem.text = `${cfg.icon} ${BRAND.shortName}: ${cfg.label}${suffix}`;
    this.stateItem.tooltip =
      state === 'error'
        ? `${BRAND.name}: ${detail || 'Unknown error'} — click for options`
        : `${BRAND.name} — ${cfg.label}`;
    this.stateItem.backgroundColor =
      state === 'error'
        ? new vscode.ThemeColor('statusBarItem.errorBackground')
        : undefined;
  }

  setConflicts(count: number): void {
    if (count === 0) {
      this.conflictItem.hide();
      return;
    }
    this.conflictItem.text = `$(warning) ${count} Agent Conflict${count > 1 ? 's' : ''}`;
    this.conflictItem.tooltip = `${count} agent lock conflict(s) — click to review`;
    this.conflictItem.backgroundColor = new vscode.ThemeColor(
      'statusBarItem.warningBackground',
    );
    this.conflictItem.show();
  }

  startConflictPolling(
    pollFn: () => Promise<number>,
    intervalMs = 30_000,
  ): void {
    this.stopConflictPolling();
    const run = async () => {
      try {
        const count = await pollFn();
        this.setConflicts(count);
      } catch {
        // silently ignore polling errors
      }
    };
    run();
    this.conflictInterval = setInterval(run, intervalMs);
  }

  stopConflictPolling(): void {
    if (this.conflictInterval) {
      clearInterval(this.conflictInterval);
      this.conflictInterval = undefined;
    }
  }

  get state(): MembraneState {
    return this._state;
  }

  dispose(): void {
    this.stopConflictPolling();
    this.stateItem.dispose();
    this.conflictItem.dispose();
  }
}
