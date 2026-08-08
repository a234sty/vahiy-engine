"""Unit tests for the reasoning layer's integration into the chat pipeline.

Covers the wiring that lets RSN-2's Knowledge Graph loop, the Qur'an corpus,
and the reasoning trace reach an actual /chat answer -- all three of which
existed but were unreachable from the live request path before this. No real
network, corpus, or LLM access: fakes stand in for every client.
"""

from collections.abc import Iterator

import pytest

from vahiy_engine.knowledge_graph.graph import KnowledgeGraph
from vahiy_engine.knowledge_graph.models import Edge, Node
from vahiy_engine.lexicon.ahit.client import EntryNotFoundError
from vahiy_engine.lexicon.client import LexiconClient
from vahiy_engine.lexicon.models import LexiconEntry
from vahiy_engine.pipeline.chat_pipeline import run_chat_pipeline
from vahiy_engine.pipeline.prompt_builder import Corpus, UserPreferences
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
            raise VerseNotFoundError(f"{reference.osis} not in {translation}")
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
    def __init__(self, ayat: dict[tuple[int, int], str], editions: list[str] | None = None) -> None:
        self._ayat = ayat
        self._editions = editions if editions is not None else ["en"]

    def available_editions(self) -> list[str]:
        return list(self._editions)

    def get_ayah(self, reference: QuranReference, edition: str | None = None) -> Ayah:
        key = (reference.surah, reference.ayah)
        if key not in self._ayat:
            raise AyahNotFoundError(reference.citation)
        return Ayah(surah=reference.surah, ayah=reference.ayah, text=self._ayat[key], edition="en")

    def iter_ayat(self, edition: str | None = None) -> Iterator[Ayah]:
        return iter([])


class FakeLexiconClient(LexiconClient):
    def __init__(self, entries: dict[str, LexiconEntry] | None = None) -> None:
        self._entries = entries or {}

    def get_entry(self, strongs_number: str) -> LexiconEntry:
        try:
            return self._entries[strongs_number]
        except KeyError as exc:
            raise EntryNotFoundError(strongs_number) from exc

    def iter_entries(self, language: str | None = None) -> Iterator[LexiconEntry]:
        return iter([])


class CapturingProvider:
    """Records the context it was handed, so tests can assert on what the
    model would actually have seen."""

    def __init__(self) -> None:
        self.context = ""

    def generate_answer(self, system_prompt: str, question: str, context: str) -> str:
        self.context = context
        return "answer"


@pytest.fixture
def abraham_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()
    graph.add_node(Node(id="abraham", type="person", labels={"en": "Abraham", "tr": "İbrahim"}))
    graph.add_edge(
        Edge(
            source_id="abraham",
            type="cross_references",
            citation="Gen.12.1",
            citation_type="osis",
        )
    )
    graph.add_edge(
        Edge(
            source_id="abraham",
            type="cross_references",
            citation="Quran.14.35",
            citation_type="quran",
        )
    )
    return graph


@pytest.fixture
def corpus() -> FakeCorpus:
    return FakeCorpus({("Gen.12.1", "YTC"): "Rab Avram'a dedi", ("Gen.12.1", "WLC"): "וַיֹּאמֶר"})


@pytest.fixture
def quran() -> FakeQuranClient:
    return FakeQuranClient({(14, 35): "And when Abraham said, my Lord..."})


def test_without_the_reasoning_arguments_no_trace_is_produced(corpus: FakeCorpus) -> None:
    # The reasoning layer is opt-in; omitting it must leave prior behavior
    # exactly as it was.
    provider = CapturingProvider()

    result = run_chat_pipeline(corpus, provider, "Who is Abraham?")

    assert result.trace is None
    assert result.primary_evidence == []
    assert "PRIMARY EVIDENCE" not in provider.context
    assert "COVERAGE LIMITS" not in provider.context


def test_quranic_evidence_reaches_the_answer_context(
    abraham_graph: KnowledgeGraph, corpus: FakeCorpus, quran: FakeQuranClient
) -> None:
    # Keyword retrieval indexes the Bible corpus only, so the Knowledge Graph
    # is the sole path by which any Qur'anic text can reach an answer.
    provider = CapturingProvider()

    result = run_chat_pipeline(
        corpus,
        provider,
        "Who is Abraham?",
        lexicon=FakeLexiconClient(),
        quran=quran,
        graph=abraham_graph,
    )

    assert "And when Abraham said, my Lord..." in provider.context
    assert "[Quran.14.35] (Qur'an)" in provider.context
    assert [e.citation for e in result.primary_evidence if e.citation_type == "quran"] == [
        "Quran.14.35"
    ]


