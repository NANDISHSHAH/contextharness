import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';
import { COMMANDS } from '../constants';
import { log, showOutput } from '../utils/output';

async function showAsMarkdownDoc(content: string, title: string): Promise<void> {
  const doc = await vscode.workspace.openTextDocument({
    content: `# ${title}\n\n${content}`,
    language: 'markdown',
  });
  await vscode.window.showTextDocument(doc, {
    preview: true,
    viewColumn: vscode.ViewColumn.Beside,
  });
}

export function registerHarvestCommands(
  context: vscode.ExtensionContext,
  runner: ContextRunner,
): void {
  // membrane.harvest
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.harvest, async () => {
      log('Command: harvest');

      const query = await vscode.window.showInputBox({
        prompt: 'Enter query for context harvesting',
        placeHolder: 'e.g., "authentication flow"',
      });

      if (!query) {
        return;
      }

      showOutput();
      log(`Harvesting context for: "${query}"`);

      const result = await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: `Membrane: Harvesting context for "${query}"`,
          cancellable: false,
        },
        async () => runner.run(['harvest', query]),
      );

      if (result.exitCode === 0) {
        log(result.stdout);
        await showAsMarkdownDoc(result.stdout || '_no context returned_', `Harvest: ${query}`);
      } else {
        log(`Harvest failed: ${result.stderr}`);
        vscode.window.showErrorMessage(`Membrane: Harvest failed — ${result.stderr || 'unknown error'}`);
      }
    }),
  );

  // membrane.ask
  context.subscriptions.push(
    vscode.commands.registerCommand(COMMANDS.ask, async () => {
      log('Command: ask');

      const question = await vscode.window.showInputBox({
        prompt: 'Ask a question about your codebase',
        placeHolder: 'e.g., "How does authentication work?"',
      });

      if (!question) {
        return;
      }

      showOutput();
      log(`Asking: "${question}"`);

      // Detect LLM availability from VSCode settings OR workspace .env
      const settingLlm = vscode.workspace
        .getConfiguration()
        .get<string>('membrane.llmProvider');
      const envLlm = runner.getEnvVar('CONTEXTPACK_LLM_PROVIDER');
      const hasAzure = !!runner.getEnvVar('AZURE_OPENAI_ENDPOINT');
      const hasOpenai = !!runner.getEnvVar('OPENAI_API_KEY');
      const useLlm = settingLlm || envLlm || (hasAzure ? 'azure_foundry' : hasOpenai ? 'openai' : '');
      const args = useLlm ? ['ask', question, '--llm'] : ['ask', question];
      log(`LLM provider resolved to: ${useLlm || '(offline)'}`);

      const result = await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: `Membrane: ${useLlm ? 'Asking LLM' : 'Synthesising offline'}: "${question}"`,
          cancellable: false,
        },
        async () => runner.run(args, { timeout: 180000 }),
      );

      if (result.exitCode === 0) {
        log(result.stdout);
        await showAsMarkdownDoc(result.stdout || '_no answer_', `Ask: ${question}`);
      } else {
        log(`Ask failed: ${result.stderr}`);
        vscode.window.showErrorMessage(`Membrane: Ask failed — ${result.stderr || 'unknown error'}`);
      }
    }),
  );
}
