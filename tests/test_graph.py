from contextpack.core.models import EntityType, ParsedEntity
from contextpack.graph.engine import ContextGraph


def test_graph_relationships():
    entities = [
        ParsedEntity(type=EntityType.CLASS, name="A", file_path="a.py", imports=["b"]),
        ParsedEntity(type=EntityType.CLASS, name="B", file_path="b.py"),
    ]
    g = ContextGraph.from_entities(entities)
    assert g.graph.number_of_nodes() >= 2
    rels = g.get_relationships()
    assert any(r.relation == "imports" for r in rels)
