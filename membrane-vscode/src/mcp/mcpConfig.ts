import * as fs from 'fs';
import * as path from 'path';
import { log } from '../utils/output';
import { MCP_SERVER_NAME, MCP_COMMAND } from '../constants';

export interface McpServerConfig {
  command: string;
  args: string[];
  env: Record<string, string>;
}

export interface McpConfig {
  mcpServers: Record<string, McpServerConfig>;
}

/**
 * Read .mcp.json from workspace root.
 */
export function readMcpConfig(workspaceRoot: string): McpConfig | null {
  const mcpPath = path.join(workspaceRoot, '.mcp.json');

  if (!fs.existsSync(mcpPath)) {
    return null;
  }

  try {
    const content = fs.readFileSync(mcpPath, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    log(`Failed to read .mcp.json: ${error}`);
    return null;
  }
}

/**
 * Write .mcp.json to workspace root.
 */
export function writeMcpConfig(config: McpConfig, workspaceRoot: string): boolean {
  const mcpPath = path.join(workspaceRoot, '.mcp.json');

  try {
    fs.writeFileSync(mcpPath, JSON.stringify(config, null, 2));
    log(`Wrote .mcp.json to ${mcpPath}`);
    return true;
  } catch (error) {
    log(`Failed to write .mcp.json: ${error}`);
    return false;
  }
}

/**
 * Configure MCP server in .mcp.json.
 * Merges context-harness server config with existing servers.
 */
export function configureMcpServer(
  workspaceRoot: string,
  uvPath: string,
): McpConfig {
  let config = readMcpConfig(workspaceRoot) || { mcpServers: {} };

  // Create or update context-harness server config
  config.mcpServers[MCP_SERVER_NAME] = {
    command: uvPath,
    args: ['run', '--extra', 'harness', MCP_COMMAND],
    env: {
      CONTEXTPACK_ROOT: workspaceRoot,
    },
  };

  return config;
}

/**
 * Get diff between old and new MCP config (for UI display).
 */
export function getMcpConfigDiff(
  oldConfig: McpConfig | null,
  newConfig: McpConfig,
): string {
  const oldServer = oldConfig?.mcpServers?.[MCP_SERVER_NAME];
  const newServer = newConfig.mcpServers[MCP_SERVER_NAME];

  if (!oldServer) {
    return `Will add context-harness server:
Command: ${newServer.command}
Args: ${newServer.args.join(' ')}
Root: ${newServer.env.CONTEXTPACK_ROOT}`;
  }

  const changes: string[] = [];

  if (oldServer.command !== newServer.command) {
    changes.push(`Command: ${oldServer.command} → ${newServer.command}`);
  }

  if (JSON.stringify(oldServer.args) !== JSON.stringify(newServer.args)) {
    changes.push(`Args: ${oldServer.args.join(' ')} → ${newServer.args.join(' ')}`);
  }

  if (oldServer.env.CONTEXTPACK_ROOT !== newServer.env.CONTEXTPACK_ROOT) {
    changes.push(`Root: ${oldServer.env.CONTEXTPACK_ROOT} → ${newServer.env.CONTEXTPACK_ROOT}`);
  }

  return changes.length > 0
    ? `Will update context-harness server:\n${changes.join('\n')}`
    : 'No changes to MCP config';
}

/**
 * Validate MCP config structure.
 */
export function validateMcpConfig(config: McpConfig): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!config.mcpServers) {
    errors.push('Missing mcpServers property');
  }

  const server = config.mcpServers?.[MCP_SERVER_NAME];
  if (!server) {
    errors.push(`Missing ${MCP_SERVER_NAME} server config`);
  } else {
    if (!server.command) {
      errors.push('Server command is empty');
    }
    if (!server.args || server.args.length === 0) {
      errors.push('Server args are empty');
    }
    if (!server.env?.CONTEXTPACK_ROOT) {
      errors.push('Server env CONTEXTPACK_ROOT is not set');
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
