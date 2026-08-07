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
from vahiy_engine.sources.ahit.client import VerseNotFoundError
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.osis import InvalidOsisReferenceError, parse_osis
from vahiy_engine.sources.quran.client import AyahNotFoundError, QuranClient
from vahiy_engine.sources.quran.models import QuranReference

PIPELINE_ID = "PIPE-concept_lookup-v0"
PIPELINE_VERSION = "0.1.0"
CONSTITUTION_VERSION = "0.2.0"

# OSIS-addressed evidence lives in one of these translations, depending on
# testament; tried in this fixed order since a given OSIS reference only
# ever resolves in one of them (WLC is Old Testament, SBLGNT is New
# Testament — they don't overlap), so the order is a determinism choice,
# not a preference ranking.
_OSIS_TRANSLATIONS_TO_TRY: tuple[str | None, ...] = ("WLC", "SBLGNT", None)


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
) -> ReasoningResult | None:
    """Run the full loop for `question`, or return None if no Knowledge
    Graph node matches — the caller falls back to non-KG handling."""
    match = _detect_intent(graph, question)
    if match is None:
        return None
    node, matched_label = match

    resolved: list[EvidenceItem] = []
    rejected: list[RejectedEvidenceItem] = []
    for edge in graph.edges_from(node.id):
        if edge.citation is None:
            continue
        item = _resolve_citation(edge, corpus, quran, lexicon)
        if item is not None:
            resolved.append(item)
        else:
            rejected.append(
                RejectedEvidenceItem(
                    citation=edge.citation,
                    citation_type=edge.citation_type or "unknown",
                    reason_code="unresolvable_in_current_corpus",
                )
            )

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


def _detect_intent(graph: KnowledgeGraph, question: str) -> tuple[Node, str] | None:
    for token in tokenize(normalize(question)):
        if token in STOPWORDS:
            continue
        matches = graph.find_by_label(token)
        if matches:
            return matches[0], token
    return None


def _resolve_citation(
    edge: Edge, corpus: CorpusClient, quran: QuranClient, lexicon: LexiconClient
) -> EvidenceItem | None:
    if edge.citation_type == "osis":
        return _resolve_osis(edge, corpus)
    if edge.citation_type == "quran":
        return _resolve_quran(edge, quran)
    if edge.citation_type == "strongs":
        return _resolve_strongs(edge, lexicon)
    return None


def _resolve_osis(edge: Edge, corpus: CorpusClient) -> EvidenceItem | None:
    try:
        reference = parse_osis(edge.citation)
    except InvalidOsisReferenceError:
        return None

    for translation in _OSIS_TRANSLATIONS_TO_TRY:
        try:
            verse = corpus.get_verse(reference, translation=translation)
        except (VerseNotFoundError, FileNotFoundError, LookupError):
            continue
        return EvidenceItem(
            citation=edge.citation, citation_type="osis", text=verse.text, note=edge.note
        )
    return None


def _resolve_quran(edge: Edge, quran: QuranClient) -> EvidenceItem | None:
    _, surah, ayah = edge.citation.split(".")
    reference = QuranReference(surah=int(surah), ayah=int(ayah))
    for edition in ("en", None):
        try:
            resolved_ayah = quran.get_ayah(reference, edition=edition)
        except (AyahNotFoundError, LookupError):
            continue
        return EvidenceItem(
            citation=edge.citation, citation_type="quran", text=resolved_ayah.text, note=edge.note
        )
    return None


def _resolve_strongs(edge: Edge, lexicon: LexiconClient) -> EvidenceItem | None:
    number = edge.citation.removeprefix("Strong:")
    try:
        entry = lexicon.get_entry(number)
    except EntryNotFoundError:
        return None
    text = f"{entry.lemma} ({entry.transliteration}): {entry.definition}"
    return EvidenceItem(citation=edge.citation, citation_type="strongs", text=text, note=edge.note)
