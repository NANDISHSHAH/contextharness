import * as vscode from 'vscode';
import { BuildService } from '../build/buildService';
import { FileWatcherManager } from '../watcher/fileWatcher';
import { COMMANDS } from '../constants';
import { log } from '../utils/output';

interface TreeProviders {
  symbolExplorer?: any;
  contextDebt?: any;
  skillGates?: any;
  agentLocks?: any;
  failurePatterns?: any;
  trustScores?: any;
  playbook?: any;
}

export function registerBuildCommands(
  context: vscode.ExtensionContext,
  buildService: BuildService,
  fileWatcher: FileWatcherManager,
  providers?: TreeProviders,
): void {
  const refreshProviders = async () => {
    try {
      if (providers?.symbolExplorer) await providers.symbolExplorer.refresh?.();
      if (providers?.contextDebt) await providers.contextDebt.refresh?.();
      if (providers?.skillGates) await providers.skillGates.refresh?.();
      if (providers?.agentLocks) await providers.agentLocks.refresh?.();
      if (providers?.failurePatterns) await providers.failurePatterns.refresh?.();
      if (providers?.trustScores) await providers.trustScores.refresh?.();
      if (providers?.playbook) await providers.playbook.refresh?.();
    } catch (error) {
      log(`Error refreshing providers: ${error}`);
    }
  };

  // membrane.build
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.build, async () => {
      log('Command: build');
      const success = await buildService.build();
      if (success) {
        await refreshProviders();
        vscode.window.showInformationMessage('Membrane: Build completed');
      } else {
        vscode.window.showErrorMessage('Membrane: Build failed');
      }
    }),
  );

  // membrane.incrementalBuild
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.incrementalBuild, async () => {
      log('Command: incremental build');
      const success = await buildService.incrementalBuild();
      if (success) {
        await refreshProviders();
      } else {
        vscode.window.showErrorMessage('Membrane: Incremental build failed');
      }
    }),
  );

  // membrane.watch
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.watch, async () => {
      log('Command: toggle watch');
      fileWatcher.toggle();
      const status = fileWatcher.isActive() ? 'enabled' : 'disabled';
      vscode.window.showInformationMessage(`Membrane: File watcher ${status}`);
    }),
  );
}
