"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/extension.ts
var extension_exports = {};
__export(extension_exports, {
  activate: () => activate,
  deactivate: () => deactivate,
  getProviders: () => getProviders
});
module.exports = __toCommonJS(extension_exports);
var vscode25 = __toESM(require("vscode"));

// src/python/detector.ts
var path = __toESM(require("path"));
var fs = __toESM(require("fs"));
var os = __toESM(require("os"));
var import_child_process = require("child_process");

// src/utils/output.ts
var vscode = __toESM(require("vscode"));

// src/constants.ts
var BRAND = {
  name: "Membrane",
  shortName: "Membrane",
  tagline: "Context Intelligence & Agent Governance",
  description: "Graph-native codebase understanding, skill gates, and agent governance."
};
var ENV_VARS = {
  CONTEXTPACK_ROOT: "CONTEXTPACK_ROOT",
  OPENAI_API_KEY: "OPENAI_API_KEY",
  CONTEXTPACK_LLM_PROVIDER: "CONTEXTPACK_LLM_PROVIDER",
  CONTEXTPACK_EMBEDDING_PROVIDER: "CONTEXTPACK_EMBEDDING_PROVIDER",
  CONTEXTPACK_VECTOR_STORE: "CONTEXTPACK_VECTOR_STORE",
  AZURE_OPENAI_ENDPOINT: "AZURE_OPENAI_ENDPOINT",
  AZURE_OPENAI_API_KEY: "AZURE_OPENAI_API_KEY",
  AZURE_OPENAI_DEPLOYMENT: "AZURE_OPENAI_DEPLOYMENT",
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT: "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
  JIRA_BASE_URL: "JIRA_BASE_URL",
  JIRA_EMAIL: "JIRA_EMAIL",
  JIRA_API_TOKEN: "JIRA_API_TOKEN",
  CONTEXTPACK_MAX_EMBED_ENTITIES: "CONTEXTPACK_MAX_EMBED_ENTITIES",
  CONTEXTPACK_GUIDELINES_MAX_CHARS: "CONTEXTPACK_GUIDELINES_MAX_CHARS"
};
var SETTINGS = {
  autoMcpConfigure: "membrane.autoMcpConfigure",
  autoWatch: "membrane.autoWatch",
  embeddingProvider: "membrane.embeddingProvider",
  llmProvider: "membrane.llmProvider",
  openaiApiKey: "membrane.openaiApiKey",
  azureEndpoint: "membrane.azureEndpoint",
  azureApiKey: "membrane.azureApiKey",
  azureDeployment: "membrane.azureDeployment",
  azureEmbeddingDeployment: "membrane.azureEmbeddingDeployment",
  jiraBaseUrl: "membrane.jiraBaseUrl",
  jiraEmail: "membrane.jiraEmail",
  jiraApiToken: "membrane.jiraApiToken",
  maxEmbedEntities: "membrane.maxEmbedEntities"
};
var COMMANDS = {
  build: "membrane.build",
  incrementalBuild: "membrane.incrementalBuild",
  watch: "membrane.watch",
  harvest: "membrane.harvest",
  ask: "membrane.ask",
  graphView: "membrane.graphView",
  skillsPlan: "membrane.skillsPlan",
  skillsRun: "membrane.skillsRun",
  skillsHistory: "membrane.skillsHistory",
  debtReport: "membrane.debtReport",
  locksShow: "membrane.locksShow",
  patternsShow: "membrane.patternsShow",
  contractsShow: "membrane.contractsShow",
  couplingTrend: "membrane.couplingTrend",
  harnessInstall: "membrane.harnessInstall",
  harnessValidate: "membrane.harnessValidate",
  setup: "membrane.setup",
  mcpConfigure: "membrane.mcpConfigure",
  openSettings: "membrane.openSettings",
  refreshSymbolExplorer: "membrane.refreshSymbolExplorer",
  refreshContextDebt: "membrane.refreshContextDebt",
  refreshSkillGates: "membrane.refreshSkillGates",
  refreshAgentLocks: "membrane.refreshAgentLocks",
  refreshFailurePatterns: "membrane.refreshFailurePatterns",
  trustShow: "membrane.trustShow",
  playbookShow: "membrane.playbookShow",
  refreshTrustScores: "membrane.refreshTrustScores",
  refreshPlaybook: "membrane.refreshPlaybook",
  showStatus: "membrane.showStatus",
  harvestPanel: "membrane.harvestPanel",
  runSkillGatesAll: "membrane.runSkillGatesAll"
};
var OUTPUT_CHANNEL = "Membrane";
var MCP_SERVER_NAME = "context-harness";
var MCP_COMMAND = "context-harness-mcp";

// src/utils/output.ts
var outputChannel = null;
function getOutputChannel() {
  if (!outputChannel) {
    outputChannel = vscode.window.createOutputChannel(OUTPUT_CHANNEL);
  }
  return outputChannel;
}
function showOutput() {
  getOutputChannel().show();
}
function log(message) {
  getOutputChannel().appendLine(`[${(/* @__PURE__ */ new Date()).toLocaleTimeString()}] ${message}`);
}
function dispose() {
  outputChannel?.dispose();
  outputChannel = null;
}

// src/python/detector.ts
function detectUvPath(extensionPath) {
  const bundledUv = getBundledUvPath(extensionPath);
  if (fs.existsSync(bundledUv)) {
    log(`Found bundled uv at: ${bundledUv}`);
    return bundledUv;
  }
  try {
    const systemUv = (0, import_child_process.execSync)("which uv 2>/dev/null || where uv", {
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "ignore"]
    }).trim();
    if (systemUv) {
      log(`Found system uv at: ${systemUv}`);
      return systemUv;
    }
  } catch {
  }
  const commonPaths = [
    path.join(os.homedir(), ".cargo", "bin", "uv"),
    path.join(os.homedir(), ".local", "bin", "uv"),
    path.join(os.homedir(), "AppData", "Local", "uv", "bin", "uv.exe")
  ];
  for (const uvPath of commonPaths) {
    if (fs.existsSync(uvPath)) {
      log(`Found uv at: ${uvPath}`);
      return uvPath;
    }
  }
  log("uv executable not found");
  return null;
}
function getBundledUvPath(extensionPath) {
  const platform = `${process.platform}-${process.arch}`;
  let name = "uv";
  if (process.platform === "win32") {
    name = "uv-win32-x64.exe";
  } else if (process.platform === "darwin") {
    if (process.arch === "arm64") {
      name = "uv-darwin-arm64";
    } else {
      name = "uv-darwin-x64";
    }
  } else {
    name = "uv-linux-x64";
  }
  return path.join(extensionPath, "resources", name);
}
async function verifyContextpack(uvPath) {
  try {
    const { execSync: execSyncImport } = require("child_process");
    const venv = getVenvPath();
    const pythonPath = getVenvPythonPath();
    if (require("fs").existsSync(pythonPath)) {
      try {
        const output = execSyncImport(`"${pythonPath}" -m contextpack.cli.main --version 2>/dev/null || "${pythonPath}" -c "import contextpack; print(contextpack.__version__)"`, {
          encoding: "utf-8",
          stdio: ["pipe", "pipe", "pipe"],
          timeout: 1e4,
          shell: true
        }).trim();
        log(`contextpack version (from venv): ${output}`);
        return { ok: true, version: output };
      } catch (venvError) {
        log(`Venv verification failed, trying uv run...`);
      }
    }
    try {
      const output = execSyncImport(`"${uvPath}" run --extra harness context --version`, {
        encoding: "utf-8",
        stdio: ["pipe", "pipe", "pipe"],
        timeout: 1e4,
        cwd: require("os").homedir()
        // Run from home directory
      }).trim();
      log(`contextpack version (from uv): ${output}`);
      return { ok: true, version: output };
    } catch (uvError) {
      log(`uv run verification also failed`);
      return { ok: false, error: "Could not verify contextpack - but installation may have succeeded" };
    }
  } catch (error) {
    const errorMsg = error.message || String(error);
    log(`contextpack verification failed: ${errorMsg}`);
    return { ok: false, error: errorMsg };
  }
}
function getVenvPath() {
  return path.join(os.homedir(), ".membrane", "venv");
}
function getVenvPythonPath() {
  const venv = getVenvPath();
  if (process.platform === "win32") {
    return path.join(venv, "Scripts", "python.exe");
  } else {
    return path.join(venv, "bin", "python");
  }
}

// src/python/installer.ts
var vscode2 = __toESM(require("vscode"));
var path2 = __toESM(require("path"));
var fs2 = __toESM(require("fs"));
var import_child_process2 = require("child_process");
async function installContextpack(uvPath, extensionPath, workspaceRoot, progress) {
  const venv = getVenvPath();
  const pythonPath = getPythonPath(venv);
  const localSourcePath = getLocalSourcePath(workspaceRoot);
  const wheelsDir = path2.join(extensionPath, "resources", "wheels");
  let actualWheelPath = null;
  if (fs2.existsSync(wheelsDir)) {
    const files = fs2.readdirSync(wheelsDir).filter((f) => f.endsWith(".whl"));
    const arch = process.arch === "arm64" ? "arm64" : "x86_64";
    const platformTag = process.platform === "darwin" ? `macosx.*${arch}` : process.platform === "win32" ? "win" : "linux";
    const platformMatch = files.find((f) => new RegExp(platformTag).test(f));
    const wheelFile = platformMatch ?? files[0];
    if (wheelFile) {
      actualWheelPath = path2.join(wheelsDir, wheelFile);
      log(`Found bundled wheel: ${wheelFile}`);
    }
  }
  const venvCreated = !fs2.existsSync(pythonPath);
  try {
    if (venvCreated) {
      progress?.report({ message: "Creating venv..." });
      log(`Creating venv at ${venv}`);
      (0, import_child_process2.execSync)(`"${uvPath}" venv "${venv}"`, { stdio: "pipe", encoding: "utf-8" });
      log("venv created");
    } else {
      log(`Reusing existing venv at ${venv}`);
    }
    progress?.report({ message: "Installing contextpack...", increment: 50 });
    let installCmd;
    if (localSourcePath) {
      log(`Installing from local workspace source: ${localSourcePath}`);
      installCmd = `"${uvPath}" pip install --python "${pythonPath}" "${localSourcePath}[harness]" -v`;
    } else if (actualWheelPath) {
      log(`Installing from bundled wheel: ${actualWheelPath}`);
      installCmd = `"${uvPath}" pip install --python "${pythonPath}" "${actualWheelPath}[harness]" -v`;
    } else {
      log("No bundled wheel \u2014 installing from PyPI...");
      installCmd = `"${uvPath}" pip install --python "${pythonPath}" "contextpack[harness]" -v`;
    }
    const output = (0, import_child_process2.execSync)(installCmd, { encoding: "utf-8", stdio: "pipe" });
    log(`install output: ${output}`);
    progress?.report({ message: "Verifying installation...", increment: 25 });
    log("Verifying contextpack installation...");
    const verifyOutput = (0, import_child_process2.execSync)(`"${pythonPath}" -c "import contextpack; print('contextpack version:', contextpack.__version__)"`, {
      encoding: "utf-8",
      stdio: "pipe"
    });
    log(`Verification: ${verifyOutput}`);
    progress?.report({ message: "Installation complete", increment: 25 });
    log("\u2713 contextpack installed and verified successfully");
    return true;
  } catch (error) {
    const errorMsg = error.stdout || error.stderr || error.message || String(error);
    log(`Installation failed: ${errorMsg}`);
    if (venvCreated && fs2.existsSync(venv)) {
      try {
        fs2.rmSync(venv, { recursive: true, force: true });
        log("Rolled back partial venv after install failure");
      } catch {
        log("Warning: could not roll back venv");
      }
    }
    vscode2.window.showErrorMessage(
      `Membrane: installation failed \u2014 ${errorMsg.slice(0, 120)}`,
      "View Logs"
    ).then((action) => {
      if (action === "View Logs") {
        vscode2.commands.executeCommand("workbench.action.output.toggleOutput");
      }
    });
    return false;
  }
}
function getLocalSourcePath(workspaceRoot) {
  const pyprojectPath = path2.join(workspaceRoot, "pyproject.toml");
  const packageInitPath = path2.join(workspaceRoot, "contextpack", "__init__.py");
  if (!fs2.existsSync(pyprojectPath) || !fs2.existsSync(packageInitPath)) {
    return null;
  }
  try {
    const pyproject = fs2.readFileSync(pyprojectPath, "utf-8");
    if (pyproject.includes('name = "contextpack"')) {
      return workspaceRoot;
    }
  } catch {
    return null;
  }
  return null;
}
function getPythonPath(venvPath) {
  if (process.platform === "win32") {
    return path2.join(venvPath, "Scripts", "python.exe");
  } else {
    return path2.join(venvPath, "bin", "python");
  }
}
function isContextpackInstalled() {
  const venv = getVenvPath();
  const pythonPath = getPythonPath(venv);
  if (!fs2.existsSync(pythonPath)) {
    return false;
  }
  try {
    (0, import_child_process2.execSync)(`"${pythonPath}" -c "import contextpack"`, {
      stdio: "pipe",
      encoding: "utf-8",
      timeout: 5e3
    });
    return true;
  } catch {
    return false;
  }
}

