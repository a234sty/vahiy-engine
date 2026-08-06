"""Ahit Corpus client implementation."""

from collections.abc import Iterator
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from vahiy_engine.config import settings
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.loaders.base import BookLoader
from vahiy_engine.sources.loaders.json_loader import JsonBookLoader
from vahiy_engine.sources.loaders.verse_list_json_loader import VerseListJsonLoader
from vahiy_engine.sources.models import Verse
from vahiy_engine.sources.osis import OsisReference

DEFAULT_TRANSLATION = "KJV"


class VerseNotFoundError(LookupError):
    """Raised when a requested verse does not exist in the given translation."""


class UnknownTranslationError(LookupError):
    """Raised when a requested translation isn't registered on this corpus client."""


@dataclass(frozen=True)
class TranslationSource:
    """Where a translation's book files live, and how to parse them.

    `paths` may list more than one directory — e.g. in ahit-corpus, YTC's Old
    and New Testament books live in separate directories but form one
    logical translation.
    """

    paths: list[Path]
    loader: BookLoader


class AhitCorpusClient(CorpusClient):
    """Reads Bible text from one or more registered translations.

    Every translation is addressed by an id (e.g. "KJV", "YTC", "SBLGNT").
    Callers that don't care which translation they're reading — the common
    case, and every existing caller today — can omit it entirely and get
    `default_translation`. Adding another translation is registering another
    entry here; it never requires changing this class.
    """

    def __init__(
        self,
        translations: dict[str, TranslationSource],
        default_translation: str = DEFAULT_TRANSLATION,
    ) -> None:
        if default_translation not in translations:
            raise ValueError(f"default_translation '{default_translation}' is not registered")

        self._translations = translations
        self._default_translation = default_translation
        self._book_cache: dict[tuple[str, str], dict[int, dict[int, str]]] = {}

    def get_verse(self, reference: OsisReference, translation: str | None = None) -> Verse:
        translation_id = translation or self._default_translation
        chapters = self._load_book(translation_id, reference.book)

        chapter = chapters.get(reference.chapter)
        text = chapter.get(reference.verse) if chapter else None
        if text is None:
            raise VerseNotFoundError(
                f"Verse '{reference.osis}' was not found in translation '{translation_id}'"
            )

        return Verse(
            osis=reference.osis,
            book=reference.book,
            chapter=reference.chapter,
            verse=reference.verse,
            text=text,
            translation=translation_id,
        )

    def iter_verses(self, translation: str | None = None) -> Iterator[Verse]:
        translation_id = translation or self._default_translation
        for book in self._list_books(translation_id):
            chapters = self._load_book(translation_id, book)
            for chapter_number in sorted(chapters):
                for verse_number in sorted(chapters[chapter_number]):
                    osis = f"{book}.{chapter_number}.{verse_number}"
                    yield Verse(
                        osis=osis,
                        book=book,
                        chapter=chapter_number,
                        verse=verse_number,
                        text=chapters[chapter_number][verse_number],
                        translation=translation_id,
                    )

    def _source(self, translation_id: str) -> TranslationSource:
        try:
            return self._translations[translation_id]
        except KeyError as exc:
            raise UnknownTranslationError(f"Unknown translation '{translation_id}'") from exc

    def _list_books(self, translation_id: str) -> list[str]:
        source = self._source(translation_id)
        books: set[str] = set()
        for root in source.paths:
            books.update(f.stem for f in root.glob("*.json"))
        return sorted(books)

    def _load_book(self, translation_id: str, book: str) -> dict[int, dict[int, str]]:
        cache_key = (translation_id, book)
        if cache_key not in self._book_cache:
            source = self._source(translation_id)
            for root in source.paths:
                if (root / f"{book}.json").is_file():
                    self._book_cache[cache_key] = source.loader.load(root, book)
                    break
            else:
                raise FileNotFoundError(
                    f"No corpus file found for book '{book}' in translation '{translation_id}'"
                )
        return self._book_cache[cache_key]


@lru_cache
def get_ahit_client() -> AhitCorpusClient:
    translations: dict[str, TranslationSource] = {
        DEFAULT_TRANSLATION: TranslationSource(
            paths=[Path(settings.ahit_corpus_path)],
            loader=JsonBookLoader(),
        ),
    }

    if settings.ahit_corpus_root:
        corpus_root = Path(settings.ahit_corpus_root)

        ytc_paths = [
            p
            for p in (
                corpus_root / "bible" / "nt" / "translations" / "tr" / "ytc",
                corpus_root / "bible" / "ot" / "translation" / "tr",
            )
            if p.is_dir()
        ]
        if ytc_paths:
            translations["YTC"] = TranslationSource(paths=ytc_paths, loader=VerseListJsonLoader())

        sblgnt_path = corpus_root / "bible" / "nt" / "original-greek"
        if sblgnt_path.is_dir():
            translations["SBLGNT"] = TranslationSource(
                paths=[sblgnt_path], loader=VerseListJsonLoader()
            )

    return AhitCorpusClient(translations=translations)
