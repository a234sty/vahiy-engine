"""The shape of one benchmark case.

Two honesty rules this schema exists to enforce:

1. `expected_evidence_citations` is never invented. A case only gets real
   citations here if those citations already exist, verified, in
   knowledge_graph/seed_data.py — reusing exactly the same no-fabrication
   discipline that governs the seed data itself (ID-5). A question the
   Knowledge Graph doesn't cover yet gets `coverage_status="not_yet_covered"`
   and an empty evidence list, not a plausible-sounding guess.

2. `expects_no_match=True` is a real, first-class pass condition, not an
   afterthought. Several categories (adversarial especially) are testing
   whether the engine correctly declines rather than fabricates — for those
   cases, `run_reasoning_loop` returning None is the CORRECT outcome, and
   the benchmark runner must score it as a pass, not treat "no answer" as
   automatic failure.
"""

from dataclasses import dataclass, field
from typing import Literal

from vahiy_engine.reasoning.trace import ConfidenceTier

Category = Literal["theological", "historical", "linguistic", "cross_scripture", "adversarial"]
CoverageStatus = Literal["gold", "not_yet_covered"]


@dataclass(frozen=True)
class BenchmarkQuestion:
    id: str
    category: Category
    question: str
    language: str = "en"
    coverage_status: CoverageStatus = "not_yet_covered"
    expected_node_id: str | None = None
    expects_no_match: bool = False
    expected_min_confidence: ConfidenceTier | None = None
    expected_evidence_citations: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""

    def __post_init__(self) -> None:
        if self.coverage_status == "gold":
            if not self.expects_no_match and self.expected_node_id is None:
                raise ValueError(f"{self.id}: gold case needs expected_node_id or expects_no_match")
        if self.coverage_status == "not_yet_covered" and self.expected_evidence_citations:
            raise ValueError(
                f"{self.id}: not_yet_covered case must not carry invented evidence citations"
            )
