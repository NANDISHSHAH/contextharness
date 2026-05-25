import { ChildProcess } from 'child_process';
import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';
import { configureMcpServer, writeMcpConfig } from './mcpConfig';
import { log } from '../utils/output';
import { SETTINGS } from '../constants';

export type McpServerStatus = 'stopped' | 'starting' | 'running' | 'stopping';

export class McpServerManager {
  private process: ChildProcess | null = null;
  private status: McpServerStatus = 'stopped';
  private restartAttempts = 0;
  private maxRestartAttempts = 3;
  private onStatusChange: vscode.EventEmitter<McpServerStatus>;

  constructor(
    private workspaceRoot: string,
    private runner: ContextRunner,
    private uvPath: string,
  ) {
    this.onStatusChange = new vscode.EventEmitter<McpServerStatus>();
  }

  get statusEvent() {
    return this.onStatusChange.event;
  }

  getStatus(): McpServerStatus {
    return this.status;
  }

  /**
   * Start the MCP server.
   */
  async start(): Promise<boolean> {
    if (this.status === 'running' || this.status === 'starting') {
      log('MCP server already running or starting');
      return true;
    }

    // Configure .mcp.json first
    const autoConfig = vscode.workspace.getConfiguration().get(SETTINGS.autoMcpConfigure);
    if (autoConfig) {
      const config = configureMcpServer(this.workspaceRoot, this.uvPath);
      writeMcpConfig(config, this.workspaceRoot);
    }

    return this._start();
  }

  private async _start(): Promise<boolean> {
    try {
      this.setStatus('starting');
      log('Starting MCP server');

      this.process = this.runner.spawnMcpServer();

      this.process.stdout?.on('data', (data) => {
        const text = data.toString().trim();
        if (text) {
          log(`MCP stdout: ${text}`);
        }
      });

      this.process.stderr?.on('data', (data) => {
        const text = data.toString().trim();
        if (text) {
          log(`MCP stderr: ${text}`);
        }
      });

      this.process.on('exit', (code) => {
        log(`MCP server exited with code ${code}`);
        this.process = null;

        if (this.status !== 'stopping') {
          // Unexpected exit, try to restart
          this._handleUnexpectedExit();
        } else {
          this.setStatus('stopped');
        }
      });

      this.process.on('error', (error) => {
        log(`MCP server error: ${error.message}`);
        this._handleUnexpectedExit();
      });

      // Give it a moment to start
      await new Promise((resolve) => setTimeout(resolve, 1000));

      this.restartAttempts = 0;
      this.setStatus('running');
      return true;
    } catch (error: any) {
      log(`Failed to start MCP server: ${error.message}`);
      this.setStatus('stopped');
      return false;
    }
  }

  /**
   * Stop the MCP server.
   */
  async stop(): Promise<boolean> {
    if (this.status === 'stopped') {
      return true;
    }

    this.setStatus('stopping');
    log('Stopping MCP server');

    if (this.process) {
      try {
        this.process.kill();
        await new Promise((resolve) => setTimeout(resolve, 500));
      } catch (error: any) {
        log(`Error stopping MCP server: ${error.message}`);
      }
    }

    this.process = null;
    this.setStatus('stopped');
    return true;
  }

  /**
   * Restart the MCP server.
   */
  async restart(): Promise<boolean> {
    await this.stop();
    await new Promise((resolve) => setTimeout(resolve, 500));
    return this._start();
  }

  /**
   * Handle unexpected exit with exponential backoff retry.
   */
  private async _handleUnexpectedExit(): Promise<void> {
    if (this.restartAttempts >= this.maxRestartAttempts) {
      log('MCP server restart attempts exceeded');
      this.setStatus('stopped');
      vscode.window.showErrorMessage(
        'Membrane MCP server stopped unexpectedly. Check output for details.',
      );
      return;
    }

    const delay = Math.pow(2, this.restartAttempts) * 1000;
    this.restartAttempts++;

    log(`Restarting MCP server in ${delay}ms (attempt ${this.restartAttempts})`);
    await new Promise((resolve) => setTimeout(resolve, delay));

    await this._start();
  }

  private setStatus(status: McpServerStatus): void {
    this.status = status;
    log(`MCP server status: ${status}`);
    this.onStatusChange.fire(status);
  }

  dispose(): void {
    this.onStatusChange.dispose();
    if (this.process) {
      this.process.kill();
    }
  }
}
