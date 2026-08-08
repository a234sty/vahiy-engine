"""Unit tests for the chat pipeline. No real network/LLM calls are made."""

from collections.abc import Iterator
from unittest.mock import MagicMock, call, patch

import pytest

from vahiy_engine.lexicon.client import LexiconClient
from vahiy_engine.lexicon.models import LexiconEntry
from vahiy_engine.pipeline.chat_pipeline import (
    DEFAULT_LIMIT,
    DEFAULT_SYSTEM_PROMPT,
    run_chat_pipeline,
)
from vahiy_engine.providers.llm.base import LLMProvider
from vahiy_engine.rag.retrieval import Source
from vahiy_engine.sources.ahit.client import VerseNotFoundError
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.models import Verse
from vahiy_engine.sources.osis import OsisReference


def make_source(osis: str = "Gen.1.1", text: str = "text", score: int = 1) -> Source:
    book, chapter, verse = osis.split(".")
    return Source(
        osis=osis, book=book, chapter=int(chapter), verse=int(verse), text=text, score=score
    )


class FakeCorpus(CorpusClient):
    """In-memory corpus for exercising the pipeline without touching disk."""

    def __init__(self, verses: list[Verse]) -> None:
        self._verses = verses

    def get_verse(self, reference: OsisReference) -> Verse:
        for verse in self._verses:
            if (verse.book, verse.chapter, verse.verse) == (
                reference.book,
                reference.chapter,
                reference.verse,
            ):
                return verse
        raise VerseNotFoundError(f"Verse '{reference.osis}' was not found")

    def iter_verses(self, translation: str | None = None) -> Iterator[Verse]:
        yield from self._verses


def make_verse(book: str, chapter: int, verse: int, text: str) -> Verse:
    return Verse(
        osis=f"{book}.{chapter}.{verse}", book=book, chapter=chapter, verse=verse, text=text
    )


class FakeProvider(LLMProvider):
    """Records calls instead of contacting a real LLM."""

    def __init__(self, answer: str = "fake answer") -> None:
        self.answer = answer
        self.calls: list[tuple[str, str, str]] = []

    def generate_answer(self, system_prompt: str, question: str, context: str) -> str:
        self.calls.append((system_prompt, question, context))
        return self.answer


# --- DEFAULT_SYSTEM_PROMPT: loaded from providers/llm/prompts/chat_system_prompt.txt ---


def test_default_system_prompt_is_loaded_from_the_prompt_file_not_empty() -> None:
    assert len(DEFAULT_SYSTEM_PROMPT) > 500


def test_default_system_prompt_forbids_favoring_any_tradition() -> None:
    lowered = DEFAULT_SYSTEM_PROMPT.lower()
    assert "do not privilege one tradition" in lowered
    assert "do not merge traditions into one vague summary" in lowered


def test_default_system_prompt_requires_grounding_in_provided_context() -> None:
    lowered = DEFAULT_SYSTEM_PROMPT.lower()
    assert "retrieved evidence" in lowered
    assert "never invent sources, quotations, verses" in lowered
    assert "coverage limits" in lowered


def test_default_system_prompt_requires_bilingual_turkish_english_output() -> None:
    lowered = DEFAULT_SYSTEM_PROMPT.lower()
    assert "turkish" in lowered
    assert "english" in lowered


# --- Orchestration wiring: mock retrieve/build_context/provider directly ---


def test_run_chat_pipeline_calls_components_in_order_with_correct_arguments() -> None:
    corpus = MagicMock()
    provider = MagicMock()
    provider.generate_answer.return_value = "The answer."
    sources = [make_source()]

    manager = MagicMock()
    with (
        patch(
            "vahiy_engine.pipeline.chat_pipeline.retrieve", return_value=sources
        ) as mock_retrieve,
        patch(
            "vahiy_engine.pipeline.chat_pipeline.build_context", return_value="built context"
        ) as mock_build_context,
    ):
        manager.attach_mock(mock_retrieve, "retrieve")
        manager.attach_mock(mock_build_context, "build_context")
        manager.attach_mock(provider.generate_answer, "generate_answer")

        result = run_chat_pipeline(corpus, provider, "What is logos?", limit=3)

    assert manager.mock_calls == [
        call.retrieve(corpus, "What is logos?", 3),
        call.build_context(
            sources,
            [],
            primary_evidence=None,
            retrieved_evidence=None,
            coverage_notes=None,
        ),
        call.generate_answer(DEFAULT_SYSTEM_PROMPT, "What is logos?", "built context"),
    ]
    # Compared field-by-field rather than whole-object: ChatResult also
    # carries the question analysis, which this test is not about.
    assert result.answer == "The answer."
    assert result.sources == sources
    assert result.trace is None


