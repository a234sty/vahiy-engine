"""Corpus loader interface."""

from abc import ABC, abstractmethod
from pathlib import Path


class BookLoader(ABC):
    """Loads a single book's chapter/verse text from a corpus directory."""

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """The file extension (without a dot) this loader expects, e.g. "json" or "xml"."""

    @abstractmethod
    def load(self, corpus_path: Path, book: str) -> dict[int, dict[int, str]]:
        """Return {chapter: {verse: text}} for the given book."""
