import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import { execSync } from 'child_process';
import { log } from '../utils/output';

/**
 * Detect uv executable path.
 * Priority: bundled → system PATH → fallback locations
 */
export function detectUvPath(extensionPath: string): string | null {
  // Try bundled uv first
  const bundledUv = getBundledUvPath(extensionPath);
  if (fs.existsSync(bundledUv)) {
    log(`Found bundled uv at: ${bundledUv}`);
    return bundledUv;
  }

  // Try system PATH
  try {
    const systemUv = execSync('which uv 2>/dev/null || where uv', {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'ignore'],
    })
      .trim();
    if (systemUv) {
      log(`Found system uv at: ${systemUv}`);
      return systemUv;
    }
  } catch {
    // Command failed, continue to other methods
  }

  // Try common installation paths
  const commonPaths = [
    path.join(os.homedir(), '.cargo', 'bin', 'uv'),
    path.join(os.homedir(), '.local', 'bin', 'uv'),
    path.join(os.homedir(), 'AppData', 'Local', 'uv', 'bin', 'uv.exe'),
  ];

  for (const uvPath of commonPaths) {
    if (fs.existsSync(uvPath)) {
      log(`Found uv at: ${uvPath}`);
      return uvPath;
    }
  }

  log('uv executable not found');
  return null;
}

/**
 * Get path to bundled uv binary for the current platform.
 */
function getBundledUvPath(extensionPath: string): string {
  const platform = `${process.platform}-${process.arch}`;
  let name = 'uv';

  if (process.platform === 'win32') {
    name = 'uv-win32-x64.exe';
  } else if (process.platform === 'darwin') {
    if (process.arch === 'arm64') {
      name = 'uv-darwin-arm64';
    } else {
      name = 'uv-darwin-x64';
    }
  } else {
    // Linux
    name = 'uv-linux-x64';
  }

  return path.join(extensionPath, 'resources', name);
}

/**
 * Verify that contextpack is installed and accessible.
 */
export async function verifyContextpack(
  uvPath: string,
): Promise<{ ok: boolean; version?: string; error?: string }> {
  try {
    const { execSync: execSyncImport } = require('child_process');
    const venv = getVenvPath();
    const pythonPath = getVenvPythonPath();

    // Try venv Python first (most reliable)
    if (require('fs').existsSync(pythonPath)) {
      try {
        const output = execSyncImport(`"${pythonPath}" -m contextpack.cli.main --version 2>/dev/null || "${pythonPath}" -c "import contextpack; print(contextpack.__version__)"`, {
          encoding: 'utf-8',
          stdio: ['pipe', 'pipe', 'pipe'],
          timeout: 10000,
          shell: true,
        }).trim();

        log(`contextpack version (from venv): ${output}`);
        return { ok: true, version: output };
      } catch (venvError) {
        log(`Venv verification failed, trying uv run...`);
      }
    }

    // Fall back to uv run (less reliable if not in a project)
    try {
      const output = execSyncImport(`"${uvPath}" run --extra harness context --version`, {
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: 10000,
        cwd: require('os').homedir(), // Run from home directory
      }).trim();

      log(`contextpack version (from uv): ${output}`);
      return { ok: true, version: output };
    } catch (uvError) {
      log(`uv run verification also failed`);
      return { ok: false, error: 'Could not verify contextpack - but installation may have succeeded' };
    }
  } catch (error: any) {
    const errorMsg = error.message || String(error);
    log(`contextpack verification failed: ${errorMsg}`);
    return { ok: false, error: errorMsg };
  }
}

/**
 * Get path to venv where contextpack should be installed.
 */
export function getVenvPath(): string {
  return path.join(os.homedir(), '.membrane', 'venv');
}

/**
 * Get Python executable path within venv.
 */
export function getVenvPythonPath(): string {
  const venv = getVenvPath();
  if (process.platform === 'win32') {
    return path.join(venv, 'Scripts', 'python.exe');
  } else {
    return path.join(venv, 'bin', 'python');
  }
}
