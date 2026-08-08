"""RSN-2's reasoning loop: intent detection -> evidence gathering (with
rejection tracking) -> confidence calculation -> trace assembly.

Stops at the trace + resolved evidence text; building an LLM context from
that evidence and generating prose remain separate steps downstream
(Separation of Responsibilities: this module retrieves and prepares
evidence, it does not interpret it).
"""

from vahiy_engine.knowledge_graph.graph import KnowledgeGraph
from vahiy_engine.knowledge_graph.models import Edge, Node
from vahiy_engine.lexicon.ahit.client import EntryNotFoundError
from vahiy_engine.lexicon.client import LexiconClient
from vahiy_engine.reasoning.confidence import calculate_confidence
from vahiy_engine.reasoning.trace import (
    DetectedIntent,
    EvidenceItem,
    PipelineInfo,
    ReasoningTrace,
    RejectedEvidenceItem,
)
from vahiy_engine.search.index import STOPWORDS, normalize, tokenize
from vahiy_engine.search.reference_parser import find_chapter_references, find_references
from vahiy_engine.sources.ahit.client import VerseNotFoundError
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.osis import InvalidOsisReferenceError, OsisReference, parse_osis
from vahiy_engine.sources.quran.client import AyahNotFoundError, QuranClient
from vahiy_engine.sources.quran.models import QuranReference

PIPELINE_ID = "PIPE-concept_lookup-v0"
PIPELINE_VERSION = "0.1.0"
CONSTITUTION_VERSION = "0.2.0"

# Readable renderings, tried in this fixed order, for the text an answer can
# actually quote. YTC leads because it is the only translation in the
# configured corpus that covers both testaments; the rest are fallbacks for
# deployments carrying different translations. Order is fixed rather than
# scored so the same question yields the same evidence on every run.
_READABLE_TRANSLATIONS: tuple[str | None, ...] = ("YTC", "KJV", None)


def _readable_translations(language: str) -> tuple[str | None, ...]:
    """Translations in preference order for `language`.

    The corpus currently carries YTC (Turkish) across both testaments and
    little else, so both orders resolve to it today; the ordering exists so
    that adding an English translation later changes behavior by data
    rather than by code.
    """
    return ("KJV", "YTC", None) if language == "en" else ("YTC", "KJV", None)


# Source-language witnesses. A given OSIS reference resolves in at most one
# of these -- WLC is Hebrew Old Testament, SBLGNT is Greek New Testament,
# and they do not overlap -- so this is a lookup, not a ranking.
_ORIGINAL_LANGUAGE_TRANSLATIONS: tuple[tuple[str, str], ...] = (
    ("WLC", "Hebrew"),
    ("SBLGNT", "Greek"),
)


class ReasoningResult:
    """The trace plus the resolved evidence text it's built from, ready for
    a context builder to turn into an LLM prompt."""

    def __init__(self, trace: ReasoningTrace, node: Node) -> None:
        self.trace = trace
        self.node = node


def run_reasoning_loop(
    graph: KnowledgeGraph,
    corpus: CorpusClient,
    quran: QuranClient,
    lexicon: LexiconClient,
    question: str,
    language: str = "en",
) -> ReasoningResult | None:
    """Run the full loop for `question`, or return None if no Knowledge
    Graph node matches — the caller falls back to non-KG handling."""
    match = _detect_intent(graph, question)
    if match is None:
        return None
    node, matched_label = match

    resolved_by_citation: dict[str, EvidenceItem] = {}
    rejected: list[RejectedEvidenceItem] = []
    for edge in graph.edges_from(node.id):
        if edge.citation is None:
            continue
        if edge.citation in resolved_by_citation:
            # Two edges (e.g. "explains" and "derives_from") citing the same
            # verse support two different claims, but it's still one source
            # -- counting it twice would inflate resolved_count and skew
            # confidence toward a stronger corroboration than actually exists.
            continue
        item = _resolve_citation(edge, corpus, quran, lexicon, language)
        if item is not None:
            resolved_by_citation[edge.citation] = item
        else:
            rejected.append(
                RejectedEvidenceItem(
                    citation=edge.citation,
                    citation_type=edge.citation_type or "unknown",
                    reason_code="unresolvable_in_current_corpus",
                )
            )
    resolved = list(resolved_by_citation.values())

    confidence = calculate_confidence(resolved, rejected)

    trace = ReasoningTrace(
        detected_intent=DetectedIntent(
            pipeline_id=PIPELINE_ID, node_id=node.id, matched_label=matched_label
        ),
        evidence_retrieved=resolved,
        evidence_rejected=rejected,
        confidence=confidence,
        pipeline=PipelineInfo(
            pipeline_id=PIPELINE_ID,
            pipeline_version=PIPELINE_VERSION,
            constitution_version=CONSTITUTION_VERSION,
        ),
    )
    return ReasoningResult(trace=trace, node=node)


# A token is skipped, even if it would otherwise match a node label, when
# the nearest preceding *content* word (stopwords don't break the scope --
# "not about YHWH" negates "YHWH" just as much as "not YHWH" does) is one of
# these. Deliberately narrow (a fixed lookback, not general sentiment
# analysis) rather than a stand-in for real pragmatic reasoning, which is a
# larger capability this single rule doesn't attempt to substitute for.
_NEGATION_CUES = frozenset({"not", "değil"})


def _is_negated(tokens: list[str], index: int) -> bool:
    for earlier in range(index - 1, -1, -1):
        if tokens[earlier] in STOPWORDS:
            continue
        return tokens[earlier] in _NEGATION_CUES
    return False


