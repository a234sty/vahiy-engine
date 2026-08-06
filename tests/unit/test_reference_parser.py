"""Unit tests for the free-text Bible reference parser."""

import pytest

from vahiy_engine.search.reference_parser import (
    BOOK_ALIASES,
    ReferenceParseError,
    parse_reference,
)


@pytest.mark.parametrize(
    "query,expected",
    [
        ("Genesis 1:1", ("Gen", 1, 1)),
        ("Gen 1:1", ("Gen", 1, 1)),
        ("Tekvin 1:1", ("Gen", 1, 1)),
        ("John 3:16", ("John", 3, 16)),
        ("Yuhanna 3:16", ("John", 3, 16)),
        ("Yuh 3:16", ("John", 3, 16)),
    ],
)
def test_parse_reference_returns_book_chapter_verse(
    query: str, expected: tuple[str, int, int]
) -> None:
    assert parse_reference(query) == expected


@pytest.mark.parametrize(
    "query,expected",
    [
        ("GENESIS 1:1", ("Gen", 1, 1)),
        ("genesis 1:1", ("Gen", 1, 1)),
        ("JoHn 3:16", ("John", 3, 16)),
        ("YUH 3:16", ("John", 3, 16)),
    ],
)
def test_parse_reference_is_case_insensitive(query: str, expected: tuple[str, int, int]) -> None:
    assert parse_reference(query) == expected


@pytest.mark.parametrize(
    "query,expected",
    [
        ("  Gen 1:1  ", ("Gen", 1, 1)),
        ("John 3 : 16", ("John", 3, 16)),
        ("Gen   1:1", ("Gen", 1, 1)),
    ],
)
def test_parse_reference_tolerates_extra_whitespace(
    query: str, expected: tuple[str, int, int]
) -> None:
    assert parse_reference(query) == expected


@pytest.mark.parametrize(
    "query",
    [
        "Gen1:1",
        "Gen 1",
        "Gen :1",
        "1:1",
        "",
        "Gen one:1",
        "Gen 1:one",
    ],
)
def test_parse_reference_rejects_malformed_input(query: str) -> None:
    with pytest.raises(ReferenceParseError):
        parse_reference(query)


def test_parse_reference_rejects_unknown_book() -> None:
    with pytest.raises(ReferenceParseError):
        parse_reference("Exodus 1:1")


def test_book_aliases_map_to_canonical_osis_codes() -> None:
    assert BOOK_ALIASES["genesis"] == "Gen"
    assert BOOK_ALIASES["gen"] == "Gen"
    assert BOOK_ALIASES["tekvin"] == "Gen"
    assert BOOK_ALIASES["john"] == "John"
    assert BOOK_ALIASES["yuhanna"] == "John"
    assert BOOK_ALIASES["yuh"] == "John"
