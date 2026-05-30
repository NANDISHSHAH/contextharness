import * as vscode from 'vscode';
import { detectUvPath, verifyContextpack } from './python/detector';
import { installContextpack, isContextpackInstalled } from './python/installer';
import { createRunner, ContextRunner } from './python/runner';
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
import { BRAND, COMMANDS } from './constants';
import { StatusBarManager } from './statusBar';
import { SymbolExplorerProvider } from './providers/symbolExplorerProvider';
import { ContextDebtProvider } from './providers/contextDebtProvider';
import { SkillGatesProvider } from './providers/skillGatesProvider';
import { AgentLocksProvider } from './providers/agentLocksProvider';
import { FailurePatternsProvider } from './providers/failurePatternsProvider';
import { TrustScoresProvider } from './providers/trustScoresProvider';
import { PlaybookProvider } from './providers/playbookProvider';
import { SkillGateDiagnosticProvider } from './diagnostics/skillGateDiagnostics';
import { WizardPanel } from './panels/WizardPanel';
import { GraphPanel } from './panels/GraphPanel';
import { HarvestPanel } from './panels/HarvestPanel';
import { DebtDashboard } from './panels/DebtDashboard';
import { registerChatParticipant } from './chatParticipant';

let buildService: BuildService | null = null;
let fileWatcher: FileWatcherManager | null = null;
let mcpManager: McpServerManager | null = null;
let statusBar: StatusBarManager | null = null;
let symbolExplorer: SymbolExplorerProvider | null = null;
let contextDebt: ContextDebtProvider | null = null;
let skillGates: SkillGatesProvider | null = null;
let agentLocks: AgentLocksProvider | null = null;
let failurePatterns: FailurePatternsProvider | null = null;
let trustScores: TrustScoresProvider | null = null;
let playbook: PlaybookProvider | null = null;
let diagnostics: SkillGateDiagnosticProvider | null = null;