// src/python/runner.ts
var import_child_process3 = require("child_process");
var fs3 = __toESM(require("fs"));
var ContextRunner = class {
  constructor(uvPath, workspaceRoot, envVars = {}) {
    this.uvPath = uvPath;
    this.workspaceRoot = workspaceRoot;
    this.envVars = envVars;
    this.venvPython = getVenvPythonPath();
    this.useVenvPython = fs3.existsSync(this.venvPython);
    if (this.useVenvPython) {
      log(`Using venv Python: ${this.venvPython}`);
    } else {
      log(`Venv Python not found, will use: ${this.uvPath} run`);
    }
  }
  venvPython;
  useVenvPython;
  /** Read an env var the runner will pass to subprocesses (from .env or settings). */
  getEnvVar(name) {
    return this.envVars[name] || process.env[name];
  }
  /**
   * Run a command and wait for completion.
   */
  async run(args, opts) {
    return new Promise((resolve) => {
      const env2 = {
        ...process.env,
        ...this.envVars,
        ...opts?.env,
        CONTEXTPACK_ROOT: this.workspaceRoot
      };
      let command;
      let cmdArgs;
      if (this.useVenvPython) {
        command = this.venvPython;
        cmdArgs = ["-m", "contextpack.cli.main", ...args];
        log(`Running: ${command} ${cmdArgs.join(" ")}`);
      } else {
        command = this.uvPath;
        cmdArgs = ["run", "--extra", "harness", "context", ...args];
        log(`Running: ${command} ${cmdArgs.join(" ")}`);
      }
      const timeout = opts?.timeout || 12e4;
      let timedOut = false;
      const timer = setTimeout(() => {
        timedOut = true;
      }, timeout);
      (0, import_child_process3.execFile)(
        command,
        cmdArgs,
        {
          cwd: opts?.cwd || this.workspaceRoot,
          env: env2,
          maxBuffer: 10 * 1024 * 1024
          // 10MB
        },
        (error, stdout, stderr) => {
          clearTimeout(timer);
          if (timedOut) {
            resolve({
              exitCode: -1,
              stdout: "",
              stderr: `Command timed out after ${timeout}ms`
            });
            return;
          }
          const exitCode = error?.code || 0;
          resolve({
            exitCode,
            stdout,
            stderr
          });
        }
      );
    });
  }
  /**
   * Run a command and parse JSON output.
   */
  async runJson(args, opts) {
    const result = await this.run(args, opts);
    if (result.exitCode !== 0) {
      log(`Command failed: ${result.stderr}`);
      return null;
    }
    try {
      return JSON.parse(result.stdout);
    } catch (error) {
      log(`Failed to parse JSON: ${result.stdout}`);
      return null;
    }
  }
  /**
   * Spawn a long-running process (watcher, MCP server, etc).
   */
  spawn(args, opts) {
    const env2 = {
      ...process.env,
      ...this.envVars,
      ...opts?.env,
      CONTEXTPACK_ROOT: this.workspaceRoot
    };
    let command;
    let cmdArgs;
    if (this.useVenvPython) {
      command = this.venvPython;
      cmdArgs = ["-m", "contextpack.cli.main", ...args];
      log(`Spawning: ${command} ${cmdArgs.join(" ")}`);
    } else {
      command = this.uvPath;
      cmdArgs = ["run", "--extra", "harness", "context", ...args];
      log(`Spawning: ${command} ${cmdArgs.join(" ")}`);
    }
    return (0, import_child_process3.spawn)(command, cmdArgs, {
      cwd: opts?.cwd || this.workspaceRoot,
      env: env2,
      stdio: ["pipe", "pipe", "pipe"]
    });
  }
  /**
   * Spawn MCP server process.
   */
  spawnMcpServer(opts) {
    const env2 = {
      ...process.env,
      ...this.envVars,
      ...opts?.env,
      CONTEXTPACK_ROOT: this.workspaceRoot
    };
    let command;
    let cmdArgs;
    if (this.useVenvPython) {
      command = this.venvPython;
      cmdArgs = ["-m", "contextpack.mcp.server"];
      log(`Spawning MCP server: ${command} ${cmdArgs.join(" ")}`);
    } else {
      command = this.uvPath;
      cmdArgs = ["run", "--extra", "harness", "context-harness-mcp"];
      log(`Spawning MCP server: ${command} ${cmdArgs.join(" ")}`);
    }
    return (0, import_child_process3.spawn)(command, cmdArgs, {
      cwd: opts?.cwd || this.workspaceRoot,
      env: env2,
      stdio: ["pipe", "pipe", "pipe"]
    });
  }
};
function createRunner(uvPath, workspaceRoot, envVars = {}) {
  return new ContextRunner(uvPath, workspaceRoot, envVars);
}

// src/utils/config.ts
var vscode4 = __toESM(require("vscode"));
var path4 = __toESM(require("path"));
var fs4 = __toESM(require("fs"));

// src/utils/workspace.ts
var vscode3 = __toESM(require("vscode"));
var path3 = __toESM(require("path"));
function getWorkspaceRoot() {
  const folder = vscode3.workspace.workspaceFolders?.[0];
  if (!folder) {
    return null;
  }
  return folder.uri.fsPath;
}
function getContextpackDir() {
  const root = getWorkspaceRoot();
  if (!root) {
    return null;
  }
  return path3.join(root, ".contextpack");
}
function getConfigPath() {
  const dir = getContextpackDir();
  if (!dir) {
    return null;
  }
  return path3.join(dir, "config.json");
}
function getProjectMapPath() {
  const dir = getContextpackDir();
  if (!dir) {
    return null;
  }
  return path3.join(dir, "project_map.json");
}
function isContextpackInitialized() {
  const configPath = getConfigPath();
  if (!configPath) {
    return false;
  }
  try {
    const fs10 = require("fs");
    return fs10.existsSync(configPath);
  } catch {
    return false;
  }
}

// src/utils/config.ts
async function buildEnvVars(secretStorage) {
  const config = vscode4.workspace.getConfiguration();
  const env2 = {
    ...process.env
  };
  const workspaceRoot = getWorkspaceRoot();
  if (workspaceRoot) {
    env2[ENV_VARS.CONTEXTPACK_ROOT] = workspaceRoot;
  }
  const embeddingProvider = config.get(SETTINGS.embeddingProvider) || "hash";
  env2[ENV_VARS.CONTEXTPACK_EMBEDDING_PROVIDER] = embeddingProvider;
  const llmProvider = config.get(SETTINGS.llmProvider);
  if (llmProvider) {
    env2[ENV_VARS.CONTEXTPACK_LLM_PROVIDER] = llmProvider;
  }
  const openaiKey = await secretStorage.get("membrane.openaiApiKey");
  if (openaiKey) {
    env2[ENV_VARS.OPENAI_API_KEY] = openaiKey;
  }
  const azureEndpoint = config.get(SETTINGS.azureEndpoint);
  if (azureEndpoint) {
    env2[ENV_VARS.AZURE_OPENAI_ENDPOINT] = azureEndpoint;
  }
  const azureKey = await secretStorage.get("membrane.azureApiKey");
  if (azureKey) {
    env2[ENV_VARS.AZURE_OPENAI_API_KEY] = azureKey;
  }
  const azureDeployment = config.get(SETTINGS.azureDeployment);
  if (azureDeployment) {
    env2[ENV_VARS.AZURE_OPENAI_DEPLOYMENT] = azureDeployment;
  }
  const azureEmbeddingDeploy = config.get(SETTINGS.azureEmbeddingDeployment);
  if (azureEmbeddingDeploy) {
    env2[ENV_VARS.AZURE_OPENAI_EMBEDDING_DEPLOYMENT] = azureEmbeddingDeploy;
  }
  const jiraUrl = config.get(SETTINGS.jiraBaseUrl);
  if (jiraUrl) {
    env2[ENV_VARS.JIRA_BASE_URL] = jiraUrl;
  }
  const jiraEmail = config.get(SETTINGS.jiraEmail);
  if (jiraEmail) {
    env2[ENV_VARS.JIRA_EMAIL] = jiraEmail;
  }
  const jiraToken = await secretStorage.get("membrane.jiraApiToken");
  if (jiraToken) {
    env2[ENV_VARS.JIRA_API_TOKEN] = jiraToken;
  }
  const maxEmbedEntities = config.get(SETTINGS.maxEmbedEntities);
  if (maxEmbedEntities) {
    env2[ENV_VARS.CONTEXTPACK_MAX_EMBED_ENTITIES] = String(maxEmbedEntities);
  }
  if (workspaceRoot) {
    const envFilePath = path4.join(workspaceRoot, ".env");
    if (fs4.existsSync(envFilePath)) {
      const envContent = fs4.readFileSync(envFilePath, "utf-8");
      const lines = envContent.split("\n");
      let loadedCount = 0;
      const loadedKeys = [];
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith("#")) {
          const eqIdx = trimmed.indexOf("=");
          if (eqIdx > 0) {
            const key = trimmed.slice(0, eqIdx).trim();
            let value = trimmed.slice(eqIdx + 1).trim();
            if (value.startsWith('"') && value.endsWith('"') || value.startsWith("'") && value.endsWith("'")) {
              value = value.slice(1, -1);
            }
            if (key && value) {
              env2[key] = value;
              loadedCount++;
              loadedKeys.push(key);
            }
          }
        }
      }
      log(`Loaded ${loadedCount} env vars from .env: ${loadedKeys.join(", ")}`);
    } else {
      log(`No .env file found at ${envFilePath}`);
    }
  }
  return env2;
}

