"""Built-in security scan — bandit."""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

from contextpack.skills.composer import SkillResult


class SecurityScanSkill:
    name = "security_scan"
    dependencies: list[str] = ["type_check"]

    async def run(self, repo_path: Path) -> SkillResult:
        t0 = time.perf_counter()
        try:
            proc = await asyncio.create_subprocess_exec(
                "bandit",
                "-r",
                ".",
                "-ll",           # medium + high severity only
                "--format", "txt",
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            elapsed = (time.perf_counter() - t0) * 1000
            output = (stdout.decode(errors="replace") + stderr.decode(errors="replace")).strip()
            # bandit returns 1 when issues found at >= configured severity
            passed = proc.returncode == 0
            findings = [
                l for l in output.splitlines()
                if l.strip() and any(kw in l for kw in ("Issue", "Severity", "CWE"))
            ][:10]
            return SkillResult(
                skill=self.name,
                passed=passed,
                duration_ms=elapsed,
                output=output[:3000],
                findings=findings,
            )
        except FileNotFoundError:
            elapsed = (time.perf_counter() - t0) * 1000
            return SkillResult(
                skill=self.name,
                passed=True,
                duration_ms=elapsed,
                output="bandit not found — skipped. Install: pip install bandit",
                findings=["⚠ bandit not available"],
            )
        except TimeoutError:
            elapsed = (time.perf_counter() - t0) * 1000
            return SkillResult(
                skill=self.name,
                passed=False,
                duration_ms=elapsed,
                output="bandit timed out (>120 s)",
            )
