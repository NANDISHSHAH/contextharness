import * as vscode from 'vscode';
import * as path from 'path';

export function getWorkspaceRoot(): string | null {
  const folder = vscode.workspace.workspaceFolders?.[0];
  if (!folder) {
    return null;
  }
  return folder.uri.fsPath;
}

export function getContextpackDir(): string | null {
  const root = getWorkspaceRoot();
  if (!root) {
    return null;
  }
  return path.join(root, '.contextpack');
}

export function getConfigPath(): string | null {
  const dir = getContextpackDir();
  if (!dir) {
    return null;
  }
  return path.join(dir, 'config.json');
}

export function getProjectMapPath(): string | null {
  const dir = getContextpackDir();
  if (!dir) {
    return null;
  }
  return path.join(dir, 'project_map.json');
}

export function getMcpJsonPath(): string | null {
  const root = getWorkspaceRoot();
  if (!root) {
    return null;
  }
  return path.join(root, '.mcp.json');
}

export function isWorkspaceOpen(): boolean {
  return getWorkspaceRoot() !== null;
}

export function isContextpackInitialized(): boolean {
  const configPath = getConfigPath();
  if (!configPath) {
    return false;
  }
  try {
    const fs = require('fs');
    return fs.existsSync(configPath);
  } catch {
    return false;
  }
}
