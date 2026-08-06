"""Loader for ahit-corpus's per-verse-list JSON translation format.

Distinct from JsonBookLoader's simpler demo-data shape
(`{"chapters": {"1": {"1": "text"}}}`). ahit-corpus translations (Greek NT,
Turkish YTC) are shaped:

    {
      "metadata": {"osis": "John", "language": "...", "translation": "...", ...},
      "chapters": {
        "1": [
          {"osis": "John.1.1", "chapter": 1, "verse": 1, "text": "..."},
          ...
        ]
      }
    }

i.e. each chapter maps to a *list* of verse objects, not a verse-keyed dict.
"""

import json
from pathlib import Path

from vahiy_engine.sources.loaders.base import BookLoader


class VerseListJsonLoader(BookLoader):
    """Loads a book from ahit-corpus's `{"metadata": ..., "chapters": {"1": [...]}}` shape."""

    def load(self, corpus_path: Path, book: str) -> dict[int, dict[int, str]]:
        book_file = corpus_path / f"{book}.json"
        if not book_file.is_file():
            raise FileNotFoundError(f"No corpus file found for book '{book}' at {book_file}")

        with book_file.open(encoding="utf-8") as f:
            raw = json.load(f)

        declared_osis = raw.get("metadata", {}).get("osis")
        if declared_osis and declared_osis != book:
            raise ValueError(
                f"{book_file} declares metadata.osis '{declared_osis}' but was loaded as "
                f"book '{book}'"
            )

        chapters: dict[int, dict[int, str]] = {}
        for chapter_key, verse_entries in raw.get("chapters", {}).items():
            verses = {int(entry["verse"]): entry["text"] for entry in verse_entries}
            chapters[int(chapter_key)] = verses

        return chapters
