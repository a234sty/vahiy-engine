"""The full 500-question bank: all five categories concatenated.

This is the single import surface `scripts/run_benchmark.py` uses. Adding a
sixth category means adding one more file and one more line here — no other
file needs to change, per Principle 8 (Extensibility).
"""

from tests.benchmark.question_bank.adversarial import ADVERSARIAL_QUESTIONS
from tests.benchmark.question_bank.cross_scripture import CROSS_SCRIPTURE_QUESTIONS
from tests.benchmark.question_bank.historical import HISTORICAL_QUESTIONS
from tests.benchmark.question_bank.linguistic import LINGUISTIC_QUESTIONS
from tests.benchmark.question_bank.schema import BenchmarkQuestion
from tests.benchmark.question_bank.theological import THEOLOGICAL_QUESTIONS

ALL_QUESTIONS: list[BenchmarkQuestion] = [
    *THEOLOGICAL_QUESTIONS,
    *HISTORICAL_QUESTIONS,
    *LINGUISTIC_QUESTIONS,
    *CROSS_SCRIPTURE_QUESTIONS,
    *ADVERSARIAL_QUESTIONS,
]

assert len(ALL_QUESTIONS) == 500
assert len({q.id for q in ALL_QUESTIONS}) == 500, "duplicate BenchmarkQuestion id detected"
