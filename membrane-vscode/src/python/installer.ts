import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { execSync } from 'child_process';
import { getVenvPath } from './detector';
import { log } from '../utils/output';

/**
 * Install contextpack wheel into ~/.membrane/venv/
 * Falls back to pip install from PyPI if wheel not bundled
 */
export async function installContextpack(
  uvPath: string,
  extensionPath: string,
  workspaceRoot: string,
  progress?: vscode.Progress<{ message?: string; increment?: number }>,
): Promise<boolean> {
  const venv = getVenvPath();
  const pythonPath = getPythonPath(venv);
  const localSourcePath = getLocalSourcePath(workspaceRoot);

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
    if (!fs.existsSync(pythonPath)) {
      progress?.report({ message: 'Creating venv...' });
      log(`Creating venv at ${venv}`);

      // Create venv on first install.
      execSync(`"${uvPath}" venv "${venv}"`, { stdio: 'pipe', encoding: 'utf-8' });
      log('venv created successfully');
    } else {
      log(`Reusing existing venv at ${venv}`);
    }

    progress?.report({ message: 'Installing contextpack...', increment: 50 });

    let installCmd = '';
    if (localSourcePath) {
      log(`Installing contextpack from local workspace source: ${localSourcePath}`);
      installCmd = `"${uvPath}" pip install --python "${pythonPath}" "${localSourcePath}[harness]" -v`;
    } else if (actualWheelPath) {
      log(`Installing contextpack from bundled wheel: ${actualWheelPath}`);
      installCmd = `"${uvPath}" pip install --python "${pythonPath}" "${actualWheelPath}[harness]" -v`;
    } else {
      log('No bundled wheel found, installing from PyPI...');
      installCmd = `"${uvPath}" pip install --python "${pythonPath}" "contextpack[harness]" -v`;
    }

    const output = execSync(installCmd, { encoding: 'utf-8', stdio: 'pipe' });
    log(`install output: ${output}`);

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
      `Membrane installation failed.\n\nError: ${errorMsg}\n\nTry manually installing:\n${uvPath} pip install --python ${pythonPath} contextpack[harness]`,
    );
    return false;
  }
}

function getLocalSourcePath(workspaceRoot: string): string | null {
  const pyprojectPath = path.join(workspaceRoot, 'pyproject.toml');
  const packageInitPath = path.join(workspaceRoot, 'contextpack', '__init__.py');

  if (!fs.existsSync(pyprojectPath) || !fs.existsSync(packageInitPath)) {
    return null;
  }

  try {
    const pyproject = fs.readFileSync(pyprojectPath, 'utf-8');
    if (pyproject.includes('name = "contextpack"')) {
      return workspaceRoot;
    }
  } catch {
    return null;
  }

  return null;
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
  if (!fs.existsSync(pythonPath)) {
    return false;
  }

  try {
    execSync(`"${pythonPath}" -c "import contextpack"`, {
      stdio: 'pipe',
      encoding: 'utf-8',
      timeout: 5000,
    });
    return true;
  } catch {
    return false;
  }
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
