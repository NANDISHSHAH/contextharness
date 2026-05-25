import * as vscode from 'vscode';
import { detectUvPath, verifyContextpack } from './python/detector';
import { installContextpack, isContextpackInstalled } from './python/installer';
import { createRunner } from './python/runner';
import { buildEnvVars } from './utils/config';
import { getWorkspaceRoot, isContextpackInitialized } from './utils/workspace';
import { McpServerManager } from './mcp/manager';
import { BuildService } from './build/buildService';
import { FileWatcherManager } from './watcher/fileWatcher';
import { registerBuildCommands } from './commands/buildCommands';
import { registerHarvestCommands } from './commands/harvestCommands';
import { registerSkillCommands } from './commands/skillCommands';
import { registerGovernanceCommands } from './commands/governanceCommands';
import { registerSetupCommands } from './commands/setupCommands';
import { log, dispose as disposeOutput } from './utils/output';
import { BRAND } from './constants';
import { SymbolExplorerProvider } from './providers/symbolExplorerProvider';
import { ContextDebtProvider } from './providers/contextDebtProvider';
import { SkillGatesProvider } from './providers/skillGatesProvider';
import { AgentLocksProvider } from './providers/agentLocksProvider';
import { FailurePatternsProvider } from './providers/failurePatternsProvider';

let buildService: BuildService | null = null;
let fileWatcher: FileWatcherManager | null = null;
let mcpManager: McpServerManager | null = null;
let symbolExplorer: SymbolExplorerProvider | null = null;
let contextDebt: ContextDebtProvider | null = null;
let skillGates: SkillGatesProvider | null = null;
let agentLocks: AgentLocksProvider | null = null;
let failurePatterns: FailurePatternsProvider | null = null;

export async function activate(context: vscode.ExtensionContext) {
  log(`${BRAND.name} activated`);

  const workspaceRoot = getWorkspaceRoot();
  if (!workspaceRoot) {
    log('No workspace folder open');
    return;
  }

  try {
    // Phase 1: Detect uv
    log('Detecting uv executable...');
    const uvPath = detectUvPath(context.extensionPath);

    if (!uvPath) {
      vscode.window.showErrorMessage(
        `${BRAND.name}: Could not find uv executable. Please install uv from https://docs.astral.sh/uv/installation/`,
      );
      return;
    }

    log(`Found uv at: ${uvPath}`);

    // Phase 2: Check if contextpack is installed, if not install it
    if (!isContextpackInstalled()) {
      log('contextpack not installed, installing...');

      const result = await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: `${BRAND.name}: Installing contextpack`,
          cancellable: false,
        },
        async (progress) => {
          return await installContextpack(uvPath, context.extensionPath, progress);
        },
      );

      if (!result) {
        vscode.window.showErrorMessage(`${BRAND.name}: Failed to install contextpack`);
        return;
      }

      log('Installation complete, continuing...');
    }

    // Phase 3: Verify contextpack (skip if just installed)
    log('Verifying contextpack installation...');
    const verification = await verifyContextpack(uvPath);

    if (!verification.ok) {
      // If verification fails but we have a venv, try to continue anyway
      log(`Verification warning: ${verification.error}, but venv exists - continuing...`);
    } else {
      log(`contextpack verified: ${verification.version}`);
    }

    // Phase 4: Build environment variables
    const envVars = await buildEnvVars(context.secrets);

    // Phase 5: Create runner
    const runner = createRunner(uvPath, workspaceRoot, envVars);

    // Phase 6: Initialize build service
    buildService = new BuildService(workspaceRoot, runner);

    // Phase 7: Initialize file watcher
    fileWatcher = new FileWatcherManager(workspaceRoot, buildService);
    fileWatcher.start();

    // Phase 8: Initialize MCP server
    mcpManager = new McpServerManager(workspaceRoot, runner, uvPath);
    await mcpManager.start();

    // Phase 9: Register tree view providers
    symbolExplorer = new SymbolExplorerProvider();
    contextDebt = new ContextDebtProvider(runner);
    skillGates = new SkillGatesProvider(runner);
    agentLocks = new AgentLocksProvider(runner);
    failurePatterns = new FailurePatternsProvider(runner);

    vscode.window.registerTreeDataProvider('membrane.symbolExplorer', symbolExplorer);
    vscode.window.registerTreeDataProvider('membrane.contextDebt', contextDebt);
    vscode.window.registerTreeDataProvider('membrane.skillGates', skillGates);
    vscode.window.registerTreeDataProvider('membrane.agentLocks', agentLocks);
    vscode.window.registerTreeDataProvider('membrane.failurePatterns', failurePatterns);

    // Phase 10: Register commands
    registerBuildCommands(context, buildService, fileWatcher, {
      symbolExplorer,
      contextDebt,
      skillGates,
      agentLocks,
      failurePatterns,
    });
    registerHarvestCommands(context, runner);
    registerSkillCommands(context, runner, {
      skillGates,
      failurePatterns,
      contextDebt,
      agentLocks,
    });
    registerGovernanceCommands(context, runner);
    registerSetupCommands(context, runner);

    // Register tree-view refresh title-bar commands
    context.subscriptions.push(
      vscode.commands.registerCommand('membrane.refreshSymbolExplorer', () =>
        symbolExplorer?.refresh(),
      ),
      vscode.commands.registerCommand('membrane.refreshContextDebt', () =>
        contextDebt?.refresh(),
      ),
      vscode.commands.registerCommand('membrane.refreshSkillGates', () =>
        skillGates?.refresh(),
      ),
      vscode.commands.registerCommand('membrane.refreshAgentLocks', () =>
        agentLocks?.refresh(),
      ),
      vscode.commands.registerCommand('membrane.refreshFailurePatterns', () =>
        failurePatterns?.refresh(),
      ),
    );

    // Initial population of providers if a build already exists
    await Promise.all([
      symbolExplorer?.refresh(),
      contextDebt?.refresh(),
      skillGates?.refresh(),
      agentLocks?.refresh(),
      failurePatterns?.refresh(),
    ]);

    // Phase 11: Show welcome message if first time
    if (!isContextpackInitialized()) {
      vscode.window.showInformationMessage(
        `${BRAND.name}: Welcome! Your workspace is ready. Run "${BRAND.name}: Build Index" to get started.`,
      );
    }

    log(`${BRAND.name} initialization complete`);
  } catch (error: any) {
    log(`Activation error: ${error.message}`);
    vscode.window.showErrorMessage(`${BRAND.name}: Initialization failed - ${error.message}`);
  }
}

export async function deactivate() {
  log(`${BRAND.name} deactivating`);

  if (fileWatcher) {
    fileWatcher.dispose();
  }

  if (mcpManager) {
    await mcpManager.stop();
    mcpManager.dispose();
  }

  if (buildService) {
    buildService.dispose();
  }

  disposeOutput();
}

export function getProviders() {
  return {
    symbolExplorer,
    contextDebt,
    skillGates,
    agentLocks,
    failurePatterns,
  };
}
