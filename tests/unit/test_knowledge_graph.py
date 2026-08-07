"""Unit tests for the in-memory Knowledge Graph store and its models."""

import pytest

from vahiy_engine.knowledge_graph.graph import KnowledgeGraph, NodeNotFoundError
from vahiy_engine.knowledge_graph.models import Edge, Node


def make_node(node_id: str, type: str = "concept", **labels: str) -> Node:
    return Node(id=node_id, type=type, labels=labels)


# --- Node/Edge model validation ---


def test_edge_requires_target_or_citation() -> None:
    with pytest.raises(ValueError, match="target_id.*citation"):
        Edge(source_id="a", type="explains")


def test_edge_accepts_target_only() -> None:
    edge = Edge(source_id="a", type="derives_from", target_id="b")
    assert edge.target_id == "b"


def test_edge_accepts_citation_only() -> None:
    edge = Edge(source_id="a", type="explains", citation="Exod.3.14", citation_type="osis")
    assert edge.citation == "Exod.3.14"


def test_edge_accepts_both_target_and_citation() -> None:
    edge = Edge(
        source_id="a",
        type="derives_from",
        target_id="b",
        citation="Exod.3.14",
        citation_type="osis",
    )
    assert edge.target_id == "b"
    assert edge.citation == "Exod.3.14"


# --- KnowledgeGraph ---


def test_add_node_and_get_node_round_trip() -> None:
    graph = KnowledgeGraph()
    node = make_node("yhwh", en="YHWH", he="יהוה")

    graph.add_node(node)

    assert graph.get_node("yhwh") == node


def test_add_node_rejects_duplicate_id() -> None:
    graph = KnowledgeGraph()
    graph.add_node(make_node("yhwh", en="YHWH"))

    with pytest.raises(ValueError, match="already registered"):
        graph.add_node(make_node("yhwh", en="YHWH again"))


def test_get_node_raises_for_missing_node() -> None:
    graph = KnowledgeGraph()

    with pytest.raises(NodeNotFoundError):
        graph.get_node("nonexistent")


def test_add_edge_rejects_reference_to_unknown_source_node() -> None:
    graph = KnowledgeGraph()
    graph.add_node(make_node("hayah", type="word", en="to be"))

    with pytest.raises(ValueError, match="unknown node"):
        graph.add_edge(Edge(source_id="nonexistent", type="derives_from", target_id="hayah"))


def test_add_edge_rejects_reference_to_unknown_target_node() -> None:
    graph = KnowledgeGraph()
    graph.add_node(make_node("yhwh", en="YHWH"))

    with pytest.raises(ValueError, match="unknown node"):
        graph.add_edge(Edge(source_id="yhwh", type="derives_from", target_id="nonexistent"))


def test_add_edge_with_citation_only_does_not_require_a_target_node() -> None:
    graph = KnowledgeGraph()
    graph.add_node(make_node("yhwh", en="YHWH"))

    graph.add_edge(
        Edge(source_id="yhwh", type="explains", citation="Exod.3.14", citation_type="osis")
    )

    assert len(graph.edges_from("yhwh")) == 1


def test_edges_from_returns_only_edges_originating_at_the_given_node() -> None:
    graph = KnowledgeGraph()
    graph.add_node(make_node("yhwh", en="YHWH"))
    graph.add_node(make_node("hayah", type="word", en="to be"))
    graph.add_edge(Edge(source_id="yhwh", type="derives_from", target_id="hayah"))
    graph.add_edge(
        Edge(source_id="hayah", type="explains", citation="Exod.3.14", citation_type="osis")
    )

    yhwh_edges = graph.edges_from("yhwh")

    assert len(yhwh_edges) == 1
    assert yhwh_edges[0].target_id == "hayah"


def test_edges_from_filters_by_type() -> None:
    graph = KnowledgeGraph()
    graph.add_node(make_node("yhwh", en="YHWH"))
    graph.add_node(make_node("hayah", type="word", en="to be"))
    graph.add_edge(Edge(source_id="yhwh", type="derives_from", target_id="hayah"))
    graph.add_edge(
        Edge(source_id="yhwh", type="explains", citation="Exod.3.14", citation_type="osis")
    )

    derives = graph.edges_from("yhwh", type="derives_from")

    assert len(derives) == 1
    assert derives[0].type == "derives_from"


def test_nodes_by_type_filters_correctly() -> None:
    graph = KnowledgeGraph()
    graph.add_node(make_node("yhwh", type="concept", en="YHWH"))
    graph.add_node(make_node("abraham", type="person", en="Abraham"))
    graph.add_node(make_node("sabbath", type="concept", en="Sabbath"))

    concepts = graph.nodes_by_type("concept")

    assert {n.id for n in concepts} == {"yhwh", "sabbath"}


def test_find_by_label_matches_case_insensitively_across_languages() -> None:
    graph = KnowledgeGraph()
    graph.add_node(make_node("sabbath", en="Sabbath", tr="Şabat", he="שַׁבָּת"))

    assert [n.id for n in graph.find_by_label("şabat")] == ["sabbath"]
    assert [n.id for n in graph.find_by_label("SABBATH")] == ["sabbath"]


def test_find_by_label_returns_empty_list_for_no_match() -> None:
    graph = KnowledgeGraph()
    graph.add_node(make_node("sabbath", en="Sabbath"))

    assert graph.find_by_label("logos") == []


def test_find_by_label_matches_turkish_dotted_capital_i() -> None:
    # Real bug, found via live testing: Python's plain str.casefold() turns
    # "İ" into "i̇" (i + a combining dot above, two characters), not plain
    # ASCII "i" — so a query already folded by normalize() (which does the
    # Turkish-specific fold to plain "i") silently failed to match a label
    # compared with bare .casefold() instead. "İbrahim kimdir?" resolved to
    # no match at all until both sides went through the same normalize().
    graph = KnowledgeGraph()
    graph.add_node(make_node("abraham", type="person", en="Abraham", tr="İbrahim"))

    assert [n.id for n in graph.find_by_label("ibrahim")] == ["abraham"]