def test_run_chat_pipeline_uses_default_limit_when_not_specified() -> None:
    corpus = MagicMock()
    provider = MagicMock()
    provider.generate_answer.return_value = "answer"

    with (
        patch("vahiy_engine.pipeline.chat_pipeline.retrieve", return_value=[]) as mock_retrieve,
        patch("vahiy_engine.pipeline.chat_pipeline.build_context", return_value=""),
    ):
        run_chat_pipeline(corpus, provider, "question")

    mock_retrieve.assert_called_once_with(corpus, "question", DEFAULT_LIMIT)


def test_run_chat_pipeline_uses_custom_system_prompt_when_given() -> None:
    provider = MagicMock()
    provider.generate_answer.return_value = "answer"

    with (
        patch("vahiy_engine.pipeline.chat_pipeline.retrieve", return_value=[]),
        patch("vahiy_engine.pipeline.chat_pipeline.build_context", return_value="ctx"),
    ):
        run_chat_pipeline(MagicMock(), provider, "question", system_prompt="Custom instructions.")

    provider.generate_answer.assert_called_once_with("Custom instructions.", "question", "ctx")


def test_run_chat_pipeline_returns_sources_from_retrieval_unchanged() -> None:
    provider = MagicMock()
    provider.generate_answer.return_value = "answer"
    sources = [make_source("Gen.1.1"), make_source("John.1.1")]

    with (
        patch("vahiy_engine.pipeline.chat_pipeline.retrieve", return_value=sources),
        patch("vahiy_engine.pipeline.chat_pipeline.build_context", return_value="ctx"),
    ):
        result = run_chat_pipeline(MagicMock(), provider, "question")

    assert result.sources == sources


# --- Reference-path branching: mock retrieve()/build_context()/corpus.get_verse ---


def test_run_chat_pipeline_reference_input_resolves_via_get_verse_and_skips_retrieve() -> None:
    corpus = MagicMock()
    corpus.get_verse.return_value = Verse(
        osis="Gen.1.1", book="Gen", chapter=1, verse=1, text="In the beginning..."
    )
    provider = MagicMock()
    provider.generate_answer.return_value = "answer"

    with (
        patch("vahiy_engine.pipeline.chat_pipeline.retrieve") as mock_retrieve,
        patch(
            "vahiy_engine.pipeline.chat_pipeline.build_context", return_value="ctx"
        ) as mock_build_context,
    ):
        run_chat_pipeline(corpus, provider, "Gen 1:1")

    mock_retrieve.assert_not_called()
    corpus.get_verse.assert_called_once_with(OsisReference(book="Gen", chapter=1, verse=1))
    mock_build_context.assert_called_once_with(
        [
            Source(
                osis="Gen.1.1", book="Gen", chapter=1, verse=1, text="In the beginning...", score=1
            )
        ],
        [],
        primary_evidence=None,
        retrieved_evidence=None,
        coverage_notes=None,
    )


def test_run_chat_pipeline_non_reference_input_skips_get_verse() -> None:
    corpus = MagicMock()
    provider = MagicMock()
    provider.generate_answer.return_value = "answer"

    with (
        patch("vahiy_engine.pipeline.chat_pipeline.retrieve", return_value=[]) as mock_retrieve,
        patch("vahiy_engine.pipeline.chat_pipeline.build_context", return_value=""),
    ):
        run_chat_pipeline(corpus, provider, "What is logos?")

    corpus.get_verse.assert_not_called()
    mock_retrieve.assert_called_once_with(corpus, "What is logos?", DEFAULT_LIMIT)


