"""Request/response schemas for /chat."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatSourceItem(BaseModel):
    osis: str
    chapter: int
    verse: int
    text: str
    score: int
    translation: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSourceItem]