// src/mcp/manager.ts
var vscode5 = __toESM(require("vscode"));

// src/mcp/mcpConfig.ts
var fs5 = __toESM(require("fs"));
var path5 = __toESM(require("path"));
function readMcpConfig(workspaceRoot) {
  const mcpPath = path5.join(workspaceRoot, ".mcp.json");
  if (!fs5.existsSync(mcpPath)) {
    return null;
  }
  try {
    const content = fs5.readFileSync(mcpPath, "utf-8");
    return JSON.parse(content);
  } catch (error) {
    log(`Failed to read .mcp.json: ${error}`);
    return null;
  }
}
function writeMcpConfig(config, workspaceRoot) {
  const mcpPath = path5.join(workspaceRoot, ".mcp.json");
  try {
    fs5.writeFileSync(mcpPath, JSON.stringify(config, null, 2));
    log(`Wrote .mcp.json to ${mcpPath}`);
    return true;
  } catch (error) {
    log(`Failed to write .mcp.json: ${error}`);
    return false;
  }
}
function configureMcpServer(workspaceRoot, uvPath) {
  let config = readMcpConfig(workspaceRoot) || { mcpServers: {} };
  config.mcpServers[MCP_SERVER_NAME] = {
    command: uvPath,
    args: ["run", "--extra", "harness", MCP_COMMAND],
    env: {
      CONTEXTPACK_ROOT: workspaceRoot
    }
  };
  return config;
}

// src/mcp/manager.ts
var McpServerManager = class {
  constructor(workspaceRoot, runner, uvPath) {
    this.workspaceRoot = workspaceRoot;
    this.runner = runner;
    this.uvPath = uvPath;
    this.onStatusChange = new vscode5.EventEmitter();
  }
  process = null;
  status = "stopped";
  restartAttempts = 0;
  maxRestartAttempts = 3;
  onStatusChange;
  get statusEvent() {
    return this.onStatusChange.event;
  }
  getStatus() {
    return this.status;
  }
  /**
   * Start the MCP server.
   */
  async start() {
    if (this.status === "running" || this.status === "starting") {
      log("MCP server already running or starting");
      return true;
    }
    const autoConfig = vscode5.workspace.getConfiguration().get(SETTINGS.autoMcpConfigure);
    if (autoConfig) {
      const config = configureMcpServer(this.workspaceRoot, this.uvPath);
      writeMcpConfig(config, this.workspaceRoot);
    }
    return this._start();
  }
  async _start() {
    try {
      this.setStatus("starting");
      log("Starting MCP server");
      this.process = this.runner.spawnMcpServer();
      this.process.stdout?.on("data", (data) => {
        const text = data.toString().trim();
        if (text) {
          log(`MCP stdout: ${text}`);
        }
      });
      this.process.stderr?.on("data", (data) => {
        const text = data.toString().trim();
        if (text) {
          log(`MCP stderr: ${text}`);
        }
      });
      this.process.on("exit", (code) => {
        log(`MCP server exited with code ${code}`);
        this.process = null;
        if (this.status !== "stopping") {
          this._handleUnexpectedExit();
        } else {
          this.setStatus("stopped");
        }
      });
      this.process.on("error", (error) => {
        log(`MCP server error: ${error.message}`);
        this._handleUnexpectedExit();
      });
      await new Promise((resolve) => setTimeout(resolve, 1e3));
      this.restartAttempts = 0;
      this.setStatus("running");
      return true;
    } catch (error) {
      log(`Failed to start MCP server: ${error.message}`);
      this.setStatus("stopped");
      return false;
    }
  }
  /**
   * Stop the MCP server.
   */
  async stop() {
    if (this.status === "stopped") {
      return true;
    }
    this.setStatus("stopping");
    log("Stopping MCP server");
    if (this.process) {
      try {
        this.process.kill();
        await new Promise((resolve) => setTimeout(resolve, 500));
      } catch (error) {
        log(`Error stopping MCP server: ${error.message}`);
      }
    }
    this.process = null;
    this.setStatus("stopped");
    return true;
  }
  /**
   * Restart the MCP server.
   */
  async restart() {
    await this.stop();
    await new Promise((resolve) => setTimeout(resolve, 500));
    return this._start();
  }
  /**
   * Handle unexpected exit with exponential backoff retry.
   */
  async _handleUnexpectedExit() {
    if (this.restartAttempts >= this.maxRestartAttempts) {
      log("MCP server restart attempts exceeded");
      this.setStatus("stopped");
      vscode5.window.showErrorMessage(
        "Membrane MCP server stopped unexpectedly. Check output for details."
      );
      return;
    }
    const delay = Math.pow(2, this.restartAttempts) * 1e3;
    this.restartAttempts++;
    log(`Restarting MCP server in ${delay}ms (attempt ${this.restartAttempts})`);
    await new Promise((resolve) => setTimeout(resolve, delay));
    await this._start();
  }
  setStatus(status) {
    this.status = status;
    log(`MCP server status: ${status}`);
    this.onStatusChange.fire(status);
  }
  dispose() {
    this.onStatusChange.dispose();
    if (this.process) {
      this.process.kill();
    }
  }
};

// src/build/buildService.ts
var vscode6 = __toESM(require("vscode"));
var BuildService = class {
  constructor(workspaceRoot, runner) {
    this.workspaceRoot = workspaceRoot;
    this.runner = runner;
  }
  async build() {
    log("Starting full build...");
    const result = await vscode6.window.withProgress(
      {
        location: vscode6.ProgressLocation.Notification,
        title: `${BRAND.name}: Building index...`,
        cancellable: false
      },
      async (progress) => {
        progress.report({ message: "Scanning codebase..." });
        return this.runner.run(["build"], { timeout: 3e5 });
      }
    );
    if (result.exitCode === 0) {
      log("Build complete");
      return true;
    }
    log(`Build failed: ${result.stderr}`);
    return false;
  }
  async incrementalBuild() {
    log("Starting incremental build...");
    const result = await this.runner.run(["build", "--incremental"], { timeout: 12e4 });
    if (result.exitCode === 0) {
      log("Incremental build complete");
      return true;
    }
    log(`Incremental build failed: ${result.stderr}`);
    return false;
  }
  dispose() {
  }
};

// src/watcher/fileWatcher.ts
var vscode7 = __toESM(require("vscode"));
var FileWatcherManager = class {
  constructor(workspaceRoot, buildService2) {
    this.workspaceRoot = workspaceRoot;
    this.buildService = buildService2;
  }
  watcher = null;
  debounceTimer = null;
  debounceMs = 1500;
  isWatching = false;
  /**
   * Start watching for file changes.
   */
  start() {
    if (this.isWatching || this.watcher) {
      return;
    }
    const autoWatch = vscode7.workspace.getConfiguration().get(SETTINGS.autoWatch, true);
    if (!autoWatch) {
      log("File watcher disabled in settings");
      return;
    }
    log("Starting file watcher (excluding .contextpack, node_modules, .git)");
    const pattern = new vscode7.RelativePattern(
      this.workspaceRoot,
      "**/*.{py,ts,tsx,js,jsx,md,yaml,yml,json}"
    );
    this.watcher = vscode7.workspace.createFileSystemWatcher(pattern, true, false, true);
    this.watcher.onDidChange((uri) => {
      if (uri.fsPath.includes(".contextpack") || uri.fsPath.includes(".mcp.json") || uri.fsPath.includes("node_modules") || uri.fsPath.includes(".git")) {
        return;
      }
      this._onFileChange();
    });
    this.watcher.onDidCreate((uri) => {
      if (uri.fsPath.includes(".contextpack") || uri.fsPath.includes(".mcp.json") || uri.fsPath.includes("node_modules") || uri.fsPath.includes(".git")) {
        return;
      }
      this._onFileChange();
    });
    this.isWatching = true;
  }
  /**
   * Stop watching for file changes.
   */
  stop() {
    if (this.watcher) {
      this.watcher.dispose();
      this.watcher = null;
    }
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }
    this.isWatching = false;
    log("Stopped file watcher");
  }
  /**
   * Toggle file watcher on/off.
   */
  toggle() {
    if (this.isWatching) {
      this.stop();
    } else {
      this.start();
    }
  }
  _onFileChange() {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(() => {
      log("Files changed, triggering incremental build");
      this.buildService.incrementalBuild();
      this.debounceTimer = null;
    }, this.debounceMs);
  }
  isActive() {
    return this.isWatching;
  }
  dispose() {
    this.stop();
  }
};

// src/commands/buildCommands.ts
var vscode8 = __toESM(require("vscode"));
function registerBuildCommands(context, buildService2, fileWatcher2, providers) {
  const refreshProviders = async () => {
    try {
      if (providers?.symbolExplorer)
        await providers.symbolExplorer.refresh?.();
      if (providers?.contextDebt)
        await providers.contextDebt.refresh?.();
      if (providers?.skillGates)
        await providers.skillGates.refresh?.();
      if (providers?.agentLocks)
        await providers.agentLocks.refresh?.();
      if (providers?.failurePatterns)
        await providers.failurePatterns.refresh?.();
      if (providers?.trustScores)
        await providers.trustScores.refresh?.();
      if (providers?.playbook)
        await providers.playbook.refresh?.();
    } catch (error) {
      log(`Error refreshing providers: ${error}`);
    }
  };
  context.subscriptions.push(
    vscode8.commands.registerCommand(COMMANDS.build, async () => {
      log("Command: build");
      const success = await buildService2.build();
      if (success) {
        await refreshProviders();
        vscode8.window.showInformationMessage("Membrane: Build completed");
      } else {
        vscode8.window.showErrorMessage("Membrane: Build failed");
      }
    })
  );
  context.subscriptions.push(
    vscode8.commands.registerCommand(COMMANDS.incrementalBuild, async () => {
      log("Command: incremental build");
      const success = await buildService2.incrementalBuild();
      if (success) {
        await refreshProviders();
      } else {
        vscode8.window.showErrorMessage("Membrane: Incremental build failed");
      }
    })
  );
  context.subscriptions.push(
    vscode8.commands.registerCommand(COMMANDS.watch, async () => {
      log("Command: toggle watch");
      fileWatcher2.toggle();
      const status = fileWatcher2.isActive() ? "enabled" : "disabled";
      vscode8.window.showInformationMessage(`Membrane: File watcher ${status}`);
    })
  );
}

