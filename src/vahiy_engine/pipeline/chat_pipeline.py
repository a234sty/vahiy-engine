"""Orchestrates the chat pipeline."""

from dataclasses import dataclass, field

from vahiy_engine.lexicon.client import LexiconClient
from vahiy_engine.lexicon.models import LexiconEntry
from vahiy_engine.providers.llm.base import LLMProvider
from vahiy_engine.rag.context_builder import build_context
from vahiy_engine.rag.retrieval import Source, retrieve
from vahiy_engine.search.lexicon_lookup import find_lexicon_term
from vahiy_engine.search.reference_parser import ReferenceParseError, parse_reference
from vahiy_engine.sources.ahit.client import VerseNotFoundError
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.models import Verse
from vahiy_engine.sources.osis import OsisReference

DEFAULT_LIMIT = 5

DEFAULT_SYSTEM_PROMPT = (
    "You are Vahiy Engine, a neutral, source-first assistant. Answer only using "
    "the provided context. If the context does not contain the answer, say so "
    "instead of guessing. Never favor any religion, denomination, sect, "
    "ideology, or theological position."
)


@dataclass(frozen=True)
class ChatResult:
    answer: str
    sources: list[Source]
    lexicon_entries: list[LexiconEntry] = field(default_factory=list)


def run_chat_pipeline(
    corpus: CorpusClient,
    provider: LLMProvider,
    question: str,
    limit: int = DEFAULT_LIMIT,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    lexicon: LexiconClient | None = None,
) -> ChatResult:
    """Answer `question` using retrieval-augmented generation over `corpus`.

    Orchestrates the existing components in a fixed sequence: resolve sources
    for `question`, build a plain-text context from them, then ask `provider`
    to generate an answer grounded in that context. Returns the answer
    together with the sources it was grounded in.

    `lexicon`, when given, is checked for a Strong's-numbered term named in
    `question` (e.g. "Logos" in "What does Logos mean in John 1:1?"); a match
    is cited in `lexicon_entries` and its definition is folded into the
    context alongside the retrieved verses. Omitting `lexicon` (the default)
    skips this entirely — every existing caller keeps its exact prior
    behavior.

    Has no FastAPI dependency and carries no state between calls — each call is
    independent, with no conversation memory.
    """
    sources = _resolve_sources(corpus, question, limit)
    lexicon_entries = _resolve_lexicon_entries(lexicon, question)
    context = build_context(sources, lexicon_entries)
    answer = provider.generate_answer(system_prompt, question, context)

    return ChatResult(answer=answer, sources=sources, lexicon_entries=lexicon_entries)


def _resolve_lexicon_entries(lexicon: LexiconClient | None, question: str) -> list[LexiconEntry]:
    if lexicon is None:
        return []
    entry = find_lexicon_term(lexicon, question)
    return [entry] if entry is not None else []


def _resolve_sources(corpus: CorpusClient, question: str, limit: int) -> list[Source]:
    """Resolve the sources for `question`.

    If `question` parses as a direct Bible reference (e.g. "Gen 1:1", "Tekvin
    1:1", "Yuh 3:16"), resolve it with a single `corpus.get_verse()` lookup
    instead of keyword search. Falls back to the existing keyword-search
    pipeline (`retrieve()`) when `question` isn't a reference, or when it is
    one but the corpus has no matching verse — keyword search over the raw
    question text is a reasonable last resort in that case, not an error.
    """
    try:
        book, chapter, verse = parse_reference(question)
    except ReferenceParseError:
        return retrieve(corpus, question, limit)

    try:
        resolved_verse = corpus.get_verse(OsisReference(book=book, chapter=chapter, verse=verse))
    except (VerseNotFoundError, FileNotFoundError):
        return retrieve(corpus, question, limit)

    return [_verse_to_source(resolved_verse)]


def _verse_to_source(verse: Verse) -> Source:
    return Source(
        osis=verse.osis,
        book=verse.book,
        chapter=verse.chapter,
        verse=verse.verse,
        text=verse.text,
        score=1,
    )
