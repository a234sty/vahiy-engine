"""Unit tests for the deterministic search engine."""

from collections.abc import Iterator

import pytest

from vahiy_engine.search.engine import search
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.models import Verse
from vahiy_engine.sources.osis import OsisReference


class FakeCorpus(CorpusClient):
    """In-memory corpus for exercising the search engine without touching disk."""

    def __init__(self, verses: list[Verse]) -> None:
        self._verses = verses

    def get_verse(self, reference: OsisReference) -> Verse:
        raise NotImplementedError

    def iter_verses(self) -> Iterator[Verse]:
        yield from self._verses


def make_verse(book: str, chapter: int, verse: int, text: str) -> Verse:
    return Verse(
        osis=f"{book}.{chapter}.{verse}", book=book, chapter=chapter, verse=verse, text=text
    )


@pytest.fixture
def corpus() -> FakeCorpus:
    return FakeCorpus(
        [
            make_verse("Gen", 1, 1, "In the beginning God created the heaven and the earth."),
            make_verse("John", 1, 1, "In the beginning was the Word, and the Word was with God."),
            make_verse(
                "John", 3, 16, "For God so loved the world, that he gave his only begotten Son."
            ),
            make_verse("Ps", 1, 1, "Başlangıçta Tanrı gökleri ve yeri yarattı. İyi bir başlangıç."),
        ]
    )


def test_search_is_case_insensitive(corpus: FakeCorpus) -> None:
    results = search(corpus, "BEGINNING")

    assert {r.verse.osis for r in results} == {"Gen.1.1", "John.1.1"}


def test_search_supports_partial_word_matching(corpus: FakeCorpus) -> None:
    results = search(corpus, "begot")

    assert [r.verse.osis for r in results] == ["John.3.16"]


def test_search_supports_exact_phrase_matching(corpus: FakeCorpus) -> None:
    results = search(corpus, "In the beginning")

    assert {r.verse.osis for r in results} == {"Gen.1.1", "John.1.1"}


def test_search_phrase_requires_contiguous_word_order(corpus: FakeCorpus) -> None:
    results = search(corpus, "beginning the In")

    assert results == []


def test_search_supports_turkish_unicode_characters(corpus: FakeCorpus) -> None:
    results = search(corpus, "başlangıçta")

    assert [r.verse.osis for r in results] == ["Ps.1.1"]


def test_search_turkish_matching_is_case_insensitive(corpus: FakeCorpus) -> None:
    results = search(corpus, "TANRI")

    assert [r.verse.osis for r in results] == ["Ps.1.1"]


def test_search_score_counts_occurrences(corpus: FakeCorpus) -> None:
    results = search(corpus, "başlangıç")

    assert len(results) == 1
    # "başlangıç" occurs in both "Başlangıçta" and "başlangıç." — two overlapping-free hits.
    assert results[0].score == 2


def test_search_ranks_equal_scores_by_osis_order(corpus: FakeCorpus) -> None:
    results = search(corpus, "God")

    # "God" occurs exactly once in each of these three verses, so the tie is
    # broken deterministically by (book, chapter, verse).
    assert [r.verse.osis for r in results] == ["Gen.1.1", "John.1.1", "John.3.16"]
    assert [r.score for r in results] == [1, 1, 1]


def test_search_is_deterministic_across_repeated_calls(corpus: FakeCorpus) -> None:
    first = search(corpus, "God")
    second = search(corpus, "God")

    assert first == second


def test_search_returns_empty_list_for_no_matches(corpus: FakeCorpus) -> None:
    assert search(corpus, "nonexistent") == []


def test_search_returns_empty_list_for_blank_query(corpus: FakeCorpus) -> None:
    assert search(corpus, "   ") == []
