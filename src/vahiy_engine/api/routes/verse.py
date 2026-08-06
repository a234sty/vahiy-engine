"""GET /verse endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Query

from vahiy_engine.api.schemas.verse import VerseResponse
from vahiy_engine.sources.ahit.client import (
    AhitCorpusClient,
    UnknownTranslationError,
    VerseNotFoundError,
    get_ahit_client,
)
from vahiy_engine.sources.osis import InvalidOsisReferenceError, parse_osis

router = APIRouter()


@router.get("/verse", response_model=VerseResponse)
async def get_verse(
    osis: str = Query(..., description="OSIS verse reference, e.g. Gen.1.1"),
    translation: str | None = Query(
        None, description="Translation id, e.g. KJV, YTC, SBLGNT. Defaults to KJV."
    ),
    client: AhitCorpusClient = Depends(get_ahit_client),
) -> VerseResponse:
    try:
        reference = parse_osis(osis)
    except InvalidOsisReferenceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        verse = client.get_verse(reference, translation)
    except UnknownTranslationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail=f"Book '{reference.book}' not found in Ahit Corpus"
        ) from exc
    except VerseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return VerseResponse(
        osis=verse.osis,
        chapter=verse.chapter,
        verse=verse.verse,
        text=verse.text,
        translation=verse.translation,
    )