// src/commands/harvestCommands.ts
var vscode10 = __toESM(require("vscode"));

// src/panels/HarvestPanel.ts
var vscode9 = __toESM(require("vscode"));
var fs6 = __toESM(require("fs"));
var path6 = __toESM(require("path"));
var HarvestPanel = class _HarvestPanel {
  constructor(panel, context, runner) {
    this.context = context;
    this.runner = runner;
    this.panel = panel;
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
    this.panel.webview.onDidReceiveMessage(
      (msg) => this.handleMessage(msg),
      null,
      this.disposables
    );
  }
  static currentPanel;
  panel;
  disposables = [];
  static show(context, runner) {
    if (_HarvestPanel.currentPanel) {
      _HarvestPanel.currentPanel.panel.reveal(vscode9.ViewColumn.Two);
      return;
    }
    const panel = vscode9.window.createWebviewPanel(
      "membrane.harvest",
      "Membrane: Harvest Context",
      vscode9.ViewColumn.Two,
      {
        enableScripts: true,
        localResourceRoots: [vscode9.Uri.joinPath(context.extensionUri, "out")],
        retainContextWhenHidden: true
      }
    );
    const instance = new _HarvestPanel(panel, context, runner);
    instance.panel.webview.html = instance.buildHtml();
    _HarvestPanel.currentPanel = instance;
  }
  buildHtml() {
    const htmlPath = path6.join(
      this.context.extensionPath,
      "webview-src",
      "harvest",
      "index.html"
    );
    const scriptUri = this.panel.webview.asWebviewUri(
      vscode9.Uri.joinPath(this.context.extensionUri, "out", "webview-harvest.js")
    );
    let html = fs6.readFileSync(htmlPath, "utf-8");
    html = html.replace(/<script src="\.\.\/harvest\.js"><\/script>/, `<script src="${scriptUri}"></script>`);
    return html;
  }
  send(msg) {
    this.panel.webview.postMessage(msg);
  }
  async handleMessage(msg) {
    switch (msg.type) {
      case "harvest": {
        const query = msg.query ?? "";
        const branch = msg.branch ?? "";
        if (!query.trim()) {
          this.send({ type: "error", message: "Please enter a query" });
          return;
        }
        log(`Harvesting context for: "${query}"`);
        this.send({ type: "loading" });
        try {
          const args = branch ? ["harvest", query, "--branch", branch] : ["harvest", query];
          const result = await this.runner.run(args, { timeout: 12e4 });
          if (result.exitCode === 0) {
            this.send({ type: "harvestResult", content: result.stdout || "(no context returned)" });
          } else {
            this.send({ type: "harvestError", error: result.stderr || "Harvest failed" });
          }
        } catch (err) {
          this.send({ type: "harvestError", error: err.message });
        }
        break;
      }
      case "openInEditor": {
        const content = msg.content ?? "";
        const doc = await vscode9.workspace.openTextDocument({
          content: `# Harvested Context

${content}`,
          language: "markdown"
        });
        vscode9.window.showTextDocument(doc, { preview: true, viewColumn: vscode9.ViewColumn.One });
        break;
      }
    }
  }
  dispose() {
    _HarvestPanel.currentPanel = void 0;
    this.panel.dispose();
    this.disposables.forEach((d) => d.dispose());
    this.disposables = [];
  }
};

// src/commands/harvestCommands.ts
async function showAsMarkdownDoc(content, title) {
  const doc = await vscode10.workspace.openTextDocument({
    content: `# ${title}

${content}`,
    language: "markdown"
  });
  await vscode10.window.showTextDocument(doc, {
    preview: true,
    viewColumn: vscode10.ViewColumn.Beside
  });
}
function registerHarvestCommands(context, runner, extensionUri) {
  context.subscriptions.push(
    vscode10.commands.registerCommand(COMMANDS.harvest, () => {
      log("Command: harvest (WebView)");
      HarvestPanel.show(context, runner);
    })
  );
  context.subscriptions.push(
    vscode10.commands.registerCommand(COMMANDS.ask, async () => {
      log("Command: ask");
      const question = await vscode10.window.showInputBox({
        prompt: "Ask a question about your codebase",
        placeHolder: 'e.g., "How does authentication work?"'
      });
      if (!question) {
        return;
      }
      showOutput();
      log(`Asking: "${question}"`);
      const settingLlm = vscode10.workspace.getConfiguration().get("membrane.llmProvider");
      const envLlm = runner.getEnvVar("CONTEXTPACK_LLM_PROVIDER");
      const hasAzure = !!runner.getEnvVar("AZURE_OPENAI_ENDPOINT");
      const hasOpenai = !!runner.getEnvVar("OPENAI_API_KEY");
      const useLlm = settingLlm || envLlm || (hasAzure ? "azure_foundry" : hasOpenai ? "openai" : "");
      const args = useLlm ? ["ask", question, "--llm"] : ["ask", question];
      log(`LLM provider resolved to: ${useLlm || "(offline)"}`);
      const result = await vscode10.window.withProgress(
        {
          location: vscode10.ProgressLocation.Notification,
          title: `Membrane: ${useLlm ? "Asking LLM" : "Synthesising offline"}: "${question}"`,
          cancellable: false
        },
        async () => runner.run(args, { timeout: 18e4 })
      );
      if (result.exitCode === 0) {
        log(result.stdout);
        await showAsMarkdownDoc(result.stdout || "_no answer_", `Ask: ${question}`);
      } else {
        log(`Ask failed: ${result.stderr}`);
        vscode10.window.showErrorMessage(`Membrane: Ask failed \u2014 ${result.stderr || "unknown error"}`);
      }
    })
  );
}

