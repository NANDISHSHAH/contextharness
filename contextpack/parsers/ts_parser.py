"""TypeScript parser via tree-sitter."""

from __future__ import annotations

import re

from contextpack.core.models import EntityType, ParsedEntity

try:
    import tree_sitter_typescript as tsts
    from tree_sitter import Language
    from tree_sitter import Parser as TSParser
except ImportError:
    tsts = None  # type: ignore[assignment]
    TSParser = None  # type: ignore[assignment,misc]

ROUTE_PATTERNS = [
    re.compile(r"\.(?:get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"@(?:Get|Post|Put|Delete|Patch)\s*\(\s*['\"]([^'\"]+)['\"]"),
]


class TypeScriptParser:
    language = "typescript"

    def __init__(self) -> None:
        self._ts: TSParser | None = None
        if tsts and TSParser:
            lang = Language(tsts.language_typescript())
            self._ts = TSParser(lang)  # tree_sitter.Parser

    def parse_file(self, path: str, content: str) -> list[ParsedEntity]:
        entities: list[ParsedEntity] = []
        if self._ts:
            entities.extend(self._parse_ts(path, content))
        entities.extend(_extract_routes(path, content))
        return entities

    def _parse_ts(self, path: str, content: str) -> list[ParsedEntity]:
        assert self._ts is not None
        tree = self._ts.parse(content.encode("utf-8"))
        entities: list[ParsedEntity] = []
        imports: list[str] = []

        def walk(node):
            if node.type in ("import_statement", "import_declaration"):
                imports.append(content[node.start_byte : node.end_byte].strip()[:200])
            elif node.type in ("class_declaration", "class_definition"):
                name = _ts_name(node, content)
                entities.append(
                    ParsedEntity(
                        type=EntityType.CLASS,
                        name=name or "AnonymousClass",
                        file_path=path,
                        line_start=node.start_point[0] + 1,
                        imports=list(imports),
                    )
                )
            elif node.type in (
                "function_declaration",
                "method_definition",
                "arrow_function",
            ):
                if (
                    node.type == "arrow_function"
                    and node.parent
                    and node.parent.type != "variable_declarator"
                ):
                    return
                name = _ts_name(node, content) or _parent_var_name(
                    node, content
                )
                if name:
                    entities.append(
                        ParsedEntity(
                            type=EntityType.FUNCTION,
                            name=name,
                            file_path=path,
                            line_start=node.start_point[0] + 1,
                            imports=list(imports),
                        )
                    )
            for child in node.children:
                walk(child)

        walk(tree.root_node)
        return entities


def _ts_name(node, content: str) -> str:
    for child in node.children:
        if child.type in ("identifier", "property_identifier", "type_identifier"):
            return content[child.start_byte : child.end_byte]
    return ""


def _parent_var_name(node, content: str) -> str:
    parent = node.parent
    if parent and parent.type == "variable_declarator":
        for child in parent.children:
            if child.type == "identifier":
                return content[child.start_byte : child.end_byte]
    return ""


def _extract_routes(path: str, content: str) -> list[ParsedEntity]:
    routes: list[ParsedEntity] = []
    for pat in ROUTE_PATTERNS:
        for m in pat.finditer(content):
            routes.append(
                ParsedEntity(
                    type=EntityType.ROUTE,
                    name=m.group(1),
                    file_path=path,
                    summary=f"HTTP route {m.group(1)}",
                )
            )
    return routes