def test_turkish_question_matches_the_same_concept(
    abraham_graph: KnowledgeGraph, corpus: FakeCorpus, quran: FakeQuranClient
) -> None:
    result = run_chat_pipeline(
        corpus,
        provider := CapturingProvider(),
        "İbrahim kimdir?",
        lexicon=FakeLexiconClient(),
        quran=quran,
        graph=abraham_graph,
    )

    assert result.trace is not None
    assert result.trace.detected_intent.node_id == "abraham"
    assert "Quran.14.35" in provider.context


def test_trace_carries_confidence_and_pipeline_provenance(
    abraham_graph: KnowledgeGraph, corpus: FakeCorpus, quran: FakeQuranClient
) -> None:
    result = run_chat_pipeline(
        corpus,
        CapturingProvider(),
        "Who is Abraham?",
        lexicon=FakeLexiconClient(),
        quran=quran,
        graph=abraham_graph,
    )

    assert result.trace is not None
    assert result.trace.confidence.resolved_count == 2
    assert set(result.trace.confidence.distinct_citation_types) == {"osis", "quran"}
    assert result.trace.pipeline.pipeline_id
    assert result.trace.pipeline.constitution_version


def test_readable_translation_and_original_language_are_both_carried(
    abraham_graph: KnowledgeGraph, corpus: FakeCorpus, quran: FakeQuranClient
) -> None:
    # Real bug found by running this end to end: the loop resolved WLC first,
    # so a user asking in Turkish received pointed Hebrew as the primary
    # evidence with no translation, leaving the model to translate it itself.
    provider = CapturingProvider()

    run_chat_pipeline(
        corpus,
        provider,
        "Who is Abraham?",
        lexicon=FakeLexiconClient(),
        quran=quran,
        graph=abraham_graph,
    )

    assert "Rab Avram'a dedi" in provider.context
    assert "Hebrew (source text): וַיֹּאמֶר" in provider.context


def test_coverage_notes_report_a_missing_quran_corpus_rather_than_silence(
    abraham_graph: KnowledgeGraph, corpus: FakeCorpus
) -> None:
    # A deployment with no Qur'an editions must say so; otherwise the absence
    # of a Qur'anic citation reads as the Qur'an having nothing to say.
    provider = CapturingProvider()

    run_chat_pipeline(
        corpus,
        provider,
        "Who is Abraham?",
        lexicon=FakeLexiconClient(),
        quran=FakeQuranClient({}, editions=[]),
        graph=abraham_graph,
    )

    assert "No Qur'an corpus is configured" in provider.context


def test_coverage_notes_name_the_uncited_source_families(
    abraham_graph: KnowledgeGraph, corpus: FakeCorpus, quran: FakeQuranClient
) -> None:
    provider = CapturingProvider()

    run_chat_pipeline(
        corpus,
        provider,
        "Who is Abraham?",
        lexicon=FakeLexiconClient(),
        quran=quran,
        graph=abraham_graph,
    )

    assert "No hadith, tafsir, rabbinic, patristic or commentary corpus" in provider.context


def test_unmatched_question_still_answers_and_discloses_that_no_concept_matched(
    abraham_graph: KnowledgeGraph, corpus: FakeCorpus, quran: FakeQuranClient
) -> None:
    provider = CapturingProvider()

    result = run_chat_pipeline(
        corpus,
        provider,
        "What is the airspeed velocity of an unladen swallow?",
        lexicon=FakeLexiconClient(),
        quran=quran,
        graph=abraham_graph,
    )

    assert result.trace is None
    assert result.answer == "answer"
    assert "matched no concept in the curated knowledge graph" in provider.context