// src/commands/skillCommands.ts
var vscode11 = __toESM(require("vscode"));
function registerSkillCommands(context, runner, providers) {
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
  context.subscriptions.push(
    vscode11.commands.registerCommand(COMMANDS.skillsPlan, async (uri) => {
      log("Command: skills plan");
      let filePath;
      if (uri?.fsPath) {
        filePath = uri.fsPath;
      } else {
        const editor = vscode11.window.activeTextEditor;
        if (!editor) {
          vscode11.window.showErrorMessage("Membrane: Open a file or right-click on a file first");
          return;
        }
        filePath = editor.document.fileName;
      }
      showOutput();
      log(`Getting skill plan for: ${filePath}`);
      const result = await runner.run(["skills", "plan", filePath]);
      if (result.exitCode === 0) {
        log(result.stdout);
        const firstLine = (result.stdout || "").split("\n").find((l) => l.includes("skills"));
        if (firstLine) {
          vscode11.window.showInformationMessage(
            `Membrane Skill Plan ready \u2014 see output for details`
          );
        }
      } else {
        log(`Skill plan failed: ${result.stderr}`);
        vscode11.window.showErrorMessage("Membrane: Skill plan failed");
      }
    })
  );
  context.subscriptions.push(
    vscode11.commands.registerCommand(COMMANDS.skillsRun, async (uri) => {
      log("Command: run skills");
      let filePath;
      if (uri?.fsPath) {
        filePath = uri.fsPath;
      } else {
        const editor = vscode11.window.activeTextEditor;
        if (!editor) {
          filePath = ".";
        } else {
          filePath = editor.document.fileName;
        }
      }
      showOutput();
      log(`Running skill gates for: ${filePath}`);
      await vscode11.window.withProgress(
        {
          location: vscode11.ProgressLocation.Notification,
          title: `Membrane: Running skill gates`,
          cancellable: false
        },
        async () => {
          const result = await runner.run(["skills", "run", filePath]);
          if (result.exitCode === 0) {
            log(result.stdout);
            vscode11.window.showInformationMessage(
              "Membrane: Skill gates passed \u2705"
            );
          } else {
            log(result.stdout || "");
            log(`Skill run failed: ${result.stderr}`);
            vscode11.window.showWarningMessage(
              "Membrane: Skill gates blocked \u2014 check Skill Gates view for details"
            );
          }
          await refreshAfterSkill();
        }
      );
    })
  );
  context.subscriptions.push(
    vscode11.commands.registerCommand(COMMANDS.skillsHistory, async () => {
      log("Command: skills history");
      showOutput();
      const result = await runner.run(["skills", "history"]);
      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Skills history failed: ${result.stderr}`);
      }
      await refreshAfterSkill();
    })
  );
}

// src/commands/governanceCommands.ts
var vscode12 = __toESM(require("vscode"));
function registerGovernanceCommands(context, runner) {
  context.subscriptions.push(
    vscode12.commands.registerCommand(COMMANDS.debtReport, async () => {
      log("Command: debt report");
      showOutput();
      const result = await runner.run(["debt"]);
      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Debt report failed: ${result.stderr}`);
      }
    })
  );
  context.subscriptions.push(
    vscode12.commands.registerCommand(COMMANDS.locksShow, async () => {
      log("Command: show locks");
      showOutput();
      const result = await runner.run(["locks"]);
      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Locks query failed: ${result.stderr}`);
      }
    })
  );
  context.subscriptions.push(
    vscode12.commands.registerCommand(COMMANDS.patternsShow, async () => {
      log("Command: show patterns");
      showOutput();
      const result = await runner.run(["patterns"]);
      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Patterns query failed: ${result.stderr}`);
      }
    })
  );
  context.subscriptions.push(
    vscode12.commands.registerCommand(COMMANDS.contractsShow, async () => {
      log("Command: show contracts");
      const symbol = await vscode12.window.showInputBox({
        prompt: "Enter symbol name",
        placeHolder: 'e.g., "authenticate"'
      });
      if (!symbol) {
        return;
      }
      showOutput();
      log(`Getting contracts for: ${symbol}`);
      const result = await runner.run(["contracts", "show", symbol]);
      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Contracts query failed: ${result.stderr}`);
      }
    })
  );
  context.subscriptions.push(
    vscode12.commands.registerCommand(COMMANDS.couplingTrend, async () => {
      log("Command: coupling trend");
      showOutput();
      const result = await runner.runJson(["coupling", "--json"]);
      if (!result || typeof result !== "object") {
        log("Coupling trend: no data yet \u2014 run builds to accumulate metrics.");
        return;
      }
      const r = result;
      const lines = ["## Coupling Trend"];
      if (r.latest) {
        lines.push(
          `Latest graph: ${r.latest.edge_count} edges / ${r.latest.node_count} nodes | ${r.latest.hub_count} hubs | ${r.latest.cycle_count} cycles`,
          `Avg coupling: ${r.latest.avg_coupling.toFixed(4)}`
        );
      }
      lines.push(
        `30d change: ${r.coupling_change_pct >= 0 ? "+" : ""}${r.coupling_change_pct}%`,
        `Hub change: ${r.hub_change >= 0 ? "+" : ""}${r.hub_change}`,
        `Cycle change: ${r.cycle_change >= 0 ? "+" : ""}${r.cycle_change}`,
        `Snapshots recorded: ${r.snapshot_count}`
      );
      if (r.is_decaying) {
        lines.push("", `\u{1F6A8} DECAY ALERT: ${r.alert_message}`);
      }
      if (r.hotspot_modules.length > 0) {
        lines.push("", `Hotspot modules: ${r.hotspot_modules.slice(0, 5).join(", ")}`);
      }
      log(lines.join("\n"));
    })
  );
  context.subscriptions.push(
    vscode12.commands.registerCommand(COMMANDS.trustShow, async () => {
      log("Command: show trust scores");
      showOutput();
      const result = await runner.run(["trust"]);
      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Trust scores failed: ${result.stderr}`);
      }
    })
  );
  context.subscriptions.push(
    vscode12.commands.registerCommand(COMMANDS.playbookShow, async () => {
      log("Command: show playbook proposals");
      showOutput();
      const result = await runner.run(["playbook"]);
      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Playbook proposals failed: ${result.stderr}`);
      }
    })
  );
}

// src/commands/setupCommands.ts
var vscode13 = __toESM(require("vscode"));
function registerSetupCommands(context, runner) {
  context.subscriptions.push(
    vscode13.commands.registerCommand(COMMANDS.harnessInstall, async () => {
      log("Command: harness install");
      showOutput();
      const result = await runner.run(["harness", "install"]);
      if (result.exitCode === 0) {
        log(result.stdout);
        vscode13.window.showInformationMessage("Membrane: Harness installed successfully");
      } else {
        log(`Harness install failed: ${result.stderr}`);
        vscode13.window.showErrorMessage("Membrane: Harness installation failed");
      }
    })
  );
  context.subscriptions.push(
    vscode13.commands.registerCommand(COMMANDS.harnessValidate, async () => {
      log("Command: harness validate");
      showOutput();
      const result = await runner.run(["harness", "validate"]);
      if (result.exitCode === 0) {
        log(result.stdout);
        vscode13.window.showInformationMessage("Membrane: Harness validation passed");
      } else {
        log(`Harness validation failed: ${result.stderr}`);
        vscode13.window.showWarningMessage("Membrane: Harness validation issues detected");
      }
    })
  );
  context.subscriptions.push(
    vscode13.commands.registerCommand(COMMANDS.mcpConfigure, async () => {
      log("Command: MCP configure");
      vscode13.window.showInformationMessage("Membrane: MCP server configuration updated");
    })
  );
  context.subscriptions.push(
    vscode13.commands.registerCommand(COMMANDS.openSettings, async () => {
      log("Command: open settings");
      vscode13.commands.executeCommand("workbench.action.openSettings", "membrane");
    })
  );
}

// src/statusBar.ts
var vscode14 = __toESM(require("vscode"));
var STATE_CONFIG = {
  initializing: { icon: "$(sync~spin)", label: "Starting..." },
  building: { icon: "$(sync~spin)", label: "Building..." },
  ready: { icon: "$(check)", label: "Ready" },
  error: { icon: "$(error)", label: "Error" },
  disabled: { icon: "$(circle-slash)", label: "Disabled" }
};
var StatusBarManager = class {
  stateItem;
  conflictItem;
  _state = "initializing";
  conflictInterval;
  constructor() {
    this.stateItem = vscode14.window.createStatusBarItem(
      vscode14.StatusBarAlignment.Left,
      10
    );
    this.stateItem.command = "membrane.showStatus";
    this.conflictItem = vscode14.window.createStatusBarItem(
      vscode14.StatusBarAlignment.Left,
      9
    );
    this.conflictItem.command = "membrane.locksShow";
    this.setState("initializing");
    this.stateItem.show();
  }
  setState(state, detail) {
    this._state = state;
    const cfg = STATE_CONFIG[state];
    const suffix = detail ? ` \u2014 ${detail.slice(0, 35)}` : "";
    this.stateItem.text = `${cfg.icon} ${BRAND.shortName}: ${cfg.label}${suffix}`;
    this.stateItem.tooltip = state === "error" ? `${BRAND.name}: ${detail || "Unknown error"} \u2014 click for options` : `${BRAND.name} \u2014 ${cfg.label}`;
    this.stateItem.backgroundColor = state === "error" ? new vscode14.ThemeColor("statusBarItem.errorBackground") : void 0;
  }
  setConflicts(count) {
    if (count === 0) {
      this.conflictItem.hide();
      return;
    }
    this.conflictItem.text = `$(warning) ${count} Agent Conflict${count > 1 ? "s" : ""}`;
    this.conflictItem.tooltip = `${count} agent lock conflict(s) \u2014 click to review`;
    this.conflictItem.backgroundColor = new vscode14.ThemeColor(
      "statusBarItem.warningBackground"
    );
    this.conflictItem.show();
  }
  startConflictPolling(pollFn, intervalMs = 3e4) {
    this.stopConflictPolling();
    const run = async () => {
      try {
        const count = await pollFn();
        this.setConflicts(count);
      } catch {
      }
    };
    run();
    this.conflictInterval = setInterval(run, intervalMs);
  }
  stopConflictPolling() {
    if (this.conflictInterval) {
      clearInterval(this.conflictInterval);
      this.conflictInterval = void 0;
    }
  }
  get state() {
    return this._state;
  }
  dispose() {
    this.stopConflictPolling();
    this.stateItem.dispose();
    this.conflictItem.dispose();
  }
};

// src/providers/symbolExplorerProvider.ts
var vscode15 = __toESM(require("vscode"));
var fs7 = __toESM(require("fs"));
var path7 = __toESM(require("path"));
var TYPE_ICONS = {
  class: "symbol-class",
  function: "symbol-function",
  method: "symbol-method",
  module: "symbol-namespace",
  api: "symbol-interface",
  route: "symbol-event",
  workflow: "symbol-misc",
  file: "symbol-file",
  service: "symbol-property"
};
var SymbolTreeItem = class extends vscode15.TreeItem {
  constructor(label, collapsibleState, entity, filePath, isFile, fileEntityCount) {
    super(label, collapsibleState);
    this.entity = entity;
    this.filePath = filePath;
    this.isFile = isFile;
    this.fileEntityCount = fileEntityCount;
    if (entity && filePath) {
      this.tooltip = entity.docstring || `${entity.type} ${entity.name} at ${path7.basename(filePath)}:${entity.line_start}`;
      this.description = `${entity.type} \xB7 L${entity.line_start}`;
      this.iconPath = new vscode15.ThemeIcon(TYPE_ICONS[entity.type] || "symbol-misc");
      const absolutePath = filePath.startsWith("/") ? filePath : path7.join(getWorkspaceRoot() || "", filePath);
      this.command = {
        command: "vscode.open",
        title: "Open File",
        arguments: [
          vscode15.Uri.file(absolutePath),
          {
            selection: new vscode15.Range(
              new vscode15.Position(Math.max(0, entity.line_start - 1), 0),
              new vscode15.Position(Math.max(0, entity.line_start - 1), 0)
            )
          }
        ]
      };
    } else if (isFile && filePath) {
      this.iconPath = vscode15.ThemeIcon.File;
      this.resourceUri = vscode15.Uri.file(
        path7.join(getWorkspaceRoot() || "", filePath)
      );
      if (typeof fileEntityCount === "number") {
        this.description = fileEntityCount > 0 ? `${fileEntityCount} symbols` : "";
      }
    }
  }
};
var SymbolExplorerProvider = class {
  _onDidChangeTreeData = new vscode15.EventEmitter();
  onDidChangeTreeData = this._onDidChangeTreeData.event;
  projectMap = null;
  workspaceRoot = null;
  entitiesByFile = /* @__PURE__ */ new Map();
  constructor() {
    this.workspaceRoot = getWorkspaceRoot();
    this.loadProjectMap();
  }
  loadProjectMap() {
    const projectMapPath = getProjectMapPath();
    if (!projectMapPath || !fs7.existsSync(projectMapPath)) {
      return;
    }
    try {
      const content = fs7.readFileSync(projectMapPath, "utf-8");
      this.projectMap = JSON.parse(content);
      this.indexEntities();
      log(`Loaded project map with ${this.projectMap?.entities.length || 0} entities`);
    } catch (error) {
      log(`Failed to load project map: ${error}`);
    }
  }
  indexEntities() {
    this.entitiesByFile.clear();
    if (!this.projectMap) {
      return;
    }
    for (const entity of this.projectMap.entities) {
      const filePath = entity.file_path || entity.file;
      if (!filePath)
        continue;
      if (!this.entitiesByFile.has(filePath)) {
        this.entitiesByFile.set(filePath, []);
      }
      this.entitiesByFile.get(filePath).push({ ...entity, file_path: filePath });
    }
    log(`Indexed entities for ${this.entitiesByFile.size} files`);
  }
  getTreeItem(element) {
    return element;
  }
  getChildren(element) {
    if (!this.projectMap) {
      this.loadProjectMap();
      if (!this.projectMap) {
        const item = new SymbolTreeItem("\u25B6 Build Index to explore symbols", vscode15.TreeItemCollapsibleState.None);
        item.command = { command: "membrane.build", title: "Build Index" };
        item.iconPath = new vscode15.ThemeIcon("play");
        return Promise.resolve([item]);
      }
    }
    if (!element) {
      const files = (this.projectMap?.files || []).map((file) => ({
        file,
        count: this.entitiesByFile.get(file.path)?.length || 0
      })).filter((f) => f.count > 0).sort((a, b) => {
        if (a.count !== b.count)
          return b.count - a.count;
        return a.file.path.localeCompare(b.file.path);
      });
      if (files.length === 0) {
        const item = new SymbolTreeItem("\u25B6 Build Index to scan symbols", vscode15.TreeItemCollapsibleState.None);
        item.command = { command: "membrane.build", title: "Build Index" };
        item.iconPath = new vscode15.ThemeIcon("play");
        return Promise.resolve([item]);
      }
      const items = files.map(
        ({ file, count }) => new SymbolTreeItem(
          file.path,
          vscode15.TreeItemCollapsibleState.Collapsed,
          void 0,
          file.path,
          true,
          count
        )
      );
      return Promise.resolve(items);
    }
    if (element.isFile && element.filePath) {
      const filePath = element.filePath;
      const entities = this.entitiesByFile.get(filePath) || [];
      const sorted = [...entities].sort((a, b) => a.line_start - b.line_start);
      const items = sorted.map(
        (entity) => new SymbolTreeItem(
          entity.name,
          vscode15.TreeItemCollapsibleState.None,
          entity,
          filePath
        )
      );
      if (items.length === 0) {
        return Promise.resolve([
          new SymbolTreeItem(
            `(no symbols in ${path7.basename(filePath)})`,
            vscode15.TreeItemCollapsibleState.None
          )
        ]);
      }
      return Promise.resolve(items);
    }
    return Promise.resolve([]);
  }
  async refresh() {
    this.loadProjectMap();
    this._onDidChangeTreeData.fire();
  }
};

// src/providers/contextDebtProvider.ts
var vscode16 = __toESM(require("vscode"));
var DebtTreeItem = class extends vscode16.TreeItem {
  constructor(label, collapsibleState, score, tier) {
    super(label, collapsibleState);
    this.score = score;
    this.tier = tier;
    if (tier) {
      this.tooltip = `Score: ${score?.toFixed(2) || "N/A"} (${tier})`;
      if (tier === "CRITICAL") {
        this.iconPath = new vscode16.ThemeIcon("error", new vscode16.Color([255, 0, 0]));
      } else if (tier === "HIGH") {
        this.iconPath = new vscode16.ThemeIcon("warning", new vscode16.Color([255, 165, 0]));
      } else {
        this.iconPath = new vscode16.ThemeIcon("check");
      }
    }
  }
};
var ContextDebtProvider = class {
  constructor(runner) {
    this.runner = runner;
  }
  _onDidChangeTreeData = new vscode16.EventEmitter();
  onDidChangeTreeData = this._onDidChangeTreeData.event;
  data = [];
  getTreeItem(element) {
    return element;
  }
  getChildren(element) {
    if (!element) {
      if (this.data.length === 0) {
        const item = new DebtTreeItem("\u25B6 Build Index to analyze context debt", vscode16.TreeItemCollapsibleState.None);
        item.command = { command: "membrane.build", title: "Build Index" };
        item.iconPath = new vscode16.ThemeIcon("play");
        return Promise.resolve([item]);
      }
      return Promise.resolve(
        this.data.map(
          (item) => new DebtTreeItem(
            item.module || "Unknown",
            vscode16.TreeItemCollapsibleState.None,
            item.score,
            item.tier
          )
        )
      );
    }
    return Promise.resolve([]);
  }
  setData(data) {
    this.data = data;
    this._onDidChangeTreeData.fire();
  }
  async refresh() {
    if (!this.runner) {
      this._onDidChangeTreeData.fire();
      return;
    }
    try {
      const result = await this.runner.runJson(["debt", "--json"]);
      if (Array.isArray(result)) {
        this.data = result;
      }
    } catch (error) {
      log(`Failed to load context debt: ${error}`);
    }
    this._onDidChangeTreeData.fire();
  }
};

// src/providers/skillGatesProvider.ts
var vscode17 = __toESM(require("vscode"));
var SkillGatesProvider = class {
  constructor(runner) {
    this.runner = runner;
  }
  _onDidChangeTreeData = new vscode17.EventEmitter();
  onDidChangeTreeData = this._onDidChangeTreeData.event;
  data = [];
  getTreeItem(element) {
    return element;
  }
  getChildren(element) {
    if (!element) {
      if (this.data.length === 0) {
        const item = new vscode17.TreeItem("\u25B6 Build Index to run skill gates", vscode17.TreeItemCollapsibleState.None);
        item.command = { command: "membrane.build", title: "Build Index" };
        item.iconPath = new vscode17.ThemeIcon("play");
        return Promise.resolve([item]);
      }
      return Promise.resolve(
        this.data.map((item) => {
          const passed = item.passed ?? item.status === "pass";
          const label = `${item.action_id || item.skill || "Unknown"} \u2014 ${passed ? "\u2713 Passed" : "\u2717 Failed"}`;
          const treeItem = new vscode17.TreeItem(label, vscode17.TreeItemCollapsibleState.None);
          treeItem.tooltip = `Agent: ${item.agent_id || "Unknown"}
Blast radius: ${item.blast_radius ?? "N/A"}`;
          treeItem.iconPath = new vscode17.ThemeIcon(passed ? "pass" : "error");
          return treeItem;
        })
      );
    }
    return Promise.resolve([]);
  }
  setData(data) {
    this.data = data;
    this._onDidChangeTreeData.fire();
  }
  async refresh() {
    if (!this.runner) {
      this._onDidChangeTreeData.fire();
      return;
    }
    try {
      const result = await this.runner.runJson(["skills", "history", "--json"]);
      if (Array.isArray(result)) {
        this.data = result;
      }
    } catch (error) {
      log(`Failed to load skill gates: ${error}`);
    }
    this._onDidChangeTreeData.fire();
  }
};

// src/providers/agentLocksProvider.ts
var vscode18 = __toESM(require("vscode"));
var AgentLocksProvider = class {
  constructor(runner) {
    this.runner = runner;
  }
  _onDidChangeTreeData = new vscode18.EventEmitter();
  onDidChangeTreeData = this._onDidChangeTreeData.event;
  data = [];
  getTreeItem(element) {
    return element;
  }
  getChildren(element) {
    if (!element) {
      if (this.data.length === 0) {
        const item = new vscode18.TreeItem("No active agent locks", vscode18.TreeItemCollapsibleState.None);
        item.iconPath = new vscode18.ThemeIcon("unlock");
        return Promise.resolve([item]);
      }
      return Promise.resolve(
        this.data.map((item) => {
          const fileCount = item.files?.length ?? 1;
          const label = `${item.agent_id || "Unknown agent"} \u2014 ${fileCount} file${fileCount > 1 ? "s" : ""}`;
          const treeItem = new vscode18.TreeItem(label, vscode18.TreeItemCollapsibleState.None);
          treeItem.tooltip = `Acquired: ${item.acquired_at || "Unknown"}
TTL: ${item.ttl_seconds ? `${item.ttl_seconds}s` : "N/A"}`;
          treeItem.iconPath = new vscode18.ThemeIcon("lock");
          treeItem.description = item.acquired_at ? `${item.acquired_at}` : void 0;
          return treeItem;
        })
      );
    }
    return Promise.resolve([]);
  }
  setData(data) {
    this.data = data;
    this._onDidChangeTreeData.fire();
  }
  async refresh() {
    if (!this.runner) {
      this._onDidChangeTreeData.fire();
      return;
    }
    try {
      const result = await this.runner.runJson(["locks", "--json"]);
      if (Array.isArray(result)) {
        this.data = result;
      }
    } catch (error) {
      log(`Failed to load agent locks: ${error}`);
    }
    this._onDidChangeTreeData.fire();
  }
};

// src/providers/failurePatternsProvider.ts
var vscode19 = __toESM(require("vscode"));
var FailurePatternsProvider = class {
  constructor(runner) {
    this.runner = runner;
  }
  _onDidChangeTreeData = new vscode19.EventEmitter();
  onDidChangeTreeData = this._onDidChangeTreeData.event;
  data = [];
  getTreeItem(element) {
    return element;
  }
  getChildren(element) {
    if (!element) {
      if (this.data.length === 0) {
        const item = new vscode19.TreeItem("No failure patterns detected", vscode19.TreeItemCollapsibleState.None);
        item.iconPath = new vscode19.ThemeIcon("check");
        return Promise.resolve([item]);
      }
      return Promise.resolve(
        this.data.map((item) => {
          const freq = item.count ?? item.frequency ?? 0;
          const severity = freq > 5 ? "High" : freq > 1 ? "Medium" : "Low";
          const icon = freq > 5 ? "error" : freq > 1 ? "warning" : "info";
          const label = `${item.category || item.pattern || "Unknown"} (${freq}x \xB7 ${severity})`;
          const treeItem = new vscode19.TreeItem(label, vscode19.TreeItemCollapsibleState.None);
          treeItem.tooltip = [
            `Pattern: ${item.pattern_id || item.pattern || "Unknown"}`,
            `Glob: ${item.glob || "N/A"}`,
            `Last seen: ${item.last_seen || "N/A"}`
          ].join("\n");
          treeItem.iconPath = new vscode19.ThemeIcon(icon);
          return treeItem;
        })
      );
    }
    return Promise.resolve([]);
  }
  setData(data) {
    this.data = data;
    this._onDidChangeTreeData.fire();
  }
  async refresh() {
    if (!this.runner) {
      this._onDidChangeTreeData.fire();
      return;
    }
    try {
      const result = await this.runner.runJson(["patterns", "--json"]);
      if (Array.isArray(result)) {
        this.data = result;
      }
    } catch (error) {
      log(`Failed to load failure patterns: ${error}`);
    }
    this._onDidChangeTreeData.fire();
  }
};

// src/providers/trustScoresProvider.ts
var vscode20 = __toESM(require("vscode"));
var TIER_ICONS = {
  1: "verified",
  2: "pass",
  3: "circle-outline",
  4: "warning",
  5: "error"
};
var TIER_LABELS = {
  1: "T1:GroundTruth",
  2: "T2:High",
  3: "T3:Medium",
  4: "T4:Low",
  5: "T5:Unverified"
};
var TrustScoresProvider = class {
  constructor(runner) {
    this.runner = runner;
  }
  _onDidChangeTreeData = new vscode20.EventEmitter();
  onDidChangeTreeData = this._onDidChangeTreeData.event;
  data = [];
  getTreeItem(element) {
    return element;
  }
  getChildren(element) {
    if (!element) {
      if (this.data.length === 0) {
        const empty = new vscode20.TreeItem("No trust data \u2014 run Build Index first");
        empty.iconPath = new vscode20.ThemeIcon("info");
        return Promise.resolve([empty]);
      }
      return Promise.resolve(
        this.data.slice(0, 50).map((entry) => {
          const label = `${entry.label}  ${entry.file}`;
          const item = new vscode20.TreeItem(label, vscode20.TreeItemCollapsibleState.None);
          const iconName = TIER_ICONS[entry.tier] ?? "circle-outline";
          item.iconPath = new vscode20.ThemeIcon(iconName);
          item.tooltip = new vscode20.MarkdownString(
            `**${entry.file}**

Tier: ${TIER_LABELS[entry.tier] ?? entry.tier}  
Score: ${entry.score.toFixed(3)}  
Type: ${entry.source_type}  

_${entry.rationale}_`
          );
          item.description = `${entry.score.toFixed(3)}`;
          return item;
        })
      );
    }
    return Promise.resolve([]);
  }
  setData(data) {
    this.data = data;
    this._onDidChangeTreeData.fire();
  }
  async refresh() {
    if (!this.runner) {
      this._onDidChangeTreeData.fire();
      return;
    }
    try {
      const result = await this.runner.runJson(["trust", "--json"]);
      if (Array.isArray(result)) {
        this.data = result;
      }
    } catch (error) {
      log(`Failed to load trust scores: ${error}`);
    }
    this._onDidChangeTreeData.fire();
  }
};

// src/providers/playbookProvider.ts
var vscode21 = __toESM(require("vscode"));
var PlaybookProvider = class {
  constructor(runner) {
    this.runner = runner;
  }
  _onDidChangeTreeData = new vscode21.EventEmitter();
  onDidChangeTreeData = this._onDidChangeTreeData.event;
  data = [];
  getTreeItem(element) {
    return element;
  }
  getChildren(element) {
    if (!element) {
      if (this.data.length === 0) {
        const empty = new vscode21.TreeItem("No proposals yet \u2014 accumulate skill gate runs");
        empty.iconPath = new vscode21.ThemeIcon("lightbulb");
        return Promise.resolve([empty]);
      }
      return Promise.resolve(
        this.data.map((proposal) => {
          const confidencePct = Math.round(proposal.confidence * 100);
          const item = new vscode21.TreeItem(
            `${proposal.policy_name}  (${confidencePct}% confidence)`,
            vscode21.TreeItemCollapsibleState.None
          );
          item.iconPath = new vscode21.ThemeIcon("lightbulb");
          item.tooltip = new vscode21.MarkdownString(
            `**${proposal.policy_name}**

${proposal.description}

**Pattern:** \`${proposal.file_pattern}\`  
**Skills:** ${proposal.skills_to_add.join(", ")}  

_${proposal.evidence}_

\`\`\`yaml
${proposal.yaml_block}
\`\`\``
          );
          item.description = proposal.file_pattern;
          return item;
        })
      );
    }
    return Promise.resolve([]);
  }
  setData(data) {
    this.data = data;
    this._onDidChangeTreeData.fire();
  }
  async refresh() {
    if (!this.runner) {
      this._onDidChangeTreeData.fire();
      return;
    }
    try {
      const result = await this.runner.runJson(["playbook", "--json"]);
      if (Array.isArray(result)) {
        this.data = result;
      }
    } catch (error) {
      log(`Failed to load playbook proposals: ${error}`);
    }
    this._onDidChangeTreeData.fire();
  }
};

