"""Parser registry and tree-sitter helpers."""

from __future__ import annotations

from contextpack.core.models import ParsedEntity
from contextpack.core.protocols import Parser

_PARSERS: dict[str, Parser] | None = None


def _load_parsers() -> dict[str, Parser]:
    global _PARSERS
    if _PARSERS is not None:
        return _PARSERS
    from contextpack.parsers.js_parser import JSParser
    from contextpack.parsers.python_parser import PythonParser
    from contextpack.parsers.ts_parser import TypeScriptParser

    _PARSERS = {
        "python": PythonParser(),
        "typescript": TypeScriptParser(),
        "javascript": JSParser(),
    }
    return _PARSERS


def get_parser_for_language(language: str) -> Parser | None:
    return _load_parsers().get(language)


def parse_project_files(root: str, files: list[tuple[str, str, str]]) -> list[ParsedEntity]:
    """Parse (rel_path, language, content) tuples."""
    entities: list[ParsedEntity] = []
    for rel_path, language, content in files:
        parser = get_parser_for_language(language)
        if not parser:
            continue
        for ent in parser.parse_file(rel_path, content):
            ent.file_path = rel_path
            ent.language = language
            entities.append(ent)
    return entities
