"""Repository scanner."""

from __future__ import annotations

from pathlib import Path

from contextpack.core.models import FileRecord, ProjectMap
from contextpack.utils.ignore import LANGUAGE_EXTENSIONS, should_ignore


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

    def scan(self) -> ProjectMap:
        files: list[FileRecord] = []
        languages: dict[str, int] = {}
        framework_hints: set[str] = set()

        for path in self._walk_files():
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
        )

    def _walk_files(self):
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            rel_parts = path.relative_to(self.root).parts
            if should_ignore(rel_parts):
                continue
            if path.name in {".DS_Store"}:
                continue
            if path.suffix.lower() in LANGUAGE_EXTENSIONS or path.suffix in {".md", ".yaml", ".yml"}:
                yield path


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
