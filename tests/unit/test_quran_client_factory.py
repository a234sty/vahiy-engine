"""Unit tests for get_quran_client()'s registration logic."""

import json
from pathlib import Path

import pytest

from vahiy_engine.config import settings
from vahiy_engine.sources.quran.client import UnknownEditionError, get_quran_client
from vahiy_engine.sources.quran.models import QuranReference


@pytest.fixture(autouse=True)
def clear_client_cache():
    get_quran_client.cache_clear()
    yield
    get_quran_client.cache_clear()


def _write_quran_file(directory: Path, filename: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(
        json.dumps({"1": [{"chapter": 1, "verse": 1, "text": "text"}]}), encoding="utf-8"
    )


def test_no_editions_register_when_configured_root_does_not_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ahit_corpus_root", "external/ahit-corpus")

    client = get_quran_client()

    with pytest.raises(UnknownEditionError):
        client.get_ayah(QuranReference(surah=1, ayah=1))


def test_registers_only_the_editions_whose_files_exist(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    quran_dir = tmp_path / "quran"
    _write_quran_file(quran_dir, "quran.json")
    _write_quran_file(quran_dir, "quran-tr.json")
    monkeypatch.setattr(settings, "ahit_corpus_root", str(tmp_path))

    client = get_quran_client()

    assert client.get_ayah(QuranReference(surah=1, ayah=1)).edition == "arabic"
    assert client.get_ayah(QuranReference(surah=1, ayah=1), edition="tr").text == "text"
    with pytest.raises(UnknownEditionError):
        client.get_ayah(QuranReference(surah=1, ayah=1), edition="en")


def test_all_four_editions_register_when_all_files_exist(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    quran_dir = tmp_path / "quran"
    for filename in ("quran.json", "quran-en.json", "quran-tr.json", "quran-transliteration.json"):
        _write_quran_file(quran_dir, filename)
    monkeypatch.setattr(settings, "ahit_corpus_root", str(tmp_path))

    client = get_quran_client()

    for edition in ("arabic", "en", "tr", "transliteration"):
        assert client.get_ayah(QuranReference(surah=1, ayah=1), edition=edition).text == "text"
