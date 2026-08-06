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


OSIS_NAMESPACE = "http://www.bibletechnologies.net/2003/OSIS/namespace"


def _write_osis_xml_book(directory: Path, book: str, text: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    doc = f"""<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="{OSIS_NAMESPACE}">
  <osisText xml:lang="he" osisIDWork="OSHB" osisRefWork="Bible">
    <div type="book" osisID="{book}">
      <chapter osisID="{book}.1">
        <verse osisID="{book}.1.1"><w>{text}</w></verse>
      </chapter>
    </div>
  </osisText>
</osis>
"""
    (directory / f"{book}.xml").write_text(doc, encoding="utf-8")


def _write_verse_map(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    doc = """<?xml version="1.0" encoding="UTF-8"?>
<verseMap xmlns="http://www.APTBibleTools.com/namespace">
  <book osisID="Gen">
    <verse wlc="Gen.32.1" kjv="Gen.31.55" type="full"/>
  </book>
</verseMap>
"""
    (directory / "VerseMap.xml").write_text(doc, encoding="utf-8")


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


def test_wlc_registers_when_real_path_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wlc_dir = tmp_path / "bible" / "ot" / "books"
    _write_osis_xml_book(wlc_dir, "Gen", "בְּרֵאשִׁית")
    _write_verse_map(wlc_dir)
    monkeypatch.setattr(settings, "ahit_corpus_root", str(tmp_path))

    client = get_ahit_client()

    wlc = client.get_verse(parse_osis("Gen.1.1"), translation="WLC")

    assert wlc.text == "בְּרֵאשִׁית"
    # The default translation is unaffected.
    assert client.get_verse(parse_osis("Gen.1.1")).translation == "KJV"


def test_wlc_registration_excludes_verse_map_from_book_discovery(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wlc_dir = tmp_path / "bible" / "ot" / "books"
    _write_osis_xml_book(wlc_dir, "Gen", "בְּרֵאשִׁית")
    _write_verse_map(wlc_dir)
    monkeypatch.setattr(settings, "ahit_corpus_root", str(tmp_path))

    client = get_ahit_client()

    assert [v.osis for v in client.iter_verses(translation="WLC")] == ["Gen.1.1"]


def test_wlc_registers_independently_of_ytc_and_sblgnt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Only the WLC directory exists — YTC's and SBLGNT's don't.
    _write_osis_xml_book(tmp_path / "bible" / "ot" / "books", "Gen", "בְּרֵאשִׁית")
    monkeypatch.setattr(settings, "ahit_corpus_root", str(tmp_path))

    client = get_ahit_client()

    assert client.get_verse(parse_osis("Gen.1.1"), translation="WLC").text == "בְּרֵאשִׁית"
    with pytest.raises(UnknownTranslationError):
        client.get_verse(parse_osis("Gen.1.1"), translation="YTC")
    with pytest.raises(UnknownTranslationError):
        client.get_verse(parse_osis("Gen.1.1"), translation="SBLGNT")
