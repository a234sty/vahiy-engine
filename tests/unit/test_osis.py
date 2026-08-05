"""Unit tests for OSIS reference parsing."""

import pytest

from vahiy_engine.sources.osis import InvalidOsisReferenceError, OsisReference, parse_osis


def test_parse_osis_returns_book_chapter_verse() -> None:
    assert parse_osis("Gen.1.1") == OsisReference(book="Gen", chapter=1, verse=1)


def test_parse_osis_roundtrips_to_canonical_string() -> None:
    assert parse_osis("John.3.16").osis == "John.3.16"


@pytest.mark.parametrize(
    "reference",
    [
        "Gen1.1",
        "Gen.1",
        "Gen.1.1.1",
        "Gen.one.1",
        "Gen.1.one",
        "Gen.0.1",
        "Gen.1.0",
        ".1.1",
        "",
    ],
)
def test_parse_osis_rejects_invalid_references(reference: str) -> None:
    with pytest.raises(InvalidOsisReferenceError):
        parse_osis(reference)
