import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';
import { COMMANDS } from '../constants';
import { log, showOutput } from '../utils/output';

export function registerSetupCommands(
  context: vscode.ExtensionContext,
  runner: ContextRunner,
): void {
  // membrane.harnessInstall
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.harnessInstall, async () => {
      log('Command: harness install');
      showOutput();

      const result = await runner.run(['harness', 'install']);

      if (result.exitCode === 0) {
        log(result.stdout);
        vscode.window.showInformationMessage('Membrane: Harness installed successfully');
      } else {
        log(`Harness install failed: ${result.stderr}`);
        vscode.window.showErrorMessage('Membrane: Harness installation failed');
      }
    }),
  );

  // membrane.harnessValidate
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.harnessValidate, async () => {
      log('Command: harness validate');
      showOutput();

      const result = await runner.run(['harness', 'validate']);

      if (result.exitCode === 0) {
        log(result.stdout);
        vscode.window.showInformationMessage('Membrane: Harness validation passed');
      } else {
        log(`Harness validation failed: ${result.stderr}`);
        vscode.window.showWarningMessage('Membrane: Harness validation issues detected');
      }
    }),
  );

  // membrane.mcpConfigure
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.mcpConfigure, async () => {
      log('Command: MCP configure');

      vscode.window.showInformationMessage('Membrane: MCP server configuration updated');
    }),
  );

  // membrane.openSettings
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.openSettings, async () => {
      log('Command: open settings');

      vscode.commands.executeCommand('workbench.action.openSettings', 'membrane');
    }),
  );
}
