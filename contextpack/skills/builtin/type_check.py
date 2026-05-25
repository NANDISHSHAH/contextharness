"""Built-in type check skill — mypy."""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

from contextpack.skills.composer import SkillResult


class TypeCheckSkill:
    name = "type_check"
    dependencies: list[str] = ["lint"]

    async def run(self, repo_path: Path) -> SkillResult:
        t0 = time.perf_counter()
        try:
            proc = await asyncio.create_subprocess_exec(
                "mypy",
                ".",
                "--ignore-missing-imports",
                "--no-error-summary",
                "--pretty",
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            elapsed = (time.perf_counter() - t0) * 1000
            output = (stdout.decode(errors="replace") + stderr.decode(errors="replace")).strip()
            findings = [l for l in output.splitlines() if "error:" in l.lower()][:10]
            return SkillResult(
                skill=self.name,
                passed=proc.returncode == 0,
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
                output="mypy not found — skipped. Install: pip install mypy",
                findings=["⚠ mypy not available"],
            )
        except asyncio.TimeoutError:
            elapsed = (time.perf_counter() - t0) * 1000
            return SkillResult(
                skill=self.name,
                passed=False,
                duration_ms=elapsed,
                output="mypy timed out (>120 s)",
            )
