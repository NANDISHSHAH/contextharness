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

      const result = await runner.run(['coupling', 'trend']);

      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Coupling trend failed: ${result.stderr}`);
      }
    }),
  );
}
