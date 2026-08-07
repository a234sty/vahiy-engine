"""Unit tests for the RSN-2 reasoning loop. No real network/corpus access —
fake clients stand in for AhitCorpusClient/QuranClient/AhitLexiconClient."""

from collections.abc import Iterator

import pytest

from vahiy_engine.knowledge_graph.graph import KnowledgeGraph
from vahiy_engine.knowledge_graph.models import Edge, Node
from vahiy_engine.lexicon.ahit.client import EntryNotFoundError
from vahiy_engine.lexicon.client import LexiconClient
from vahiy_engine.lexicon.models import LexiconEntry
from vahiy_engine.reasoning.loop import run_reasoning_loop
from vahiy_engine.reasoning.trace import ConfidenceTier
from vahiy_engine.sources.ahit.client import VerseNotFoundError
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.models import Verse
from vahiy_engine.sources.osis import OsisReference
from vahiy_engine.sources.quran.client import AyahNotFoundError
from vahiy_engine.sources.quran.models import Ayah, QuranReference


class FakeCorpus(CorpusClient):
    def __init__(self, verses: dict[tuple[str, str | None], str]) -> None:
        self._verses = verses

    def get_verse(self, reference: OsisReference, translation: str | None = None) -> Verse:
        key = (reference.osis, translation)
        if key not in self._verses:
            raise VerseNotFoundError(f"{reference.osis} not found in {translation}")
        return Verse(
            osis=reference.osis,
            book=reference.book,
            chapter=reference.chapter,
            verse=reference.verse,
            text=self._verses[key],
            translation=translation or "KJV",
        )

    def iter_verses(self, translation: str | None = None) -> Iterator[Verse]:
        return iter([])


class FakeQuranClient:
    def __init__(self, ayat: dict[tuple[int, int, str | None], str]) -> None:
        self._ayat = ayat

    def get_ayah(self, reference: QuranReference, edition: str | None = None) -> Ayah:
        key = (reference.surah, reference.ayah, edition)
        if key not in self._ayat:
            raise AyahNotFoundError(f"{reference.citation} not found in edition {edition}")
        return Ayah(
            surah=reference.surah,
            ayah=reference.ayah,
            text=self._ayat[key],
            edition=edition or "arabic",
        )

    def iter_ayat(self, edition: str | None = None) -> Iterator[Ayah]:
        return iter([])


class FakeLexiconClient(LexiconClient):
    def __init__(self, entries: dict[str, LexiconEntry]) -> None:
        self._entries = entries

    def get_entry(self, strongs_number: str) -> LexiconEntry:
        try:
            return self._entries[strongs_number]
        except KeyError as exc:
            raise EntryNotFoundError(strongs_number) from exc

    def iter_entries(self, language: str | None = None) -> Iterator[LexiconEntry]:
        return iter([])


def make_h3068() -> LexiconEntry:
    return LexiconEntry(
        strongs_number="H3068",
        language="hebrew",
        lemma="יְהֹוָה",
        transliteration="Yᵉhôvâh",
        definition="the existing One",
    )


@pytest.fixture
def yhwh_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()
    graph.add_node(Node(id="yhwh", type="concept", labels={"en": "YHWH", "he": "יהוה"}))
    graph.add_edge(
        Edge(source_id="yhwh", type="explains", citation="Exod.3.14", citation_type="osis")
    )
    graph.add_edge(
        Edge(
            source_id="yhwh", type="attributed_to", citation="Strong:H3068", citation_type="strongs"
        )
    )
    return graph


def test_returns_none_when_no_node_matches() -> None:
    graph = KnowledgeGraph()
    graph.add_node(Node(id="yhwh", type="concept", labels={"en": "YHWH"}))
    corpus = FakeCorpus({})
    quran = FakeQuranClient({})
    lexicon = FakeLexiconClient({})

    result = run_reasoning_loop(graph, corpus, quran, lexicon, "What is faith?")

    assert result is None


def test_detects_intent_and_matches_the_yhwh_node(yhwh_graph: KnowledgeGraph) -> None:
    corpus = FakeCorpus({("Exod.3.14", "WLC"): "I AM THAT I AM"})
    lexicon = FakeLexiconClient({"H3068": make_h3068()})

    result = run_reasoning_loop(
        yhwh_graph, corpus, FakeQuranClient({}), lexicon, "What does YHWH mean?"
    )

    assert result is not None
    assert result.trace.detected_intent.node_id == "yhwh"
    assert result.trace.detected_intent.matched_label == "yhwh"


def test_osis_evidence_resolves_via_wlc(yhwh_graph: KnowledgeGraph) -> None:
    corpus = FakeCorpus({("Exod.3.14", "WLC"): "wlc text"})
    lexicon = FakeLexiconClient({"H3068": make_h3068()})

    result = run_reasoning_loop(yhwh_graph, corpus, FakeQuranClient({}), lexicon, "YHWH")

    osis_evidence = [e for e in result.trace.evidence_retrieved if e.citation_type == "osis"]
    assert len(osis_evidence) == 1
    assert osis_evidence[0].text == "wlc text"


def test_osis_evidence_falls_back_to_sblgnt_when_not_in_wlc() -> None:
    graph = KnowledgeGraph()
    graph.add_node(Node(id="sabbath", type="concept", labels={"en": "Sabbath"}))
    graph.add_edge(
        Edge(source_id="sabbath", type="cross_references", citation="Heb.4.9", citation_type="osis")
    )
    corpus = FakeCorpus({("Heb.4.9", "SBLGNT"): "sblgnt text"})

    result = run_reasoning_loop(
        graph, corpus, FakeQuranClient({}), FakeLexiconClient({}), "Sabbath"
    )

    assert result.trace.evidence_retrieved[0].text == "sblgnt text"


