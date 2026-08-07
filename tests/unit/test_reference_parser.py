"""Unit tests for the free-text Bible reference parser."""

import pytest

from vahiy_engine.search.reference_parser import (
    BOOK_ALIASES,
    ReferenceParseError,
    find_chapter_references,
    find_references,
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
        parse_reference("Leviticus 1:1")


def test_book_aliases_map_to_canonical_osis_codes() -> None:
    assert BOOK_ALIASES["genesis"] == "Gen"
    assert BOOK_ALIASES["gen"] == "Gen"
    assert BOOK_ALIASES["tekvin"] == "Gen"
    assert BOOK_ALIASES["exodus"] == "Exod"
    assert BOOK_ALIASES["exod"] == "Exod"
    assert BOOK_ALIASES["john"] == "John"
    assert BOOK_ALIASES["yuhanna"] == "John"
    assert BOOK_ALIASES["yuh"] == "John"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("How does Exodus 3:14 explain the meaning of God's name?", [("Exod", 3, 14)]),
        ("What is Genesis 2:3 about?", [("Gen", 2, 3)]),
        ("No reference in this sentence at all.", []),
        (
            "Compare Genesis 1:1 with Gen 2:3 in the same question.",
            [("Gen", 1, 1), ("Gen", 2, 3)],
        ),
        ("GENESIS 1:1 in all caps", [("Gen", 1, 1)]),
    ],
)
def test_find_references_locates_embedded_references(
    text: str, expected: list[tuple[str, int, int]]
) -> None:
    assert find_references(text) == expected


def test_find_references_ignores_a_similar_but_unknown_book_name() -> None:
    assert find_references("What does Leviticus 1:1 say?") == []


def test_find_references_does_not_match_a_bare_word_before_a_number_pair() -> None:
    # "chapter 3:14" should not spuriously resolve -- only a real book alias
    # from BOOK_ALIASES may anchor a match, never an arbitrary preceding word.
    assert find_references("See chapter 3:14 of the outline.") == []


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            "How do circumcision requirements compare between Genesis 17 and Islamic practice?",
            [("Gen", 17)],
        ),
        ("Genesis 17 and Exodus 20 both matter here.", [("Gen", 17), ("Exod", 20)]),
        ("No chapter mentioned here.", []),
    ],
)
def test_find_chapter_references_locates_chapter_only_mentions(
    text: str, expected: list[tuple[str, int]]
) -> None:
    assert find_chapter_references(text) == expected


def test_find_chapter_references_does_not_also_match_a_full_verse_reference() -> None:
    # "Genesis 17:5" should be found by find_references() as a precise verse
    # citation, not additionally picked up here as a bare "Genesis 17"
    # chapter mention -- the negative lookahead exists for exactly this.
    assert find_chapter_references("See Genesis 17:5 for the renaming.") == []
