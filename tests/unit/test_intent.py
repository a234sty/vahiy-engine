"""Unit tests for question analysis: intent, depth, complexity, language.

Pure and deterministic -- no corpus, no network, no model call.
"""

import pytest

from vahiy_engine.reasoning.intent import (
    Complexity,
    Depth,
    IntentType,
    analyze_question,
)


@pytest.mark.parametrize(
    "question,expected",
    [
        ("Yuhanna 3:16 ne diyor?", "tr"),
        ("Şabat nedir?", "tr"),
        ("İbrahim kimdir?", "tr"),
        ("hayah kelimesi ne anlama gelir?", "tr"),
        ("What does YHWH mean?", "en"),
        ("Who is Abraham?", "en"),
    ],
)
def test_language_is_detected_from_letters_or_function_words(question: str, expected: str) -> None:
    assert analyze_question(question).language == expected


@pytest.mark.parametrize(
    "question,expected",
    [
        ("What does Genesis 1:1 say?", IntentType.VERSE_EXPLANATION),
        ("Yuhanna 3:16 ne diyor?", IntentType.VERSE_EXPLANATION),
        ("What does the Greek word kyrios mean?", IntentType.WORD_MEANING),
        ("Compare the Sabbath in the Bible and the Quran", IntentType.COMPARISON),
        ("When was the Exodus dated?", IntentType.HISTORICAL_EXPLANATION),
        ("How is this verse translated?", IntentType.TRANSLATION_HELP),
        ("What is God?", IntentType.DOCTRINAL_EXPLANATION),
        ("Who is Abraham?", IntentType.DOCTRINAL_EXPLANATION),
        ("asdkfj qqqq", IntentType.UNKNOWN),
    ],
)
def test_intent_is_classified_from_question_markers(question: str, expected: IntentType) -> None:
    assert analyze_question(question).intent is expected


def test_turkish_suffixed_comparison_words_are_recognized() -> None:
    # Real miss, found by running the classifier on real questions rather
    # than on the vocabulary it was written against: the marker list holds
    # "fark" and "ahit", but a Turkish speaker writes "farklı" and
    # "Ahit'te", and exact set membership silently failed on both.
    analysis = analyze_question("Mesih kavramı Kuran ve Yeni Ahitte nasıl farklı?")

    assert analysis.intent is IntentType.COMPARISON
    assert analysis.complexity is Complexity.DEEP


def test_short_english_words_do_not_prefix_match_spuriously() -> None:
    # The suffix rule must not fire on short stems: "sin" is a listed
    # concept, but "single" is not a theological question.
    assert analyze_question("Is this a single item?").intent is IntentType.UNKNOWN


def test_person_question_is_answered_at_standard_depth_not_broad() -> None:
    # "İsa kimdir?" should get a scaled answer, not fourteen screens.
    analysis = analyze_question("İsa kimdir?")

    assert analysis.intent is IntentType.DOCTRINAL_EXPLANATION
    assert analysis.depth is Depth.STANDARD


def test_broad_concept_question_earns_broad_depth() -> None:
    assert analyze_question("Tanrı nedir?").depth is Depth.BROAD


def test_explicit_citation_narrows_depth_even_with_a_meaning_marker() -> None:
    analysis = analyze_question("What does Genesis 1:1 mean?")

    assert analysis.depth is Depth.NARROW
    assert analysis.complexity is Complexity.SIMPLE


def test_two_named_traditions_make_a_question_deep_without_a_compare_verb() -> None:
    analysis = analyze_question("Does the Quran describe Abraham as the Torah does?")

    assert analysis.intent is IntentType.COMPARISON
    assert analysis.complexity is Complexity.DEEP


def test_long_multi_clause_question_is_deep() -> None:
    analysis = analyze_question(
        "Is there an ontological difference between the Christology of Paul and "
        "the Christology of John, and if so what follows for how the doctrine "
        "of the incarnation was later formulated in the creeds?"
    )

    assert analysis.complexity is Complexity.DEEP


def test_analysis_is_deterministic() -> None:
    # Reproducibility is the reason this layer is rules rather than a model
    # call; a test that would fail if that ever changed is worth having.
    question = "Mesih kavramı Kuran ve Yeni Ahitte nasıl farklı?"

    assert analyze_question(question) == analyze_question(question)


def test_signals_record_which_rules_fired() -> None:
    analysis = analyze_question("Compare the Sabbath in the Bible and the Quran")

    assert "language:en" in analysis.signals
    assert any("comparison" in signal or "tradition" in signal for signal in analysis.signals)


def test_empty_question_does_not_crash() -> None:
    analysis = analyze_question("")

    assert analysis.intent is IntentType.UNKNOWN
    assert analysis.language == "en"
