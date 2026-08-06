"""Parses free-text Bible references (English and Turkish) into book/chapter/verse."""

import re

BOOK_ALIASES: dict[str, str] = {
    "genesis": "Gen",
    "gen": "Gen",
    "tekvin": "Gen",
    "john": "John",
    "yuhanna": "John",
    "yuh": "John",
}
"""Maps a lowercased book name/abbreviation (English or Turkish) to its canonical OSIS book code."""

_REFERENCE_PATTERN = re.compile(r"^\s*(?P<book>.+?)\s+(?P<chapter>\d+)\s*:\s*(?P<verse>\d+)\s*$")


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
