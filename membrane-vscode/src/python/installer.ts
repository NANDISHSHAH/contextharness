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

  // Find bundled wheel — prefer platform-specific, fall back to any .whl
  const wheelsDir = path.join(extensionPath, 'resources', 'wheels');
  let actualWheelPath: string | null = null;

  if (fs.existsSync(wheelsDir)) {
    const files = fs.readdirSync(wheelsDir).filter(f => f.endsWith('.whl'));
    const arch = process.arch === 'arm64' ? 'arm64' : 'x86_64';
    const platformTag = process.platform === 'darwin' ? `macosx.*${arch}` : process.platform === 'win32' ? 'win' : 'linux';
    const platformMatch = files.find(f => new RegExp(platformTag).test(f));
    const wheelFile = platformMatch ?? files[0]; // fall back to first wheel
    if (wheelFile) {
      actualWheelPath = path.join(wheelsDir, wheelFile);
      log(`Found bundled wheel: ${wheelFile}`);
    }
  }

  const venvCreated = !fs.existsSync(pythonPath);

  try {
    if (venvCreated) {
      progress?.report({ message: 'Creating venv...' });
      log(`Creating venv at ${venv}`);
      execSync(`"${uvPath}" venv "${venv}"`, { stdio: 'pipe', encoding: 'utf-8' });
      log('venv created');
    } else {
      log(`Reusing existing venv at ${venv}`);
    }

    progress?.report({ message: 'Installing contextpack...', increment: 50 });

    let installCmd: string;
    if (localSourcePath) {
      log(`Installing from local workspace source: ${localSourcePath}`);
      installCmd = `"${uvPath}" pip install --python "${pythonPath}" "${localSourcePath}[harness]" -v`;
    } else if (actualWheelPath) {
      log(`Installing from bundled wheel: ${actualWheelPath}`);
      installCmd = `"${uvPath}" pip install --python "${pythonPath}" "${actualWheelPath}[harness]" -v`;
    } else {
      log('No bundled wheel — installing from PyPI...');
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
    log(`Installation failed: ${errorMsg}`);

    // Roll back the venv only if we created it in this call
    if (venvCreated && fs.existsSync(venv)) {
      try {
        fs.rmSync(venv, { recursive: true, force: true });
        log('Rolled back partial venv after install failure');
      } catch {
        log('Warning: could not roll back venv');
      }
    }

    vscode.window.showErrorMessage(
      `Membrane: installation failed — ${errorMsg.slice(0, 120)}`,
      'View Logs',
    ).then(action => {
      if (action === 'View Logs') {
        vscode.commands.executeCommand('workbench.action.output.toggleOutput');
      }
    });
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
