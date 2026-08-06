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
        assert set(item.keys()) == {"osis", "chapter", "verse", "text", "score", "translation"}
        assert item["score"] >= 1


def test_search_supports_partial_word_matching() -> None:
    response = client.get("/search", params={"query": "begotten"})

    osis_refs = {item["osis"] for item in response.json()["results"]}
    assert osis_refs == {"John.1.14", "John.3.16"}


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
    assert [item["score"] for item in first] == [2, 1, 1, 1, 1, 1, 1, 1, 1, 1]


def test_search_returns_empty_results_for_no_matches() -> None:
    response = client.get("/search", params={"query": "xyznonexistentword"})

    assert response.status_code == 200
    assert response.json()["results"] == []


def test_search_requires_non_empty_query() -> None:
    response = client.get("/search", params={"query": ""})

    assert response.status_code == 422


def test_search_falls_back_to_keywords_for_a_natural_language_question() -> None:
    # This exact sentence appears nowhere in the corpus, but its content words
    # ("created", "heaven", "earth") do — the keyword fallback surfaces the
    # relevant verses where a pure exact-phrase search would find nothing.
    # Acts.4.12 ("...under heaven...") only shares the common word "heaven",
    # so it ranks below Gen.1.2, which shares the rarer word "earth" too.
    response = client.get("/search", params={"query": "Who created the heaven and the earth?"})

    body = response.json()
    assert [item["osis"] for item in body["results"]] == ["Gen.1.1", "Acts.4.12", "Gen.1.2"]
    assert [item["score"] for item in body["results"]] == [3, 1, 1]


def test_search_finds_relevant_verses_for_previously_unanswerable_theological_questions() -> None:
    # These questions used to return nothing at all — not because of a ranking
    # bug, but because the sample corpus had no verses on these topics. Now
    # that it does, the keyword fallback correctly surfaces them.
    cases = {
        "Who is Jesus?": {"John.11.25", "John.14.6", "Mark.12.29", "Matt.1.21", "Rom.10.9"},
        "What is faith?": {"Eph.2.8", "Heb.11.1"},
        "How can I be saved?": {"Acts.4.12", "Eph.2.8", "Rom.10.9"},
        "What happens after death?": {"Rev.21.4"},
    }
    for query, expected_osis in cases.items():
        response = client.get("/search", params={"query": query})
        osis_refs = {item["osis"] for item in response.json()["results"]}
        assert osis_refs == expected_osis, query


def test_search_ranks_discriminative_verses_above_generic_ones_for_god_is_one() -> None:
    # This is the exact case that used to rank Gen.1.1/John.3.16 first: "god"
    # appears in nearly every verse, so without rarity weighting it dominated
    # the ranking. Deut.6.4 and Mark.12.29 both also match the much rarer
    # word "one" and now correctly outrank the generic "god"-only matches.
    response = client.get("/search", params={"query": "Does the Bible say God is one?"})

    osis_refs = [item["osis"] for item in response.json()["results"]]
    assert osis_refs.index("Deut.6.4") < osis_refs.index("Gen.1.1")
    assert osis_refs.index("Mark.12.29") < osis_refs.index("John.3.16")


def test_search_ignores_punctuation_differences_for_exact_phrase_matching() -> None:
    # The verse has a comma ("Word, and") this query omits.
    response = client.get("/search", params={"query": "the Word and the Word was with God"})

    osis_refs = {item["osis"] for item in response.json()["results"]}
    assert osis_refs == {"John.1.1"}
