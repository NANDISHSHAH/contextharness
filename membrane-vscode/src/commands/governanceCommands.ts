import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';
import { COMMANDS } from '../constants';
import { log, showOutput } from '../utils/output';

export function registerGovernanceCommands(
  context: vscode.ExtensionContext,
  runner: ContextRunner,
): void {
  // membrane.debtReport
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.debtReport, async () => {
      log('Command: debt report');
      showOutput();

      const result = await runner.run(['debt']);

      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Debt report failed: ${result.stderr}`);
      }
    }),
  );

  // membrane.locksShow
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.locksShow, async () => {
      log('Command: show locks');
      showOutput();

      const result = await runner.run(['locks']);

      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Locks query failed: ${result.stderr}`);
      }
    }),
  );

  // membrane.patternsShow
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.patternsShow, async () => {
      log('Command: show patterns');
      showOutput();

      const result = await runner.run(['patterns']);

      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Patterns query failed: ${result.stderr}`);
      }
    }),
  );

  // membrane.contractsShow
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.contractsShow, async () => {
      log('Command: show contracts');

      const symbol = await vscode.window.showInputBox({
        prompt: 'Enter symbol name',
        placeHolder: 'e.g., "authenticate"',
      });

      if (!symbol) {
        return;
      }

      showOutput();
      log(`Getting contracts for: ${symbol}`);

      const result = await runner.run(['contracts', 'show', symbol]);

      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Contracts query failed: ${result.stderr}`);
      }
    }),
  );

  // membrane.couplingTrend
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.couplingTrend, async () => {
      log('Command: coupling trend');
      showOutput();

      const result = await runner.runJson(['coupling', '--json']);
      if (!result || typeof result !== 'object') {
        log('Coupling trend: no data yet — run builds to accumulate metrics.');
        return;
      }

      const r = result as {
        coupling_change_pct: number;
        hub_change: number;
        cycle_change: number;
        is_decaying: boolean;
        alert_message: string;
        hotspot_modules: string[];
        snapshot_count: number;
        latest?: {
          edge_count: number;
          node_count: number;
          hub_count: number;
          cycle_count: number;
          avg_coupling: number;
        };
      };

      const lines: string[] = ['## Coupling Trend'];
      if (r.latest) {
        lines.push(
          `Latest graph: ${r.latest.edge_count} edges / ${r.latest.node_count} nodes | ` +
            `${r.latest.hub_count} hubs | ${r.latest.cycle_count} cycles`,
          `Avg coupling: ${r.latest.avg_coupling.toFixed(4)}`,
        );
      }
      lines.push(
        `30d change: ${r.coupling_change_pct >= 0 ? '+' : ''}${r.coupling_change_pct}%`,
        `Hub change: ${r.hub_change >= 0 ? '+' : ''}${r.hub_change}`,
        `Cycle change: ${r.cycle_change >= 0 ? '+' : ''}${r.cycle_change}`,
        `Snapshots recorded: ${r.snapshot_count}`,
      );
      if (r.is_decaying) {
        lines.push('', `🚨 DECAY ALERT: ${r.alert_message}`);
      }
      if (r.hotspot_modules.length > 0) {
        lines.push('', `Hotspot modules: ${r.hotspot_modules.slice(0, 5).join(', ')}`);
      }
      log(lines.join('\n'));
    }),
  );

  // membrane.trustShow
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.trustShow, async () => {
      log('Command: show trust scores');
      showOutput();

      const result = await runner.run(['trust']);

      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Trust scores failed: ${result.stderr}`);
      }
    }),
  );

  // membrane.playbookShow
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.playbookShow, async () => {
      log('Command: show playbook proposals');
      showOutput();

      const result = await runner.run(['playbook']);

      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Playbook proposals failed: ${result.stderr}`);
      }
    }),
  );
}
