import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { ENV_VARS, SETTINGS } from '../constants';
import { getWorkspaceRoot } from './workspace';
import { log } from './output';

/**
 * Build environment variables from VSCode settings.
 * Maps VSCode settings to Python environment variable names.
 */
export async function buildEnvVars(
  secretStorage: vscode.SecretStorage,
): Promise<Record<string, string>> {
  const config = vscode.workspace.getConfiguration();
  const env: Record<string, string> = {
    ...process.env,
  };

  const workspaceRoot = getWorkspaceRoot();
  if (workspaceRoot) {
    env[ENV_VARS.CONTEXTPACK_ROOT] = workspaceRoot;
  }

  // Embedding provider
  const embeddingProvider = config.get<string>(SETTINGS.embeddingProvider) || 'hash';
  env[ENV_VARS.CONTEXTPACK_EMBEDDING_PROVIDER] = embeddingProvider;

  // LLM provider
  const llmProvider = config.get<string>(SETTINGS.llmProvider);
  if (llmProvider) {
    env[ENV_VARS.CONTEXTPACK_LLM_PROVIDER] = llmProvider;
  }

  // OpenAI API key
  const openaiKey = await secretStorage.get('membrane.openaiApiKey');
  if (openaiKey) {
    env[ENV_VARS.OPENAI_API_KEY] = openaiKey;
  }

  // Azure OpenAI settings
  const azureEndpoint = config.get<string>(SETTINGS.azureEndpoint);
  if (azureEndpoint) {
    env[ENV_VARS.AZURE_OPENAI_ENDPOINT] = azureEndpoint;
  }

  const azureKey = await secretStorage.get('membrane.azureApiKey');
  if (azureKey) {
    env[ENV_VARS.AZURE_OPENAI_API_KEY] = azureKey;
  }

  const azureDeployment = config.get<string>(SETTINGS.azureDeployment);
  if (azureDeployment) {
    env[ENV_VARS.AZURE_OPENAI_DEPLOYMENT] = azureDeployment;
  }

  const azureEmbeddingDeploy = config.get<string>(SETTINGS.azureEmbeddingDeployment);
  if (azureEmbeddingDeploy) {
    env[ENV_VARS.AZURE_OPENAI_EMBEDDING_DEPLOYMENT] = azureEmbeddingDeploy;
  }

  // Jira settings
  const jiraUrl = config.get<string>(SETTINGS.jiraBaseUrl);
  if (jiraUrl) {
    env[ENV_VARS.JIRA_BASE_URL] = jiraUrl;
  }

  const jiraEmail = config.get<string>(SETTINGS.jiraEmail);
  if (jiraEmail) {
    env[ENV_VARS.JIRA_EMAIL] = jiraEmail;
  }

  const jiraToken = await secretStorage.get('membrane.jiraApiToken');
  if (jiraToken) {
    env[ENV_VARS.JIRA_API_TOKEN] = jiraToken;
  }

  // Max embed entities
  const maxEmbedEntities = config.get<number>(SETTINGS.maxEmbedEntities);
  if (maxEmbedEntities) {
    env[ENV_VARS.CONTEXTPACK_MAX_EMBED_ENTITIES] = String(maxEmbedEntities);
  }

  // Load .env file from workspace root if it exists (takes precedence over VSCode settings)
  if (workspaceRoot) {
    const envFilePath = path.join(workspaceRoot, '.env');
    if (fs.existsSync(envFilePath)) {
      const envContent = fs.readFileSync(envFilePath, 'utf-8');
      const lines = envContent.split('\n');
      let loadedCount = 0;
      const loadedKeys: string[] = [];
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#')) {
          const eqIdx = trimmed.indexOf('=');
          if (eqIdx > 0) {
            const key = trimmed.slice(0, eqIdx).trim();
            let value = trimmed.slice(eqIdx + 1).trim();
            // Strip surrounding quotes
            if (
              (value.startsWith('"') && value.endsWith('"')) ||
              (value.startsWith("'") && value.endsWith("'"))
            ) {
              value = value.slice(1, -1);
            }
            if (key && value) {
              env[key] = value;
              loadedCount++;
              // Only log key names, not values (might be secrets)
              loadedKeys.push(key);
            }
          }
        }
      }
      log(`Loaded ${loadedCount} env vars from .env: ${loadedKeys.join(', ')}`);
    } else {
      log(`No .env file found at ${envFilePath}`);
    }
  }

  return env;
}

/**
 * Ensure critical settings are set or warn the user.
 */
export function validateSettings(): string[] {
  const warnings: string[] = [];
  const config = vscode.workspace.getConfiguration();

  const embeddingProvider = config.get<string>(SETTINGS.embeddingProvider);
  if (!embeddingProvider || embeddingProvider === 'hash') {
    // hash is the default, no warning needed
  } else if (embeddingProvider === 'openai') {
    const hasKey = config.get<string>(SETTINGS.openaiApiKey);
    if (!hasKey) {
      warnings.push('OpenAI embedding provider selected but API key not configured');
    }
  } else if (embeddingProvider === 'azure_foundry') {
    const hasEndpoint = config.get<string>(SETTINGS.azureEndpoint);
    const hasDeployment = config.get<string>(SETTINGS.azureDeployment);
    if (!hasEndpoint || !hasDeployment) {
      warnings.push('Azure OpenAI embedding provider selected but endpoint/deployment not configured');
    }
  }

  return warnings;
}
