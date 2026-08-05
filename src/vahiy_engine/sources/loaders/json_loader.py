"""JSON corpus loader."""

import json
from pathlib import Path

from vahiy_engine.sources.loaders.base import BookLoader


class JsonBookLoader(BookLoader):
    """Loads a book from a '<book>.json' file shaped as {"chapters": {"1": {"1": "..."}}}."""

    def load(self, corpus_path: Path, book: str) -> dict[int, dict[int, str]]:
        book_file = corpus_path / f"{book}.json"
        if not book_file.is_file():
            raise FileNotFoundError(f"No corpus file found for book '{book}' at {book_file}")

        with book_file.open(encoding="utf-8") as f:
            raw = json.load(f)

        return {
            int(chapter): {int(verse): text for verse, text in verses.items()}
            for chapter, verses in raw.get("chapters", {}).items()
        }