// src/diagnostics/skillGateDiagnostics.ts
var vscode22 = __toESM(require("vscode"));
var SkillGateDiagnosticProvider = class {
  constructor(runner) {
    this.runner = runner;
    this.collection = vscode22.languages.createDiagnosticCollection("membrane-skill-gates");
  }
  collection;
  running = false;
  async runForFiles(uris) {
    if (this.running || uris.length === 0)
      return;
    this.running = true;
    try {
      const filePaths = uris.map((u) => u.fsPath).join(",");
      const violations = await this.runner.runJson(
        ["skills", "run", "--files", filePaths, "--json"]
      );
      this.applyViolations(violations ?? []);
    } catch (err) {
      log(`Skill gate diagnostics error: ${err}`);
    } finally {
      this.running = false;
    }
  }
  async runForChangedFiles() {
    const changed = await this.getGitChangedFiles();
    if (changed.length > 0)
      await this.runForFiles(changed);
  }
  applyViolations(violations) {
    this.collection.clear();
    const byFile = /* @__PURE__ */ new Map();
    for (const v of violations) {
      const uri = vscode22.Uri.file(v.file);
      const startLine = Math.max(0, (v.line ?? 1) - 1);
      const range = new vscode22.Range(startLine, v.col ?? 0, startLine, v.col_end ?? 999);
      const msg = v.blast_radius != null ? `[Membrane/${v.skill}] ${v.message} (blast radius: ${v.blast_radius})` : `[Membrane/${v.skill}] ${v.message}`;
      const diag = new vscode22.Diagnostic(
        range,
        msg,
        v.severity === "error" ? vscode22.DiagnosticSeverity.Error : vscode22.DiagnosticSeverity.Warning
      );
      diag.source = `membrane`;
      diag.code = v.skill;
      const key = uri.toString();
      if (!byFile.has(key))
        byFile.set(key, []);
      byFile.get(key).push(diag);
    }
    byFile.forEach((diags, key) => this.collection.set(vscode22.Uri.parse(key), diags));
  }
  hookFileSave(context) {
    context.subscriptions.push(
      vscode22.workspace.onDidSaveTextDocument((doc) => {
        if (doc.uri.scheme === "file") {
          this.runForFiles([doc.uri]);
        }
      })
    );
    context.subscriptions.push(
      vscode22.commands.registerCommand("membrane.runSkillGatesAll", async () => {
        await vscode22.window.withProgress(
          { location: vscode22.ProgressLocation.Notification, title: "Membrane: Running skill gates..." },
          async () => this.runForChangedFiles()
        );
        vscode22.commands.executeCommand("workbench.action.problems.focus");
      })
    );
  }
  async getGitChangedFiles() {
    const { exec: exec2 } = require("child_process");
    const workspaceRoot = vscode22.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!workspaceRoot)
      return [];
    return new Promise((resolve) => {
      exec2("git diff --name-only HEAD", { cwd: workspaceRoot }, (err, stdout) => {
        if (err) {
          resolve([]);
          return;
        }
        const files = stdout.trim().split("\n").filter(Boolean);
        resolve(files.map((f) => vscode22.Uri.file(`${workspaceRoot}/${f}`)));
      });
    });
  }
  dispose() {
    this.collection.dispose();
  }
};

