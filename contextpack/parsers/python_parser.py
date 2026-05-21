"""Python parser — tree-sitter with ast fallback."""

from __future__ import annotations

import ast

from contextpack.core.models import EntityType, ParsedEntity

try:
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser as TSParser
except ImportError:
    tspython = None  # type: ignore[assignment]
    TSParser = None  # type: ignore[assignment,misc]


class PythonParser:
    language = "python"

    def __init__(self) -> None:
        self._ts: TSParser | None = None
        if tspython and TSParser:
            lang = Language(tspython.language())
            self._ts = TSParser(lang)

    def parse_file(self, path: str, content: str) -> list[ParsedEntity]:
        if self._ts:
            try:
                return self._parse_tree_sitter(path, content)
            except Exception:
                pass
        return self._parse_ast(path, content)

    def _parse_tree_sitter(self, path: str, content: str) -> list[ParsedEntity]:
        assert self._ts is not None
        tree = self._ts.parse(content.encode("utf-8"))
        entities: list[ParsedEntity] = []
        imports: list[str] = []

        def walk(node):
            if node.type == "import_statement" or node.type == "import_from_statement":
                imports.append(content[node.start_byte : node.end_byte].strip())
            elif node.type == "class_definition":
                name = _child_identifier(node, content)
                entities.append(
                    ParsedEntity(
                        type=EntityType.CLASS,
                        name=name or "AnonymousClass",
                        file_path=path,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        imports=list(imports),
                        dependencies=[],
                    )
                )
            elif node.type == "function_definition":
                name = _child_identifier(node, content)
                parent = node.parent
                etype = EntityType.METHOD if parent and parent.type == "class_definition" else EntityType.FUNCTION
                entities.append(
                    ParsedEntity(
                        type=etype,
                        name=name or "anonymous",
                        file_path=path,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        imports=list(imports),
                    )
                )
            for child in node.children:
                walk(child)

        walk(tree.root_node)
        return entities

    def _parse_ast(self, path: str, content: str) -> list[ParsedEntity]:
        entities: list[ParsedEntity] = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return entities

        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.get_source_segment(content, node) or "")
            elif isinstance(node, ast.ClassDef):
                entities.append(
                    ParsedEntity(
                        type=EntityType.CLASS,
                        name=node.name,
                        file_path=path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        docstring=ast.get_docstring(node) or "",
                        imports=imports.copy(),
                    )
                )
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                entities.append(
                    ParsedEntity(
                        type=EntityType.FUNCTION,
                        name=node.name,
                        file_path=path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        docstring=ast.get_docstring(node) or "",
                        imports=imports.copy(),
                    )
                )
        return entities


def _child_identifier(node, content: str) -> str:
    for child in node.children:
        if child.type == "identifier":
            return content[child.start_byte : child.end_byte]
    return ""
