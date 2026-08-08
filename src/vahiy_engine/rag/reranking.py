"""Deterministic reranking of retrieved candidates.

Candidates arrive from several sub-queries whose raw scores are not
comparable: a Qur'an keyword count and a Bible keyword count are computed
over different corpora of different sizes, and a directly cited passage
carries no keyword score at all. Ranking them by raw score would let the
largest corpus win on volume.

So each candidate is scored on three explainable components:

- position within its own sub-query, which is the only place its raw score
  is meaningfully comparable,
- the facet's weight, because a passage the question actually cited outranks
  one that merely shares vocabulary,
- a diversity penalty, because ten verses from one chapter answer a question
  worse than five verses from five books.

No learned model and no embeddings: the same candidates in the same order
always produce the same ranking, which is what makes an answer reproducible
and a ranking disputable.
"""

from dataclasses import dataclass

from vahiy_engine.rag.executor import Candidate
from vahiy_engine.rag.planner import Facet

# A cited passage is what was asked about. Cross-corpus facets sit above bare
# keyword usage because they are the ones a comparative question needs and
# the ones a single-corpus ranking would otherwise bury.
_FACET_WEIGHTS: dict[Facet, float] = {
    Facet.CITED_PASSAGE: 3.0,
    Facet.ORIGINAL_LANGUAGE: 1.6,
    Facet.QURAN_USAGE: 1.4,
    Facet.SCRIPTURE_USAGE: 1.0,
}

_DIVERSITY_PENALTY = 0.35


@dataclass(frozen=True)
class RankedCandidate:
    candidate: Candidate
    score: float
    explanation: str


def _group_key(candidate: Candidate) -> str:
    """The unit diversity is measured over: a biblical book, or a surah."""
    head, _, rest = candidate.citation.partition(".")
    if candidate.citation_type == "quran":
        surah = rest.split(".")[0] if rest else "?"
        return f"quran:{surah}"
    return f"bible:{head}"


def rerank(candidates: tuple[Candidate, ...]) -> tuple[RankedCandidate, ...]:
    """Rank candidates across sub-queries, most useful first."""
    if not candidates:
        return ()

    # Position score: 1.0 for a sub-query's best hit, decaying with rank, so
    # a candidate competes on how well it answered its own sub-question
    # rather than on a raw count from a corpus of arbitrary size.
    scored: list[RankedCandidate] = []
    for candidate in candidates:
        position = 1.0 / (1.0 + candidate.rank_in_subquery)
        weight = _FACET_WEIGHTS.get(candidate.facet, 1.0)
        scored.append(
            RankedCandidate(
                candidate=candidate,
                score=position * weight,
                explanation=(
                    f"facet={candidate.facet.value} (x{weight:g}), "
                    f"rank {candidate.rank_in_subquery + 1} in {candidate.subquery_id}"
                ),
            )
        )

    scored.sort(key=lambda r: (-r.score, r.candidate.citation))

    # Diversity: each additional candidate from an already-represented book or
    # surah is progressively discounted, applied after the initial ordering so
    # the penalty depends only on that deterministic order.
    seen: dict[str, int] = {}
    adjusted: list[RankedCandidate] = []
    for ranked in scored:
        key = _group_key(ranked.candidate)
        repeats = seen.get(key, 0)
        seen[key] = repeats + 1
        if repeats == 0:
            adjusted.append(ranked)
            continue
        penalty = _DIVERSITY_PENALTY * repeats
        adjusted.append(
            RankedCandidate(
                candidate=ranked.candidate,
                score=ranked.score / (1.0 + penalty),
                explanation=f"{ranked.explanation}; {repeats} earlier hit(s) from {key}",
            )
        )

    adjusted.sort(key=lambda r: (-r.score, r.candidate.citation))
    return tuple(adjusted)
