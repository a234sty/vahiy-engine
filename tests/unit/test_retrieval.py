"""Unit tests for the retrieval layer."""

from collections.abc import Iterator

import pytest

from vahiy_engine.rag.retrieval import Source, retrieve
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.models import Verse
from vahiy_engine.sources.osis import OsisReference


class FakeCorpus(CorpusClient):
    """In-memory corpus for exercising retrieval without touching disk."""

    def __init__(self, verses: list[Verse]) -> None:
        self._verses = verses

    def get_verse(self, reference: OsisReference) -> Verse:
        raise NotImplementedError

    def iter_verses(self, translation: str | None = None) -> Iterator[Verse]:
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
            make_verse("Gen", 1, 2, "And the Spirit of God moved upon the face of the waters."),
            make_verse("Gen", 1, 3, "And God said, Let there be light: and there was light."),
            make_verse("John", 1, 1, "In the beginning was the Word, and the Word was with God."),
            make_verse("John", 3, 16, "For God so loved the world, that he gave his only Son."),
        ]
    )


def test_retrieve_returns_source_objects(corpus: FakeCorpus) -> None:
    results = retrieve(corpus, "beginning", limit=10)

    assert all(isinstance(r, Source) for r in results)
    first = results[0]
    assert (first.osis, first.book, first.chapter, first.verse) == ("Gen.1.1", "Gen", 1, 1)
    assert first.text == "In the beginning God created the heaven and the earth."
    assert first.score == 1


def test_retrieve_truncates_to_top_n(corpus: FakeCorpus) -> None:
    results = retrieve(corpus, "God", limit=2)

    assert len(results) == 2


def test_retrieve_preserves_search_engine_ranking(corpus: FakeCorpus) -> None:
    results = retrieve(corpus, "God", limit=100)

    assert [r.osis for r in results] == [
        "Gen.1.1",
        "Gen.1.2",
        "Gen.1.3",
        "John.1.1",
        "John.3.16",
    ]


def test_retrieve_limit_larger_than_matches_returns_all_matches(corpus: FakeCorpus) -> None:
    results = retrieve(corpus, "beginning", limit=1000)

    assert len(results) == 2


def test_retrieve_returns_empty_list_for_no_matches(corpus: FakeCorpus) -> None:
    assert retrieve(corpus, "nonexistent", limit=10) == []


def test_retrieve_is_deterministic_across_repeated_calls(corpus: FakeCorpus) -> None:
    first = retrieve(corpus, "God", limit=3)
    second = retrieve(corpus, "God", limit=3)

    assert first == second


@pytest.mark.parametrize("limit", [0, -1, -10])
def test_retrieve_rejects_non_positive_limit(corpus: FakeCorpus, limit: int) -> None:
    with pytest.raises(ValueError):
        retrieve(corpus, "God", limit=limit)


def test_retrieve_limit_one_returns_single_top_result(corpus: FakeCorpus) -> None:
    results = retrieve(corpus, "God", limit=1)

    assert len(results) == 1
    assert results[0].osis == "Gen.1.1"
