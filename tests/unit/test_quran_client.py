"""Unit tests for QuranClient. Fragment shapes verified against the real
ahit-corpus quran*.json files (all four editions share one shape)."""

import json
from pathlib import Path

import pytest

from vahiy_engine.sources.quran.client import (
    AyahNotFoundError,
    QuranClient,
    QuranEdition,
    UnknownEditionError,
)
from vahiy_engine.sources.quran.models import QuranReference


def write_edition(directory: Path, filename: str, surahs: dict[int, list[dict]]) -> Path:
    path = directory / filename
    path.write_text(
        json.dumps({str(s): entries for s, entries in surahs.items()}), encoding="utf-8"
    )
    return path


@pytest.fixture
def arabic_path(tmp_path: Path) -> Path:
    return write_edition(
        tmp_path,
        "quran.json",
        {
            1: [{"chapter": 1, "verse": 1, "text": "بِسْمِ اللَّهِ"}],
            14: [{"chapter": 14, "verse": 35, "text": "arabic ibrahim prayer"}],
        },
    )


@pytest.fixture
def en_path(tmp_path: Path) -> Path:
    return write_edition(
        tmp_path,
        "quran-en.json",
        {14: [{"chapter": 14, "verse": 35, "text": "My Lord, make this city secure"}]},
    )


@pytest.fixture
def client(arabic_path: Path, en_path: Path) -> QuranClient:
    return QuranClient(
        editions={
            "arabic": QuranEdition(path=arabic_path),
            "en": QuranEdition(path=en_path),
        },
        default_edition="arabic",
    )


def test_get_ayah_returns_matching_text(client: QuranClient) -> None:
    ayah = client.get_ayah(QuranReference(surah=1, ayah=1))

    assert ayah.text == "بِسْمِ اللَّهِ"
    assert ayah.edition == "arabic"


def test_get_ayah_reads_the_requested_edition(client: QuranClient) -> None:
    ayah = client.get_ayah(QuranReference(surah=14, ayah=35), edition="en")

    assert ayah.text == "My Lord, make this city secure"


def test_get_ayah_raises_for_missing_ayah(client: QuranClient) -> None:
    with pytest.raises(AyahNotFoundError):
        client.get_ayah(QuranReference(surah=99, ayah=99))


def test_get_ayah_raises_for_unknown_edition(client: QuranClient) -> None:
    with pytest.raises(UnknownEditionError):
        client.get_ayah(QuranReference(surah=1, ayah=1), edition="fr")


def test_iter_ayat_yields_in_sorted_surah_ayah_order(arabic_path: Path, tmp_path: Path) -> None:
    client = QuranClient(editions={"arabic": QuranEdition(path=arabic_path)})

    ayat = list(client.iter_ayat())

    assert [(a.surah, a.ayah) for a in ayat] == [(1, 1), (14, 35)]


def test_client_with_no_editions_raises_on_any_query() -> None:
    client = QuranClient(editions={})

    with pytest.raises(UnknownEditionError):
        client.get_ayah(QuranReference(surah=1, ayah=1))


def test_quran_reference_citation_format() -> None:
    assert QuranReference(surah=14, ayah=35).citation == "Quran.14.35"
