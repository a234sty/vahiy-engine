"""Qur'an client implementation."""

from collections.abc import Iterator
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from vahiy_engine.config import settings
from vahiy_engine.sources.quran.loader import QuranJsonLoader
from vahiy_engine.sources.quran.models import Ayah, QuranReference

DEFAULT_EDITION = "arabic"


class AyahNotFoundError(LookupError):
    """Raised when a requested surah:ayah does not exist in the given edition."""


class UnknownEditionError(LookupError):
    """Raised when a requested edition isn't registered on this client."""


@dataclass(frozen=True)
class QuranEdition:
    """Where one edition's file lives — always exactly one file, like a lexicon source."""

    path: Path


class QuranClient:
    """Reads Qur'an text from one or more registered editions.

    Mirrors AhitLexiconClient, not AhitCorpusClient: there is no bundled
    default edition shipped with the app the way KJV is bundled for Bible
    text, so a client with zero registered editions is a valid, ungraceful
    state to construct (matching how a lexicon client can exist with no
    lexicon loaded) — callers find out at query time, via UnknownEditionError,
    not at construction time.
    """

    def __init__(
        self, editions: dict[str, QuranEdition], default_edition: str = DEFAULT_EDITION
    ) -> None:
        self._editions = editions
        self._default_edition = default_edition
        self._loader = QuranJsonLoader()
        self._cache: dict[str, dict[tuple[int, int], Ayah]] = {}

    def get_ayah(self, reference: QuranReference, edition: str | None = None) -> Ayah:
        edition_id = edition or self._default_edition
        ayat = self._load(edition_id)
        key = (reference.surah, reference.ayah)
        if key not in ayat:
            raise AyahNotFoundError(
                f"Ayah '{reference.citation}' was not found in edition '{edition_id}'"
            )
        return ayat[key]

    def available_editions(self) -> list[str]:
        """Which editions this client can actually serve, in registration order.

        Public because callers need to state honestly what this deployment
        does and does not have: a client with zero editions is a valid state
        (see the class docstring), and the difference between "the Qur'an has
        nothing on this" and "no Qur'an corpus is configured here" is exactly
        the kind of distinction this engine must not blur.
        """
        return list(self._editions)

    def iter_ayat(self, edition: str | None = None) -> Iterator[Ayah]:
        edition_id = edition or self._default_edition
        ayat = self._load(edition_id)
        for key in sorted(ayat):
            yield ayat[key]

    def _load(self, edition_id: str) -> dict[tuple[int, int], Ayah]:
        if edition_id not in self._editions:
            raise UnknownEditionError(f"Unknown Qur'an edition '{edition_id}'")
        if edition_id not in self._cache:
            self._cache[edition_id] = self._loader.load(self._editions[edition_id].path, edition_id)
        return self._cache[edition_id]


@lru_cache
def get_quran_client() -> QuranClient:
    editions: dict[str, QuranEdition] = {}

    if settings.ahit_corpus_root:
        quran_dir = Path(settings.ahit_corpus_root) / "quran"
        for edition_id, filename in (
            ("arabic", "quran.json"),
            ("en", "quran-en.json"),
            ("tr", "quran-tr.json"),
            ("transliteration", "quran-transliteration.json"),
        ):
            path = quran_dir / filename
            if path.is_file():
                editions[edition_id] = QuranEdition(path=path)

    return QuranClient(editions=editions)
