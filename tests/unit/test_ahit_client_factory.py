"""Unit tests for get_ahit_client()'s translation registration logic."""

import json
from pathlib import Path

import pytest

from vahiy_engine.config import settings
from vahiy_engine.sources.ahit.client import UnknownTranslationError, get_ahit_client
from vahiy_engine.sources.osis import parse_osis


@pytest.fixture(autouse=True)
def clear_client_cache():
    get_ahit_client.cache_clear()
    yield
    get_ahit_client.cache_clear()


def test_default_ahit_corpus_root_matches_setup_corpus_scripts_default() -> None:
    # config.py's default and setup_corpus.sh's default clone target must
    # stay in sync — that's what makes "run the script, it just works" true
    # with zero extra configuration.
    assert settings.ahit_corpus_root == "external/ahit-corpus"


def test_only_kjv_registers_when_configured_root_does_not_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ahit_corpus_root", "external/ahit-corpus")

    client = get_ahit_client()

    with pytest.raises(UnknownTranslationError):
        client.get_verse(parse_osis("Gen.1.1"), translation="YTC")
    # KJV (the bundled sample data) still works.
    assert client.get_verse(parse_osis("Gen.1.1")).translation == "KJV"


def test_only_kjv_registers_when_ahit_corpus_root_path_does_not_exist(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(settings, "ahit_corpus_root", str(tmp_path / "does-not-exist"))

    client = get_ahit_client()

    assert client.get_verse(parse_osis("Gen.1.1")).translation == "KJV"


def _write_verse_list_book(directory: Path, osis: str, translation: str, text: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{osis}.json").write_text(
        json.dumps(
            {
                "metadata": {"osis": osis, "translation": translation},
                "chapters": {
                    "1": [{"osis": f"{osis}.1.1", "chapter": 1, "verse": 1, "text": text}]
                },
            }
        ),
        encoding="utf-8",
    )


def test_ytc_and_sblgnt_register_when_real_paths_exist(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write_verse_list_book(
        tmp_path / "bible" / "nt" / "translations" / "tr" / "ytc", "John", "YTC", "ytc nt text"
    )
    _write_verse_list_book(
        tmp_path / "bible" / "ot" / "translation" / "tr", "Gen", "YTC", "ytc ot text"
    )
    _write_verse_list_book(
        tmp_path / "bible" / "nt" / "original-greek", "John", "SBLGNT", "greek text"
    )
    monkeypatch.setattr(settings, "ahit_corpus_root", str(tmp_path))

    client = get_ahit_client()

    ytc_nt = client.get_verse(parse_osis("John.1.1"), translation="YTC")
    ytc_ot = client.get_verse(parse_osis("Gen.1.1"), translation="YTC")
    sblgnt = client.get_verse(parse_osis("John.1.1"), translation="SBLGNT")

    assert ytc_nt.text == "ytc nt text"
    assert ytc_ot.text == "ytc ot text"
    assert sblgnt.text == "greek text"
    # The default translation is unaffected by any of this.
    assert client.get_verse(parse_osis("Gen.1.1")).translation == "KJV"


def test_sblgnt_registers_independently_of_ytc(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Only the Greek NT directory exists — YTC's directories don't.
    _write_verse_list_book(
        tmp_path / "bible" / "nt" / "original-greek", "John", "SBLGNT", "greek only"
    )
    monkeypatch.setattr(settings, "ahit_corpus_root", str(tmp_path))

    client = get_ahit_client()

    assert client.get_verse(parse_osis("John.1.1"), translation="SBLGNT").text == "greek only"
    with pytest.raises(UnknownTranslationError):
        client.get_verse(parse_osis("John.1.1"), translation="YTC")
