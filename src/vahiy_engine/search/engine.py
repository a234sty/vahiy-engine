"""Deterministic search engine."""

from collections.abc import Iterable
from dataclasses import dataclass

from vahiy_engine.search.index import STOPWORDS, IndexedVerse, build_index, normalize, tokenize
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.models import Verse


@dataclass(frozen=True)
class SearchResult:
    verse: Verse
    score: int


def search(corpus: CorpusClient, query: str) -> list[SearchResult]:
    """Search every verse in the corpus for `query`.

    Matching has two tiers, tried in order:

    1. Exact phrase / partial-word: a normalized substring search. A
       single-word query matches anywhere inside a word (partial-word
       matching), and a multi-word query only matches verses containing that
       exact word sequence (exact phrase matching). This tier is unchanged
       from the original implementation.
    2. Keyword fallback: used only when tier 1 finds nothing anywhere in the
       corpus — the common case for natural-language questions, which rarely
       appear verbatim in any verse. The query is tokenized, common stopwords
       (English and Turkish question/function words) are dropped, and each
       verse is scored by the summed occurrences of the remaining content
       tokens — still substring-matched per token, so partial-word matching
       carries over into this tier too.

    Either way, results are ranked by score descending, with ties broken by
    (book, chapter, verse) so identical queries always return the same order.
    """
    normalized_query = normalize(query.strip())
    if not normalized_query:
        return []

    index = build_index(corpus)

    phrase_matches = _search_by_phrase(index, normalized_query)
    if phrase_matches:
        return phrase_matches

    return _search_by_keywords(index, normalized_query)


def _search_by_phrase(index: list[IndexedVerse], normalized_query: str) -> list[SearchResult]:
    results = [
        SearchResult(verse=iv.verse, score=_count_occurrences(iv.normalized_text, normalized_query))
        for iv in index
    ]
    return _ranked(r for r in results if r.score > 0)


def _search_by_keywords(index: list[IndexedVerse], normalized_query: str) -> list[SearchResult]:
    tokens = [t for t in tokenize(normalized_query) if t not in STOPWORDS]
    if not tokens:
        return []

    results = []
    for iv in index:
        score = sum(_count_occurrences(iv.normalized_text, token) for token in tokens)
        if score > 0:
            results.append(SearchResult(verse=iv.verse, score=score))

    return _ranked(results)


def _ranked(results: Iterable[SearchResult]) -> list[SearchResult]:
    matches = list(results)
    matches.sort(key=lambda r: (-r.score, r.verse.book, r.verse.chapter, r.verse.verse))
    return matches


def _count_occurrences(haystack: str, needle: str) -> int:
    count = 0
    start = 0
    while (index := haystack.find(needle, start)) != -1:
        count += 1
        start = index + len(needle)
    return count
