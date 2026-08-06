"""Ahit Corpus lexicon client implementation."""

from collections.abc import Iterator
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from vahiy_engine.config import settings
from vahiy_engine.lexicon.client import LexiconClient
from vahiy_engine.lexicon.loaders.base import LexiconLoader
from vahiy_engine.lexicon.loaders.greek_strongs_xml_loader import GreekStrongsXmlLoader
from vahiy_engine.lexicon.loaders.hebrew_strongs_xml_loader import HebrewStrongsXmlLoader
from vahiy_engine.lexicon.models import LexiconEntry


class EntryNotFoundError(LookupError):
    """Raised when a requested Strong's number isn't in any registered lexicon."""


@dataclass(frozen=True)
class LexiconSource:
    """Where one language's lexicon file lives, and how to parse it.

    Unlike the corpus layer's TranslationSource, a lexicon source is
    always exactly one file — ahit-corpus ships one file per language
    (lexicon/greek/strongsgreek.xml, lexicon/hebrew/StrongHebrewG.xml)
    covering that whole language's dictionary, not a directory of
    per-book files.
    """

    path: Path
    loader: LexiconLoader


class AhitLexiconClient(LexiconClient):
    """Reads Strong's dictionary entries from one or more registered lexicons.

    Mirrors AhitCorpusClient's registry pattern: adding another lexicon (a
    new language, or a different edition of an existing one) is
    registering another LexiconSource here; it never requires changing
    this class.
    """

    def __init__(self, sources: list[LexiconSource]) -> None:
        self._sources = sources
        self._entries_cache: dict[str, LexiconEntry] | None = None

    def get_entry(self, strongs_number: str) -> LexiconEntry:
        try:
            return self._load_all()[strongs_number]
        except KeyError as exc:
            raise EntryNotFoundError(f"No lexicon entry found for '{strongs_number}'") from exc

    def iter_entries(self, language: str | None = None) -> Iterator[LexiconEntry]:
        entries = self._load_all()
        for strongs_number in sorted(entries, key=_sort_key):
            entry = entries[strongs_number]
            if language is None or entry.language == language:
                yield entry

    def _load_all(self) -> dict[str, LexiconEntry]:
        if self._entries_cache is None:
            merged: dict[str, LexiconEntry] = {}
            for source in self._sources:
                merged.update(source.loader.load(source.path))
            self._entries_cache = merged
        return self._entries_cache


def _sort_key(strongs_number: str) -> tuple[str, int]:
    return (strongs_number[0], int(strongs_number[1:]))


@lru_cache
def get_lexicon_client() -> AhitLexiconClient:
    sources: list[LexiconSource] = []

    if settings.ahit_corpus_root:
        corpus_root = Path(settings.ahit_corpus_root)

        greek_path = corpus_root / "lexicon" / "greek" / "strongsgreek.xml"
        if greek_path.is_file():
            sources.append(LexiconSource(path=greek_path, loader=GreekStrongsXmlLoader()))

        hebrew_path = corpus_root / "lexicon" / "hebrew" / "StrongHebrewG.xml"
        if hebrew_path.is_file():
            sources.append(LexiconSource(path=hebrew_path, loader=HebrewStrongsXmlLoader()))

    return AhitLexiconClient(sources=sources)