def test_run_chat_pipeline_reference_not_in_corpus_falls_back_to_retrieve() -> None:
    corpus = MagicMock()
    corpus.get_verse.side_effect = VerseNotFoundError("Verse 'Gen.99.99' was not found")
    provider = MagicMock()
    provider.generate_answer.return_value = "answer"

    with (
        patch("vahiy_engine.pipeline.chat_pipeline.retrieve", return_value=[]) as mock_retrieve,
        patch("vahiy_engine.pipeline.chat_pipeline.build_context", return_value=""),
    ):
        run_chat_pipeline(corpus, provider, "Gen 99:99")

    mock_retrieve.assert_called_once_with(corpus, "Gen 99:99", DEFAULT_LIMIT)


# --- End-to-end with real retrieve()/build_context() and a fake (non-network) provider ---


@pytest.fixture
def corpus() -> FakeCorpus:
    return FakeCorpus(
        [
            make_verse("Gen", 1, 1, "In the beginning God created the heaven and the earth."),
            make_verse("John", 1, 1, "In the beginning was the Word, and the Word was with God."),
        ]
    )


def test_run_chat_pipeline_end_to_end_with_fake_corpus_and_provider(corpus: FakeCorpus) -> None:
    provider = FakeProvider("Genesis 1:1 describes the creation of the heavens and the earth.")

    result = run_chat_pipeline(corpus, provider, "beginning", limit=5)

    assert result.answer == "Genesis 1:1 describes the creation of the heavens and the earth."
    assert [s.osis for s in result.sources] == ["Gen.1.1", "John.1.1"]

    system_prompt, question, context = provider.calls[0]
    assert system_prompt == DEFAULT_SYSTEM_PROMPT
    assert question == "beginning"
    assert "[Gen.1.1]" in context
    assert "In the beginning God created the heaven and the earth." in context
    assert "[John.1.1]" in context


def test_run_chat_pipeline_respects_limit_end_to_end(corpus: FakeCorpus) -> None:
    provider = FakeProvider("answer")

    result = run_chat_pipeline(corpus, provider, "beginning", limit=1)

    assert len(result.sources) == 1
    assert result.sources[0].osis == "Gen.1.1"


def test_run_chat_pipeline_provider_called_exactly_once(corpus: FakeCorpus) -> None:
    provider = FakeProvider("answer")

    run_chat_pipeline(corpus, provider, "beginning")

    assert len(provider.calls) == 1


def test_run_chat_pipeline_resolves_reference_end_to_end(corpus: FakeCorpus) -> None:
    provider = FakeProvider("Genesis 1:1 describes the creation of the heavens and the earth.")

    result = run_chat_pipeline(corpus, provider, "Gen 1:1")

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
    _, question, context = provider.calls[0]
    assert question == "Gen 1:1"
    assert context == "[Gen.1.1]\nIn the beginning God created the heaven and the earth."


def test_run_chat_pipeline_resolves_turkish_alias_reference_end_to_end(corpus: FakeCorpus) -> None:
    provider = FakeProvider("answer")

    result = run_chat_pipeline(corpus, provider, "Tekvin 1:1")

    assert [s.osis for s in result.sources] == ["Gen.1.1"]


def test_run_chat_pipeline_falls_back_when_referenced_verse_missing(corpus: FakeCorpus) -> None:
    # "Gen 5:5" parses as a valid reference, but this corpus fixture only has
    # Gen.1.1 and John.1.1 — the pipeline must fall back to keyword search over
    # the literal question text rather than error out.
    provider = FakeProvider("answer")

    result = run_chat_pipeline(corpus, provider, "Gen 5:5")

    assert result.sources == []
    assert provider.calls[0][1] == "Gen 5:5"


def test_chat_pipeline_module_has_no_fastapi_dependency() -> None:
    import inspect

    import vahiy_engine.pipeline.chat_pipeline as module

    assert "fastapi" not in inspect.getsource(module)


# --- Lexicon wiring: mock find_lexicon_term/build_context directly ---


def make_lexicon_entry(strongs_number: str = "G3056") -> LexiconEntry:
    return LexiconEntry(
        strongs_number=strongs_number,
        language="greek",
        lemma="λόγος",
        transliteration="lógos",
        definition="something said",
    )


