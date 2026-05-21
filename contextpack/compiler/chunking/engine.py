"""Semantic chunking for embedding and retrieval."""

from __future__ import annotations

from contextpack.core.models import ParsedEntity, SemanticChunk
from contextpack.utils.tokens import estimate_tokens


class ChunkingEngine:
    def chunk_entities(self, entities: list[ParsedEntity]) -> list[SemanticChunk]:
        chunks: list[SemanticChunk] = []
        by_file: dict[str, list[ParsedEntity]] = {}
        for ent in entities:
            by_file.setdefault(ent.file_path, []).append(ent)

        for file_path, file_ents in by_file.items():
            module_names = [e.name for e in file_ents]
            summary = f"Module {file_path}: {', '.join(module_names[:12])}"
            mod_content = "\n".join(
                f"{e.type} {e.name}: {e.docstring or e.summary}" for e in file_ents[:30]
            )
            chunks.append(
                SemanticChunk(
                    type="module",
                    name=file_path,
                    file_path=file_path,
                    summary=summary,
                    content=mod_content,
                    dependencies=_collect_deps(file_ents),
                    token_estimate=estimate_tokens(mod_content),
                )
            )

        for ent in entities:
            text = ent.docstring or ent.summary or f"{ent.type} {ent.name} in {ent.file_path}"
            chunks.append(
                SemanticChunk(
                    type=str(ent.type),
                    name=ent.name,
                    file_path=ent.file_path,
                    summary=text[:500],
                    content=text,
                    dependencies=ent.dependencies + ent.imports[:8],
                    token_estimate=estimate_tokens(text),
                )
            )
        return chunks


def _collect_deps(entities: list[ParsedEntity]) -> list[str]:
    deps: set[str] = set()
    for e in entities:
        deps.update(e.dependencies)
        deps.update(i[:60] for i in e.imports)
    return sorted(deps)[:20]
