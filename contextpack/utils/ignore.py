"""Default ignore patterns for repository scanning."""

from __future__ import annotations

import fnmatch
from pathlib import Path

IGNORE_DIRS = {
    # Python
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "site-packages",
    "egg-info",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    # JS/TS
    "node_modules",
    ".next",
    ".nuxt",
    ".svelte-kit",
    ".turbo",
    ".parcel-cache",
    "storybook-static",
    ".angular",
    # Build outputs
    "dist",
    "build",
    "out",
    "target",
    "coverage",
    ".coverage",
    "tmp",
    ".tmp",
    ".cache",
    # Vendored / generated
    "vendor",
    "generated",
    "auto-generated",
    # VCS / tooling
    ".git",
    ".contextpack",
    "chroma",
}

# Files to skip by suffix or exact name — these are generated/binary/lock files
# with no semantic value for code intelligence
IGNORE_FILE_SUFFIXES = {
    ".min.js",
    ".min.css",
    ".d.ts",    # TypeScript declarations — generated from .ts source
    ".map",     # source maps
    ".pb.go",   # protobuf generated (Go)
    "_pb2.py",  # protobuf generated (Python)
}

IGNORE_FILE_NAMES = {
    ".DS_Store",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Pipfile.lock",
    "poetry.lock",
    "composer.lock",
    "Gemfile.lock",
}

LANGUAGE_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
}


def should_ignore(path_parts: tuple[str, ...]) -> bool:
    """Return True if any directory component is in the ignore list."""
    return any(part in IGNORE_DIRS for part in path_parts)


def should_ignore_file(name: str) -> bool:
    """Return True if the file should be skipped based on name/suffix heuristics."""
    if name in IGNORE_FILE_NAMES:
        return True
    # Check multi-part suffixes like .min.js, .d.ts, _pb2.py
    lower = name.lower()
    return any(lower.endswith(suf) for suf in IGNORE_FILE_SUFFIXES)


def load_gitignore_patterns(root: Path) -> list[str]:
    """Read .gitignore and .contextpackignore from root, return non-empty non-comment lines."""
    patterns: list[str] = []
    for fname in (".gitignore", ".contextpackignore"):
        p = root / fname
        if not p.is_file():
            continue
        try:
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
        except OSError:
            pass
    return patterns


def matches_gitignore(rel_path: str, patterns: list[str]) -> bool:
    """Return True if rel_path matches any gitignore-style pattern."""
    # Normalise to forward slashes
    rel = rel_path.replace("\\", "/")
    name = rel.split("/")[-1]
    for pat in patterns:
        # Patterns with / are path-relative; without / match the filename only
        if "/" in pat.lstrip("/"):
            if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat.lstrip("/")):
                return True
        else:
            if fnmatch.fnmatch(name, pat):
                return True
            # Also match as a directory prefix
            if fnmatch.fnmatch(rel.split("/")[0], pat):
                return True
    return False
