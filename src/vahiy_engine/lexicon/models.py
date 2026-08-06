"""Lexicon entry domain model."""

from pydantic import BaseModel


class LexiconEntry(BaseModel):
    """A single Strong's-numbered dictionary entry (Hebrew or Greek).

    `strongs_number` is normalized to the spec's own citation form — a
    language letter followed by the number with no leading zeros (e.g.
    "G3056", "H1") — regardless of how the source file itself formats the
    number (ahit-corpus's Greek dictionary zero-pads it: strongs="03056").
    """

    strongs_number: str
    language: str
    lemma: str
    transliteration: str | None = None
    pronunciation: str | None = None
    definition: str
    kjv_translation: str | None = None
