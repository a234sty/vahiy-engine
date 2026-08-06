"""Deterministic search engine."""

import math
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
       exact word sequence (exact phrase matching). Ranked by occurrence
       count, ties broken by (book, chapter, verse).
    2. Keyword fallback: used only when tier 1 finds nothing anywhere in the
       corpus — the common case for natural-language questions, which rarely
       appear verbatim in any verse. The query is tokenized, common stopwords
       (English and Turkish question/function words) are dropped, and each
       verse is scored by the summed occurrences of the remaining content
       tokens — still substring-matched per token, so partial-word matching
       carries over into this tier too. Ranking (not the returned `score`,
       which stays a plain occurrence count) additionally weights each token
       by rarity across the corpus, so a verse matching a distinctive word
       (e.g. "one") outranks one that only matches a word nearly every verse
       contains (e.g. "god").

    Either tier returns the same identical, deterministic ordering across
    repeated calls with the same corpus and query.
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
    matches = [r for r in results if r.score > 0]
    matches.sort(key=lambda r: (-r.score, r.verse.book, r.verse.chapter, r.verse.verse))
    return matches


def _search_by_keywords(index: list[IndexedVerse], normalized_query: str) -> list[SearchResult]:
    tokens = [t for t in tokenize(normalized_query) if t not in STOPWORDS]
    if not tokens:
        return []

    total_verses = len(index)
    document_frequency = {
        token: sum(1 for iv in index if _count_occurrences(iv.normalized_text, token) > 0)
        for token in set(tokens)
    }

    scored: list[tuple[float, SearchResult]] = []
    for iv in index:
        occurrences = {token: _count_occurrences(iv.normalized_text, token) for token in tokens}
        raw_score = sum(occurrences.values())
        if raw_score == 0:
            continue

        rank_key = sum(
            count * _inverse_document_frequency(document_frequency[token], total_verses)
            for token, count in occurrences.items()
        )
        scored.append((rank_key, SearchResult(verse=iv.verse, score=raw_score)))

    scored.sort(
        key=lambda pair: (-pair[0], pair[1].verse.book, pair[1].verse.chapter, pair[1].verse.verse)
    )
    return [result for _, result in scored]


def _inverse_document_frequency(document_frequency: int, total_verses: int) -> float:
    """Rare terms (low document frequency, e.g. "one") weigh more than common
    ones (e.g. "god", present in nearly every verse), smoothed to stay finite
    and positive even when a term is in every verse or appears only once."""
    return math.log((total_verses + 1) / (document_frequency + 1)) + 1


def _count_occurrences(haystack: str, needle: str) -> int:
    count = 0
    start = 0
    while (index := haystack.find(needle, start)) != -1:
        count += 1
        start = index + len(needle)
    return count
