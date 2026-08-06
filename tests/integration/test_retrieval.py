"""Integration tests for the retrieval layer against the real Ahit Corpus files."""

from vahiy_engine.rag.retrieval import Source, retrieve
from vahiy_engine.sources.ahit.client import get_ahit_client


def test_retrieve_reads_real_sample_corpus_from_disk() -> None:
    client = get_ahit_client()

    results = retrieve(client, "beginning", limit=10)

    assert {r.osis for r in results} == {"Gen.1.1", "John.1.1"}
    assert all(isinstance(r, Source) for r in results)


def test_retrieve_respects_limit_against_real_corpus() -> None:
    client = get_ahit_client()

    results = retrieve(client, "God", limit=1)

    assert len(results) == 1


def test_retrieve_ranking_matches_across_multiple_books() -> None:
    client = get_ahit_client()

    results = retrieve(client, "God", limit=100)

    assert [r.osis for r in results] == [
        "John.1.1",
        "Deut.6.4",
        "Eph.2.8",
        "Gen.1.1",
        "Gen.1.2",
        "Gen.1.3",
        "John.3.16",
        "Mark.12.29",
        "Rev.21.4",
        "Rom.10.9",
    ]
    assert [r.score for r in results] == [2, 1, 1, 1, 1, 1, 1, 1, 1, 1]