export async function activate(context: vscode.ExtensionContext) {
  log(`${BRAND.name} activated`);

  // Status bar is always created — user can always see extension state.
  statusBar = new StatusBarManager();
  context.subscriptions.push(statusBar);

  const workspaceRoot = getWorkspaceRoot();
  if (!workspaceRoot) {
    statusBar.setState('disabled', 'no workspace folder');
    log('No workspace folder open');
    return;
  }

  // membrane.showStatus — opens quick pick with recovery actions.
  context.subscriptions.push(
    vscode.commands.registerCommand('membrane.showStatus', async () => {
      const pick = await vscode.window.showQuickPick(
        [
          { label: '$(refresh) Retry Setup', detail: 'Re-run the full activation sequence' },
          { label: '$(output) View Logs', detail: 'Open the Membrane output channel' },
          { label: '$(gear) Open Settings', detail: 'Open Membrane extension settings' },
          { label: '$(play) Run Build Index', detail: 'Index codebase symbols and graph' },
        ],
        { placeHolder: `Membrane — ${statusBar?.state ?? 'unknown'}` },
      );
      if (!pick) return;
      if (pick.label.includes('Retry')) vscode.commands.executeCommand('workbench.action.reloadWindow');
      if (pick.label.includes('Logs'))  vscode.commands.executeCommand('workbench.action.output.toggleOutput');
      if (pick.label.includes('Settings')) vscode.commands.executeCommand('workbench.action.openSettings', 'membrane');
      if (pick.label.includes('Build')) vscode.commands.executeCommand(COMMANDS.build);
    }),
  );

  let runner: ContextRunner;

  try {
    // Step 1: Detect uv
    statusBar.setState('initializing', 'checking uv');
    log('Detecting uv executable...');
    const uvPath = detectUvPath(context.extensionPath);

    if (!uvPath) {
      statusBar.setState('error', 'uv not found — install from astral.sh/uv');
      vscode.window.showErrorMessage(
        `${BRAND.name}: Could not find uv executable.`,
        'Install uv',
      ).then(action => {
        if (action === 'Install uv') {
          vscode.env.openExternal(vscode.Uri.parse('https://docs.astral.sh/uv/installation/'));
        }
      });
      return;
    }
    log(`Found uv at: ${uvPath}`);

    // Step 2: Install contextpack if needed
    if (!isContextpackInstalled()) {
      statusBar.setState('initializing', 'installing contextpack');
      log('contextpack not installed, installing...');

      const installed = await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: `${BRAND.name}: Installing contextpack`,
          cancellable: false,
        },
        async (progress) => installContextpack(uvPath, context.extensionPath, workspaceRoot, progress),
      );

      if (!installed) {
        statusBar.setState('error', 'contextpack install failed');
        return;
      }
      log('Installation complete.');
    }

    // Step 3: Verify (non-fatal — warn but continue)
    statusBar.setState('initializing', 'verifying installation');
    const verification = await verifyContextpack(uvPath);
    if (!verification.ok) {
      log(`Verification warning: ${verification.error} — continuing anyway`);
    } else {
      log(`contextpack verified: ${verification.version}`);
    }

    // Step 4: Build env + runner
    const envVars = await buildEnvVars(context.secrets);
    runner = createRunner(uvPath, workspaceRoot, envVars);

    // Step 5: Build service + file watcher
    buildService = new BuildService(workspaceRoot, runner);
    fileWatcher = new FileWatcherManager(workspaceRoot, buildService);
    fileWatcher.start();

    // Step 6: MCP server (non-fatal — providers still work without it)
    statusBar.setState('initializing', 'starting MCP server');
    try {
      mcpManager = new McpServerManager(workspaceRoot, runner, uvPath);
      await mcpManager.start();
    } catch (mcpErr: any) {
      log(`MCP server failed to start: ${mcpErr.message} — continuing without MCP`);
    }

  } catch (err: any) {
    statusBar.setState('error', err.message?.slice(0, 40));
    log(`Activation error: ${err.message}`);
    vscode.window.showErrorMessage(
      `${BRAND.name}: Initialization failed — ${err.message}`,
      'View Logs',
    ).then(action => {
      if (action === 'View Logs') vscode.commands.executeCommand('workbench.action.output.toggleOutput');
    });
    return;
  }

  // Step 7: Register providers (always, even if MCP isn't ready)
  symbolExplorer    = new SymbolExplorerProvider();
  contextDebt       = new ContextDebtProvider(runner);
  skillGates        = new SkillGatesProvider(runner);
  agentLocks        = new AgentLocksProvider(runner);
  failurePatterns   = new FailurePatternsProvider(runner);
  trustScores       = new TrustScoresProvider(runner);
  playbook          = new PlaybookProvider(runner);

  vscode.window.registerTreeDataProvider('membrane.symbolExplorer', symbolExplorer);
  vscode.window.registerTreeDataProvider('membrane.contextDebt',    contextDebt);
  vscode.window.registerTreeDataProvider('membrane.skillGates',     skillGates);
  vscode.window.registerTreeDataProvider('membrane.agentLocks',     agentLocks);
  vscode.window.registerTreeDataProvider('membrane.failurePatterns', failurePatterns);
  vscode.window.registerTreeDataProvider('membrane.trustScores',    trustScores);
  vscode.window.registerTreeDataProvider('membrane.playbook',       playbook);

  // Step 8: Register commands
  registerBuildCommands(context, buildService, fileWatcher, {
    symbolExplorer, contextDebt, skillGates, agentLocks, failurePatterns, trustScores, playbook,
  });
  registerHarvestCommands(context, runner, context.extensionUri);
  registerSkillCommands(context, runner, { skillGates, failurePatterns, contextDebt, agentLocks });
  registerGovernanceCommands(context, runner);
  registerSetupCommands(context, runner);

  // Tree-view refresh commands
  context.subscriptions.push(
    vscode.commands.registerCommand('membrane.refreshSymbolExplorer', () => symbolExplorer?.refresh()),
    vscode.commands.registerCommand('membrane.refreshContextDebt',    () => contextDebt?.refresh()),
    vscode.commands.registerCommand('membrane.refreshSkillGates',     () => skillGates?.refresh()),
    vscode.commands.registerCommand('membrane.refreshAgentLocks',     () => agentLocks?.refresh()),
    vscode.commands.registerCommand('membrane.refreshFailurePatterns', () => failurePatterns?.refresh()),
    vscode.commands.registerCommand('membrane.refreshTrustScores',    () => trustScores?.refresh()),
    vscode.commands.registerCommand('membrane.refreshPlaybook',       () => playbook?.refresh()),
  );

  // Graph, Harvest, and Debt panel commands
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.graphView, () =>
      GraphPanel.show(context, runner),
    ),
    vscode.commands.registerCommand('membrane.harvestPanel', () =>
      HarvestPanel.show(context, runner),
    ),
    vscode.commands.registerCommand('membrane.debtDashboard', () =>
      DebtDashboard.show(runner),
    ),
  );

  // Phase 3: @membrane chat participant
  registerChatParticipant(context, runner);

  // Step 9: Skill gate diagnostics
  diagnostics = new SkillGateDiagnosticProvider(runner);
  diagnostics.hookFileSave(context);
  context.subscriptions.push(diagnostics);

  // Step 10: Conflict polling on status bar
  statusBar.startConflictPolling(async () => {
    try {
      const locks = await runner.runJson(['locks', '--json']);
      return Array.isArray(locks) ? locks.length : 0;
    } catch {
      return 0;
    }
  });

  // Step 11: Failure pattern warnings on active file change
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor(async (editor) => {
      if (!editor || editor.document.uri.scheme !== 'file') return;
      const filePath = editor.document.uri.fsPath;
      try {
        const patterns = await runner.runJson(['patterns', '--file', filePath, '--json']);
        if (Array.isArray(patterns) && patterns.length > 0) {
          const action = await vscode.window.showWarningMessage(
            `${BRAND.name}: ${patterns.length} known failure pattern(s) in this file`,
            'Review Patterns',
            'Dismiss',
          );
          if (action === 'Review Patterns') {
            vscode.commands.executeCommand(COMMANDS.patternsShow);
          }
        }
      } catch {
        // file may not be indexed — ignore
      }
    }),
  );

  // Initial provider refresh
  await Promise.allSettled([
    symbolExplorer.refresh(),
    contextDebt.refresh(),
    skillGates.refresh(),
    agentLocks.refresh(),
    failurePatterns.refresh(),
    trustScores.refresh(),
    playbook.refresh(),
  ]);

  statusBar.setState('ready');

  // First-run wizard
  const initialized = context.globalState.get<boolean>('membrane.initialized');
  if (!initialized && !isContextpackInitialized()) {
    WizardPanel.show(context, runner);
  } else if (!isContextpackInitialized()) {
    vscode.window.showInformationMessage(
      `${BRAND.name}: Ready. Run "Build Index" (${COMMANDS.build}) to index your codebase.`,
      'Build Now',
    ).then(action => {
      if (action === 'Build Now') vscode.commands.executeCommand(COMMANDS.build);
    });
  }

  log(`${BRAND.name} initialization complete`);
}

export async function deactivate() {
  log(`${BRAND.name} deactivating`);
  fileWatcher?.dispose();
  if (mcpManager) {
    await mcpManager.stop();
    mcpManager.dispose();
  }
  buildService?.dispose();
  disposeOutput();
}

export function getProviders() {
  return { symbolExplorer, contextDebt, skillGates, agentLocks, failurePatterns, trustScores, playbook };
}
