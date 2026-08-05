"""Request/response schemas for /search."""

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    osis: str
    chapter: int
    verse: int
    text: str
    score: int


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
