"""Repository scanner."""

from __future__ import annotations

from pathlib import Path

from contextpack.core.models import FileRecord, ProjectMap
from contextpack.utils.ignore import (
    LANGUAGE_EXTENSIONS,
    load_gitignore_patterns,
    matches_gitignore,
    should_ignore,
    should_ignore_file,
)


FRAMEWORK_MARKERS: dict[str, list[str]] = {
    "fastapi": ["from fastapi", "FastAPI("],
    "django": ["from django", "django."],
    "flask": ["from flask", "Flask("],
    "express": ["express()", "require('express')"],
    "react": ["from 'react'", 'from "react"'],
    "next": ["next/", "from 'next'"],
}


class RepositoryScanner:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self._gitignore_patterns = load_gitignore_patterns(self.root)

    def scan(self) -> ProjectMap:
        files: list[FileRecord] = []
        languages: dict[str, int] = {}
        framework_hints: set[str] = set()
        files_skipped = 0

        for path, skipped in self._walk_files():
            if skipped:
                files_skipped += 1
                continue
            rel = str(path.relative_to(self.root))
            ext = path.suffix.lower()
            lang = LANGUAGE_EXTENSIONS.get(ext, "")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
            hints = _detect_frameworks(path) if path.stat().st_size < 200_000 else []
            framework_hints.update(hints)
            files.append(
                FileRecord(
                    path=rel,
                    language=lang,
                    size_bytes=path.stat().st_size,
                    framework_hints=hints,
                )
            )

        return ProjectMap(
            root=str(self.root),
            files=files,
            languages=languages,
            frameworks=sorted(framework_hints),
            files_skipped=files_skipped,
        )

    def _walk_files(self):
        """Yield (path, skipped: bool). skipped=True means the file was filtered out."""
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            rel_path = path.relative_to(self.root)
            rel_parts = rel_path.parts

            # Directory-level ignore
            if should_ignore(rel_parts):
                yield path, True
                continue

            # File-level ignore (generated, lock files, etc.)
            if should_ignore_file(path.name):
                yield path, True
                continue

            # .gitignore / .contextpackignore patterns
            if self._gitignore_patterns and matches_gitignore(
                str(rel_path), self._gitignore_patterns
            ):
                yield path, True
                continue

            # Only yield code + doc files
            if path.suffix.lower() in LANGUAGE_EXTENSIONS or path.suffix in {".md", ".yaml", ".yml"}:
                yield path, False


def _detect_frameworks(path: Path) -> list[str]:
    found: list[str] = []
    try:
        sample = path.read_text(encoding="utf-8", errors="replace")[:8000]
    except OSError:
        return found
    for name, markers in FRAMEWORK_MARKERS.items():
        if any(m in sample for m in markers):
            found.append(name)
    return found
