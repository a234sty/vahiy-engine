"""Unit tests for the prompt contract layer: user-turn rendering, output
contract selection, and source preferences."""

import pytest

from vahiy_engine.pipeline.prompt_builder import (
    AnswerFormat,
    Corpus,
    PromptInputs,
    UserPreferences,
    build_user_prompt,
    load_response_contract,
)
from vahiy_engine.reasoning.intent import analyze_question


def make_inputs(**overrides: object) -> PromptInputs:
    defaults: dict[str, object] = {
        "question": "İbrahim kimdir?",
        "analysis": analyze_question("İbrahim kimdir?"),
        "evidence": "[Gen.12.1] (Bible)\nRab Avram'a dedi",
    }
    defaults.update(overrides)
    return PromptInputs(**defaults)  # type: ignore[arg-type]


def test_every_frame_slot_is_filled() -> None:
    prompt = build_user_prompt(make_inputs())

    for heading in (
        "USER QUESTION",
        "CONVERSATION CONTEXT",
        "USER LANGUAGE",
        "DETECTED INTENT",
        "OPTIONAL USER PREFERENCES",
        "AVAILABLE SOURCES / RETRIEVED EVIDENCE",
        "OPTIONAL SOURCE PRIORITY",
    ):
        assert heading in prompt
    assert "İbrahim kimdir?" in prompt
    assert "Rab Avram'a dedi" in prompt


def test_no_template_placeholder_is_left_unsubstituted() -> None:
    prompt = build_user_prompt(make_inputs())

    for placeholder in (
        "{user_question}",
        "{conversation_context}",
        "{user_language}",
        "{detected_intent}",
        "{user_preferences}",
        "{retrieved_evidence}",
        "{source_priority}",
        "{response_contract}",
    ):
        assert placeholder not in prompt


def test_turkish_question_instructs_a_turkish_first_answer() -> None:
    prompt = build_user_prompt(make_inputs())

    assert "answer in Turkish first" in prompt


def test_detected_intent_is_offered_as_guidance_not_as_a_constraint() -> None:
    # The classifier is a rule set, not an oracle. Telling the model it may
    # override a misclassification beats forcing a wrong answer shape.
    prompt = build_user_prompt(make_inputs())

    assert "guidance" in prompt
    assert "not a constraint" in prompt


def test_absent_optional_slots_say_so_rather_than_rendering_empty() -> None:
    prompt = build_user_prompt(make_inputs())

    assert prompt.count("(none provided)") >= 3


def test_markdown_contract_is_selected_by_default() -> None:
    prompt = build_user_prompt(make_inputs())

    assert "## Direct Answer" in prompt
    assert "Return valid JSON only" not in prompt


def test_json_contract_is_selected_when_requested() -> None:
    prompt = build_user_prompt(make_inputs(answer_format=AnswerFormat.JSON))

    assert "Return valid JSON only" in prompt
    assert "## Direct Answer" not in prompt


@pytest.mark.parametrize("answer_format", list(AnswerFormat))
def test_every_answer_format_has_a_loadable_contract(answer_format: AnswerFormat) -> None:
    assert load_response_contract(answer_format).strip()


def test_empty_evidence_is_stated_rather_than_left_blank() -> None:
    prompt = build_user_prompt(make_inputs(evidence=""))

    assert "no evidence was retrieved" in prompt


# --- UserPreferences ---


def test_no_corpus_filter_allows_every_citation_type() -> None:
    preferences = UserPreferences()

    assert all(preferences.allows(t) for t in ("osis", "quran", "strongs"))


def test_corpus_filter_admits_only_the_selected_families() -> None:
    preferences = UserPreferences(corpora=(Corpus.BIBLE,))

    assert preferences.allows("osis")
    assert not preferences.allows("quran")
    assert not preferences.allows("strongs")


def test_corpus_filter_description_warns_against_backfilling_from_memory() -> None:
    # A filter that merely narrows the prompt while the model supplies the
    # excluded material from training data is not a filter.
    described = UserPreferences(corpora=(Corpus.BIBLE,)).describe()

    assert "do not supply it from your own knowledge" in described


def test_preferences_describe_traditions_and_translation() -> None:
    described = UserPreferences(traditions=("Sunni", "Protestant"), translation="YTC").describe()

    assert "Sunni" in described
    assert "Protestant" in described
    assert "YTC" in described


def test_empty_preferences_describe_as_not_provided() -> None:
    assert UserPreferences().describe() == "(none provided)"
