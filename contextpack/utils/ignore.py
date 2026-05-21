"""Default ignore patterns for repository scanning."""

IGNORE_DIRS = {
    "node_modules",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".git",
    "__pycache__",
    ".contextpack",
    "chroma",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "site-packages",
    "egg-info",
}

IGNORE_FILES = {".DS_Store"}

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
    return any(part in IGNORE_DIRS for part in path_parts)
