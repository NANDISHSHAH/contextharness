"""JavaScript parser — reuses TS tree-sitter grammar where possible."""

from __future__ import annotations

from contextpack.core.models import ParsedEntity
from contextpack.parsers.ts_parser import TypeScriptParser, _extract_routes

try:
    import tree_sitter_javascript as tsjs
    from tree_sitter import Language
    from tree_sitter import Parser as TSParserCore
except ImportError:
    tsjs = None  # type: ignore[assignment]
    TSParserCore = None  # type: ignore[assignment,misc]


class JSParser:
    language = "javascript"

    def __init__(self) -> None:
        self._ts: TSParserCore | None = None
        if tsjs and TSParserCore:
            lang = Language(tsjs.language())
            self._ts = TSParserCore(lang)
        self._fallback = TypeScriptParser()

    def parse_file(self, path: str, content: str) -> list[ParsedEntity]:
        if self._ts:
            return self._fallback._parse_ts(path, content) + _extract_routes(path, content)  # noqa: SLF001
        return self._fallback.parse_file(path, content)