def _detect_intent(graph: KnowledgeGraph, question: str) -> tuple[Node, str] | None:
    # A citation embedded directly in the question ("How does Exodus 3:14
    # explain...") is a more precise signal than any single keyword, and is
    # tried first: a question can cite a verse without ever naming the
    # concept it's evidence for, which find_by_label alone can't catch.
    for book, chapter, verse in find_references(question):
        citation = f"{book}.{chapter}.{verse}"
        matches = graph.find_by_citation(citation)
        if matches:
            return matches[0], citation

    # A chapter-only mention ("Genesis 17", no verse) is a weaker signal
    # than an exact verse citation but still more precise than a bare
    # keyword, so it's tried next, before falling back to label matching.
    for book, chapter in find_chapter_references(question):
        matches = graph.find_by_chapter(book, chapter)
        if matches:
            return matches[0], f"{book}.{chapter}"

    tokens = tokenize(normalize(question))
    for index, token in enumerate(tokens):
        if token in STOPWORDS:
            continue
        if _is_negated(tokens, index):
            continue
        matches = graph.find_by_label(token)
        if matches:
            return matches[0], token
    return None


def _resolve_citation(
    edge: Edge,
    corpus: CorpusClient,
    quran: QuranClient,
    lexicon: LexiconClient,
    language: str = "en",
) -> EvidenceItem | None:
    if edge.citation_type == "osis":
        return _resolve_osis(edge, corpus, language)
    if edge.citation_type == "quran":
        return _resolve_quran(edge, quran, language)
    if edge.citation_type == "strongs":
        return _resolve_strongs(edge, lexicon)
    return None


def _resolve_osis(edge: Edge, corpus: CorpusClient, language: str = "en") -> EvidenceItem | None:
    """Resolve one OSIS citation into a readable text plus, where the corpus
    has it, the same verse in its source language.

    Falls back to the source-language text as the readable text when no
    translation resolves: an answer quoting pointed Hebrew is worse than one
    quoting a translation, but far better than silently dropping a citation
    the knowledge graph verified.
    """
    try:
        reference = parse_osis(edge.citation)
    except InvalidOsisReferenceError:
        return None

    original_text, original_language = _resolve_original_language(reference, corpus)

    readable = _first_resolving(reference, corpus, _readable_translations(language))
    if readable is None:
        if original_text is None:
            return None
        # Only a source-language witness exists; use it as the quotable text
        # and don't also repeat it as the "original", which would render the
        # same string twice.
        return EvidenceItem(
            citation=edge.citation,
            citation_type="osis",
            text=original_text,
            note=edge.note,
            original_language=original_language,
        )

    return EvidenceItem(
        citation=edge.citation,
        citation_type="osis",
        text=readable,
        note=edge.note,
        original_text=original_text,
        original_language=original_language,
    )


def _first_resolving(
    reference: OsisReference, corpus: CorpusClient, translations: tuple[str | None, ...]
) -> str | None:
    for translation in translations:
        try:
            return corpus.get_verse(reference, translation=translation).text
        except (VerseNotFoundError, FileNotFoundError, LookupError):
            continue
    return None


def _resolve_original_language(
    reference: OsisReference, corpus: CorpusClient
) -> tuple[str | None, str | None]:
    for translation, language in _ORIGINAL_LANGUAGE_TRANSLATIONS:
        try:
            return corpus.get_verse(reference, translation=translation).text, language
        except (VerseNotFoundError, FileNotFoundError, LookupError):
            continue
    return None, None


def _resolve_quran(edge: Edge, quran: QuranClient, language: str = "en") -> EvidenceItem | None:
    """Resolve one Qur'an citation into a readable translation plus, where
    the corpus has them, the Arabic original and its transliteration.

    Previously this tried only the English edition, which silently discarded
    the Arabic, the Turkish and the transliteration the corpus actually
    ships -- so an answer could never quote the Qur'an in its own language,
    and a Turkish user got English. Found by listing the editions rather
    than trusting the resolution order.
    """
    _, surah, ayah = edge.citation.split(".")
    reference = QuranReference(surah=int(surah), ayah=int(ayah))

    readable = _first_ayah(quran, reference, _readable_quran_editions(language))
    original = _first_ayah(quran, reference, ("arabic",))
    transliteration = _first_ayah(quran, reference, ("transliteration",))

    text = readable or original
    if text is None:
        return None

    # Only carry the alternates that actually differ from the quoted text.
    # A deployment whose editions overlap (or a partially populated corpus)
    # would otherwise render the same string three times under three labels,
    # which reads as three independent witnesses rather than one.
    return EvidenceItem(
        citation=edge.citation,
        citation_type="quran",
        text=text,
        note=edge.note,
        original_text=original if original is not None and original != text else None,
        original_language="Arabic" if original is not None and original != text else None,
        transliteration=(
            transliteration if transliteration is not None and transliteration != text else None
        ),
    )


def _readable_quran_editions(language: str) -> tuple[str, ...]:
    """Translation editions in preference order for `language`.

    The user's own language leads; the other is kept as a fallback so a
    missing edition degrades to a translation the reader can still use
    rather than to untransliterated Arabic.
    """
    return ("tr", "en") if language == "tr" else ("en", "tr")


def _first_ayah(
    quran: QuranClient, reference: QuranReference, editions: tuple[str, ...]
) -> str | None:
    for edition in editions:
        try:
            return quran.get_ayah(reference, edition=edition).text
        except (AyahNotFoundError, LookupError):
            continue
    return None


def _resolve_strongs(edge: Edge, lexicon: LexiconClient) -> EvidenceItem | None:
    number = edge.citation.removeprefix("Strong:")
    try:
        entry = lexicon.get_entry(number)
    except EntryNotFoundError:
        return None
    text = f"{entry.lemma} ({entry.transliteration}): {entry.definition}"
    return EvidenceItem(citation=edge.citation, citation_type="strongs", text=text, note=edge.note)
