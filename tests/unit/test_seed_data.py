"""Unit tests for the seed Knowledge Graph's structure (no corpus access)."""

from vahiy_engine.knowledge_graph.seed_data import build_seed_graph


def test_builds_without_error() -> None:
    build_seed_graph()


def test_yhwh_sabbath_abraham_are_all_present_with_expected_types() -> None:
    graph = build_seed_graph()

    assert graph.get_node("yhwh").type == "concept"
    assert graph.get_node("sabbath").type == "concept"
    assert graph.get_node("abraham").type == "person"


def test_yhwh_is_findable_by_label() -> None:
    graph = build_seed_graph()

    assert [n.id for n in graph.find_by_label("YHWH")] == ["yhwh"]


def test_sabbath_is_findable_by_turkish_label() -> None:
    graph = build_seed_graph()

    assert [n.id for n in graph.find_by_label("Şabat")] == ["sabbath"]


def test_abraham_is_findable_by_turkish_label() -> None:
    graph = build_seed_graph()

    assert [n.id for n in graph.find_by_label("İbrahim")] == ["abraham"]


def test_abraham_cites_both_torah_and_quran() -> None:
    graph = build_seed_graph()

    citation_types = {e.citation_type for e in graph.edges_from("abraham")}

    assert citation_types == {"osis", "quran"}


def test_abraham_has_no_hadith_or_tafsir_citations_yet() -> None:
    # Documents a known, disclosed gap rather than a silent one: no Hadith or
    # Tafsir corpus is ingested yet, so none should be cited here despite
    # being architecturally anticipated (PART_IX in vahiy-engine-brain).
    graph = build_seed_graph()

    citation_types = {e.citation_type for e in graph.edges_from("abraham")}

    assert "hadith" not in citation_types
    assert "tafsir" not in citation_types


def test_yhwh_derives_from_edge_points_at_a_real_node() -> None:
    graph = build_seed_graph()

    derives = graph.edges_from("yhwh", type="derives_from")

    assert len(derives) == 1
    assert derives[0].target_id == "hayah"
    assert graph.get_node("hayah") is not None


def test_every_citation_edge_has_a_citation_type() -> None:
    graph = build_seed_graph()

    for node_id in ("yhwh", "sabbath", "abraham", "hayah", "kyrios"):
        for edge in graph.edges_from(node_id):
            if edge.citation is not None:
                assert (
                    edge.citation_type is not None
                ), f"edge {edge} has a citation with no citation_type"