// src/panels/WizardPanel.ts
var vscode23 = __toESM(require("vscode"));
var fs8 = __toESM(require("fs"));
var path8 = __toESM(require("path"));
var WizardPanel = class _WizardPanel {
  constructor(panel, context, runner) {
    this.context = context;
    this.runner = runner;
    this.panel = panel;
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
    this.panel.webview.onDidReceiveMessage(
      (msg) => this.handleMessage(msg),
      null,
      this.disposables
    );
  }
  static currentPanel;
  panel;
  disposables = [];
  static show(context, runner) {
    if (_WizardPanel.currentPanel) {
      _WizardPanel.currentPanel.panel.reveal(vscode23.ViewColumn.One);
      return;
    }
    const panel = vscode23.window.createWebviewPanel(
      "membrane.wizard",
      "Membrane: Setup Wizard",
      vscode23.ViewColumn.One,
      {
        enableScripts: true,
        localResourceRoots: [vscode23.Uri.joinPath(context.extensionUri, "out")],
        retainContextWhenHidden: true
      }
    );
    const instance = new _WizardPanel(panel, context, runner);
    instance.panel.webview.html = instance.buildHtml();
    _WizardPanel.currentPanel = instance;
  }
  buildHtml() {
    const htmlPath = path8.join(
      this.context.extensionPath,
      "webview-src",
      "wizard",
      "index.html"
    );
    const scriptUri = this.panel.webview.asWebviewUri(
      vscode23.Uri.joinPath(this.context.extensionUri, "out", "webview-wizard.js")
    );
    let html = fs8.readFileSync(htmlPath, "utf-8");
    html = html.replace(/<script src="\.\.\/wizard\.js"><\/script>/, `<script src="${scriptUri}"></script>`);
    return html;
  }
  send(msg) {
    this.panel.webview.postMessage(msg);
  }
  log(text) {
    log(`[Wizard] ${text}`);
    this.send({ type: "wizardProgress", message: text });
  }
  async handleMessage(msg) {
    switch (msg.type) {
      case "wizardStep": {
        const step = msg.step ?? 0;
        if (step === 1)
          await this.runStep1CheckUv();
        if (step === 2)
          await this.runStep2Install();
        if (step === 3)
          await this.runStep3Init();
        if (step === 4)
          await this.runStep4Build();
        if (step === 5)
          await this.runStep5Mcp();
        break;
      }
      case "wizardSkip":
        this.context.globalState.update("membrane.initialized", true);
        this.dispose();
        break;
      case "wizardFinish":
        this.context.globalState.update("membrane.initialized", true);
        vscode23.window.showInformationMessage("Membrane: Setup complete! Your codebase is indexed and ready.");
        this.dispose();
        break;
    }
  }
  async runStep1CheckUv() {
    this.log("Checking uv executable...");
    const uvPath = detectUvPath(this.context.extensionPath);
    if (uvPath) {
      this.log(`\u2713 uv found at: ${uvPath}`);
    } else {
      this.log("\u2717 uv not found. Install from https://docs.astral.sh/uv/installation/");
    }
  }
  async runStep2Install() {
    if (isContextpackInstalled()) {
      this.log("\u2713 contextpack already installed");
      return;
    }
    this.log("Installing contextpack...");
    const uvPath = detectUvPath(this.context.extensionPath);
    if (!uvPath) {
      this.log("\u2717 uv not found \u2014 cannot install");
      return;
    }
    const workspaceRoot = vscode23.workspace.workspaceFolders?.[0]?.uri.fsPath ?? "";
    const ok = await installContextpack(uvPath, this.context.extensionPath, workspaceRoot, {
      report: ({ message }) => {
        if (message)
          this.log(message);
      }
    });
    this.log(ok ? "\u2713 contextpack installed" : "\u2717 Installation failed \u2014 check Membrane output channel");
  }
  async runStep3Init() {
    this.log("Initializing workspace...");
    try {
      const res = await this.runner.run(["init"]);
      this.log(res.exitCode === 0 ? "\u2713 Workspace initialized" : `\u2717 Init failed: ${res.stderr}`);
    } catch (err) {
      this.log(`\u2717 Init error: ${err.message}`);
    }
  }
  async runStep4Build() {
    this.log("Building index (this may take a minute)...");
    try {
      const res = await this.runner.run(["build"], { timeout: 3e5 });
      this.log(res.exitCode === 0 ? "\u2713 Index built successfully" : `\u2717 Build failed: ${res.stderr}`);
    } catch (err) {
      this.log(`\u2717 Build error: ${err.message}`);
    }
  }
  async runStep5Mcp() {
    this.log("Configuring MCP server...");
    try {
      const res = await this.runner.run(["harness", "install"]);
      this.log(res.exitCode === 0 ? "\u2713 MCP server configured" : `\u2717 MCP config failed: ${res.stderr}`);
    } catch (err) {
      this.log(`\u2717 MCP error: ${err.message}`);
    }
  }
  dispose() {
    _WizardPanel.currentPanel = void 0;
    this.panel.dispose();
    this.disposables.forEach((d) => d.dispose());
    this.disposables = [];
  }
};

