"""Deterministic search engine."""

from dataclasses import dataclass

from vahiy_engine.search.index import build_index, normalize
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.models import Verse


@dataclass(frozen=True)
class SearchResult:
    verse: Verse
    score: int


def search(corpus: CorpusClient, query: str) -> list[SearchResult]:
    """Search every verse in the corpus for `query`.

    Matching is a normalized substring search: a single-word query matches
    anywhere inside a word (partial-word matching), and a multi-word query only
    matches verses containing that exact word sequence (exact phrase matching).
    Both fall out of the same substring check, so no separate mode is needed.

    Results are ranked by occurrence count, descending, with ties broken by
    (book, chapter, verse) so identical queries always return the same order.
    """
    normalized_query = normalize(query.strip())
    if not normalized_query:
        return []

    results = [
        SearchResult(verse=iv.verse, score=_count_occurrences(iv.normalized_text, normalized_query))
        for iv in build_index(corpus)
    ]
    matches = [r for r in results if r.score > 0]
    matches.sort(key=lambda r: (-r.score, r.verse.book, r.verse.chapter, r.verse.verse))
    return matches


def _count_occurrences(haystack: str, needle: str) -> int:
    count = 0
    start = 0
    while (index := haystack.find(needle, start)) != -1:
        count += 1
        start = index + len(needle)
    return count
