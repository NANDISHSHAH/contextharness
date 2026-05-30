import { execFile, exec, spawn, ChildProcess } from 'child_process';
import { getVenvPath, getVenvPythonPath } from './detector';
import * as path from 'path';
import * as fs from 'fs';
import { log } from '../utils/output';

export interface RunResult {
  exitCode: number;
  stdout: string;
  stderr: string;
}

export interface RunOptions {
  cwd?: string;
  env?: Record<string, string>;
  timeout?: number;
}

export interface SpawnOptions {
  cwd?: string;
  env?: Record<string, string>;
}

/**
 * Execute context CLI commands via venv Python or uv run.
 */
export class ContextRunner {
  private venvPython: string;
  private useVenvPython: boolean;

  constructor(
    private uvPath: string,
    private workspaceRoot: string,
    private envVars: Record<string, string> = {},
  ) {
    this.venvPython = getVenvPythonPath();
    // Use venv Python if it exists and is executable
    this.useVenvPython = fs.existsSync(this.venvPython);
    if (this.useVenvPython) {
      log(`Using venv Python: ${this.venvPython}`);
    } else {
      log(`Venv Python not found, will use: ${this.uvPath} run`);
    }
  }

  /** Read an env var the runner will pass to subprocesses (from .env or settings). */
  getEnvVar(name: string): string | undefined {
    return this.envVars[name] || process.env[name];
  }

  /**
   * Run a command and wait for completion.
   */
  async run(args: string[], opts?: RunOptions): Promise<RunResult> {
    return new Promise((resolve) => {
      const env = {
        ...process.env,
        ...this.envVars,
        ...opts?.env,
        CONTEXTPACK_ROOT: this.workspaceRoot,
      };

      let command: string;
      let cmdArgs: string[];

      if (this.useVenvPython) {
        // Use venv Python directly
        command = this.venvPython;
        cmdArgs = ['-m', 'contextpack.cli.main', ...args];
        log(`Running: ${command} ${cmdArgs.join(' ')}`);
      } else {
        // Fall back to uv run
        command = this.uvPath;
        cmdArgs = ['run', '--extra', 'harness', 'context', ...args];
        log(`Running: ${command} ${cmdArgs.join(' ')}`);
      }

      const timeout = opts?.timeout || 120000;
      let timedOut = false;

      const timer = setTimeout(() => {
        timedOut = true;
      }, timeout);

      execFile(
        command,
        cmdArgs,
        {
          cwd: opts?.cwd || this.workspaceRoot,
          env,
          maxBuffer: 10 * 1024 * 1024, // 10MB
        },
        (error, stdout, stderr) => {
          clearTimeout(timer);

          if (timedOut) {
            resolve({
              exitCode: -1,
              stdout: '',
              stderr: `Command timed out after ${timeout}ms`,
            });
            return;
          }

          const exitCode = error?.code || 0;
          resolve({
            exitCode,
            stdout,
            stderr,
          });
        },
      );
    });
  }

  /**
   * Run a command and parse JSON output.
   */
  async runJson<T>(args: string[], opts?: RunOptions): Promise<T | null> {
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
  spawn(args: string[], opts?: SpawnOptions): ChildProcess {
    const env = {
      ...process.env,
      ...this.envVars,
      ...opts?.env,
      CONTEXTPACK_ROOT: this.workspaceRoot,
    };

    let command: string;
    let cmdArgs: string[];

    if (this.useVenvPython) {
      command = this.venvPython;
      cmdArgs = ['-m', 'contextpack.cli.main', ...args];
      log(`Spawning: ${command} ${cmdArgs.join(' ')}`);
    } else {
      command = this.uvPath;
      cmdArgs = ['run', '--extra', 'harness', 'context', ...args];
      log(`Spawning: ${command} ${cmdArgs.join(' ')}`);
    }

    return spawn(command, cmdArgs, {
      cwd: opts?.cwd || this.workspaceRoot,
      env,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
  }

  /**
   * Spawn MCP server process.
   */
  spawnMcpServer(opts?: SpawnOptions): ChildProcess {
    const env = {
      ...process.env,
      ...this.envVars,
      ...opts?.env,
      CONTEXTPACK_ROOT: this.workspaceRoot,
    };

    let command: string;
    let cmdArgs: string[];

    if (this.useVenvPython) {
      command = this.venvPython;
      cmdArgs = ['-m', 'contextpack.mcp.server'];
      log(`Spawning MCP server: ${command} ${cmdArgs.join(' ')}`);
    } else {
      command = this.uvPath;
      cmdArgs = ['run', '--extra', 'harness', 'context-harness-mcp'];
      log(`Spawning MCP server: ${command} ${cmdArgs.join(' ')}`);
    }

    return spawn(command, cmdArgs, {
      cwd: opts?.cwd || this.workspaceRoot,
      env,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
  }
}

/**
 * Create a ContextRunner instance.
 */
export function createRunner(
  uvPath: string,
  workspaceRoot: string,
  envVars: Record<string, string> = {},
): ContextRunner {
  return new ContextRunner(uvPath, workspaceRoot, envVars);
}
