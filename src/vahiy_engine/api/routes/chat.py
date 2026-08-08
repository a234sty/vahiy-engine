"""POST /chat endpoint."""

from fastapi import APIRouter, Depends

from vahiy_engine.api.schemas.chat import (
    ChatConfidence,
    ChatLexiconSourceItem,
    ChatPreferences,
    ChatQuestionAnalysis,
    ChatQuranSourceItem,
    ChatReasoning,
    ChatRequest,
    ChatResponse,
    ChatSourceItem,
)
from vahiy_engine.knowledge_graph.graph import KnowledgeGraph
from vahiy_engine.knowledge_graph.seed_data import get_knowledge_graph
from vahiy_engine.lexicon.ahit.client import AhitLexiconClient, get_lexicon_client
from vahiy_engine.pipeline.chat_pipeline import ChatResult, run_chat_pipeline
from vahiy_engine.pipeline.prompt_builder import AnswerFormat, Corpus, UserPreferences
from vahiy_engine.providers.llm import get_llm_provider, tier_model_for
from vahiy_engine.providers.llm.base import LLMProvider
from vahiy_engine.reasoning.intent import Complexity, analyze_question
from vahiy_engine.sources.ahit.client import AhitCorpusClient, get_ahit_client
from vahiy_engine.sources.quran.client import QuranClient, get_quran_client

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def post_chat(
    request: ChatRequest,
    corpus: AhitCorpusClient = Depends(get_ahit_client),
    provider: LLMProvider = Depends(get_llm_provider),
    lexicon: AhitLexiconClient = Depends(get_lexicon_client),
    quran: QuranClient = Depends(get_quran_client),
    graph: KnowledgeGraph = Depends(get_knowledge_graph),
) -> ChatResponse:
    provider = _tier(provider, analyze_question(request.message).complexity)

    result = run_chat_pipeline(
        corpus,
        provider,
        request.message,
        lexicon=lexicon,
        quran=quran,
        graph=graph,
        preferences=_preferences(request.preferences),
        conversation_context=request.conversation_context,
        answer_format=AnswerFormat(request.answer_format),
    )

    return ChatResponse(
        answer=result.answer,
        sources=[
            ChatSourceItem(
                osis=s.osis,
                chapter=s.chapter,
                verse=s.verse,
                text=s.text,
                score=s.score,
                translation=s.translation,
            )
            for s in result.sources
        ],
        lexicon_sources=[
            ChatLexiconSourceItem(
                strongs_number=e.strongs_number,
                lemma=e.lemma,
                transliteration=e.transliteration,
                definition=e.definition,
            )
            for e in result.lexicon_entries
        ],
        quran_sources=_quran_sources(result),
        confidence=_confidence(result),
        reasoning=_reasoning(result),
        analysis=_analysis(result),
        withheld_by_preference=list(result.withheld_by_preference),
    )


def _tier(default: LLMProvider, complexity: Complexity) -> LLMProvider:
    """Swap in a complexity-matched model, but only where one is configured.

    Which model to use depends on the question: a verse lookup and a
    cross-scripture comparison should not cost the same. But the provider is
    still injected normally, and this returns it untouched when the
    deployment configures no tier for this complexity -- so tiering is an
    opt-in refinement rather than a bypass of dependency injection, and an
    overridden provider (in tests, or any caller supplying its own) is never
    silently discarded.
    """
    if tier_model_for(complexity) is None:
        return default
    return get_llm_provider(complexity)


def _preferences(preferences: ChatPreferences | None) -> UserPreferences | None:
    if preferences is None:
        return None
    return UserPreferences(
        corpora=tuple(Corpus(c) for c in preferences.corpora),
        traditions=tuple(preferences.traditions),
        translation=preferences.translation,
        source_priority=tuple(preferences.source_priority),
        notes=preferences.notes,
    )


def _quran_sources(result: ChatResult) -> list[ChatQuranSourceItem]:
    """Qur'anic evidence, split back out of the reasoning trace.

    Qur'anic text reaches an answer only through the Knowledge Graph -- the
    keyword retriever indexes the Bible corpus alone -- so this reads from
    the trace rather than from `result.sources`.
    """
    items: list[ChatQuranSourceItem] = []
    for evidence in result.primary_evidence:
        if evidence.citation_type != "quran":
            continue
        _, surah, ayah = evidence.citation.split(".")
        items.append(
            ChatQuranSourceItem(
                citation=evidence.citation,
                surah=int(surah),
                ayah=int(ayah),
                text=evidence.text,
                original_text=evidence.original_text,
                transliteration=evidence.transliteration,
            )
        )
    return items


def _confidence(result: ChatResult) -> ChatConfidence | None:
    if result.trace is None:
        return None
    calculation = result.trace.confidence
    return ChatConfidence(
        level=calculation.tier.value,
        derivation=calculation.derivation,
        resolved_count=calculation.resolved_count,
        rejected_count=calculation.rejected_count,
        evidence_types=calculation.distinct_citation_types,
    )


def _reasoning(result: ChatResult) -> ChatReasoning | None:
    if result.trace is None:
        return None
    trace = result.trace
    return ChatReasoning(
        matched_concept=trace.detected_intent.node_id,
        matched_on=trace.detected_intent.matched_label,
        pipeline_id=trace.pipeline.pipeline_id,
        pipeline_version=trace.pipeline.pipeline_version,
        constitution_version=trace.pipeline.constitution_version,
        unresolved_citations=[item.citation for item in trace.evidence_rejected],
    )


def _analysis(result: ChatResult) -> ChatQuestionAnalysis | None:
    if result.analysis is None:
        return None
    analysis = result.analysis
    return ChatQuestionAnalysis(
        intent=analysis.intent.value,
        depth=analysis.depth.value,
        complexity=analysis.complexity.value,
        language=analysis.language,
        signals=list(analysis.signals),
    )
