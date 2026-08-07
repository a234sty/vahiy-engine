#!/usr/bin/env python3
"""Run the 500-question scientific benchmark live and report honest results.

This is deliberately NOT a pytest-collected file. The 500-question bank
(tests/benchmark/question_bank/) currently has gold expectations for only
~125 of its 500 cases -- the rest are real, uncovered questions left at
coverage_status="not_yet_covered" rather than padded with invented
expectations (see question_bank/schema.py). Making that a pytest suite
would either fail CI permanently on ~375 cases with no ground truth to
fail against, or silently skip them -- both hide the actual measurement.
Instead this script is the measurement instrument: it runs every question
through the real reasoning loop, scores what has a gold expectation, and
reports what doesn't as NOT_YET_COVERED rather than fabricating a verdict
for it. The existing tests/benchmark/test_reasoning_benchmark.py (20 cases)
remains the CI-gating regression suite; this script is separate and is run
by a human (or CI job) that wants the full scientific picture.

Usage:
    AHIT_CORPUS_ROOT=/path/to/ahit-corpus python scripts/run_benchmark.py
    AHIT_CORPUS_ROOT=/path/to/ahit-corpus python scripts/run_benchmark.py --category theological
    AHIT_CORPUS_ROOT=/path/to/ahit-corpus python scripts/run_benchmark.py --verbose

Requires AHIT_CORPUS_ROOT pointed at a real ahit-corpus checkout (same
requirement as every other live-corpus test in this repo); exits with a
clear message, not a stack trace, if it isn't set correctly.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tests.benchmark.question_bank.all_questions import ALL_QUESTIONS
from tests.benchmark.question_bank.schema import BenchmarkQuestion

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


@dataclass
class CaseResult:
    question: BenchmarkQuestion
    status: str  # "PASS" | "FAIL" | "NOT_YET_COVERED" | "ERROR"
    reasons: list[str] = field(default_factory=list)
    reproducible: bool | None = None


def _verify_real_corpus() -> None:
    corpus = get_ahit_client()
    try:
        corpus.get_verse(parse_osis("Exod.3.14"), translation="WLC")
    except Exception:
        print(
            "AHIT_CORPUS_ROOT is not pointed at a real ahit-corpus checkout.\n"
            "This benchmark measures the engine against real evidence, so it "
            "refuses to run against missing/fake data. Set AHIT_CORPUS_ROOT and "
            "retry.",
            file=sys.stderr,
        )
        sys.exit(1)


def _run_once(question: BenchmarkQuestion) -> ReasoningResult | None:
    graph = build_seed_graph()
    return run_reasoning_loop(
        graph, get_ahit_client(), get_quran_client(), get_lexicon_client(), question.question
    )


def _check_reproducibility(question: BenchmarkQuestion, first: ReasoningResult | None) -> bool:
    second = _run_once(question)
    if first is None or second is None:
        return first is None and second is None
    if first.trace.detected_intent != second.trace.detected_intent:
        return False
    if first.trace.confidence != second.trace.confidence:
        return False
    first_citations = {e.citation for e in first.trace.evidence_retrieved}
    second_citations = {e.citation for e in second.trace.evidence_retrieved}
    return first_citations == second_citations


def _score(question: BenchmarkQuestion) -> CaseResult:
    if question.coverage_status == "not_yet_covered":
        return CaseResult(question=question, status="NOT_YET_COVERED")

    try:
        result = _run_once(question)
    except Exception as exc:  # noqa: BLE001 - a crash on any input is itself a finding
        return CaseResult(
            question=question, status="ERROR", reasons=[f"{type(exc).__name__}: {exc}"]
        )

    reasons: list[str] = []

    if question.expects_no_match:
        if result is not None:
            reasons.append(
                f"expected no match, but matched node '{result.trace.detected_intent.node_id}'"
            )
    else:
        if result is None:
            reasons.append(f"expected a match on node '{question.expected_node_id}', got none")
        else:
            if result.trace.detected_intent.node_id != question.expected_node_id:
                reasons.append(
                    f"expected node '{question.expected_node_id}', "
                    f"got '{result.trace.detected_intent.node_id}'"
                )
            if question.expected_min_confidence is not None:
                actual_rank = _CONFIDENCE_RANK[result.trace.confidence.tier]
                min_rank = _CONFIDENCE_RANK[question.expected_min_confidence]
                if actual_rank < min_rank:
                    reasons.append(
                        f"confidence {result.trace.confidence.tier} below minimum "
                        f"{question.expected_min_confidence}"
                    )
            actual_citations = {e.citation for e in result.trace.evidence_retrieved}
            missing = set(question.expected_evidence_citations) - actual_citations
            if missing:
                reasons.append(f"missing expected evidence citations: {sorted(missing)}")

    reproducible = _check_reproducibility(question, result)
    if not reproducible:
        reasons.append("trace was not reproducible across two runs")

    status = "PASS" if not reasons else "FAIL"
    return CaseResult(question=question, status=status, reasons=reasons, reproducible=reproducible)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", default=None, help="Only run one category")
    parser.add_argument(
        "--verbose", action="store_true", help="Print every case, not just failures"
    )
    args = parser.parse_args()

    _verify_real_corpus()

    questions = ALL_QUESTIONS
    if args.category:
        questions = [q for q in questions if q.category == args.category]
        if not questions:
            print(f"No questions found for category '{args.category}'", file=sys.stderr)
            sys.exit(1)

    results = [_score(q) for q in questions]

    by_category: dict[str, list[CaseResult]] = {}
    for r in results:
        by_category.setdefault(r.question.category, []).append(r)

    print("=" * 72)
    print("VAHIY ENGINE -- SCIENTIFIC BENCHMARK RESULTS")
    print("=" * 72)

    overall = Counter(r.status for r in results)

    for category, cat_results in sorted(by_category.items()):
        counts = Counter(r.status for r in cat_results)
        scored = counts["PASS"] + counts["FAIL"] + counts["ERROR"]
        pass_rate = f"{counts['PASS']}/{scored}" if scored else "n/a"
        print(
            f"\n{category:>16}: {len(cat_results)} questions | "
            f"gold-scored {scored} (pass {pass_rate}) | "
            f"not_yet_covered {counts['NOT_YET_COVERED']} | "
            f"errors {counts['ERROR']}"
        )
        for r in cat_results:
            if r.status == "NOT_YET_COVERED" and not args.verbose:
                continue
            if r.status == "PASS" and not args.verbose:
                continue
            marker = {"PASS": "PASS", "FAIL": "FAIL", "ERROR": "ERR ", "NOT_YET_COVERED": "n/a "}[
                r.status
            ]
            line = f"    [{marker}] {r.question.id}: {r.question.question!r}"
            print(line)
            for reason in r.reasons:
                print(f"             - {reason}")

    scored_total = overall["PASS"] + overall["FAIL"] + overall["ERROR"]
    print("\n" + "=" * 72)
    print(f"TOTAL: {len(results)} questions")
    print(
        f"  gold-scored:      {scored_total} "
        f"(PASS {overall['PASS']}, FAIL {overall['FAIL']}, ERROR {overall['ERROR']})"
    )
    print(f"  not_yet_covered:  {overall['NOT_YET_COVERED']}")
    if scored_total:
        print(f"  pass rate (of gold-scored only): {overall['PASS'] / scored_total:.1%}")
    print(
        "\nnot_yet_covered questions are real, unanswered questions -- they are "
        "not counted as failures because there is no fabricated gold expectation "
        "to fail against. Growing the Knowledge Graph's coverage (not this "
        "script) is what turns them into scored cases."
    )
    print("=" * 72)

    if overall["FAIL"] or overall["ERROR"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
