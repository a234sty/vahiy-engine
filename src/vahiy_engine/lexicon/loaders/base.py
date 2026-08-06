"""Lexicon loader interface."""

from abc import ABC, abstractmethod
from pathlib import Path

from vahiy_engine.lexicon.models import LexiconEntry


class LexiconLoader(ABC):
    """Parses one lexicon file into every entry it contains.

    Unlike `BookLoader`, a lexicon isn't split across per-book files — each
    source (e.g. ahit-corpus's Greek or Hebrew Strong's dictionary) is a
    single file covering its whole language, so a loader parses that one
    file wholesale rather than being asked for one book at a time.
    """

    @property
    @abstractmethod
    def language(self) -> str:
        """The language this loader parses (e.g. "greek", "hebrew")."""

    @abstractmethod
    def load(self, lexicon_path: Path) -> dict[str, LexiconEntry]:
        """Return {strongs_number: entry} for every entry in `lexicon_path`."""
