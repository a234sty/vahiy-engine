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


def test_search_prefers_exact_phrase_over_keyword_fallback(corpus: FakeCorpus) -> None:
    # "beginning the In" is a reordering of a phrase that DOES appear verbatim
    # elsewhere ("In the beginning"), so it has zero exact-phrase substring
    # matches — deliberately, to prove tier 1 (phrase) is order-sensitive. That
    # used to mean zero results overall. Now tier 2 (keyword fallback) catches
    # it via its one real content word, "beginning" — the same behavior a
    # natural-language question relies on. This is the one intentional,
    # documented behavior change in this change: a scrambled phrase now
    # resolves the same way any other multi-word natural-language query would.
    results = search(corpus, "beginning the In")

    assert {r.verse.osis for r in results} == {"Gen.1.1", "John.1.1"}


def test_search_exact_phrase_still_wins_over_keyword_fallback_when_present(
    corpus: FakeCorpus,
) -> None:
    # When the exact phrase IS present verbatim, tier 1 alone determines the
    # result set — tier 2 never runs, so this is unchanged from before.
    results = search(corpus, "In the beginning")

    assert {r.verse.osis for r in results} == {"Gen.1.1", "John.1.1"}


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


# --- Keyword fallback: natural-language questions that don't appear verbatim ---


def test_search_falls_back_to_keywords_for_a_natural_language_question(corpus: FakeCorpus) -> None:
    # The full question never appears verbatim in any verse, but its one real
    # content word ("beginning") does — this is exactly the gap the keyword
    # fallback closes for real user questions.
    results = search(corpus, "What is the beginning of the Bible")

    assert {r.verse.osis for r in results} == {"Gen.1.1", "John.1.1"}


def test_search_keyword_fallback_ignores_pure_stopword_queries(corpus: FakeCorpus) -> None:
    results = search(corpus, "What is it")

    assert results == []


def test_search_keyword_fallback_scores_by_summed_token_occurrences(corpus: FakeCorpus) -> None:
    # Word order differs from any verse, so tier 1 finds nothing; tier 2 scores
    # each verse by how many of {"god", "beginning"} it contains, and how often.
    results = search(corpus, "God beginning")

    assert [r.verse.osis for r in results] == ["Gen.1.1", "John.1.1", "John.3.16"]
    assert [r.score for r in results] == [2, 2, 1]


def test_search_keyword_fallback_supports_partial_word_matching_per_token(
    corpus: FakeCorpus,
) -> None:
    # "begot" and "son" are each matched as substrings, same as tier 1 does for
    # a single-word query — "begot" partially matches "begotten".
    results = search(corpus, "the begot son")

    assert [r.verse.osis for r in results] == ["John.3.16"]
    assert results[0].score == 2


def test_search_ignores_punctuation_differences_for_exact_phrase_matching(
    corpus: FakeCorpus,
) -> None:
    # The verse text has a comma ("Word, and") that this query omits; without
    # punctuation-insensitive normalization this wouldn't match at all.
    results = search(corpus, "the Word and the Word was with God")

    assert [r.verse.osis for r in results] == ["John.1.1"]


def test_search_keyword_fallback_weights_rare_terms_above_common_ones() -> None:
    # "Aaa" and "Zzz" tie at raw score 2 ("Aaa" has two "god"s; "Zzz" has one
    # "god" and one "one"). Without rarity weighting, the (book, chapter,
    # verse) tie-break would rank "Aaa" first purely alphabetically. "one" is
    # far rarer across this corpus than "god" (appears in 1 of 4 verses vs.
    # all 4), so it should carry more weight — "Zzz" must rank first despite
    # sorting last alphabetically, proving the ranking is rarity-driven and
    # not just an accident of the tie-break order.
    corpus = FakeCorpus(
        [
            make_verse("Aaa", 1, 1, "God is great and God is good"),
            make_verse("Zzz", 1, 1, "our God is one"),
            make_verse("Mmm", 1, 1, "God is with us"),
            make_verse("Nnn", 1, 1, "the God of our fathers"),
        ]
    )

    results = search(corpus, "God one")

    assert [r.verse.osis for r in results][:2] == ["Zzz.1.1", "Aaa.1.1"]
    assert [r.score for r in results][:2] == [2, 2]
