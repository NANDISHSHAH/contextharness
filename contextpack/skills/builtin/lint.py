"""Built-in lint skill — ruff (primary), flake8 (fallback)."""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

from contextpack.skills.composer import SkillResult


class LintSkill:
    name = "lint"
    dependencies: list[str] = []

    async def run(self, repo_path: Path) -> SkillResult:
        t0 = time.perf_counter()

        # Try ruff first (fast, modern)
        ret = await _cmd(["ruff", "check", "--output-format=concise", "."], repo_path)
        if ret is not None:
            code, out, err = ret
            elapsed = (time.perf_counter() - t0) * 1000
            output = (out + err).strip()
            findings = [l for l in output.splitlines() if l.strip() and ("error" in l.lower() or "E" in l)][:10]
            return SkillResult(
                skill=self.name,
                passed=code == 0,
                duration_ms=elapsed,
                output=output[:2000],
                findings=findings,
            )

        # Try flake8
        ret = await _cmd(["flake8", "--max-line-length=120", "."], repo_path)
        if ret is not None:
            code, out, err = ret
            elapsed = (time.perf_counter() - t0) * 1000
            output = (out + err).strip()
            findings = output.splitlines()[:10]
            return SkillResult(
                skill=self.name,
                passed=code == 0,
                duration_ms=elapsed,
                output=output[:2000],
                findings=findings,
            )

        elapsed = (time.perf_counter() - t0) * 1000
        return SkillResult(
            skill=self.name,
            passed=True,          # degrade gracefully — don't block the gate
            duration_ms=elapsed,
            output=(
                "⚠ No linter found in PATH (tried ruff, flake8).\n"
                "Install ruff so skill gates can enforce lint:\n"
                "  uv sync --extra harness   # adds ruff to the harness extra\n"
                "  # or: pip install ruff"
            ),
            findings=["⚠ No linter found — run: uv sync --extra harness"],
        )


async def _cmd(
    cmd: list[str], cwd: Path, timeout: int = 60
) -> tuple[int, str, str] | None:
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return (
            proc.returncode or 0,
            stdout.decode(errors="replace"),
            stderr.decode(errors="replace"),
        )
    except FileNotFoundError:
        return None
    except asyncio.TimeoutError:
        return None
