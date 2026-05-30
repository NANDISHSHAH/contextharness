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
var vscode19 = __toESM(require("vscode"));

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
  refreshFailurePatterns: "membrane.refreshFailurePatterns"
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
async function installContextpack(uvPath, extensionPath, progress) {
  const venv = getVenvPath();
  const pythonPath = getPythonPath(venv);
  const wheelsDir = path2.join(extensionPath, "resources", "wheels");
  let actualWheelPath = null;
  if (fs2.existsSync(wheelsDir)) {
    const files = fs2.readdirSync(wheelsDir);
    const wheelFile = files.find((f) => f.endsWith(".whl"));
    if (wheelFile) {
      actualWheelPath = path2.join(wheelsDir, wheelFile);
    }
  }
  try {
    progress?.report({ message: "Creating venv..." });
    log(`Creating venv at ${venv}`);
    (0, import_child_process2.execSync)(`"${uvPath}" venv "${venv}"`, { stdio: "pipe", encoding: "utf-8" });
    log("venv created successfully");
    progress?.report({ message: "Installing contextpack...", increment: 50 });
    let installCmd = "";
    if (actualWheelPath) {
      log(`Installing contextpack from bundled wheel: ${actualWheelPath}`);
      installCmd = `"${pythonPath}" -m pip install "${actualWheelPath}[harness]" -v`;
    } else {
      log("No bundled wheel found, installing from PyPI...");
      installCmd = `"${pythonPath}" -m pip install contextpack[harness] -v`;
    }
    const output = (0, import_child_process2.execSync)(installCmd, { encoding: "utf-8", stdio: "pipe" });
    log(`pip output: ${output}`);
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
    log(`\u274C Installation failed: ${errorMsg}`);
    vscode2.window.showErrorMessage(
      `Membrane installation failed.

Error: ${errorMsg}

Try manually installing:
${pythonPath} -m pip install contextpack[harness]`
    );
    return false;
  }
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
  return fs2.existsSync(pythonPath);
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
      const env = {
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
          env,
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
    const env = {
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
      env,
      stdio: ["pipe", "pipe", "pipe"]
    });
  }
  /**
   * Spawn MCP server process.
   */
  spawnMcpServer(opts) {
    const env = {
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
      env,
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
    const fs8 = require("fs");
    return fs8.existsSync(configPath);
  } catch {
    return false;
  }
}

