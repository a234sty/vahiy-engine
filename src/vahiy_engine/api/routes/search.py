"""GET /search endpoint."""

from fastapi import APIRouter, Depends, Query

from vahiy_engine.api.schemas.search import SearchResponse, SearchResultItem
from vahiy_engine.search.engine import search
from vahiy_engine.sources.ahit.client import AhitCorpusClient, get_ahit_client

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def get_search(
    query: str = Query(
        ..., min_length=1, description="Search text; supports partial words and exact phrases"
    ),
    client: AhitCorpusClient = Depends(get_ahit_client),
) -> SearchResponse:
    results = search(client, query)

    return SearchResponse(
        query=query,
        results=[
            SearchResultItem(
                osis=r.verse.osis,
                chapter=r.verse.chapter,
                verse=r.verse.verse,
                text=r.verse.text,
                score=r.score,
                translation=r.verse.translation,
            )
            for r in results
        ],
    )
