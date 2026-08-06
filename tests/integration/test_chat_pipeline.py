"""Integration tests for the chat pipeline against the real Ahit Corpus files.

No real network/LLM calls are made — the provider is a hand-written fake.
"""

from vahiy_engine.pipeline.chat_pipeline import DEFAULT_SYSTEM_PROMPT, run_chat_pipeline
from vahiy_engine.providers.llm.base import LLMProvider
from vahiy_engine.rag.retrieval import Source
from vahiy_engine.sources.ahit.client import get_ahit_client


class FakeProvider(LLMProvider):
    """Records calls instead of contacting a real LLM."""

    def __init__(self, answer: str = "fake answer") -> None:
        self.answer = answer
        self.calls: list[tuple[str, str, str]] = []

    def generate_answer(self, system_prompt: str, question: str, context: str) -> str:
        self.calls.append((system_prompt, question, context))
        return self.answer


# --- Reference path: resolved directly via get_verse(), no keyword search ---


def test_reference_input_resolves_exact_verse_via_get_verse() -> None:
    corpus = get_ahit_client()
    provider = FakeProvider("Genesis 1:1 describes the creation of the heavens and the earth.")

    result = run_chat_pipeline(corpus, provider, "Genesis 1:1")

    assert result.sources == [
        Source(
            osis="Gen.1.1",
            book="Gen",
            chapter=1,
            verse=1,
            text="In the beginning God created the heaven and the earth.",
            score=1,
        )
    ]
    system_prompt, question, context = provider.calls[0]
    assert system_prompt == DEFAULT_SYSTEM_PROMPT
    assert question == "Genesis 1:1"
    assert context == "[Gen.1.1]\nIn the beginning God created the heaven and the earth."


def test_reference_input_accepts_abbreviation() -> None:
    result = run_chat_pipeline(get_ahit_client(), FakeProvider(), "Gen 1:1")

    assert [s.osis for s in result.sources] == ["Gen.1.1"]


def test_reference_input_accepts_turkish_alias() -> None:
    # "Tekvin" and "Yuh" are Turkish aliases for Genesis/John; the corpus itself
    # only has the English (KJV) text, so this resolves to the same verse as
    # its English equivalent, proving the alias maps to the right OSIS book.
    genesis_result = run_chat_pipeline(get_ahit_client(), FakeProvider(), "Tekvin 1:1")
    john_result = run_chat_pipeline(get_ahit_client(), FakeProvider(), "Yuh 3:16")

    assert [s.osis for s in genesis_result.sources] == ["Gen.1.1"]
    assert [s.osis for s in john_result.sources] == ["John.3.16"]


def test_reference_input_returns_single_source_not_ranked_list() -> None:
    result = run_chat_pipeline(get_ahit_client(), FakeProvider(), "John 3:16", limit=5)

    assert len(result.sources) == 1
    assert result.sources[0].score == 1


# --- Keyword-search path: unchanged, exercised against the real corpus ---


def test_keyword_input_still_uses_search_across_books() -> None:
    result = run_chat_pipeline(get_ahit_client(), FakeProvider(), "beginning")

    assert [s.osis for s in result.sources] == ["Gen.1.1", "John.1.1"]


def test_keyword_input_respects_limit() -> None:
    result = run_chat_pipeline(get_ahit_client(), FakeProvider(), "God", limit=1)

    assert len(result.sources) == 1


def test_keyword_input_is_unaffected_by_reference_detection() -> None:
    result = run_chat_pipeline(get_ahit_client(), FakeProvider(), "logos")

    assert result.sources == []


def test_natural_language_question_retrieves_relevant_verse_end_to_end() -> None:
    # A real user question, not a reference and not a verbatim phrase from any
    # verse — the keyword fallback in search() is what makes this resolve.
    provider = FakeProvider("Genesis 1:1 says God created the heaven and the earth.")

    result = run_chat_pipeline(get_ahit_client(), provider, "Who created the heaven and the earth?")

    assert [s.osis for s in result.sources] == ["Gen.1.1", "Gen.1.2"]
    _, question, context = provider.calls[0]
    assert question == "Who created the heaven and the earth?"
    assert "[Gen.1.1]" in context
    assert "In the beginning God created the heaven and the earth." in context


# --- Reference syntax with no matching verse: graceful fallback, not an error ---


def test_reference_not_in_corpus_falls_back_to_keyword_search() -> None:
    # "Gen 99:99" is a syntactically valid reference, but the sample corpus
    # only has Genesis chapter 1 — this must not raise, just fall back.
    result = run_chat_pipeline(get_ahit_client(), FakeProvider("no matches"), "Gen 99:99")

    assert result.sources == []
    assert result.answer == "no matches"