// src/utils/config.ts
async function buildEnvVars(secretStorage) {
  const config = vscode4.workspace.getConfiguration();
  const env = {
    ...process.env
  };
  const workspaceRoot = getWorkspaceRoot();
  if (workspaceRoot) {
    env[ENV_VARS.CONTEXTPACK_ROOT] = workspaceRoot;
  }
  const embeddingProvider = config.get(SETTINGS.embeddingProvider) || "hash";
  env[ENV_VARS.CONTEXTPACK_EMBEDDING_PROVIDER] = embeddingProvider;
  const llmProvider = config.get(SETTINGS.llmProvider);
  if (llmProvider) {
    env[ENV_VARS.CONTEXTPACK_LLM_PROVIDER] = llmProvider;
  }
  const openaiKey = await secretStorage.get("membrane.openaiApiKey");
  if (openaiKey) {
    env[ENV_VARS.OPENAI_API_KEY] = openaiKey;
  }
  const azureEndpoint = config.get(SETTINGS.azureEndpoint);
  if (azureEndpoint) {
    env[ENV_VARS.AZURE_OPENAI_ENDPOINT] = azureEndpoint;
  }
  const azureKey = await secretStorage.get("membrane.azureApiKey");
  if (azureKey) {
    env[ENV_VARS.AZURE_OPENAI_API_KEY] = azureKey;
  }
  const azureDeployment = config.get(SETTINGS.azureDeployment);
  if (azureDeployment) {
    env[ENV_VARS.AZURE_OPENAI_DEPLOYMENT] = azureDeployment;
  }
  const azureEmbeddingDeploy = config.get(SETTINGS.azureEmbeddingDeployment);
  if (azureEmbeddingDeploy) {
    env[ENV_VARS.AZURE_OPENAI_EMBEDDING_DEPLOYMENT] = azureEmbeddingDeploy;
  }
  const jiraUrl = config.get(SETTINGS.jiraBaseUrl);
  if (jiraUrl) {
    env[ENV_VARS.JIRA_BASE_URL] = jiraUrl;
  }
  const jiraEmail = config.get(SETTINGS.jiraEmail);
  if (jiraEmail) {
    env[ENV_VARS.JIRA_EMAIL] = jiraEmail;
  }
  const jiraToken = await secretStorage.get("membrane.jiraApiToken");
  if (jiraToken) {
    env[ENV_VARS.JIRA_API_TOKEN] = jiraToken;
  }
  const maxEmbedEntities = config.get(SETTINGS.maxEmbedEntities);
  if (maxEmbedEntities) {
    env[ENV_VARS.CONTEXTPACK_MAX_EMBED_ENTITIES] = String(maxEmbedEntities);
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
              env[key] = value;
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
  return env;
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
var vscode7 = __toESM(require("vscode"));

// src/build/statusBar.ts
var vscode6 = __toESM(require("vscode"));
var fs6 = __toESM(require("fs"));
var path6 = __toESM(require("path"));
var StatusBarManager = class {
  buildStatusItem;
  stalenessItem;
  agentLocksItem;
  currentBuildStatus = {
    state: "idle",
    message: "Membrane"
  };
  constructor() {
    this.buildStatusItem = vscode6.window.createStatusBarItem(
      vscode6.StatusBarAlignment.Left,
      100
    );
    this.buildStatusItem.command = COMMANDS.build;
    this.updateBuildStatus();
    this.stalenessItem = vscode6.window.createStatusBarItem(
      vscode6.StatusBarAlignment.Left,
      99
    );
    this.stalenessItem.command = COMMANDS.debtReport;
    this.updateStaleness();
    this.agentLocksItem = vscode6.window.createStatusBarItem(
      vscode6.StatusBarAlignment.Left,
      98
    );
    this.agentLocksItem.command = COMMANDS.locksShow;
    this.updateAgentLocks();
    this.buildStatusItem.show();
    this.stalenessItem.show();
    this.agentLocksItem.show();
  }
  updateBuildStatus(status) {
    if (status) {
      this.currentBuildStatus = status;
    }
    const { state, message } = this.currentBuildStatus;
    let icon = "$(check)";
    let color = void 0;
    if (state === "building") {
      icon = "$(loading~spin)";
    } else if (state === "stale") {
      icon = "$(warning)";
      color = "statusBarItem.warningBackground";
    } else if (state === "error") {
      icon = "$(error)";
      color = "statusBarItem.errorBackground";
    }
    this.buildStatusItem.text = `${icon} ${BRAND.shortName}: ${message}`;
    if (color) {
      this.buildStatusItem.backgroundColor = new vscode6.ThemeColor(color);
    } else {
      this.buildStatusItem.backgroundColor = void 0;
    }
  }
  updateStaleness() {
    const contextpackDir = getContextpackDir();
    if (!contextpackDir) {
      this.stalenessItem.text = "$(clock) No workspace";
      return;
    }
    const configPath = path6.join(contextpackDir, "config.json");
    if (!fs6.existsSync(configPath)) {
      this.stalenessItem.text = "$(clock) Not initialized";
      return;
    }
    try {
      const config = JSON.parse(fs6.readFileSync(configPath, "utf-8"));
      const lastBuildTime = config.built_at ? new Date(config.built_at).getTime() : Date.now();
      const now = Date.now();
      const diff = now - lastBuildTime;
      const hours = Math.floor(diff / (1e3 * 60 * 60));
      const minutes = Math.floor(diff % (1e3 * 60 * 60) / (1e3 * 60));
      let timeStr;
      if (hours > 24) {
        timeStr = `${Math.floor(hours / 24)}d ago`;
      } else if (hours > 0) {
        timeStr = `${hours}h ago`;
      } else if (minutes > 0) {
        timeStr = `${minutes}m ago`;
      } else {
        timeStr = "now";
      }
      this.stalenessItem.text = `$(clock) ${timeStr}`;
    } catch (error) {
      log(`Failed to read config.json: ${error}`);
      this.stalenessItem.text = "$(clock) Error reading config";
    }
  }
  updateAgentLocks(count = 0) {
    if (count === 0) {
      this.agentLocksItem.text = "$(person) 0 agents";
    } else if (count === 1) {
      this.agentLocksItem.text = "$(person) 1 agent";
    } else {
      this.agentLocksItem.text = `$(person) ${count} agents`;
    }
  }
  dispose() {
    this.buildStatusItem.dispose();
    this.stalenessItem.dispose();
    this.agentLocksItem.dispose();
  }
};

// src/build/buildService.ts
var BuildService = class {
  constructor(workspaceRoot, runner) {
    this.workspaceRoot = workspaceRoot;
    this.runner = runner;
    this.statusBar = new StatusBarManager();
  }
  isBuilding = false;
  statusBar;
  /**
   * Full build of the index.
   */
  async build(showProgress = true) {
    if (this.isBuilding) {
      vscode7.window.showInformationMessage("Membrane: Build already in progress");
      return false;
    }
    this.isBuilding = true;
    this.statusBar.updateBuildStatus({ state: "building", message: "Building..." });
    try {
      if (showProgress) {
        return await vscode7.window.withProgress(
          {
            location: vscode7.ProgressLocation.Notification,
            title: "Membrane: Building index",
            cancellable: true
          },
          async (progress) => {
            return await this._buildWithProgress(progress);
          }
        );
      } else {
        const result = await this.runner.run(["build", "."]);
        return result.exitCode === 0;
      }
    } finally {
      this.isBuilding = false;
      this.statusBar.updateStaleness();
    }
  }
  async _buildWithProgress(progress) {
    return new Promise((resolve) => {
      log("Starting build with progress tracking");
      const proc = this.runner.spawn(["build", "."]);
      let stdout = "";
      let stderr = "";
      let completed = false;
      let processExited = false;
      const buildTimeout = setTimeout(() => {
        if (!processExited) {
          log("\u26A0\uFE0F Build timeout - killing process");
          proc.kill();
          this.isBuilding = false;
          this.statusBar.updateBuildStatus({ state: "error", message: "Build timeout" });
          vscode7.window.showErrorMessage(
            "Membrane: Build timed out after 5 minutes. The process may be stuck."
          );
          resolve(false);
        }
      }, 3e5);
      proc.stdout?.on("data", (data) => {
        const text = data.toString();
        stdout += text;
        log(text.trim());
        if (text.includes("scan")) {
          progress.report({ message: "Scanning files...", increment: 10 });
        } else if (text.includes("parse")) {
          progress.report({ message: "Parsing code...", increment: 20 });
        } else if (text.includes("graph")) {
          progress.report({ message: "Building graph...", increment: 20 });
        } else if (text.includes("chunk")) {
          progress.report({ message: "Chunking content...", increment: 20 });
        } else if (text.includes("embed")) {
          progress.report({ message: "Embedding entities...", increment: 15 });
        } else if (text.includes("store")) {
          progress.report({ message: "Storing to database...", increment: 15 });
        }
        if (text.includes("Build complete") || text.includes("total")) {
          completed = true;
          progress.report({ message: "Build complete", increment: 0 });
        }
      });
      proc.stderr?.on("data", (data) => {
        const text = data.toString();
        stderr += text;
        if (text.trim()) {
          log(`[stderr] ${text.trim()}`);
        }
      });
      proc.on("exit", (code) => {
        clearTimeout(buildTimeout);
        processExited = true;
        log(`Build process exited with code: ${code}`);
        if (code === 0) {
          log("\u2705 Build succeeded");
          this.statusBar.updateBuildStatus({ state: "ready", message: "Ready" });
          resolve(true);
        } else {
          log(`\u274C Build failed with code ${code}`);
          this.statusBar.updateBuildStatus({ state: "error", message: "Build failed" });
          vscode7.window.showErrorMessage(
            `Membrane: Build failed with code ${code}. Check output for details.`
          );
          resolve(false);
        }
      });
      proc.on("error", (error) => {
        clearTimeout(buildTimeout);
        log(`\u274C Build process error: ${error.message}`);
        this.statusBar.updateBuildStatus({ state: "error", message: "Build error" });
        vscode7.window.showErrorMessage(`Membrane: Build process error - ${error.message}`);
        resolve(false);
      });
    });
  }
  /**
   * Incremental build (for file watcher).
   */
  async incrementalBuild() {
    return this.build(false);
  }
  getStatusBar() {
    return this.statusBar;
  }
  dispose() {
    this.statusBar.dispose();
  }
};

// src/watcher/fileWatcher.ts
var vscode8 = __toESM(require("vscode"));
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
    const autoWatch = vscode8.workspace.getConfiguration().get(SETTINGS.autoWatch, true);
    if (!autoWatch) {
      log("File watcher disabled in settings");
      return;
    }
    log("Starting file watcher (excluding .contextpack, node_modules, .git)");
    const pattern = new vscode8.RelativePattern(
      this.workspaceRoot,
      "**/*.{py,ts,tsx,js,jsx,md,yaml,yml,json}"
    );
    this.watcher = vscode8.workspace.createFileSystemWatcher(pattern, true, false, true);
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
var vscode9 = __toESM(require("vscode"));
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
    } catch (error) {
      log(`Error refreshing providers: ${error}`);
    }
  };
  context.subscriptions.push(
    vscode9.commands.registerCommand(COMMANDS.build, async () => {
      log("Command: build");
      const success = await buildService2.build();
      if (success) {
        await refreshProviders();
        vscode9.window.showInformationMessage("Membrane: Build completed");
      } else {
        vscode9.window.showErrorMessage("Membrane: Build failed");
      }
    })
  );
  context.subscriptions.push(
    vscode9.commands.registerCommand(COMMANDS.incrementalBuild, async () => {
      log("Command: incremental build");
      const success = await buildService2.incrementalBuild();
      if (success) {
        await refreshProviders();
      } else {
        vscode9.window.showErrorMessage("Membrane: Incremental build failed");
      }
    })
  );
  context.subscriptions.push(
    vscode9.commands.registerCommand(COMMANDS.watch, async () => {
      log("Command: toggle watch");
      fileWatcher2.toggle();
      const status = fileWatcher2.isActive() ? "enabled" : "disabled";
      vscode9.window.showInformationMessage(`Membrane: File watcher ${status}`);
    })
  );
}

