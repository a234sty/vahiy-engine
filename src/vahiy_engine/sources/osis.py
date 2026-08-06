"""OSIS reference parsing and validation."""

from dataclasses import dataclass


class InvalidOsisReferenceError(ValueError):
    """Raised when a string is not a valid OSIS verse reference."""


@dataclass(frozen=True)
class OsisReference:
    book: str
    chapter: int
    verse: int

    @property
    def osis(self) -> str:
        return f"{self.book}.{self.chapter}.{self.verse}"


def parse_osis(reference: str) -> OsisReference:
    """Parse a single-verse OSIS reference such as 'Gen.1.1' into its parts."""
    parts = reference.strip().split(".")

    if len(parts) != 3 or not parts[0]:
        raise InvalidOsisReferenceError(f"'{reference}' is not a valid OSIS verse reference")

    book, chapter, verse = parts

    try:
        chapter_number = int(chapter)
        verse_number = int(verse)
    except ValueError as exc:
        raise InvalidOsisReferenceError(
            f"'{reference}' is not a valid OSIS verse reference"
        ) from exc

    if chapter_number < 1 or verse_number < 1:
        raise InvalidOsisReferenceError(f"'{reference}' is not a valid OSIS verse reference")

    return OsisReference(book=book, chapter=chapter_number, verse=verse_number)
