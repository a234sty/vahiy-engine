"""Orchestrates the chat pipeline."""

import importlib.resources
from dataclasses import dataclass, field

from vahiy_engine.knowledge_graph.graph import KnowledgeGraph
from vahiy_engine.lexicon.client import LexiconClient
from vahiy_engine.lexicon.models import LexiconEntry
from vahiy_engine.pipeline.prompt_builder import (
    AnswerFormat,
    PromptInputs,
    UserPreferences,
    build_user_prompt,
)
from vahiy_engine.providers.llm.base import LLMProvider
from vahiy_engine.rag.context_builder import build_context
from vahiy_engine.rag.retrieval import Source, retrieve
from vahiy_engine.reasoning.confidence import calculate_confidence
from vahiy_engine.reasoning.intent import QuestionAnalysis, analyze_question
from vahiy_engine.reasoning.loop import run_reasoning_loop
from vahiy_engine.reasoning.trace import EvidenceItem, ReasoningTrace
from vahiy_engine.search.lexicon_lookup import find_lexicon_term
from vahiy_engine.search.reference_parser import ReferenceParseError, parse_reference
from vahiy_engine.sources.ahit.client import VerseNotFoundError
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.models import Verse
from vahiy_engine.sources.osis import OsisReference
from vahiy_engine.sources.quran.client import QuranClient

DEFAULT_LIMIT = 5


def _load_default_system_prompt() -> str:
    prompt_dir = importlib.resources.files("vahiy_engine.providers.llm") / "prompts"
    return (prompt_dir / "chat_system_prompt.txt").read_text(encoding="utf-8").strip()


DEFAULT_SYSTEM_PROMPT = _load_default_system_prompt()


@dataclass(frozen=True)
class ChatResult:
    answer: str
    sources: list[Source]
    lexicon_entries: list[LexiconEntry] = field(default_factory=list)
    trace: ReasoningTrace | None = None
    analysis: QuestionAnalysis | None = None
    withheld_by_preference: tuple[str, ...] = ()
    """Citations the caller's own source filter excluded. Reported rather
    than silently dropped, so a filtered answer stays distinguishable from a
    corpus that simply had nothing on the topic."""

    @property
    def primary_evidence(self) -> list[EvidenceItem]:
        """The curated Knowledge Graph citations behind this answer, if the
        reasoning layer ran and matched a concept."""
        return list(self.trace.evidence_retrieved) if self.trace is not None else []


def run_chat_pipeline(
    corpus: CorpusClient,
    provider: LLMProvider,
    question: str,
    limit: int = DEFAULT_LIMIT,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    lexicon: LexiconClient | None = None,
    quran: QuranClient | None = None,
    graph: KnowledgeGraph | None = None,
    preferences: UserPreferences | None = None,
    conversation_context: str | None = None,
    answer_format: AnswerFormat = AnswerFormat.MARKDOWN,
) -> ChatResult:
    """Answer `question` using retrieval-augmented generation over `corpus`.

    Orchestrates the components in a fixed sequence: run the reasoning layer
    (when it is wired up), resolve keyword sources for `question`, build a
    plain-text context from both, then ask `provider` to generate an answer
    grounded in that context. Returns the answer together with the sources
    and the reasoning trace it was grounded in.

    `lexicon`, when given, is checked for a Strong's-numbered term named in
    `question` (e.g. "Logos" in "What does Logos mean in John 1:1?"); a match
    is cited in `lexicon_entries` and its definition is folded into the
    context alongside the retrieved verses.

    `graph` and `quran`, when given together with `lexicon`, engage RSN-2's
    reasoning loop *before* keyword retrieval. That loop matches the question
    against curated Knowledge Graph concepts and resolves their verified
    citations across all configured corpora -- Bible, Qur'an and Strong's
    alike -- producing evidence that is primary (someone verified this
    citation is about this concept) rather than incidental (these words
    ranked highly). Keyword retrieval still runs and is still included, as
    supporting evidence; the reasoning layer adds to the context, it never
    replaces it. This is also the only path by which Qur'anic text reaches an
    answer at all, since keyword retrieval covers the Bible corpus only.

    Every one of those three is optional and defaults to None. Called without
    them, this function behaves exactly as it did before the reasoning layer
    existed -- same sources, same context bytes, same answer -- so no caller
    is forced to adopt it.

    Has no FastAPI dependency and carries no state between calls — each call is
    independent, with no conversation memory.
    """
    analysis = analyze_question(question)
    trace = _run_reasoning(graph, corpus, quran, lexicon, question, analysis.language)
    trace, withheld = _apply_source_preferences(trace, preferences)

    sources = _resolve_sources(corpus, question, limit)
    lexicon_entries = _resolve_lexicon_entries(lexicon, question)

    evidence = build_context(
        sources,
        lexicon_entries,
        primary_evidence=trace.evidence_retrieved if trace is not None else None,
        coverage_notes=(_coverage_notes(quran, trace, withheld) if graph is not None else None),
    )

    if graph is None:
        # No reasoning layer wired up: keep the original, untemplated user
        # turn so callers predating the prompt contract see no change.
        context = evidence
    else:
        context = build_user_prompt(
            PromptInputs(
                question=question,
                analysis=analysis,
                evidence=evidence,
                preferences=preferences or UserPreferences(),
                conversation_context=conversation_context,
                answer_format=answer_format,
            )
        )

    answer = provider.generate_answer(system_prompt, question, context)

    return ChatResult(
        answer=answer,
        sources=sources,
        lexicon_entries=lexicon_entries,
        trace=trace,
        analysis=analysis,
        withheld_by_preference=withheld,
    )


