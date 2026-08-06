"""Unit tests for the Ahit Corpus client's multi-translation registry."""

import json
from pathlib import Path

import pytest

from vahiy_engine.sources.ahit.client import (
    AhitCorpusClient,
    TranslationSource,
    UnknownTranslationError,
    VerseNotFoundError,
)
from vahiy_engine.sources.loaders.json_loader import JsonBookLoader
from vahiy_engine.sources.loaders.verse_list_json_loader import VerseListJsonLoader
from vahiy_engine.sources.osis import parse_osis


def write_kjv_style_book(directory: Path, book: str, text: str) -> None:
    (directory / f"{book}.json").write_text(
        json.dumps({"book": book, "chapters": {"1": {"1": text}}}),
        encoding="utf-8",
    )


def write_verse_list_style_book(directory: Path, book: str, translation: str, text: str) -> None:
    (directory / f"{book}.json").write_text(
        json.dumps(
            {
                "metadata": {"book": book, "osis": book, "translation": translation},
                "chapters": {
                    "1": [{"osis": f"{book}.1.1", "chapter": 1, "verse": 1, "text": text}]
                },
            }
        ),
        encoding="utf-8",
    )


@pytest.fixture
def kjv_path(tmp_path: Path) -> Path:
    directory = tmp_path / "kjv"
    directory.mkdir()
    write_kjv_style_book(directory, "Gen", "In the beginning...")
    return directory


@pytest.fixture
def default_client(kjv_path: Path) -> AhitCorpusClient:
    return AhitCorpusClient(
        translations={"KJV": TranslationSource(paths=[kjv_path], loader=JsonBookLoader())}
    )


def test_get_verse_returns_matching_text(default_client: AhitCorpusClient) -> None:
    verse = default_client.get_verse(parse_osis("Gen.1.1"))

    assert verse.osis == "Gen.1.1"
    assert verse.text == "In the beginning..."


def test_get_verse_defaults_to_default_translation(default_client: AhitCorpusClient) -> None:
    verse = default_client.get_verse(parse_osis("Gen.1.1"))

    assert verse.translation == "KJV"


def test_get_verse_raises_for_missing_verse(default_client: AhitCorpusClient) -> None:
    with pytest.raises(VerseNotFoundError):
        default_client.get_verse(parse_osis("Gen.1.99"))


def test_get_verse_raises_for_missing_book(default_client: AhitCorpusClient) -> None:
    with pytest.raises(FileNotFoundError):
        default_client.get_verse(parse_osis("Exod.1.1"))


def test_constructor_rejects_unregistered_default_translation(kjv_path: Path) -> None:
    with pytest.raises(ValueError, match="default_translation"):
        AhitCorpusClient(
            translations={"KJV": TranslationSource(paths=[kjv_path], loader=JsonBookLoader())},
            default_translation="YTC",
        )


# --- Multiple registered translations ---


@pytest.fixture
def ytc_path(tmp_path: Path) -> Path:
    directory = tmp_path / "ytc"
    directory.mkdir()
    write_verse_list_style_book(directory, "Gen", "YTC", "Başlangıçta Tanrı gökleri yarattı.")
    return directory


@pytest.fixture
def multi_translation_client(kjv_path: Path, ytc_path: Path) -> AhitCorpusClient:
    return AhitCorpusClient(
        translations={
            "KJV": TranslationSource(paths=[kjv_path], loader=JsonBookLoader()),
            "YTC": TranslationSource(paths=[ytc_path], loader=VerseListJsonLoader()),
        }
    )


def test_get_verse_reads_the_requested_translation(
    multi_translation_client: AhitCorpusClient,
) -> None:
    kjv_verse = multi_translation_client.get_verse(parse_osis("Gen.1.1"))
    ytc_verse = multi_translation_client.get_verse(parse_osis("Gen.1.1"), translation="YTC")

    assert kjv_verse.text == "In the beginning..."
    assert kjv_verse.translation == "KJV"
    assert ytc_verse.text == "Başlangıçta Tanrı gökleri yarattı."
    assert ytc_verse.translation == "YTC"


def test_get_verse_raises_for_unknown_translation(
    multi_translation_client: AhitCorpusClient,
) -> None:
    with pytest.raises(UnknownTranslationError):
        multi_translation_client.get_verse(parse_osis("Gen.1.1"), translation="NONEXISTENT")


def test_iter_verses_reads_the_requested_translation(
    multi_translation_client: AhitCorpusClient,
) -> None:
    kjv_verses = list(multi_translation_client.iter_verses())
    ytc_verses = list(multi_translation_client.iter_verses(translation="YTC"))

    assert [v.translation for v in kjv_verses] == ["KJV"]
    assert [v.translation for v in ytc_verses] == ["YTC"]
    assert ytc_verses[0].text == "Başlangıçta Tanrı gökleri yarattı."


def test_iter_verses_raises_for_unknown_translation(
    multi_translation_client: AhitCorpusClient,
) -> None:
    with pytest.raises(UnknownTranslationError):
        list(multi_translation_client.iter_verses(translation="NONEXISTENT"))


# --- A translation spanning multiple root directories (like YTC OT + NT) ---


def test_translation_can_span_multiple_root_directories(tmp_path: Path) -> None:
    old_testament_dir = tmp_path / "ot"
    new_testament_dir = tmp_path / "nt"
    old_testament_dir.mkdir()
    new_testament_dir.mkdir()
    write_verse_list_style_book(old_testament_dir, "Gen", "YTC", "OT text")
    write_verse_list_style_book(new_testament_dir, "John", "YTC", "NT text")

    client = AhitCorpusClient(
        translations={
            "YTC": TranslationSource(
                paths=[old_testament_dir, new_testament_dir], loader=VerseListJsonLoader()
            )
        },
        default_translation="YTC",
    )

    genesis = client.get_verse(parse_osis("Gen.1.1"))
    john = client.get_verse(parse_osis("John.1.1"))

    assert genesis.text == "OT text"
    assert john.text == "NT text"