// src/panels/GraphPanel.ts
var vscode24 = __toESM(require("vscode"));
var fs9 = __toESM(require("fs"));
var path9 = __toESM(require("path"));
var GraphPanel = class {
  static async show(context, runner) {
    const panel = vscode24.window.createWebviewPanel(
      "membrane.graph",
      "Membrane: Dependency Graph",
      vscode24.ViewColumn.One,
      {
        enableScripts: true,
        // Allow loading from vis.js CDN (graphify uses it)
        enableExternalUris: true,
        retainContextWhenHidden: true
      }
    );
    panel.webview.html = getLoadingHtml();
    const workspaceRoot = getWorkspaceRoot();
    if (!workspaceRoot) {
      panel.webview.html = getErrorHtml("No workspace folder open");
      return;
    }
    const outputPath = path9.join(workspaceRoot, ".membrane", "graph.html");
    try {
      const membraneDir = path9.join(workspaceRoot, ".membrane");
      if (!fs9.existsSync(membraneDir)) {
        fs9.mkdirSync(membraneDir, { recursive: true });
      }
      log(`Generating dependency graph to ${outputPath}...`);
      const result = await vscode24.window.withProgress(
        {
          location: vscode24.ProgressLocation.Notification,
          title: "Membrane: Generating dependency graph...",
          cancellable: false
        },
        async () => runner.run(["graphify", "--output", outputPath], { timeout: 3e5 })
      );
      if (result.exitCode !== 0) {
        log(`graphify failed: ${result.stderr}`);
        panel.webview.html = await getBuiltinGraphHtml(context, panel.webview, runner);
        return;
      }
      if (!fs9.existsSync(outputPath)) {
        panel.webview.html = getErrorHtml("graphify ran but did not produce output");
        return;
      }
      log(`Graph generated. Loading...`);
      const graphHtml = fs9.readFileSync(outputPath, "utf-8");
      panel.webview.html = graphHtml;
    } catch (err) {
      log(`GraphPanel error: ${err.message}`);
      panel.webview.html = await getBuiltinGraphHtml(context, panel.webview, runner);
    }
  }
};
async function getBuiltinGraphHtml(context, webview, runner) {
  const scriptUri = webview.asWebviewUri(
    vscode24.Uri.joinPath(context.extensionUri, "out", "webview-graph.js")
  );
  let graphData = { nodes: [], edges: [] };
  try {
    const neighbours = await runner.runJson(["graph", "neighbours", "--json"]);
    if (neighbours)
      graphData = neighbours;
  } catch {
  }
  const htmlPath = path9.join(context.extensionPath, "webview-src", "graph", "index.html");
  if (!fs9.existsSync(htmlPath)) {
    return getErrorHtml("Graph view HTML not found");
  }
  let html = fs9.readFileSync(htmlPath, "utf-8");
  html = html.replace(/<script src="\.\.\/graph\.js"><\/script>/, `<script src="${scriptUri}"></script>`);
  html = html.replace("</body>", `<script>window.__GRAPH_DATA__ = ${JSON.stringify(graphData)};</script></body>`);
  return html;
}
function getLoadingHtml() {
  return `<!DOCTYPE html><html><body style="background:#1e1e1e;color:#e0e0e0;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;">
    <div style="text-align:center">
      <div style="font-size:24px;margin-bottom:12px">\u26A1</div>
      <div>Generating dependency graph...</div>
    </div>
  </body></html>`;
}
function getErrorHtml(message) {
  return `<!DOCTYPE html><html><body style="background:#1e1e1e;color:#e0e0e0;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;">
    <div style="text-align:center">
      <div style="font-size:24px;margin-bottom:12px;color:#f44">\u2717</div>
      <div>${message}</div>
      <div style="margin-top:12px;font-size:12px;color:#888">Run "Build Index" first, then try again</div>
    </div>
  </body></html>`;
}

// src/extension.ts
var buildService = null;
var fileWatcher = null;
var mcpManager = null;
var statusBar = null;
var symbolExplorer = null;
var contextDebt = null;
var skillGates = null;
var agentLocks = null;
var failurePatterns = null;
var trustScores = null;
var playbook = null;
var diagnostics = null;
async function activate(context) {
  log(`${BRAND.name} activated`);
  statusBar = new StatusBarManager();
  context.subscriptions.push(statusBar);
  const workspaceRoot = getWorkspaceRoot();
  if (!workspaceRoot) {
    statusBar.setState("disabled", "no workspace folder");
    log("No workspace folder open");
    return;
  }
  context.subscriptions.push(
    vscode25.commands.registerCommand("membrane.showStatus", async () => {
      const pick = await vscode25.window.showQuickPick(
        [
          { label: "$(refresh) Retry Setup", detail: "Re-run the full activation sequence" },
          { label: "$(output) View Logs", detail: "Open the Membrane output channel" },
          { label: "$(gear) Open Settings", detail: "Open Membrane extension settings" },
          { label: "$(play) Run Build Index", detail: "Index codebase symbols and graph" }
        ],
        { placeHolder: `Membrane \u2014 ${statusBar?.state ?? "unknown"}` }
      );
      if (!pick)
        return;
      if (pick.label.includes("Retry"))
        vscode25.commands.executeCommand("workbench.action.reloadWindow");
      if (pick.label.includes("Logs"))
        vscode25.commands.executeCommand("workbench.action.output.toggleOutput");
      if (pick.label.includes("Settings"))
        vscode25.commands.executeCommand("workbench.action.openSettings", "membrane");
      if (pick.label.includes("Build"))
        vscode25.commands.executeCommand(COMMANDS.build);
    })
  );
  let runner;
  try {
    statusBar.setState("initializing", "checking uv");
    log("Detecting uv executable...");
    const uvPath = detectUvPath(context.extensionPath);
    if (!uvPath) {
      statusBar.setState("error", "uv not found \u2014 install from astral.sh/uv");
      vscode25.window.showErrorMessage(
        `${BRAND.name}: Could not find uv executable.`,
        "Install uv"
      ).then((action) => {
        if (action === "Install uv") {
          vscode25.env.openExternal(vscode25.Uri.parse("https://docs.astral.sh/uv/installation/"));
        }
      });
      return;
    }
    log(`Found uv at: ${uvPath}`);
    if (!isContextpackInstalled()) {
      statusBar.setState("initializing", "installing contextpack");
      log("contextpack not installed, installing...");
      const installed = await vscode25.window.withProgress(
        {
          location: vscode25.ProgressLocation.Notification,
          title: `${BRAND.name}: Installing contextpack`,
          cancellable: false
        },
        async (progress) => installContextpack(uvPath, context.extensionPath, workspaceRoot, progress)
      );
      if (!installed) {
        statusBar.setState("error", "contextpack install failed");
        return;
      }
      log("Installation complete.");
    }
    statusBar.setState("initializing", "verifying installation");
    const verification = await verifyContextpack(uvPath);
    if (!verification.ok) {
      log(`Verification warning: ${verification.error} \u2014 continuing anyway`);
    } else {
      log(`contextpack verified: ${verification.version}`);
    }
    const envVars = await buildEnvVars(context.secrets);
    runner = createRunner(uvPath, workspaceRoot, envVars);
    buildService = new BuildService(workspaceRoot, runner);
    fileWatcher = new FileWatcherManager(workspaceRoot, buildService);
    fileWatcher.start();
    statusBar.setState("initializing", "starting MCP server");
    try {
      mcpManager = new McpServerManager(workspaceRoot, runner, uvPath);
      await mcpManager.start();
    } catch (mcpErr) {
      log(`MCP server failed to start: ${mcpErr.message} \u2014 continuing without MCP`);
    }
  } catch (err) {
    statusBar.setState("error", err.message?.slice(0, 40));
    log(`Activation error: ${err.message}`);
    vscode25.window.showErrorMessage(
      `${BRAND.name}: Initialization failed \u2014 ${err.message}`,
      "View Logs"
    ).then((action) => {
      if (action === "View Logs")
        vscode25.commands.executeCommand("workbench.action.output.toggleOutput");
    });
    return;
  }
  symbolExplorer = new SymbolExplorerProvider();
  contextDebt = new ContextDebtProvider(runner);
  skillGates = new SkillGatesProvider(runner);
  agentLocks = new AgentLocksProvider(runner);
  failurePatterns = new FailurePatternsProvider(runner);
  trustScores = new TrustScoresProvider(runner);
  playbook = new PlaybookProvider(runner);
  vscode25.window.registerTreeDataProvider("membrane.symbolExplorer", symbolExplorer);
  vscode25.window.registerTreeDataProvider("membrane.contextDebt", contextDebt);
  vscode25.window.registerTreeDataProvider("membrane.skillGates", skillGates);
  vscode25.window.registerTreeDataProvider("membrane.agentLocks", agentLocks);
  vscode25.window.registerTreeDataProvider("membrane.failurePatterns", failurePatterns);
  vscode25.window.registerTreeDataProvider("membrane.trustScores", trustScores);
  vscode25.window.registerTreeDataProvider("membrane.playbook", playbook);
  registerBuildCommands(context, buildService, fileWatcher, {
    symbolExplorer,
    contextDebt,
    skillGates,
    agentLocks,
    failurePatterns,
    trustScores,
    playbook
  });
  registerHarvestCommands(context, runner, context.extensionUri);
  registerSkillCommands(context, runner, { skillGates, failurePatterns, contextDebt, agentLocks });
  registerGovernanceCommands(context, runner);
  registerSetupCommands(context, runner);
  context.subscriptions.push(
    vscode25.commands.registerCommand("membrane.refreshSymbolExplorer", () => symbolExplorer?.refresh()),
    vscode25.commands.registerCommand("membrane.refreshContextDebt", () => contextDebt?.refresh()),
    vscode25.commands.registerCommand("membrane.refreshSkillGates", () => skillGates?.refresh()),
    vscode25.commands.registerCommand("membrane.refreshAgentLocks", () => agentLocks?.refresh()),
    vscode25.commands.registerCommand("membrane.refreshFailurePatterns", () => failurePatterns?.refresh()),
    vscode25.commands.registerCommand("membrane.refreshTrustScores", () => trustScores?.refresh()),
    vscode25.commands.registerCommand("membrane.refreshPlaybook", () => playbook?.refresh())
  );
  context.subscriptions.push(
    vscode25.commands.registerCommand(
      COMMANDS.graphView,
      () => GraphPanel.show(context, runner)
    ),
    vscode25.commands.registerCommand(
      "membrane.harvestPanel",
      () => HarvestPanel.show(context, runner)
    )
  );
  diagnostics = new SkillGateDiagnosticProvider(runner);
  diagnostics.hookFileSave(context);
  context.subscriptions.push(diagnostics);
  statusBar.startConflictPolling(async () => {
    try {
      const locks = await runner.runJson(["locks", "--json"]);
      return Array.isArray(locks) ? locks.length : 0;
    } catch {
      return 0;
    }
  });
  context.subscriptions.push(
    vscode25.window.onDidChangeActiveTextEditor(async (editor) => {
      if (!editor || editor.document.uri.scheme !== "file")
        return;
      const filePath = editor.document.uri.fsPath;
      try {
        const patterns = await runner.runJson(["patterns", "--file", filePath, "--json"]);
        if (Array.isArray(patterns) && patterns.length > 0) {
          const action = await vscode25.window.showWarningMessage(
            `${BRAND.name}: ${patterns.length} known failure pattern(s) in this file`,
            "Review Patterns",
            "Dismiss"
          );
          if (action === "Review Patterns") {
            vscode25.commands.executeCommand(COMMANDS.patternsShow);
          }
        }
      } catch {
      }
    })
  );
  await Promise.allSettled([
    symbolExplorer.refresh(),
    contextDebt.refresh(),
    skillGates.refresh(),
    agentLocks.refresh(),
    failurePatterns.refresh(),
    trustScores.refresh(),
    playbook.refresh()
  ]);
  statusBar.setState("ready");
  const initialized = context.globalState.get("membrane.initialized");
  if (!initialized && !isContextpackInitialized()) {
    WizardPanel.show(context, runner);
  } else if (!isContextpackInitialized()) {
    vscode25.window.showInformationMessage(
      `${BRAND.name}: Ready. Run "Build Index" (${COMMANDS.build}) to index your codebase.`,
      "Build Now"
    ).then((action) => {
      if (action === "Build Now")
        vscode25.commands.executeCommand(COMMANDS.build);
    });
  }
  log(`${BRAND.name} initialization complete`);
}
async function deactivate() {
  log(`${BRAND.name} deactivating`);
  fileWatcher?.dispose();
  if (mcpManager) {
    await mcpManager.stop();
    mcpManager.dispose();
  }
  buildService?.dispose();
  dispose();
}
function getProviders() {
  return { symbolExplorer, contextDebt, skillGates, agentLocks, failurePatterns, trustScores, playbook };
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  activate,
  deactivate,
  getProviders
});
