"""Unit tests for search normalization and indexing."""

from collections.abc import Iterator

from vahiy_engine.search.index import build_index, normalize
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.models import Verse
from vahiy_engine.sources.osis import OsisReference


def test_normalize_lowercases_ascii_text() -> None:
    assert normalize("In The Beginning") == "in the beginning"


def test_normalize_preserves_turkish_letters_other_than_i() -> None:
    assert normalize("çĞöŞü ÇĞÖŞÜ") == "çğöşü çğöşü"


def test_normalize_folds_all_turkish_i_variants_to_one_form() -> None:
    # "ı" (dotless), ASCII "I", "İ" (dotted) and "i" must all fold together so
    # plain-ASCII input reliably matches correctly-cased Turkish text.
    variants = ["tanrı", "TANRI", "Tanrı", "TANRİ"]
    assert len({normalize(v) for v in variants}) == 1


class FakeCorpus(CorpusClient):
    def __init__(self, verses: list[Verse]) -> None:
        self._verses = verses

    def get_verse(self, reference: OsisReference) -> Verse:
        raise NotImplementedError

    def iter_verses(self) -> Iterator[Verse]:
        yield from self._verses


def test_build_index_normalizes_every_verse_in_corpus_order() -> None:
    verses = [
        Verse(osis="Gen.1.1", book="Gen", chapter=1, verse=1, text="In The Beginning"),
        Verse(osis="John.1.1", book="John", chapter=1, verse=1, text="Tanrı"),
    ]
    index = build_index(FakeCorpus(verses))

    assert [iv.normalized_text for iv in index] == ["in the beginning", "tanri"]
    assert [iv.verse.osis for iv in index] == ["Gen.1.1", "John.1.1"]
