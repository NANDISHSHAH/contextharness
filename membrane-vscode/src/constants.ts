/**
 * Membrane constants: brand strings, command IDs, environment variable names.
 */

export const BRAND = {
  name: 'Membrane',
  shortName: 'Membrane',
  tagline: 'Context Intelligence & Agent Governance',
  description:
    'Graph-native codebase understanding, skill gates, and agent governance.',
};

// Environment variable names (map VSCode settings to Python env vars)
export const ENV_VARS = {
  CONTEXTPACK_ROOT: 'CONTEXTPACK_ROOT',
  OPENAI_API_KEY: 'OPENAI_API_KEY',
  CONTEXTPACK_LLM_PROVIDER: 'CONTEXTPACK_LLM_PROVIDER',
  CONTEXTPACK_EMBEDDING_PROVIDER: 'CONTEXTPACK_EMBEDDING_PROVIDER',
  CONTEXTPACK_VECTOR_STORE: 'CONTEXTPACK_VECTOR_STORE',
  AZURE_OPENAI_ENDPOINT: 'AZURE_OPENAI_ENDPOINT',
  AZURE_OPENAI_API_KEY: 'AZURE_OPENAI_API_KEY',
  AZURE_OPENAI_DEPLOYMENT: 'AZURE_OPENAI_DEPLOYMENT',
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT',
  JIRA_BASE_URL: 'JIRA_BASE_URL',
  JIRA_EMAIL: 'JIRA_EMAIL',
  JIRA_API_TOKEN: 'JIRA_API_TOKEN',
  CONTEXTPACK_MAX_EMBED_ENTITIES: 'CONTEXTPACK_MAX_EMBED_ENTITIES',
  CONTEXTPACK_GUIDELINES_MAX_CHARS: 'CONTEXTPACK_GUIDELINES_MAX_CHARS',
};

// VSCode settings keys
export const SETTINGS = {
  autoMcpConfigure: 'membrane.autoMcpConfigure',
  autoWatch: 'membrane.autoWatch',
  embeddingProvider: 'membrane.embeddingProvider',
  llmProvider: 'membrane.llmProvider',
  openaiApiKey: 'membrane.openaiApiKey',
  azureEndpoint: 'membrane.azureEndpoint',
  azureApiKey: 'membrane.azureApiKey',
  azureDeployment: 'membrane.azureDeployment',
  azureEmbeddingDeployment: 'membrane.azureEmbeddingDeployment',
  jiraBaseUrl: 'membrane.jiraBaseUrl',
  jiraEmail: 'membrane.jiraEmail',
  jiraApiToken: 'membrane.jiraApiToken',
  maxEmbedEntities: 'membrane.maxEmbedEntities',
};

// Command IDs
export const COMMANDS = {
  build: 'membrane.build',
  incrementalBuild: 'membrane.incrementalBuild',
  watch: 'membrane.watch',
  harvest: 'membrane.harvest',
  ask: 'membrane.ask',
  graphView: 'membrane.graphView',
  skillsPlan: 'membrane.skillsPlan',
  skillsRun: 'membrane.skillsRun',
  skillsHistory: 'membrane.skillsHistory',
  debtReport: 'membrane.debtReport',
  locksShow: 'membrane.locksShow',
  patternsShow: 'membrane.patternsShow',
  contractsShow: 'membrane.contractsShow',
  couplingTrend: 'membrane.couplingTrend',
  harnessInstall: 'membrane.harnessInstall',
  harnessValidate: 'membrane.harnessValidate',
  setup: 'membrane.setup',
  mcpConfigure: 'membrane.mcpConfigure',
  openSettings: 'membrane.openSettings',
  refreshSymbolExplorer: 'membrane.refreshSymbolExplorer',
  refreshContextDebt: 'membrane.refreshContextDebt',
  refreshSkillGates: 'membrane.refreshSkillGates',
  refreshAgentLocks: 'membrane.refreshAgentLocks',
  refreshFailurePatterns: 'membrane.refreshFailurePatterns',
  trustShow: 'membrane.trustShow',
  playbookShow: 'membrane.playbookShow',
  refreshTrustScores: 'membrane.refreshTrustScores',
  refreshPlaybook: 'membrane.refreshPlaybook',
  showStatus: 'membrane.showStatus',
  harvestPanel: 'membrane.harvestPanel',
  runSkillGatesAll: 'membrane.runSkillGatesAll',
};

// View IDs
export const VIEWS = {
  symbolExplorer: 'membrane.symbolExplorer',
  contextDebt: 'membrane.contextDebt',
  skillGates: 'membrane.skillGates',
  agentLocks: 'membrane.agentLocks',
  failurePatterns: 'membrane.failurePatterns',
  trustScores: 'membrane.trustScores',
  playbook: 'membrane.playbook',
};

// Output channel name
export const OUTPUT_CHANNEL = 'Membrane';

// MCP server name (must match Python backend)
export const MCP_SERVER_NAME = 'context-harness';
export const MCP_COMMAND = 'context-harness-mcp';
