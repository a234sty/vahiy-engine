"""Knowledge Graph node and edge models."""

from pydantic import BaseModel, Field, model_validator


class Node(BaseModel):
    """A concept, person, or lexical item.

    `labels` maps a language code to that node's name in that language
    (e.g. {"en": "Abraham", "he": "אַבְרָהָם", "ar": "إبراهيم", "tr": "İbrahim"}),
    giving one node a stable multilingual identity rather than one node per
    language, per KM-1's multilingual concept identity requirement.
    """

    id: str
    type: str
    labels: dict[str, str] = Field(default_factory=dict)
    notes: str | None = None


class Edge(BaseModel):
    """A relationship from `source_id`, to another node and/or to a citation.

    At least one of `target_id` (another node) or `citation` (external
    evidence this relationship rests on) must be given — an edge that points
    at neither is not evidence of anything. Both may be given together (e.g.
    "YHWH derives_from Hayah, per Exodus 3:14").
    """

    source_id: str
    type: str
    target_id: str | None = None
    citation: str | None = None
    citation_type: str | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _requires_target_or_citation(self) -> "Edge":
        if self.target_id is None and self.citation is None:
            raise ValueError("An edge must have a target_id, a citation, or both")
        return self
