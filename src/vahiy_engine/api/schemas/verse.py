"""Request/response schemas for /verse."""

from pydantic import BaseModel


class VerseResponse(BaseModel):
    osis: str
    chapter: int
    verse: int
    text: str
    translation: str