// src/commands/harvestCommands.ts
var vscode10 = __toESM(require("vscode"));
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
function registerHarvestCommands(context, runner) {
  context.subscriptions.push(
    vscode10.commands.registerCommand(COMMANDS.harvest, async () => {
      log("Command: harvest");
      const query = await vscode10.window.showInputBox({
        prompt: "Enter query for context harvesting",
        placeHolder: 'e.g., "authentication flow"'
      });
      if (!query) {
        return;
      }
      showOutput();
      log(`Harvesting context for: "${query}"`);
      const result = await vscode10.window.withProgress(
        {
          location: vscode10.ProgressLocation.Notification,
          title: `Membrane: Harvesting context for "${query}"`,
          cancellable: false
        },
        async () => runner.run(["harvest", query])
      );
      if (result.exitCode === 0) {
        log(result.stdout);
        await showAsMarkdownDoc(result.stdout || "_no context returned_", `Harvest: ${query}`);
      } else {
        log(`Harvest failed: ${result.stderr}`);
        vscode10.window.showErrorMessage(`Membrane: Harvest failed \u2014 ${result.stderr || "unknown error"}`);
      }
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
      const result = await runner.run(["coupling", "trend"]);
      if (result.exitCode === 0) {
        log(result.stdout);
      } else {
        log(`Coupling trend failed: ${result.stderr}`);
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

// src/providers/symbolExplorerProvider.ts
var vscode14 = __toESM(require("vscode"));
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
var SymbolTreeItem = class extends vscode14.TreeItem {
  constructor(label, collapsibleState, entity, filePath, isFile, fileEntityCount) {
    super(label, collapsibleState);
    this.entity = entity;
    this.filePath = filePath;
    this.isFile = isFile;
    this.fileEntityCount = fileEntityCount;
    if (entity && filePath) {
      this.tooltip = entity.docstring || `${entity.type} ${entity.name} at ${path7.basename(filePath)}:${entity.line_start}`;
      this.description = `${entity.type} \xB7 L${entity.line_start}`;
      this.iconPath = new vscode14.ThemeIcon(TYPE_ICONS[entity.type] || "symbol-misc");
      const absolutePath = filePath.startsWith("/") ? filePath : path7.join(getWorkspaceRoot() || "", filePath);
      this.command = {
        command: "vscode.open",
        title: "Open File",
        arguments: [
          vscode14.Uri.file(absolutePath),
          {
            selection: new vscode14.Range(
              new vscode14.Position(Math.max(0, entity.line_start - 1), 0),
              new vscode14.Position(Math.max(0, entity.line_start - 1), 0)
            )
          }
        ]
      };
    } else if (isFile && filePath) {
      this.iconPath = vscode14.ThemeIcon.File;
      this.resourceUri = vscode14.Uri.file(
        path7.join(getWorkspaceRoot() || "", filePath)
      );
      if (typeof fileEntityCount === "number") {
        this.description = fileEntityCount > 0 ? `${fileEntityCount} symbols` : "";
      }
    }
  }
};
var SymbolExplorerProvider = class {
  _onDidChangeTreeData = new vscode14.EventEmitter();
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
        return Promise.resolve([
          new SymbolTreeItem(
            'No project map found. Run "Build Index" first.',
            vscode14.TreeItemCollapsibleState.None
          )
        ]);
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
        return Promise.resolve([
          new SymbolTreeItem(
            'No symbols found. Run "Build Index" to scan code.',
            vscode14.TreeItemCollapsibleState.None
          )
        ]);
      }
      const items = files.map(
        ({ file, count }) => new SymbolTreeItem(
          file.path,
          vscode14.TreeItemCollapsibleState.Collapsed,
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
          vscode14.TreeItemCollapsibleState.None,
          entity,
          filePath
        )
      );
      if (items.length === 0) {
        return Promise.resolve([
          new SymbolTreeItem(
            `(no symbols in ${path7.basename(filePath)})`,
            vscode14.TreeItemCollapsibleState.None
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
var vscode15 = __toESM(require("vscode"));
var DebtTreeItem = class extends vscode15.TreeItem {
  constructor(label, collapsibleState, score, tier) {
    super(label, collapsibleState);
    this.score = score;
    this.tier = tier;
    if (tier) {
      this.tooltip = `Score: ${score?.toFixed(2) || "N/A"} (${tier})`;
      if (tier === "CRITICAL") {
        this.iconPath = new vscode15.ThemeIcon("error", new vscode15.Color([255, 0, 0]));
      } else if (tier === "HIGH") {
        this.iconPath = new vscode15.ThemeIcon("warning", new vscode15.Color([255, 165, 0]));
      } else {
        this.iconPath = new vscode15.ThemeIcon("check");
      }
    }
  }
};
var ContextDebtProvider = class {
  constructor(runner) {
    this.runner = runner;
  }
  _onDidChangeTreeData = new vscode15.EventEmitter();
  onDidChangeTreeData = this._onDidChangeTreeData.event;
  data = [];
  getTreeItem(element) {
    return element;
  }
  getChildren(element) {
    if (!element) {
      if (this.data.length === 0) {
        return Promise.resolve([
          new DebtTreeItem('Run "Build Index" to analyze context debt', vscode15.TreeItemCollapsibleState.None)
        ]);
      }
      return Promise.resolve(
        this.data.map(
          (item) => new DebtTreeItem(
            item.module || "Unknown",
            vscode15.TreeItemCollapsibleState.None,
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
var vscode16 = __toESM(require("vscode"));
var SkillGatesProvider = class {
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
        return Promise.resolve([
          new vscode16.TreeItem("No skill gate results yet")
        ]);
      }
      return Promise.resolve(
        this.data.map((item) => {
          const item_obj = new vscode16.TreeItem(
            `${item.action_id || "Unknown"} - ${item.passed ? "\u2713 Passed" : "\u2717 Failed"}`,
            vscode16.TreeItemCollapsibleState.Collapsed
          );
          item_obj.tooltip = `Agent: ${item.agent_id || "Unknown"}`;
          return item_obj;
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
var vscode17 = __toESM(require("vscode"));
var AgentLocksProvider = class {
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
        return Promise.resolve([
          new vscode17.TreeItem("No active agent locks")
        ]);
      }
      return Promise.resolve(
        this.data.map((item) => {
          const item_obj = new vscode17.TreeItem(
            `${item.agent_id || "Unknown"} - ${item.files?.length || 0} files`,
            vscode17.TreeItemCollapsibleState.None
          );
          item_obj.tooltip = `Acquired: ${item.acquired_at || "Unknown"}`;
          item_obj.iconPath = new vscode17.ThemeIcon("lock");
          return item_obj;
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
var vscode18 = __toESM(require("vscode"));
var FailurePatternsProvider = class {
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
        return Promise.resolve([
          new vscode18.TreeItem("No failure patterns detected")
        ]);
      }
      return Promise.resolve(
        this.data.map((item) => {
          const item_obj = new vscode18.TreeItem(
            `${item.category || "Unknown"} (${item.count || 0}x)`,
            vscode18.TreeItemCollapsibleState.None
          );
          item_obj.tooltip = `Pattern: ${item.pattern_id || "Unknown"}
Glob: ${item.glob || "N/A"}`;
          item_obj.iconPath = new vscode18.ThemeIcon("alert");
          return item_obj;
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

// src/extension.ts
var buildService = null;
var fileWatcher = null;
var mcpManager = null;
var symbolExplorer = null;
var contextDebt = null;
var skillGates = null;
var agentLocks = null;
var failurePatterns = null;
async function activate(context) {
  log(`${BRAND.name} activated`);
  const workspaceRoot = getWorkspaceRoot();
  if (!workspaceRoot) {
    log("No workspace folder open");
    return;
  }
  try {
    log("Detecting uv executable...");
    const uvPath = detectUvPath(context.extensionPath);
    if (!uvPath) {
      vscode19.window.showErrorMessage(
        `${BRAND.name}: Could not find uv executable. Please install uv from https://docs.astral.sh/uv/installation/`
      );
      return;
    }
    log(`Found uv at: ${uvPath}`);
    if (!isContextpackInstalled()) {
      log("contextpack not installed, installing...");
      const result = await vscode19.window.withProgress(
        {
          location: vscode19.ProgressLocation.Notification,
          title: `${BRAND.name}: Installing contextpack`,
          cancellable: false
        },
        async (progress) => {
          return await installContextpack(uvPath, context.extensionPath, progress);
        }
      );
      if (!result) {
        vscode19.window.showErrorMessage(`${BRAND.name}: Failed to install contextpack`);
        return;
      }
      log("Installation complete, continuing...");
    }
    log("Verifying contextpack installation...");
    const verification = await verifyContextpack(uvPath);
    if (!verification.ok) {
      log(`Verification warning: ${verification.error}, but venv exists - continuing...`);
    } else {
      log(`contextpack verified: ${verification.version}`);
    }
    const envVars = await buildEnvVars(context.secrets);
    const runner = createRunner(uvPath, workspaceRoot, envVars);
    buildService = new BuildService(workspaceRoot, runner);
    fileWatcher = new FileWatcherManager(workspaceRoot, buildService);
    fileWatcher.start();
    mcpManager = new McpServerManager(workspaceRoot, runner, uvPath);
    await mcpManager.start();
    symbolExplorer = new SymbolExplorerProvider();
    contextDebt = new ContextDebtProvider(runner);
    skillGates = new SkillGatesProvider(runner);
    agentLocks = new AgentLocksProvider(runner);
    failurePatterns = new FailurePatternsProvider(runner);
    vscode19.window.registerTreeDataProvider("membrane.symbolExplorer", symbolExplorer);
    vscode19.window.registerTreeDataProvider("membrane.contextDebt", contextDebt);
    vscode19.window.registerTreeDataProvider("membrane.skillGates", skillGates);
    vscode19.window.registerTreeDataProvider("membrane.agentLocks", agentLocks);
    vscode19.window.registerTreeDataProvider("membrane.failurePatterns", failurePatterns);
    registerBuildCommands(context, buildService, fileWatcher, {
      symbolExplorer,
      contextDebt,
      skillGates,
      agentLocks,
      failurePatterns
    });
    registerHarvestCommands(context, runner);
    registerSkillCommands(context, runner, {
      skillGates,
      failurePatterns,
      contextDebt,
      agentLocks
    });
    registerGovernanceCommands(context, runner);
    registerSetupCommands(context, runner);
    context.subscriptions.push(
      vscode19.commands.registerCommand(
        "membrane.refreshSymbolExplorer",
        () => symbolExplorer?.refresh()
      ),
      vscode19.commands.registerCommand(
        "membrane.refreshContextDebt",
        () => contextDebt?.refresh()
      ),
      vscode19.commands.registerCommand(
        "membrane.refreshSkillGates",
        () => skillGates?.refresh()
      ),
      vscode19.commands.registerCommand(
        "membrane.refreshAgentLocks",
        () => agentLocks?.refresh()
      ),
      vscode19.commands.registerCommand(
        "membrane.refreshFailurePatterns",
        () => failurePatterns?.refresh()
      )
    );
    await Promise.all([
      symbolExplorer?.refresh(),
      contextDebt?.refresh(),
      skillGates?.refresh(),
      agentLocks?.refresh(),
      failurePatterns?.refresh()
    ]);
    if (!isContextpackInitialized()) {
      vscode19.window.showInformationMessage(
        `${BRAND.name}: Welcome! Your workspace is ready. Run "${BRAND.name}: Build Index" to get started.`
      );
    }
    log(`${BRAND.name} initialization complete`);
  } catch (error) {
    log(`Activation error: ${error.message}`);
    vscode19.window.showErrorMessage(`${BRAND.name}: Initialization failed - ${error.message}`);
  }
}
async function deactivate() {
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
  dispose();
}
function getProviders() {
  return {
    symbolExplorer,
    contextDebt,
    skillGates,
    agentLocks,
    failurePatterns
  };
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  activate,
  deactivate,
  getProviders
});
