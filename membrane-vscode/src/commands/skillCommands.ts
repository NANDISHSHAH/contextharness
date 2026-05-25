import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';
import { COMMANDS } from '../constants';
import { log, showOutput } from '../utils/output';

interface RefreshableProviders {
  skillGates?: { refresh: () => Promise<void> | void };
  failurePatterns?: { refresh: () => Promise<void> | void };
  contextDebt?: { refresh: () => Promise<void> | void };
  agentLocks?: { refresh: () => Promise<void> | void };
}

export function registerSkillCommands(
  context: vscode.ExtensionContext,
  runner: ContextRunner,
  providers?: RefreshableProviders,
): void {
  const refreshAfterSkill = async () => {
    try {
      await providers?.skillGates?.refresh();
      await providers?.failurePatterns?.refresh();
      await providers?.contextDebt?.refresh();
      await providers?.agentLocks?.refresh();
    } catch (e) {
      log(`Provider refresh error: ${e}`);
    }
  };

  // membrane.skillsPlan
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.skillsPlan, async (uri?: vscode.Uri) => {
      log('Command: skills plan');

      let filePath: string | undefined;
      if (uri?.fsPath) {
        filePath = uri.fsPath;
      } else {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
          vscode.window.showErrorMessage('Membrane: Open a file or right-click on a file first');
          return;
        }
        filePath = editor.document.fileName;
      }

      showOutput();
      log(`Getting skill plan for: ${filePath}`);

      const result = await runner.run(['skills', 'plan', filePath]);

      if (result.exitCode === 0) {
        log(result.stdout);
        // Show plan in a quick info popup
        const firstLine = (result.stdout || '')
          .split('\n')
          .find((l) => l.includes('skills'));
        if (firstLine) {
          vscode.window.showInformationMessage(
            `Membrane Skill Plan ready — see output for details`,
          );
        }
      } else {
        log(`Skill plan failed: ${result.stderr}`);
        vscode.window.showErrorMessage('Membrane: Skill plan failed');
      }
    }),
  );

  // membrane.skillsRun
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.skillsRun, async (uri?: vscode.Uri) => {
      log('Command: run skills');

      let filePath: string | undefined;
      if (uri?.fsPath) {
        filePath = uri.fsPath;
      } else {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
          // Default to running on the workspace root
          filePath = '.';
        } else {
          filePath = editor.document.fileName;
        }
      }

      showOutput();
      log(`Running skill gates for: ${filePath}`);

      await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: `Membrane: Running skill gates`,
          cancellable: false,
        },
        async () => {
          const result = await runner.run(['skills', 'run', filePath!]);
          if (result.exitCode === 0) {
            log(result.stdout);
            vscode.window.showInformationMessage(
              'Membrane: Skill gates passed ✅',
            );
          } else {
            log(result.stdout || '');
            log(`Skill run failed: ${result.stderr}`);
            vscode.window.showWarningMessage(
              'Membrane: Skill gates blocked — check Skill Gates view for details',
            );
          }
          await refreshAfterSkill();
        },
      );
    }),
  );

  // membrane.skillsHistory
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.skillsHistory, async () => {
      log('Command: skills history');
      showOutput();

      const result = await runner.run(['skills', 'history']);

      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Skills history failed: ${result.stderr}`);
      }
      await refreshAfterSkill();
    }),
  );
}
