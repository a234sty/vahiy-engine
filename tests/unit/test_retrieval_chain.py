"""Unit tests for the multi-sub-query retrieval chain:
planner -> executor -> reranking -> selection.

No real corpus: fakes stand in, sized so that coverage thresholds and
budgets are actually exercised rather than trivially satisfied.
"""

from collections.abc import Iterator

import pytest

from vahiy_engine.rag.executor import Candidate, execute_plan
from vahiy_engine.rag.planner import (
    Facet,
    SourceKind,
    extract_search_terms,
    plan_retrieval,
    usable_translations,
)
from vahiy_engine.rag.reranking import rerank
from vahiy_engine.rag.selection import select_evidence
from vahiy_engine.reasoning.intent import Depth, analyze_question
from vahiy_engine.sources.ahit.client import VerseNotFoundError
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.models import Verse
from vahiy_engine.sources.osis import OsisReference
from vahiy_engine.sources.quran.models import Ayah, QuranReference


class FakeCorpus(CorpusClient):
    """A corpus with per-translation content, so translation selection and
    the usable-coverage threshold are both really exercised."""

    def __init__(self, by_translation: dict[str, list[Verse]], default: str = "KJV") -> None:
        self._by_translation = by_translation
        self._default = default

    def get_verse(self, reference: OsisReference, translation: str | None = None) -> Verse:
        for verse in self._by_translation.get(translation or self._default, []):
            if verse.osis == reference.osis:
                return verse
        raise VerseNotFoundError(reference.osis)

    def iter_verses(self, translation: str | None = None) -> Iterator[Verse]:
        yield from self._by_translation.get(translation or self._default, [])


class FakeQuran:
    def __init__(self, ayat: list[Ayah], editions: tuple[str, ...] = ("tr", "en")) -> None:
        self._ayat = ayat
        self._editions = editions

    def available_editions(self) -> list[str]:
        return list(self._editions)

    def get_ayah(self, reference: QuranReference, edition: str | None = None) -> Ayah:
        for ayah in self._ayat:
            if (ayah.surah, ayah.ayah) == (reference.surah, reference.ayah):
                return ayah
        raise LookupError(reference.citation)

    def iter_ayat(self, edition: str | None = None) -> Iterator[Ayah]:
        yield from self._ayat


def make_verses(book: str, count: int, text: str) -> list[Verse]:
    return [
        Verse(osis=f"{book}.1.{i}", book=book, chapter=1, verse=i, text=text, translation="YTC")
        for i in range(1, count + 1)
    ]


@pytest.fixture
def corpus() -> FakeCorpus:
    # YTC is above the usability threshold; KJV is a sample below it, exactly
    # like the repository's bundled 17-verse KJV.
    return FakeCorpus(
        {
            "YTC": make_verses("Matt", 60, "Mesih Yeşua hakkında") + make_verses("Rom", 60, "iman"),
            "KJV": make_verses("Gen", 5, "In the beginning"),
        },
        default="KJV",
    )


@pytest.fixture
def quran() -> FakeQuran:
    return FakeQuran(
        [Ayah(surah=5, ayah=17, text="Meryem oğlu Mesih", edition="tr")]
        + [Ayah(surah=2, ayah=n, text="iman edenler", edition="tr") for n in range(1, 20)]
    )


# --- Search-term extraction ---


@pytest.mark.parametrize(
    "question,expected",
    [
        ("Mesih ne demek?", ("mesih",)),
        ("Pavlus ne diyor?", ("pavlus",)),
        ("Mesih kavramı Kuran ve Yeni Ahitte nasıl farklı?", ("mesih",)),
        ("What does the word kyrios mean?", ("kyrios",)),
    ],
)
def test_framing_and_corpus_names_are_stripped_from_search_terms(
    question: str, expected: tuple[str, ...]
) -> None:
    # Real defect this guards: "ne demek" left "demek" as a search term, and
    # because "demek" occurs in ordinary narration it outranked the actual
    # subject -- "Mesih ne demek?" returned Luke 5:23 and Mark 2:9.
    assert extract_search_terms(question) == expected


def test_search_term_extraction_is_order_preserving_and_deduplicated() -> None:
    assert extract_search_terms("Mesih ve Mesih ve Pavlus") == ("mesih", "pavlus")


# --- Planning ---


