"""Confidence calculation: KM-4/KM-5 in code.

Deliberately simple and deterministic for v0.1 — count-and-diversity based,
not a learned score — because "Reproducibility" (Principle 10) is best
served by a calculation any two implementations would compute identically
from the same evidence, and a scheme this legible is easy to audit and to
extend later without breaking existing traces.
"""

from vahiy_engine.reasoning.trace import (
    ConfidenceCalculation,
    ConfidenceTier,
    EvidenceItem,
    RejectedEvidenceItem,
)


def calculate_confidence(
    resolved: list[EvidenceItem], rejected: list[RejectedEvidenceItem]
) -> ConfidenceCalculation:
    distinct_types = sorted({item.citation_type for item in resolved})
    resolved_count = len(resolved)
    rejected_count = len(rejected)

    if resolved_count == 0:
        tier = ConfidenceTier.NONE
        derivation = "No evidence resolved against the currently configured corpus."
    elif resolved_count >= 3 and len(distinct_types) >= 2:
        tier = ConfidenceTier.HIGH
        derivation = (
            f"{resolved_count} sources resolved across {len(distinct_types)} "
            f"independent evidence types ({', '.join(distinct_types)})."
        )
    elif resolved_count >= 2:
        tier = ConfidenceTier.MEDIUM
        derivation = f"{resolved_count} sources resolved, {len(distinct_types)} evidence type(s)."
    else:
        tier = ConfidenceTier.LOW
        derivation = f"Only {resolved_count} source resolved."

    if rejected_count:
        derivation += (
            f" {rejected_count} additional citation(s) in the knowledge graph did not "
            "resolve against the currently configured corpus."
        )

    return ConfidenceCalculation(
        tier=tier,
        resolved_count=resolved_count,
        rejected_count=rejected_count,
        distinct_citation_types=distinct_types,
        derivation=derivation,
    )
