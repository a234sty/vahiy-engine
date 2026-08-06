"""Unit tests for AhitLexiconClient's multi-source registry."""

from pathlib import Path

import pytest

from vahiy_engine.lexicon.ahit.client import AhitLexiconClient, EntryNotFoundError, LexiconSource
from vahiy_engine.lexicon.loaders.base import LexiconLoader
from vahiy_engine.lexicon.models import LexiconEntry


class FakeLexiconLoader(LexiconLoader):
    """Minimal loader test double — parses "number|lemma|definition" lines."""

    def __init__(self, language: str) -> None:
        self._language = language

    @property
    def language(self) -> str:
        return self._language

    def load(self, lexicon_path: Path) -> dict[str, LexiconEntry]:
        entries: dict[str, LexiconEntry] = {}
        for line in lexicon_path.read_text(encoding="utf-8").splitlines():
            number, lemma, definition = line.split("|")
            entries[number] = LexiconEntry(
                strongs_number=number,
                language=self._language,
                lemma=lemma,
                definition=definition,
            )
        return entries


@pytest.fixture
def greek_path(tmp_path: Path) -> Path:
    path = tmp_path / "greek.txt"
    path.write_text("G3056|λόγος|something said\nG1|Α|first letter", encoding="utf-8")
    return path


@pytest.fixture
def hebrew_path(tmp_path: Path) -> Path:
    path = tmp_path / "hebrew.txt"
    path.write_text("H1|אָב|father\nH165|אֱהִי|where", encoding="utf-8")
    return path


@pytest.fixture
def client(greek_path: Path, hebrew_path: Path) -> AhitLexiconClient:
    return AhitLexiconClient(
        sources=[
            LexiconSource(path=greek_path, loader=FakeLexiconLoader("greek")),
            LexiconSource(path=hebrew_path, loader=FakeLexiconLoader("hebrew")),
        ]
    )


def test_get_entry_returns_matching_entry(client: AhitLexiconClient) -> None:
    entry = client.get_entry("G3056")

    assert entry.lemma == "λόγος"
    assert entry.definition == "something said"


def test_get_entry_raises_for_unknown_number(client: AhitLexiconClient) -> None:
    with pytest.raises(EntryNotFoundError):
        client.get_entry("G99999")


def test_iter_entries_yields_every_registered_source_when_unfiltered(
    client: AhitLexiconClient,
) -> None:
    numbers = [e.strongs_number for e in client.iter_entries()]

    assert set(numbers) == {"G3056", "G1", "H1", "H165"}


def test_iter_entries_filters_by_language(client: AhitLexiconClient) -> None:
    greek_numbers = [e.strongs_number for e in client.iter_entries(language="greek")]
    hebrew_numbers = [e.strongs_number for e in client.iter_entries(language="hebrew")]

    assert greek_numbers == ["G1", "G3056"]
    assert hebrew_numbers == ["H1", "H165"]


def test_iter_entries_orders_deterministically_by_language_then_number(
    client: AhitLexiconClient,
) -> None:
    numbers = [e.strongs_number for e in client.iter_entries()]

    assert numbers == ["G1", "G3056", "H1", "H165"]


def test_client_with_no_sources_has_no_entries() -> None:
    empty_client = AhitLexiconClient(sources=[])

    assert list(empty_client.iter_entries()) == []
    with pytest.raises(EntryNotFoundError):
        empty_client.get_entry("G1")
