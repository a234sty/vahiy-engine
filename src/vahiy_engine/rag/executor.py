"""Executes a retrieval plan against the real corpora.

Every sub-query in the plan is run against the corpus and translation it
names. Nothing here invents, substitutes, or falls back to a different
source than the one planned: if a sub-query returns nothing, that is
recorded as nothing rather than backfilled from somewhere else.

This module also contains the only Qur'an text search in the engine. Before
it, `QuranClient.iter_ayat` existed and was called by nothing -- Qur'anic
text could reach an answer only by exact citation from the small curated
knowledge graph, which meant no question could ever discover a Qur'anic
passage it did not already name.
"""

from dataclasses import dataclass
from functools import lru_cache

from vahiy_engine.rag.planner import Facet, RetrievalPlan, SourceKind, SubQuery
from vahiy_engine.search.engine import search
from vahiy_engine.search.index import STOPWORDS, normalize, tokenize
from vahiy_engine.sources.ahit.client import VerseNotFoundError
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.osis import InvalidOsisReferenceError, parse_osis
from vahiy_engine.sources.quran.client import QuranClient


@dataclass(frozen=True)
class Candidate:
    """One retrieved passage, tagged with which sub-question found it."""

    citation: str
    citation_type: str
    text: str
    source_label: str
    facet: Facet
    subquery_id: str
    raw_score: float
    rank_in_subquery: int


@dataclass(frozen=True)
class ExecutedPlan:
    plan: RetrievalPlan
    candidates: tuple[Candidate, ...]
    empty_subqueries: tuple[str, ...]
    """Sub-queries that ran and found nothing. Distinct from the plan's
    `skipped`, which never ran at all."""


def execute_plan(
    plan: RetrievalPlan, corpus: CorpusClient, quran: QuranClient | None = None
) -> ExecutedPlan:
    candidates: list[Candidate] = []
    empty: list[str] = []

    for subquery in plan.subqueries:
        if subquery.facet is Facet.CITED_PASSAGE:
            found = _resolve_cited(subquery, corpus)
        elif subquery.source is SourceKind.BIBLE:
            found = _search_bible(subquery, corpus)
        elif subquery.source is SourceKind.QURAN and quran is not None:
            found = _search_quran(subquery, quran)
        else:
            found = []

        if found:
            candidates.extend(found)
        else:
            empty.append(
                f"{subquery.id} ({subquery.facet.value}) searched "
                f"{subquery.edition or 'the default source'} and found no match."
            )

    return ExecutedPlan(plan=plan, candidates=tuple(candidates), empty_subqueries=tuple(empty))


def _resolve_cited(subquery: SubQuery, corpus: CorpusClient) -> list[Candidate]:
    try:
        reference = parse_osis(subquery.query)
    except InvalidOsisReferenceError:
        return []

    for translation in (None, "YTC", "KJV", "WLC", "SBLGNT"):
        try:
            verse = corpus.get_verse(reference, translation=translation)
        except (VerseNotFoundError, FileNotFoundError, LookupError):
            continue
        return [
            Candidate(
                citation=verse.osis,
                citation_type="osis",
                text=verse.text,
                source_label=f"Bible ({verse.translation})",
                facet=subquery.facet,
                subquery_id=subquery.id,
                # A directly cited passage is exactly what was asked about; it
                # does not compete with keyword hits on lexical overlap.
                raw_score=1.0,
                rank_in_subquery=0,
            )
        ]
    return []


def _search_bible(subquery: SubQuery, corpus: CorpusClient) -> list[Candidate]:
    results = search(corpus, subquery.query, translation=subquery.edition)
    return [
        Candidate(
            citation=result.verse.osis,
            citation_type="osis",
            text=result.verse.text,
            source_label=f"Bible ({result.verse.translation})",
            facet=subquery.facet,
            subquery_id=subquery.id,
            raw_score=float(result.score),
            rank_in_subquery=rank,
        )
        for rank, result in enumerate(results[: subquery.limit])
    ]


def _search_quran(subquery: SubQuery, quran: QuranClient) -> list[Candidate]:
    edition = subquery.edition or "en"
    index = _quran_index(quran, edition)
    if not index:
        return []

    tokens = [t for t in tokenize(normalize(subquery.query)) if t not in STOPWORDS]
    if not tokens:
        return []

    scored: list[tuple[int, str, str]] = []
    for citation, normalized_text, original_text in index:
        score = sum(normalized_text.count(token) for token in tokens)
        if score:
            scored.append((score, citation, original_text))

    # Deterministic: highest score first, ties broken by citation order in the
    # index, which is itself sorted by surah then ayah.
    order = {citation: position for position, (citation, _, _) in enumerate(index)}
    scored.sort(key=lambda row: (-row[0], order[row[1]]))

    return [
        Candidate(
            citation=citation,
            citation_type="quran",
            text=text,
            source_label=f"Qur'an ({edition})",
            facet=subquery.facet,
            subquery_id=subquery.id,
            raw_score=float(score),
            rank_in_subquery=rank,
        )
        for rank, (score, citation, text) in enumerate(scored[: subquery.limit])
    ]


@lru_cache(maxsize=4)
def _quran_index(quran: QuranClient, edition: str) -> tuple[tuple[str, str, str], ...]:
    """(citation, normalized text, original text) for every ayah in `edition`.

    Cached for the same reason the Bible index is: 6,236 ayat are normalized
    per build, and a single question can issue more than one Qur'an
    sub-query.
    """
    try:
        ayat = list(quran.iter_ayat(edition=edition))
    except (LookupError, FileNotFoundError, ValueError):
        return ()
    return tuple(
        (f"Quran.{ayah.surah}.{ayah.ayah}", normalize(ayah.text), ayah.text) for ayah in ayat
    )
