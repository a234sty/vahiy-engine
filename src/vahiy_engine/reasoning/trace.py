"""The reasoning trace: RSN-5's schema, in code.

Every field here maps directly to RSN-5 in vahiy-engine-brain: detected
intent, evidence retrieved, evidence rejected, the confidence calculation
(a derivation, not a bare label), and the pipeline identity the run executed
under. This is what FND-5's Independent Implementation Test compares across
implementations — the structured fields, not prose built from them.
"""

from enum import StrEnum

from pydantic import BaseModel


class ConfidenceTier(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class EvidenceItem(BaseModel):
    """One piece of evidence that was actually resolved and used.

    `text` is the readable rendering an answer can quote. `original_text`,
    when the corpus has one, is the same passage in its source language --
    carried alongside rather than instead of the translation, because an
    answer that shows only pointed Hebrew forces the model to translate it
    itself, and an answer that shows only a translation cannot support a
    claim about the original wording. Both present means neither has to be
    invented.
    """

    citation: str
    citation_type: str
    text: str
    role: str = "primary"
    note: str | None = None
    original_text: str | None = None
    original_language: str | None = None
    transliteration: str | None = None


class RejectedEvidenceItem(BaseModel):
    """One piece of evidence the knowledge graph named, that did not make it
    into the answer — present even when empty, per RSN-5: an empty rejected
    list is itself information (nothing needed excluding), not the same
    claim as never having checked."""

    citation: str
    citation_type: str
    reason_code: str


class DetectedIntent(BaseModel):
    pipeline_id: str
    node_id: str
    matched_label: str


class ConfidenceCalculation(BaseModel):
    tier: ConfidenceTier
    resolved_count: int
    rejected_count: int
    distinct_citation_types: list[str]
    derivation: str


class PipelineInfo(BaseModel):
    pipeline_id: str
    pipeline_version: str
    constitution_version: str


class ReasoningTrace(BaseModel):
    detected_intent: DetectedIntent
    evidence_retrieved: list[EvidenceItem]
    evidence_rejected: list[RejectedEvidenceItem]
    confidence: ConfidenceCalculation
    pipeline: PipelineInfo
