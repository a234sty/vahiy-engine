"""Integration tests for the /search endpoint."""

from fastapi.testclient import TestClient

from vahiy_engine.main import app

client = TestClient(app)


def test_search_returns_matching_verses_across_books() -> None:
    response = client.get("/search", params={"query": "beginning"})

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "beginning"
    osis_refs = {item["osis"] for item in body["results"]}
    assert osis_refs == {"Gen.1.1", "John.1.1"}


def test_search_results_include_required_fields() -> None:
    response = client.get("/search", params={"query": "beginning"})

    for item in response.json()["results"]:
        assert set(item.keys()) == {"osis", "chapter", "verse", "text", "score"}
        assert item["score"] >= 1


def test_search_supports_partial_word_matching() -> None:
    response = client.get("/search", params={"query": "begotten"})

    osis_refs = {item["osis"] for item in response.json()["results"]}
    assert osis_refs == {"John.3.16"}


def test_search_supports_exact_phrase_matching() -> None:
    response = client.get("/search", params={"query": "God so loved the world"})

    osis_refs = {item["osis"] for item in response.json()["results"]}
    assert osis_refs == {"John.3.16"}


def test_search_is_case_insensitive() -> None:
    lower = client.get("/search", params={"query": "beginning"}).json()["results"]
    upper = client.get("/search", params={"query": "BEGINNING"}).json()["results"]

    assert lower == upper


def test_search_results_are_deterministically_ordered() -> None:
    first = client.get("/search", params={"query": "God"}).json()["results"]
    second = client.get("/search", params={"query": "God"}).json()["results"]

    assert first == second
    # John.1.1 mentions "God" twice, everything else once, so it ranks first;
    # the remaining score-1 ties are broken by (book, chapter, verse) order.
    assert [item["osis"] for item in first] == [
        "John.1.1",
        "Gen.1.1",
        "Gen.1.2",
        "Gen.1.3",
        "John.3.16",
    ]
    assert [item["score"] for item in first] == [2, 1, 1, 1, 1]


def test_search_returns_empty_results_for_no_matches() -> None:
    response = client.get("/search", params={"query": "xyznonexistentword"})

    assert response.status_code == 200
    assert response.json()["results"] == []


def test_search_requires_non_empty_query() -> None:
    response = client.get("/search", params={"query": ""})

    assert response.status_code == 422
