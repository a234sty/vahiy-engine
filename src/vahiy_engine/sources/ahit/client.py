"""Ahit Corpus client implementation."""

from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from vahiy_engine.config import settings
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.loaders.base import BookLoader
from vahiy_engine.sources.loaders.json_loader import JsonBookLoader
from vahiy_engine.sources.models import Verse
from vahiy_engine.sources.osis import OsisReference


class VerseNotFoundError(LookupError):
    """Raised when a requested verse does not exist in the corpus."""


class AhitCorpusClient(CorpusClient):
    """Reads Bible text from a configurable local Ahit Corpus directory."""

    def __init__(self, corpus_path: Path, loader: BookLoader | None = None) -> None:
        self._corpus_path = corpus_path
        self._loader = loader or JsonBookLoader()
        self._book_cache: dict[str, dict[int, dict[int, str]]] = {}

    def get_verse(self, reference: OsisReference) -> Verse:
        chapters = self._load_book(reference.book)

        chapter = chapters.get(reference.chapter)
        text = chapter.get(reference.verse) if chapter else None
        if text is None:
            raise VerseNotFoundError(f"Verse '{reference.osis}' was not found in Ahit Corpus")

        return Verse(
            osis=reference.osis,
            book=reference.book,
            chapter=reference.chapter,
            verse=reference.verse,
            text=text,
        )

    def iter_verses(self) -> Iterator[Verse]:
        for book in self._list_books():
            chapters = self._load_book(book)
            for chapter_number in sorted(chapters):
                for verse_number in sorted(chapters[chapter_number]):
                    osis = f"{book}.{chapter_number}.{verse_number}"
                    yield Verse(
                        osis=osis,
                        book=book,
                        chapter=chapter_number,
                        verse=verse_number,
                        text=chapters[chapter_number][verse_number],
                    )

    def _list_books(self) -> list[str]:
        return sorted(f.stem for f in self._corpus_path.glob("*.json"))

    def _load_book(self, book: str) -> dict[int, dict[int, str]]:
        if book not in self._book_cache:
            self._book_cache[book] = self._loader.load(self._corpus_path, book)
        return self._book_cache[book]


@lru_cache
def get_ahit_client() -> AhitCorpusClient:
    return AhitCorpusClient(corpus_path=Path(settings.ahit_corpus_path))
