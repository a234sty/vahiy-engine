"""The growing benchmark (v0.1 priority 5): every question below is checked
against expected reasoning (which node), evidence (how much, how diverse),
confidence (the minimum tier that evidence should earn), and reproducibility
(the same question run twice must produce an identical trace skeleton, per
FND-5's Independent Implementation Test).

To grow this benchmark: add a BenchmarkCase to BENCHMARK_CASES. That's the
whole extension surface — no other file needs to change, per Principle 8
(Extensibility).

Requires AHIT_CORPUS_ROOT pointed at a real ahit-corpus checkout; skips
cleanly otherwise, consistent with every other live-corpus test in this
suite.
"""

from dataclasses import dataclass

import pytest

from vahiy_engine.knowledge_graph.seed_data import build_seed_graph
from vahiy_engine.lexicon.ahit.client import get_lexicon_client
from vahiy_engine.reasoning.loop import ReasoningResult, run_reasoning_loop
from vahiy_engine.reasoning.trace import ConfidenceTier
from vahiy_engine.sources.ahit.client import get_ahit_client
from vahiy_engine.sources.osis import parse_osis
from vahiy_engine.sources.quran.client import get_quran_client

_CONFIDENCE_RANK = {
    ConfidenceTier.NONE: 0,
    ConfidenceTier.LOW: 1,
    ConfidenceTier.MEDIUM: 2,
    ConfidenceTier.HIGH: 3,
}


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    question: str
    expected_node_id: str
    min_confidence: ConfidenceTier
    min_resolved_evidence: int
    expected_citation_types: frozenset[str]


BENCHMARK_CASES: list[BenchmarkCase] = [
    BenchmarkCase(
        id="yhwh-english",
        question="What does YHWH mean?",
        expected_node_id="yhwh",
        min_confidence=ConfidenceTier.HIGH,
        min_resolved_evidence=3,
        expected_citation_types=frozenset({"osis", "strongs"}),
    ),
    BenchmarkCase(
        id="sabbath-english",
        question="What is the Sabbath?",
        expected_node_id="sabbath",
        min_confidence=ConfidenceTier.MEDIUM,
        min_resolved_evidence=5,
        expected_citation_types=frozenset({"osis"}),
    ),
    BenchmarkCase(
        id="sabbath-turkish",
        question="Şabat nedir?",
        expected_node_id="sabbath",
        min_confidence=ConfidenceTier.MEDIUM,
        min_resolved_evidence=5,
        expected_citation_types=frozenset({"osis"}),
    ),
    BenchmarkCase(
        id="abraham-english",
        question="Who is Abraham?",
        expected_node_id="abraham",
        min_confidence=ConfidenceTier.HIGH,
        min_resolved_evidence=6,
        expected_citation_types=frozenset({"osis", "quran"}),
    ),
    BenchmarkCase(
        id="abraham-turkish",
        question="İbrahim kimdir?",
        expected_node_id="abraham",
        min_confidence=ConfidenceTier.HIGH,
        min_resolved_evidence=6,
        expected_citation_types=frozenset({"osis", "quran"}),
    ),
]


def _requires_real_corpus() -> None:
    corpus = get_ahit_client()
    try:
        corpus.get_verse(parse_osis("Exod.3.14"), translation="WLC")
    except Exception:
        pytest.skip("AHIT_CORPUS_ROOT not pointed at a real ahit-corpus checkout")


def _run(case: BenchmarkCase) -> ReasoningResult:
    graph = build_seed_graph()
    result = run_reasoning_loop(
        graph, get_ahit_client(), get_quran_client(), get_lexicon_client(), case.question
    )
    assert result is not None, f"{case.id}: expected a KG match, got none"
    return result


@pytest.mark.parametrize("case", BENCHMARK_CASES, ids=lambda c: c.id)
def test_reasoning(case: BenchmarkCase) -> None:
    _requires_real_corpus()
    result = _run(case)

    assert result.trace.detected_intent.node_id == case.expected_node_id


@pytest.mark.parametrize("case", BENCHMARK_CASES, ids=lambda c: c.id)
def test_evidence(case: BenchmarkCase) -> None:
    _requires_real_corpus()
    result = _run(case)

    assert result.trace.confidence.resolved_count >= case.min_resolved_evidence
    assert result.trace.confidence.rejected_count == 0, (
        f"{case.id}: seed data cites something the real corpus doesn't resolve "
        f"({result.trace.evidence_rejected})"
    )
    actual_types = {e.citation_type for e in result.trace.evidence_retrieved}
    assert case.expected_citation_types <= actual_types


@pytest.mark.parametrize("case", BENCHMARK_CASES, ids=lambda c: c.id)
def test_confidence(case: BenchmarkCase) -> None:
    _requires_real_corpus()
    result = _run(case)

    actual_rank = _CONFIDENCE_RANK[result.trace.confidence.tier]
    minimum_rank = _CONFIDENCE_RANK[case.min_confidence]
    assert actual_rank >= minimum_rank, (
        f"{case.id}: confidence {result.trace.confidence.tier} is below the "
        f"minimum {case.min_confidence}"
    )


@pytest.mark.parametrize("case", BENCHMARK_CASES, ids=lambda c: c.id)
def test_reproducibility(case: BenchmarkCase) -> None:
    # FND-5's Independent Implementation Test, operationalized: the same
    # question against the same evidence must produce the same trace
    # skeleton on every run -- not identical prose (nothing here generates
    # prose), but identical intent, evidence set, and confidence.
    _requires_real_corpus()
    first = _run(case)
    second = _run(case)

    assert first.trace.detected_intent == second.trace.detected_intent
    assert first.trace.confidence == second.trace.confidence
    assert {e.citation for e in first.trace.evidence_retrieved} == {
        e.citation for e in second.trace.evidence_retrieved
    }
