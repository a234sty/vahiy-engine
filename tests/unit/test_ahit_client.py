"""Unit tests for the Ahit Corpus client."""

import json
from pathlib import Path

import pytest

from vahiy_engine.sources.ahit.client import AhitCorpusClient, VerseNotFoundError
from vahiy_engine.sources.osis import parse_osis


@pytest.fixture
def corpus_path(tmp_path: Path) -> Path:
    book_file = tmp_path / "Gen.json"
    book_file.write_text(
        json.dumps({"book": "Gen", "chapters": {"1": {"1": "In the beginning..."}}}),
        encoding="utf-8",
    )
    return tmp_path


def test_get_verse_returns_matching_text(corpus_path: Path) -> None:
    client = AhitCorpusClient(corpus_path=corpus_path)

    verse = client.get_verse(parse_osis("Gen.1.1"))

    assert verse.osis == "Gen.1.1"
    assert verse.text == "In the beginning..."


def test_get_verse_raises_for_missing_verse(corpus_path: Path) -> None:
    client = AhitCorpusClient(corpus_path=corpus_path)

    with pytest.raises(VerseNotFoundError):
        client.get_verse(parse_osis("Gen.1.99"))


def test_get_verse_raises_for_missing_book(corpus_path: Path) -> None:
    client = AhitCorpusClient(corpus_path=corpus_path)

    with pytest.raises(FileNotFoundError):
        client.get_verse(parse_osis("Exod.1.1"))
