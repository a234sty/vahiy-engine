"""Retrieval orchestration over search and sources."""

from dataclasses import dataclass

from vahiy_engine.search.engine import SearchResult, search
from vahiy_engine.sources.client import CorpusClient


@dataclass(frozen=True)
class Source:
    """A single retrieved passage, ready to be handed to the future context builder.

    Decoupled from SearchResult on purpose: this is the stable output shape for
    every retrieval strategy (deterministic keyword search today, semantic
    retrieval later), so downstream consumers never need to know which one ran.
    """

    osis: str
    book: str
    chapter: int
    verse: int
    text: str
    score: int


def retrieve(corpus: CorpusClient, query: str, limit: int) -> list[Source]:
    """Retrieve the top `limit` ranked passages for `query` from `corpus`.

    Ranking is delegated entirely to the deterministic search engine; this
    function only truncates to the top N and adapts the results into Source
    objects. It performs no AI/LLM calls and no embedding-based reranking.

    This is the stable retrieval API: a future semantic retriever can replace
    the call to `search()` below without changing this function's signature or
    the Source shape callers depend on.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")

    results = search(corpus, query)
    return [_to_source(result) for result in results[:limit]]


def _to_source(result: SearchResult) -> Source:
    return Source(
        osis=result.verse.osis,
        book=result.verse.book,
        chapter=result.verse.chapter,
        verse=result.verse.verse,
        text=result.verse.text,
        score=result.score,
    )