def test_a_question_is_decomposed_into_several_source_targeted_subqueries(
    corpus: FakeCorpus, quran: FakeQuran
) -> None:
    question = "Mesih kavramı Kuran ve Yeni Ahitte nasıl farklı?"
    plan = plan_retrieval(question, analyze_question(question), corpus, quran)

    facets = {sq.facet for sq in plan.subqueries}
    assert Facet.SCRIPTURE_USAGE in facets
    assert Facet.QURAN_USAGE in facets
    assert len(plan.subqueries) >= 2


def test_turkish_question_targets_the_turkish_translation_and_edition(
    corpus: FakeCorpus, quran: FakeQuran
) -> None:
    question = "Mesih kavramı nedir?"
    plan = plan_retrieval(question, analyze_question(question), corpus, quran)

    bible = next(sq for sq in plan.subqueries if sq.source is SourceKind.BIBLE)
    quran_sq = next(sq for sq in plan.subqueries if sq.source is SourceKind.QURAN)
    assert bible.edition == "YTC"
    assert quran_sq.edition == "tr"


def test_a_translation_below_the_coverage_threshold_is_not_planned_against(
    corpus: FakeCorpus,
) -> None:
    # KJV holds five verses here. A search against it would return nothing
    # while looking exactly like retrieval ran.
    assert usable_translations(corpus, ("KJV",)) == ()
    assert usable_translations(corpus, ("YTC",)) == ("YTC",)


def test_an_uncited_original_language_corpus_is_skipped_with_a_stated_reason(
    corpus: FakeCorpus, quran: FakeQuran
) -> None:
    question = "Mesih nedir?"
    plan = plan_retrieval(question, analyze_question(question), corpus, quran)

    assert any("Latin script" in reason for reason in plan.skipped)
    assert not any(sq.facet is Facet.ORIGINAL_LANGUAGE for sq in plan.subqueries)


def test_a_narrow_non_comparative_question_does_not_search_the_quran_and_says_why(
    corpus: FakeCorpus, quran: FakeQuran
) -> None:
    question = "What does Genesis 1:1 mean?"
    plan = plan_retrieval(question, analyze_question(question), corpus, quran)

    assert not any(sq.source is SourceKind.QURAN for sq in plan.subqueries)
    assert any("scope decision" in reason for reason in plan.skipped)


def test_a_cited_passage_is_planned_as_its_own_subquery(
    corpus: FakeCorpus, quran: FakeQuran
) -> None:
    question = "What does Genesis 1:1 mean?"
    plan = plan_retrieval(question, analyze_question(question), corpus, quran)

    cited = [sq for sq in plan.subqueries if sq.facet is Facet.CITED_PASSAGE]
    assert [sq.query for sq in cited] == ["Gen.1.1"]


def test_missing_quran_client_is_recorded_as_not_searched_not_as_no_result(
    corpus: FakeCorpus,
) -> None:
    question = "Mesih kavramı nedir?"
    plan = plan_retrieval(question, analyze_question(question), corpus, None)

    assert any("No Qur'an client is wired up" in reason for reason in plan.skipped)


def test_depth_sets_the_per_subquery_limit(corpus: FakeCorpus, quran: FakeQuran) -> None:
    broad = plan_retrieval("Tanrı nedir?", analyze_question("Tanrı nedir?"), corpus, quran)
    narrow_q = "What does Genesis 1:1 mean?"
    narrow = plan_retrieval(narrow_q, analyze_question(narrow_q), corpus, quran)

    broad_limit = max(sq.limit for sq in broad.subqueries)
    narrow_limit = max(sq.limit for sq in narrow.subqueries)
    assert broad_limit > narrow_limit


# --- Execution ---


def test_the_quran_is_actually_searched_by_keyword(corpus: FakeCorpus, quran: FakeQuran) -> None:
    # Before this chain existed, QuranClient.iter_ayat was called by nothing:
    # Qur'anic text could only be reached by a citation already in the graph.
    question = "Mesih kavramı Kuran ve Yeni Ahitte nasıl farklı?"
    plan = plan_retrieval(question, analyze_question(question), corpus, quran)
    executed = execute_plan(plan, corpus, quran)

    quran_hits = [c for c in executed.candidates if c.citation_type == "quran"]
    assert quran_hits
    assert quran_hits[0].citation == "Quran.5.17"


def test_both_corpora_contribute_candidates_to_a_comparative_question(
    corpus: FakeCorpus, quran: FakeQuran
) -> None:
    question = "Mesih kavramı Kuran ve Yeni Ahitte nasıl farklı?"
    executed = execute_plan(
        plan_retrieval(question, analyze_question(question), corpus, quran), corpus, quran
    )

    assert {c.citation_type for c in executed.candidates} == {"osis", "quran"}


