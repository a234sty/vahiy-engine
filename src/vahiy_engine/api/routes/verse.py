"""GET /verse endpoint."""

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query

from vahiy_engine.api.schemas.verse import VerseResponse
from vahiy_engine.config import settings
from vahiy_engine.sources.ahit.client import AhitCorpusClient, VerseNotFoundError
from vahiy_engine.sources.osis import InvalidOsisReferenceError, parse_osis

router = APIRouter()


@lru_cache
def get_ahit_client() -> AhitCorpusClient:
    return AhitCorpusClient(corpus_path=Path(settings.ahit_corpus_path))


@router.get("/verse", response_model=VerseResponse)
async def get_verse(
    osis: str = Query(..., description="OSIS verse reference, e.g. Gen.1.1"),
    client: AhitCorpusClient = Depends(get_ahit_client),
) -> VerseResponse:
    try:
        reference = parse_osis(osis)
    except InvalidOsisReferenceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        verse = client.get_verse(reference)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail=f"Book '{reference.book}' not found in Ahit Corpus"
        ) from exc
    except VerseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return VerseResponse(osis=verse.osis, chapter=verse.chapter, verse=verse.verse, text=verse.text)
