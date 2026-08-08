"""Chooses which ranked candidates actually reach the answer.

Ranking orders candidates; selection decides how many survive and enforces
two things ordering alone cannot:

- a budget, so a narrow question is not flooded and a broad one is not
  starved,
- facet coverage, so a comparative question cannot come back with ten
  biblical passages and nothing from the Qur'an merely because the Bible
  corpus is four times larger and therefore wins on raw hit count.

The second is the point. Without a reserved slot per facet, "compare X in
the Bible and the Qur'an" silently degrades into "here is what the Bible
says", which is precisely the failure the engine is supposed to prevent.
"""

from dataclasses import dataclass

from vahiy_engine.rag.planner import Facet
from vahiy_engine.rag.reranking import RankedCandidate
from vahiy_engine.reasoning.intent import Depth
from vahiy_engine.reasoning.trace import EvidenceItem

_BUDGETS: dict[Depth, int] = {Depth.NARROW: 4, Depth.STANDARD: 8, Depth.BROAD: 16}

# Every facet that produced anything is guaranteed at least this many slots
# before the budget is filled by score alone.
_RESERVED_PER_FACET = 2


@dataclass(frozen=True)
class SelectedEvidence:
    items: tuple[EvidenceItem, ...]
    selected: tuple[RankedCandidate, ...]
    dropped_for_budget: int
    facet_counts: dict[str, int]


def select_evidence(ranked: tuple[RankedCandidate, ...], depth: Depth) -> SelectedEvidence:
    """Pick the evidence that reaches the answer, under a depth-set budget."""
    budget = _BUDGETS[depth]

    # Deduplicate by citation, keeping the highest-scoring occurrence. The
    # same verse can be found by more than one sub-query; it is still one
    # piece of evidence and must not occupy two slots or be counted twice by
    # the confidence calculation downstream.
    best_by_citation: dict[str, RankedCandidate] = {}
    for item in ranked:
        existing = best_by_citation.get(item.candidate.citation)
        if existing is None or item.score > existing.score:
            best_by_citation[item.candidate.citation] = item
    unique = sorted(
        best_by_citation.values(),
        key=lambda r: (-r.score, r.candidate.citation),
    )

    by_facet: dict[Facet, list[RankedCandidate]] = {}
    for item in unique:
        by_facet.setdefault(item.candidate.facet, []).append(item)

    chosen: list[RankedCandidate] = []
    taken: set[str] = set()

    # Pass one: reserve slots so every facet that found something is
    # represented, in a fixed facet order so the result is deterministic.
    for facet in sorted(by_facet, key=lambda f: f.value):
        for item in by_facet[facet][:_RESERVED_PER_FACET]:
            if len(chosen) >= budget:
                break
            chosen.append(item)
            taken.add(item.candidate.citation)

    # Pass two: fill the remaining budget by score.
    for item in unique:
        if len(chosen) >= budget:
            break
        if item.candidate.citation in taken:
            continue
        chosen.append(item)
        taken.add(item.candidate.citation)

    chosen.sort(key=lambda r: (-r.score, r.candidate.citation))

    facet_counts: dict[str, int] = {}
    for item in chosen:
        facet_counts[item.candidate.facet.value] = (
            facet_counts.get(item.candidate.facet.value, 0) + 1
        )

    return SelectedEvidence(
        items=tuple(_to_evidence(item) for item in chosen),
        selected=tuple(chosen),
        dropped_for_budget=max(0, len(unique) - len(chosen)),
        facet_counts=facet_counts,
    )


def _to_evidence(ranked: RankedCandidate) -> EvidenceItem:
    candidate = ranked.candidate
    return EvidenceItem(
        citation=candidate.citation,
        citation_type=candidate.citation_type,
        text=candidate.text,
        role="retrieved",
        note=(f"Found by sub-question '{candidate.facet.value}' in " f"{candidate.source_label}."),
    )