def test_a_subquery_that_finds_nothing_is_reported_rather_than_dropped(
    corpus: FakeCorpus, quran: FakeQuran
) -> None:
    question = "zzzunmatchableterm nedir?"
    executed = execute_plan(
        plan_retrieval(question, analyze_question(question), corpus, quran), corpus, quran
    )

    assert executed.candidates == ()
    assert executed.empty_subqueries


# --- Reranking ---


def make_candidate(citation: str, facet: Facet, rank: int = 0, subquery_id: str = "q") -> Candidate:
    return Candidate(
        citation=citation,
        citation_type="quran" if citation.startswith("Quran") else "osis",
        text="text",
        source_label="src",
        facet=facet,
        subquery_id=subquery_id,
        raw_score=1.0,
        rank_in_subquery=rank,
    )


def test_a_directly_cited_passage_outranks_a_keyword_hit() -> None:
    ranked = rerank(
        (
            make_candidate("Rom.1.1", Facet.SCRIPTURE_USAGE, rank=0),
            make_candidate("Gen.1.1", Facet.CITED_PASSAGE, rank=0),
        )
    )

    assert ranked[0].candidate.citation == "Gen.1.1"


def test_repeated_hits_from_one_book_are_progressively_discounted() -> None:
    ranked = rerank(
        tuple(make_candidate(f"Matt.1.{i}", Facet.SCRIPTURE_USAGE, rank=i) for i in range(3))
        + (make_candidate("Rom.1.1", Facet.SCRIPTURE_USAGE, rank=2),)
    )

    # Rom shares rank 2 with Matt.1.2 but is the first hit from its book, so
    # the diversity penalty puts it ahead.
    citations = [r.candidate.citation for r in ranked]
    assert citations.index("Rom.1.1") < citations.index("Matt.1.2")


def test_reranking_is_deterministic() -> None:
    candidates = (
        make_candidate("Matt.1.1", Facet.SCRIPTURE_USAGE),
        make_candidate("Quran.5.17", Facet.QURAN_USAGE),
    )

    assert [r.candidate.citation for r in rerank(candidates)] == [
        r.candidate.citation for r in rerank(candidates)
    ]


def test_every_ranked_candidate_carries_an_explanation() -> None:
    ranked = rerank((make_candidate("Matt.1.1", Facet.SCRIPTURE_USAGE),))

    assert "facet=scripture_usage" in ranked[0].explanation


# --- Selection ---


def test_a_comparative_question_keeps_quran_evidence_despite_a_larger_bible_corpus() -> None:
    # The failure this prevents: the Bible corpus is several times larger, so
    # ranking alone lets it fill every slot and a comparison silently becomes
    # a one-sided answer.
    bible = tuple(
        make_candidate(f"Matt.1.{i}", Facet.SCRIPTURE_USAGE, rank=i, subquery_id="b")
        for i in range(10)
    )
    quran = (make_candidate("Quran.5.17", Facet.QURAN_USAGE, rank=9, subquery_id="q"),)

    selected = select_evidence(rerank(bible + quran), Depth.NARROW)

    assert "quran_usage" in selected.facet_counts
    assert any(item.citation == "Quran.5.17" for item in selected.items)


def test_the_same_citation_found_twice_occupies_one_slot() -> None:
    duplicated = (
        make_candidate("Matt.1.1", Facet.SCRIPTURE_USAGE, rank=0, subquery_id="a"),
        make_candidate("Matt.1.1", Facet.QURAN_USAGE, rank=3, subquery_id="b"),
    )

    selected = select_evidence(rerank(duplicated), Depth.BROAD)

    assert [item.citation for item in selected.items] == ["Matt.1.1"]


@pytest.mark.parametrize(
    "depth,maximum", [(Depth.NARROW, 4), (Depth.STANDARD, 8), (Depth.BROAD, 16)]
)
def test_the_depth_budget_caps_how_much_evidence_reaches_the_answer(
    depth: Depth, maximum: int
) -> None:
    many = tuple(make_candidate(f"Matt.{i}.1", Facet.SCRIPTURE_USAGE, rank=i) for i in range(40))

    selected = select_evidence(rerank(many), depth)

    assert len(selected.items) == maximum
    assert selected.dropped_for_budget == 40 - maximum


def test_selected_evidence_records_which_subquestion_found_it() -> None:
    selected = select_evidence(
        rerank((make_candidate("Quran.5.17", Facet.QURAN_USAGE),)), Depth.NARROW
    )

    assert "quran_usage" in selected.items[0].note