def test_unresolvable_curated_citations_are_disclosed_not_dropped(
    corpus: FakeCorpus, quran: FakeQuranClient
) -> None:
    graph = KnowledgeGraph()
    graph.add_node(Node(id="abraham", type="person", labels={"en": "Abraham"}))
    graph.add_edge(
        Edge(
            source_id="abraham",
            type="cross_references",
            citation="Gen.12.1",
            citation_type="osis",
        )
    )
    graph.add_edge(
        Edge(
            source_id="abraham",
            type="cross_references",
            citation="Quran.99.99",
            citation_type="quran",
        )
    )
    provider = CapturingProvider()

    result = run_chat_pipeline(
        corpus,
        provider,
        "Who is Abraham?",
        lexicon=FakeLexiconClient(),
        quran=quran,
        graph=graph,
    )

    assert result.trace is not None
    assert [i.citation for i in result.trace.evidence_rejected] == ["Quran.99.99"]
    assert "Quran.99.99" in provider.context


# --- Source preferences must reach retrieval, not just the prompt ---


def test_corpus_filter_removes_excluded_evidence_from_the_model_context(
    abraham_graph: KnowledgeGraph, corpus: FakeCorpus, quran: FakeQuranClient
) -> None:
    provider = CapturingProvider()

    result = run_chat_pipeline(
        corpus,
        provider,
        "Who is Abraham?",
        lexicon=FakeLexiconClient(),
        quran=quran,
        graph=abraham_graph,
        preferences=UserPreferences(corpora=(Corpus.BIBLE,)),
    )

    assert "And when Abraham said, my Lord..." not in provider.context
    assert [e.citation for e in result.primary_evidence] == ["Gen.12.1"]


def test_filtered_out_citations_are_disclosed_not_silently_dropped(
    abraham_graph: KnowledgeGraph, corpus: FakeCorpus, quran: FakeQuranClient
) -> None:
    # A filtered answer must stay distinguishable from a corpus that had
    # nothing to say on the topic.
    provider = CapturingProvider()

    result = run_chat_pipeline(
        corpus,
        provider,
        "Who is Abraham?",
        lexicon=FakeLexiconClient(),
        quran=quran,
        graph=abraham_graph,
        preferences=UserPreferences(corpora=(Corpus.BIBLE,)),
    )

    assert result.withheld_by_preference == ("Quran.14.35",)
    assert "Your source filter excluded these citations" in provider.context
    assert "Quran.14.35" in provider.context


def test_confidence_is_recalculated_after_filtering(
    abraham_graph: KnowledgeGraph, corpus: FakeCorpus, quran: FakeQuranClient
) -> None:
    # Confidence must reflect the evidence that actually reached the answer,
    # not the evidence that would have been available unfiltered.
    unfiltered = run_chat_pipeline(
        corpus,
        CapturingProvider(),
        "Who is Abraham?",
        lexicon=FakeLexiconClient(),
        quran=quran,
        graph=abraham_graph,
    )
    filtered = run_chat_pipeline(
        corpus,
        CapturingProvider(),
        "Who is Abraham?",
        lexicon=FakeLexiconClient(),
        quran=quran,
        graph=abraham_graph,
        preferences=UserPreferences(corpora=(Corpus.BIBLE,)),
    )

    assert unfiltered.trace is not None and filtered.trace is not None
    assert unfiltered.trace.confidence.resolved_count == 2
    assert filtered.trace.confidence.resolved_count == 1


def test_question_analysis_is_returned_with_the_answer(
    abraham_graph: KnowledgeGraph, corpus: FakeCorpus, quran: FakeQuranClient
) -> None:
    result = run_chat_pipeline(
        corpus,
        CapturingProvider(),
        "İbrahim kimdir?",
        lexicon=FakeLexiconClient(),
        quran=quran,
        graph=abraham_graph,
    )

    assert result.analysis is not None
    assert result.analysis.language == "tr"


def test_reasoning_layer_renders_the_full_prompt_contract(
    abraham_graph: KnowledgeGraph, corpus: FakeCorpus, quran: FakeQuranClient
) -> None:
    provider = CapturingProvider()

    run_chat_pipeline(
        corpus,
        provider,
        "Who is Abraham?",
        lexicon=FakeLexiconClient(),
        quran=quran,
        graph=abraham_graph,
    )

    assert "USER QUESTION" in provider.context
    assert "DETECTED INTENT" in provider.context
    assert "## Direct Answer" in provider.context
