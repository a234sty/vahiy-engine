"""Verse/Passage/Source domain models."""

from pydantic import BaseModel


class Verse(BaseModel):
    osis: str
    book: str
    chapter: int
    verse: int
    text: str
