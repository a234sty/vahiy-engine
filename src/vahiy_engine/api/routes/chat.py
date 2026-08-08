"""POST /chat endpoint."""

from fastapi import APIRouter, Depends

from vahiy_engine.api.schemas.chat import (
    ChatConfidence,
    ChatLexiconSourceItem,
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
from vahiy_engine.providers.llm import get_llm_provider
from vahiy_engine.providers.llm.base import LLMProvider
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
    result = run_chat_pipeline(
        corpus, provider, request.message, lexicon=lexicon, quran=quran, graph=graph
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
