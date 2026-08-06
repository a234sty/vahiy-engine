"""Unit tests for the lexicon layer's abstract interfaces and model.

No real Strong's XML parsing happens here — that's GreekStrongsXmlLoader and
HebrewStrongsXmlLoader (later commits). This only proves the shape of the
abstraction itself, the same way the corpus layer's ABCs were proven before
any concrete loader existed.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import ValidationError

from vahiy_engine.lexicon.client import LexiconClient
from vahiy_engine.lexicon.loaders.base import LexiconLoader
from vahiy_engine.lexicon.models import LexiconEntry


def test_lexicon_entry_requires_its_core_fields() -> None:
    with pytest.raises(ValidationError):
        LexiconEntry()  # type: ignore[call-arg]


def test_lexicon_entry_optional_fields_default_to_none() -> None:
    entry = LexiconEntry(
        strongs_number="G3056",
        language="greek",
        lemma="λόγος",
        definition="something said",
    )

    assert entry.transliteration is None
    assert entry.pronunciation is None
    assert entry.kjv_translation is None


def test_lexicon_entry_accepts_all_fields() -> None:
    entry = LexiconEntry(
        strongs_number="G3056",
        language="greek",
        lemma="λόγος",
        transliteration="logos",
        pronunciation="log'-os",
        definition="something said",
        kjv_translation="word",
    )

    assert entry.strongs_number == "G3056"
    assert entry.language == "greek"
    assert entry.lemma == "λόγος"
    assert entry.transliteration == "logos"
    assert entry.pronunciation == "log'-os"
    assert entry.kjv_translation == "word"


class FakeLexiconLoader(LexiconLoader):
    """Minimal loader test double, purely to prove the ABC's shape."""

    language = "greek"

    def load(self, lexicon_path: Path) -> dict[str, LexiconEntry]:
        return {
            "G3056": LexiconEntry(
                strongs_number="G3056",
                language="greek",
                lemma="λόγος",
                definition="something said",
            )
        }


def test_lexicon_loader_reports_its_language() -> None:
    assert FakeLexiconLoader().language == "greek"


def test_lexicon_loader_load_returns_entries_keyed_by_strongs_number(tmp_path: Path) -> None:
    entries = FakeLexiconLoader().load(tmp_path / "unused.xml")

    assert entries["G3056"].lemma == "λόγος"


class FakeLexiconClient(LexiconClient):
    """Minimal client test double, purely to prove the ABC's shape."""

    def __init__(self, entries: dict[str, LexiconEntry]) -> None:
        self._entries = entries

    def get_entry(self, strongs_number: str) -> LexiconEntry:
        return self._entries[strongs_number]

    def iter_entries(self, language: str | None = None) -> Iterator[LexiconEntry]:
        for entry in self._entries.values():
            if language is None or entry.language == language:
                yield entry


def test_lexicon_client_get_entry_returns_the_matching_entry() -> None:
    logos = LexiconEntry(
        strongs_number="G3056", language="greek", lemma="λόγος", definition="something said"
    )
    client = FakeLexiconClient({"G3056": logos})

    assert client.get_entry("G3056") is logos


def test_lexicon_client_iter_entries_filters_by_language() -> None:
    logos = LexiconEntry(
        strongs_number="G3056", language="greek", lemma="λόγος", definition="something said"
    )
    ab = LexiconEntry(strongs_number="H1", language="hebrew", lemma="אָב", definition="father")
    client = FakeLexiconClient({"G3056": logos, "H1": ab})

    assert list(client.iter_entries(language="greek")) == [logos]
    assert list(client.iter_entries(language="hebrew")) == [ab]
    assert {e.strongs_number for e in client.iter_entries()} == {"G3056", "H1"}