def test_strongs_evidence_resolves_to_lemma_and_definition(yhwh_graph: KnowledgeGraph) -> None:
    corpus = FakeCorpus({("Exod.3.14", "WLC"): "wlc text"})
    lexicon = FakeLexiconClient({"H3068": make_h3068()})

    result = run_reasoning_loop(yhwh_graph, corpus, FakeQuranClient({}), lexicon, "YHWH")

    strongs_evidence = [e for e in result.trace.evidence_retrieved if e.citation_type == "strongs"]
    assert len(strongs_evidence) == 1
    assert "יְהֹוָה" in strongs_evidence[0].text
    assert "existing One" in strongs_evidence[0].text


def test_same_citation_on_two_edges_is_not_counted_twice() -> None:
    # Real bug, found via live testing: YHWH's "explains" edge and its
    # "derives_from" edge both cite Exod.3.14 (they support two different
    # claims about the same verse). Resolving each edge independently
    # counted the same underlying source twice, inflating resolved_count
    # and skewing confidence toward stronger corroboration than actually
    # exists.
    graph = KnowledgeGraph()
    graph.add_node(Node(id="yhwh", type="concept", labels={"en": "YHWH"}))
    graph.add_node(Node(id="hayah", type="word", labels={"en": "to be"}))
    graph.add_edge(
        Edge(source_id="yhwh", type="explains", citation="Exod.3.14", citation_type="osis")
    )
    graph.add_edge(
        Edge(
            source_id="yhwh",
            type="derives_from",
            target_id="hayah",
            citation="Exod.3.14",
            citation_type="osis",
        )
    )
    corpus = FakeCorpus({("Exod.3.14", "WLC"): "text"})

    result = run_reasoning_loop(graph, corpus, FakeQuranClient({}), FakeLexiconClient({}), "YHWH")

    assert len(result.trace.evidence_retrieved) == 1
    assert result.trace.confidence.resolved_count == 1


def test_unresolvable_citation_is_tracked_as_rejected_not_dropped(
    yhwh_graph: KnowledgeGraph,
) -> None:
    # Corpus doesn't have Exod.3.14 in any translation -- only the lexicon resolves.
    corpus = FakeCorpus({})
    lexicon = FakeLexiconClient({"H3068": make_h3068()})

    result = run_reasoning_loop(yhwh_graph, corpus, FakeQuranClient({}), lexicon, "YHWH")

    assert len(result.trace.evidence_retrieved) == 1
    assert len(result.trace.evidence_rejected) == 1
    assert result.trace.evidence_rejected[0].citation == "Exod.3.14"
    assert result.trace.evidence_rejected[0].reason_code == "unresolvable_in_current_corpus"


def test_confidence_is_high_with_diverse_resolved_evidence() -> None:
    graph = KnowledgeGraph()
    graph.add_node(Node(id="yhwh", type="concept", labels={"en": "YHWH"}))
    graph.add_edge(
        Edge(source_id="yhwh", type="explains", citation="Exod.3.14", citation_type="osis")
    )
    graph.add_edge(
        Edge(source_id="yhwh", type="explains", citation="Rom.10.13", citation_type="osis")
    )
    graph.add_edge(
        Edge(
            source_id="yhwh", type="attributed_to", citation="Strong:H3068", citation_type="strongs"
        )
    )
    corpus = FakeCorpus({("Exod.3.14", "WLC"): "a", ("Rom.10.13", "SBLGNT"): "b"})
    lexicon = FakeLexiconClient({"H3068": make_h3068()})

    result = run_reasoning_loop(graph, corpus, FakeQuranClient({}), lexicon, "YHWH")

    assert result.trace.confidence.tier == ConfidenceTier.HIGH
    assert result.trace.confidence.resolved_count == 3


def test_confidence_is_none_when_nothing_resolves(yhwh_graph: KnowledgeGraph) -> None:
    corpus = FakeCorpus({})
    lexicon = FakeLexiconClient({})

    result = run_reasoning_loop(yhwh_graph, corpus, FakeQuranClient({}), lexicon, "YHWH")

    assert result.trace.confidence.tier == ConfidenceTier.NONE
    assert result.trace.confidence.resolved_count == 0


def test_stopwords_are_never_matched_to_a_node() -> None:
    graph = KnowledgeGraph()
    # A pathological node whose label collides with a stopword.
    graph.add_node(Node(id="collider", type="concept", labels={"en": "is"}))

    result = run_reasoning_loop(
        graph, FakeCorpus({}), FakeQuranClient({}), FakeLexiconClient({}), "What is faith?"
    )

    assert result is None


def test_trace_pipeline_info_is_populated(yhwh_graph: KnowledgeGraph) -> None:
    corpus = FakeCorpus({("Exod.3.14", "WLC"): "text"})
    lexicon = FakeLexiconClient({"H3068": make_h3068()})

    result = run_reasoning_loop(yhwh_graph, corpus, FakeQuranClient({}), lexicon, "YHWH")

    assert result.trace.pipeline.pipeline_id
    assert result.trace.pipeline.pipeline_version
    assert result.trace.pipeline.constitution_version
