"""Parses free-text Bible references (English and Turkish) into book/chapter/verse."""

import re

BOOK_ALIASES: dict[str, str] = {
    "genesis": "Gen",
    "gen": "Gen",
    "tekvin": "Gen",
    "exodus": "Exod",
    "exod": "Exod",
    "john": "John",
    "yuhanna": "John",
    "yuh": "John",
}
"""Maps a lowercased book name/abbreviation (English or Turkish) to its canonical OSIS book code."""

_REFERENCE_PATTERN = re.compile(r"^\s*(?P<book>.+?)\s+(?P<chapter>\d+)\s*:\s*(?P<verse>\d+)\s*$")

# Built from BOOK_ALIASES (longest alias first, so alternation prefers the
# fuller name at a given start position) rather than a generic `.+?` book
# group: find_references() scans free text, where an unbounded `.+?` would
# have no reliable stopping point. Word boundaries keep "Exod" from matching
# inside an unrelated longer word.
_EMBEDDED_REFERENCE_PATTERN = re.compile(
    r"\b(?P<book>"
    + "|".join(sorted((re.escape(alias) for alias in BOOK_ALIASES), key=len, reverse=True))
    + r")\b\.?\s+(?P<chapter>\d+)\s*:\s*(?P<verse>\d+)",
    re.IGNORECASE,
)


class ReferenceParseError(ValueError):
    """Raised when a string is not a recognizable Bible reference."""


def parse_reference(query: str) -> tuple[str, int, int]:
    """Parse a free-text Bible reference into (book, chapter, verse).

    Accepts English and Turkish book names/abbreviations, e.g. "Genesis 1:1",
    "Gen 1:1", "Tekvin 1:1", "John 3:16", "Yuhanna 3:16", "Yuh 3:16". Book
    matching is case-insensitive and looked up in BOOK_ALIASES; the returned
    book is always the canonical code ("Gen" or "John").

    Args:
        query: A reference string shaped like "<book> <chapter>:<verse>".

    Returns:
        A (book, chapter, verse) tuple, e.g. ("Gen", 1, 1).

    Raises:
        ReferenceParseError: if `query` doesn't match the expected shape, or
            its book name isn't a recognized alias.
    """
    match = _REFERENCE_PATTERN.match(query)
    if match is None:
        raise ReferenceParseError(f"'{query}' is not a valid Bible reference")

    book_name = match.group("book").strip()
    book = BOOK_ALIASES.get(book_name.lower())
    if book is None:
        raise ReferenceParseError(f"Unknown book '{book_name}' in '{query}'")

    chapter = int(match.group("chapter"))
    verse = int(match.group("verse"))

    return book, chapter, verse


def find_references(text: str) -> list[tuple[str, int, int]]:
    """Find every Bible reference embedded anywhere in free text.

    Unlike `parse_reference`, `text` doesn't have to be *only* a reference --
    "How does Exodus 3:14 explain the meaning of God's name?" finds one
    reference and ignores the surrounding sentence. Matching is scoped to
    the known book names/abbreviations in BOOK_ALIASES (not a generic "any
    word(s) before a chapter:verse" pattern), so this only fires on an
    actual recognized book name, never an arbitrary word that happens to
    precede a number pair.

    Returns references in the order they appear, as (book, chapter, verse)
    tuples with the canonical OSIS book code -- empty if none are found.
    """
    references = []
    for match in _EMBEDDED_REFERENCE_PATTERN.finditer(text):
        book = BOOK_ALIASES[match.group("book").lower()]
        chapter = int(match.group("chapter"))
        verse = int(match.group("verse"))
        references.append((book, chapter, verse))
    return references
