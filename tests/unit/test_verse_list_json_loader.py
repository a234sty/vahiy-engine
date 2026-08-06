"""Unit tests for VerseListJsonLoader, using real ahit-corpus sample content.

The fixture text below is verbatim from ahit-corpus (github.com/a234sty/ahit-corpus)
commit 6f2d539: bible/nt/original-greek/John.json and
bible/nt/translations/tr/ytc/John.json — captured by direct inspection, not
guessed, so these tests prove the loader against the real file shape.
"""

import json
from pathlib import Path

import pytest

from vahiy_engine.sources.loaders.verse_list_json_loader import VerseListJsonLoader

GREEK_JOHN_1_1 = "Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν, καὶ θεὸς ἦν ὁ λόγος. "
TURKISH_JOHN_1_1 = "Başlangıçta Söz vardı ve Söz Tanrı'yla birlikteydi ve Söz Tanrı’ydı."


def write_real_shaped_john(directory: Path, osis: str, translation: str, verses: dict) -> None:
    """Write a book file shaped exactly like the real ahit-corpus NT JSON files."""
    (directory / f"{osis}.json").write_text(
        json.dumps(
            {
                "metadata": {
                    "book": osis,
                    "osis": osis,
                    "language": "grc" if translation == "SBLGNT" else "tr",
                    "translation": translation,
                },
                "chapters": {
                    str(chapter): [
                        {
                            "osis": f"{osis}.{chapter}.{verse}",
                            "chapter": chapter,
                            "verse": verse,
                            "text": text,
                        }
                        for verse, text in chapter_verses.items()
                    ]
                    for chapter, chapter_verses in verses.items()
                },
            }
        ),
        encoding="utf-8",
    )


def test_loader_parses_real_greek_nt_shape(tmp_path: Path) -> None:
    write_real_shaped_john(tmp_path, "John", "SBLGNT", {1: {1: GREEK_JOHN_1_1}})

    chapters = VerseListJsonLoader().load(tmp_path, "John")

    assert chapters[1][1] == GREEK_JOHN_1_1


def test_loader_parses_real_turkish_ytc_shape(tmp_path: Path) -> None:
    write_real_shaped_john(tmp_path, "John", "YTC", {1: {1: TURKISH_JOHN_1_1}})

    chapters = VerseListJsonLoader().load(tmp_path, "John")

    assert chapters[1][1] == TURKISH_JOHN_1_1


def test_loader_handles_multiple_chapters_and_verses(tmp_path: Path) -> None:
    write_real_shaped_john(
        tmp_path,
        "John",
        "SBLGNT",
        {1: {1: "verse one", 2: "verse two"}, 3: {16: "verse sixteen"}},
    )

    chapters = VerseListJsonLoader().load(tmp_path, "John")

    assert chapters[1][1] == "verse one"
    assert chapters[1][2] == "verse two"
    assert chapters[3][16] == "verse sixteen"


def test_loader_raises_file_not_found_for_missing_book(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        VerseListJsonLoader().load(tmp_path, "Nonexistent")


def test_loader_raises_when_metadata_osis_does_not_match_requested_book(tmp_path: Path) -> None:
    # The file is named John.json but internally claims to be a different book —
    # a real integrity problem the loader should refuse to silently paper over.
    (tmp_path / "John.json").write_text(
        json.dumps({"metadata": {"osis": "Mark"}, "chapters": {}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="declares metadata.osis 'Mark'"):
        VerseListJsonLoader().load(tmp_path, "John")


def test_loader_works_without_metadata_block(tmp_path: Path) -> None:
    # Not every future translation file is guaranteed to include metadata;
    # the loader should still parse the chapters it does have.
    (tmp_path / "John.json").write_text(
        json.dumps({"chapters": {"1": [{"verse": 1, "text": "no metadata here"}]}}),
        encoding="utf-8",
    )

    chapters = VerseListJsonLoader().load(tmp_path, "John")

    assert chapters[1][1] == "no metadata here"