def _apply_source_preferences(
    trace: ReasoningTrace | None, preferences: UserPreferences | None
) -> tuple[ReasoningTrace | None, tuple[str, ...]]:
    """Filter curated evidence down to the source families the caller allowed.

    This is what keeps a source preference from being a menu item that
    changes nothing: excluded citations are removed from the evidence the
    model ever sees, and their identifiers are returned so the exclusion can
    be disclosed instead of looking like absence.
    """
    if trace is None or preferences is None or not preferences.corpora:
        return trace, ()

    kept = [item for item in trace.evidence_retrieved if preferences.allows(item.citation_type)]
    withheld = tuple(
        item.citation
        for item in trace.evidence_retrieved
        if not preferences.allows(item.citation_type)
    )
    if not withheld:
        return trace, ()

    return (
        trace.model_copy(
            update={
                "evidence_retrieved": kept,
                "confidence": calculate_confidence(kept, list(trace.evidence_rejected)),
            }
        ),
        withheld,
    )


def _run_reasoning(
    graph: KnowledgeGraph | None,
    corpus: CorpusClient,
    quran: QuranClient | None,
    lexicon: LexiconClient | None,
    question: str,
    language: str,
) -> ReasoningTrace | None:
    """Run RSN-2's loop when every dependency it needs is wired up.

    The loop resolves Bible, Qur'an and Strong's citations, so it needs all
    three clients; with any of them missing it could only ever report the
    absent ones as unresolvable, which would understate confidence rather
    than measure it. Returns None when the loop isn't wired up or when the
    question matches no curated concept -- both are ordinary outcomes, not
    errors, and the caller falls back to keyword retrieval alone.
    """
    if graph is None or quran is None or lexicon is None:
        return None

    result = run_reasoning_loop(graph, corpus, quran, lexicon, question, language)
    return result.trace if result is not None else None


def _coverage_notes(
    quran: QuranClient | None,
    trace: ReasoningTrace | None,
    withheld: tuple[str, ...] = (),
) -> list[str]:
    """State what this deployment can and cannot cite.

    Derived from live client state rather than hardcoded, so it stays true as
    corpora are added: the model is told which source families actually exist
    here, and is therefore able to report a gap as a gap instead of filling
    it from its own background knowledge.
    """
    notes: list[str] = []

    available = ["Bible (multiple translations)", "Strong's lexicons (Hebrew and Greek)"]
    if quran is not None and quran.available_editions():
        available.append("Qur'an")
    notes.append(
        "Source families configured in this deployment: "
        + "; ".join(available)
        + ". No hadith, tafsir, rabbinic, patristic or commentary corpus is "
        "configured, so no such source can be cited here."
    )

    if quran is not None and not quran.available_editions():
        notes.append(
            "No Qur'an corpus is configured in this deployment. The absence of a "
            "Qur'anic citation below reflects that configuration, not the "
            "Qur'an's silence on the topic."
        )

    if trace is None:
        notes.append(
            "This question matched no concept in the curated knowledge graph, so "
            "the evidence below is keyword retrieval over the Bible corpus only, "
            "and its relevance has not been verified."
        )
    elif trace.evidence_rejected:
        unresolved = ", ".join(item.citation for item in trace.evidence_rejected)
        notes.append(
            f"These curated citations did not resolve against the configured "
            f"corpus and are therefore absent from the evidence above: {unresolved}."
        )

    if withheld:
        notes.append(
            "Your source filter excluded these citations, which the knowledge "
            "graph does hold for this question: " + ", ".join(withheld) + ". "
            "Their absence is the filter's doing, not the corpus's."
        )

    return notes


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
