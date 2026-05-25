import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import { execSync, spawn } from 'child_process';
import { getVenvPath } from './detector';
import { log } from '../utils/output';

/**
 * Install contextpack wheel into ~/.membrane/venv/
 * Falls back to pip install from PyPI if wheel not bundled
 */
export async function installContextpack(
  uvPath: string,
  extensionPath: string,
  progress?: vscode.Progress<{ message?: string; increment?: number }>,
): Promise<boolean> {
  const venv = getVenvPath();
  const pythonPath = getPythonPath(venv);

  // Find bundled wheel (optional)
  const wheelsDir = path.join(extensionPath, 'resources', 'wheels');
  let actualWheelPath: string | null = null;

  if (fs.existsSync(wheelsDir)) {
    const files = fs.readdirSync(wheelsDir);
    const wheelFile = files.find(f => f.endsWith('.whl'));
    if (wheelFile) {
      actualWheelPath = path.join(wheelsDir, wheelFile);
    }
  }

  try {
    progress?.report({ message: 'Creating venv...' });
    log(`Creating venv at ${venv}`);

    // Create venv
    execSync(`"${uvPath}" venv "${venv}"`, { stdio: 'pipe', encoding: 'utf-8' });
    log('venv created successfully');

    progress?.report({ message: 'Installing contextpack...', increment: 50 });

    let installCmd = '';
    if (actualWheelPath) {
      log(`Installing contextpack from bundled wheel: ${actualWheelPath}`);
      installCmd = `"${pythonPath}" -m pip install "${actualWheelPath}[harness]" -v`;
    } else {
      log('No bundled wheel found, installing from PyPI...');
      installCmd = `"${pythonPath}" -m pip install contextpack[harness] -v`;
    }

    const output = execSync(installCmd, { encoding: 'utf-8', stdio: 'pipe' });
    log(`pip output: ${output}`);

    // Verify installation
    progress?.report({ message: 'Verifying installation...', increment: 25 });
    log('Verifying contextpack installation...');

    const verifyOutput = execSync(`"${pythonPath}" -c "import contextpack; print('contextpack version:', contextpack.__version__)"`, {
      encoding: 'utf-8',
      stdio: 'pipe',
    });
    log(`Verification: ${verifyOutput}`);

    progress?.report({ message: 'Installation complete', increment: 25 });
    log('✓ contextpack installed and verified successfully');
    return true;
  } catch (error: any) {
    const errorMsg = error.stdout || error.stderr || error.message || String(error);
    log(`❌ Installation failed: ${errorMsg}`);
    vscode.window.showErrorMessage(
      `Membrane installation failed.\n\nError: ${errorMsg}\n\nTry manually installing:\n${pythonPath} -m pip install contextpack[harness]`,
    );
    return false;
  }
}

/**
 * Get Python executable path for a venv.
 */
function getPythonPath(venvPath: string): string {
  if (process.platform === 'win32') {
    return path.join(venvPath, 'Scripts', 'python.exe');
  } else {
    return path.join(venvPath, 'bin', 'python');
  }
}

/**
 * Check if contextpack is already installed.
 */
export function isContextpackInstalled(): boolean {
  const venv = getVenvPath();
  const pythonPath = getPythonPath(venv);
  return fs.existsSync(pythonPath);
}

/**
 * Uninstall contextpack from venv (cleanup).
 */
export async function uninstallContextpack(): Promise<boolean> {
  try {
    const venv = getVenvPath();
    if (fs.existsSync(venv)) {
      log(`Removing venv at ${venv}`);
      fs.rmSync(venv, { recursive: true, force: true });
      return true;
    }
    return false;
  } catch (error: any) {
    log(`Failed to uninstall: ${error.message}`);
    return false;
  }
}
