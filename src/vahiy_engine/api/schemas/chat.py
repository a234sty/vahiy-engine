"""Request/response schemas for /chat.

Everything the reasoning layer adds is optional with a default, so a client
written against the earlier Bible-only response keeps working unchanged.
"""

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


class ChatLexiconSourceItem(BaseModel):
    strongs_number: str
    lemma: str
    transliteration: str | None
    definition: str


class ChatQuranSourceItem(BaseModel):
    """A Qur'anic citation, addressed in its own surah:ayah shape rather than
    forced into the Bible's book/chapter/verse fields."""

    citation: str
    surah: int
    ayah: int
    text: str


class ChatConfidence(BaseModel):
    """How well-supported the answer is, as a derivation rather than a bare
    label -- `derivation` states in words why the tier is what it is, so the
    number of sources behind an answer is inspectable, not asserted."""

    level: str
    derivation: str
    resolved_count: int
    rejected_count: int
    evidence_types: list[str]


class ChatReasoning(BaseModel):
    """Provenance for the answer: which curated concept the question was
    matched to, what matched it, which pipeline version produced it, and
    which curated citations could not be resolved.

    This is the reasoning trace surfaced to the caller -- the same structured
    fields the engine's reproducibility test compares between runs, so an
    answer can be re-derived and checked rather than taken on trust.
    """

    matched_concept: str
    matched_on: str
    pipeline_id: str
    pipeline_version: str
    constitution_version: str
    unresolved_citations: list[str] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSourceItem]
    lexicon_sources: list[ChatLexiconSourceItem] = []
    quran_sources: list[ChatQuranSourceItem] = []
    confidence: ChatConfidence | None = None
    reasoning: ChatReasoning | None = None
