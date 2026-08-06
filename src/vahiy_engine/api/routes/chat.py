"""POST /chat endpoint."""

from fastapi import APIRouter, Depends

from vahiy_engine.api.schemas.chat import (
    ChatLexiconSourceItem,
    ChatRequest,
    ChatResponse,
    ChatSourceItem,
)
from vahiy_engine.lexicon.ahit.client import AhitLexiconClient, get_lexicon_client
from vahiy_engine.pipeline.chat_pipeline import run_chat_pipeline
from vahiy_engine.providers.llm import get_llm_provider
from vahiy_engine.providers.llm.base import LLMProvider
from vahiy_engine.sources.ahit.client import AhitCorpusClient, get_ahit_client

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def post_chat(
    request: ChatRequest,
    corpus: AhitCorpusClient = Depends(get_ahit_client),
    provider: LLMProvider = Depends(get_llm_provider),
    lexicon: AhitLexiconClient = Depends(get_lexicon_client),
) -> ChatResponse:
    result = run_chat_pipeline(corpus, provider, request.message, lexicon=lexicon)

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
    )