def test_run_chat_pipeline_without_lexicon_client_never_calls_find_lexicon_term() -> None:
    provider = MagicMock()
    provider.generate_answer.return_value = "answer"

    with (
        patch("vahiy_engine.pipeline.chat_pipeline.retrieve", return_value=[]),
        patch("vahiy_engine.pipeline.chat_pipeline.build_context", return_value="ctx"),
        patch("vahiy_engine.pipeline.chat_pipeline.find_lexicon_term") as mock_find,
    ):
        result = run_chat_pipeline(MagicMock(), provider, "What is logos?")

    mock_find.assert_not_called()
    assert result.lexicon_entries == []


def test_run_chat_pipeline_passes_matched_lexicon_entry_to_build_context() -> None:
    provider = MagicMock()
    provider.generate_answer.return_value = "answer"
    entry = make_lexicon_entry()

    with (
        patch("vahiy_engine.pipeline.chat_pipeline.retrieve", return_value=[]),
        patch(
            "vahiy_engine.pipeline.chat_pipeline.build_context", return_value="ctx"
        ) as mock_build_context,
        patch("vahiy_engine.pipeline.chat_pipeline.find_lexicon_term", return_value=entry),
    ):
        result = run_chat_pipeline(MagicMock(), provider, "What is logos?", lexicon=MagicMock())

    mock_build_context.assert_called_once_with(
        [], [entry], primary_evidence=None, retrieved_evidence=None, coverage_notes=None
    )
    assert result.lexicon_entries == [entry]


def test_run_chat_pipeline_no_lexicon_match_passes_empty_list() -> None:
    provider = MagicMock()
    provider.generate_answer.return_value = "answer"

    with (
        patch("vahiy_engine.pipeline.chat_pipeline.retrieve", return_value=[]),
        patch(
            "vahiy_engine.pipeline.chat_pipeline.build_context", return_value="ctx"
        ) as mock_build_context,
        patch("vahiy_engine.pipeline.chat_pipeline.find_lexicon_term", return_value=None),
    ):
        result = run_chat_pipeline(MagicMock(), provider, "no match", lexicon=MagicMock())

    mock_build_context.assert_called_once_with(
        [], [], primary_evidence=None, retrieved_evidence=None, coverage_notes=None
    )
    assert result.lexicon_entries == []


# --- Lexicon wiring: end-to-end with a real FakeLexiconClient ---


class FakeLexiconClient(LexiconClient):
    def __init__(self, entries: list[LexiconEntry]) -> None:
        self._entries = entries

    def get_entry(self, strongs_number: str) -> LexiconEntry:
        for entry in self._entries:
            if entry.strongs_number == strongs_number:
                return entry
        raise LookupError(strongs_number)

    def iter_entries(self, language: str | None = None) -> Iterator[LexiconEntry]:
        for entry in self._entries:
            if language is None or entry.language == language:
                yield entry


def test_run_chat_pipeline_end_to_end_cites_verse_and_lexicon_source_together(
    corpus: FakeCorpus,
) -> None:
    # Mirrors ENGINE_SPEC.md's own worked example: a question naming both a
    # verse and a Greek word should cite both kinds of source together.
    lexicon = FakeLexiconClient([make_lexicon_entry()])
    provider = FakeProvider("Logos means 'word' — see John 1:1.")

    result = run_chat_pipeline(corpus, provider, "What does logos mean?", lexicon=lexicon)

    assert result.lexicon_entries == [make_lexicon_entry()]
    _, _, context = provider.calls[0]
    assert "[Strong:G3056]" in context
    assert "something said" in context


def test_run_chat_pipeline_end_to_end_no_lexicon_match_leaves_entries_empty(
    corpus: FakeCorpus,
) -> None:
    lexicon = FakeLexiconClient([make_lexicon_entry()])
    provider = FakeProvider("answer")

    result = run_chat_pipeline(corpus, provider, "beginning", lexicon=lexicon)

    assert result.lexicon_entries == []
    _, _, context = provider.calls[0]
    assert "Strong:" not in context
