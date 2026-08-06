"""Unit tests for get_lexicon_client()'s registration logic."""

from pathlib import Path

import pytest

from vahiy_engine.config import settings
from vahiy_engine.lexicon.ahit.client import EntryNotFoundError, get_lexicon_client

OSIS_NAMESPACE = "http://www.bibletechnologies.net/2003/OSIS/namespace"


@pytest.fixture(autouse=True)
def clear_client_cache():
    get_lexicon_client.cache_clear()
    yield
    get_lexicon_client.cache_clear()


def _write_greek_lexicon(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    doc = (
        "<strongsdictionary><entries>"
        '<entry strongs="03056"><strongs>3056</strongs>'
        '<greek unicode="λόγος" translit="lógos"/>'
        '<pronunciation strongs="log\'-os"/>'
        "<strongs_def> something said </strongs_def>"
        "<kjv_def>:--word.</kjv_def></entry>"
        "</entries></strongsdictionary>"
    )
    (directory / "strongsgreek.xml").write_text(doc, encoding="utf-8")


def _write_hebrew_lexicon(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    doc = (
        f'<osis xmlns="{OSIS_NAMESPACE}"><osisText><div type="glossary">'
        '<div type="entry" n="1">'
        '<w lemma="אָב" xlit="ʼâb" ID="H1">אב</w>'
        "<list><item>1) father</item></list>"
        '<note type="translation">father</note>'
        "</div>"
        "</div></osisText></osis>"
    )
    (directory / "StrongHebrewG.xml").write_text(doc, encoding="utf-8")


def test_no_lexicons_register_when_configured_root_does_not_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ahit_corpus_root", "external/ahit-corpus")

    client = get_lexicon_client()

    with pytest.raises(EntryNotFoundError):
        client.get_entry("G3056")


def test_greek_and_hebrew_register_when_real_paths_exist(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write_greek_lexicon(tmp_path / "lexicon" / "greek")
    _write_hebrew_lexicon(tmp_path / "lexicon" / "hebrew")
    monkeypatch.setattr(settings, "ahit_corpus_root", str(tmp_path))

    client = get_lexicon_client()

    logos = client.get_entry("G3056")
    ab = client.get_entry("H1")

    assert logos.lemma == "λόγος"
    assert ab.lemma == "אָב"


def test_greek_registers_independently_of_hebrew(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Only the Greek dictionary exists — Hebrew's doesn't.
    _write_greek_lexicon(tmp_path / "lexicon" / "greek")
    monkeypatch.setattr(settings, "ahit_corpus_root", str(tmp_path))

    client = get_lexicon_client()

    assert client.get_entry("G3056").lemma == "λόγος"
    with pytest.raises(EntryNotFoundError):
        client.get_entry("H1")


def test_hebrew_registers_independently_of_greek(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Only the Hebrew dictionary exists — Greek's doesn't.
    _write_hebrew_lexicon(tmp_path / "lexicon" / "hebrew")
    monkeypatch.setattr(settings, "ahit_corpus_root", str(tmp_path))

    client = get_lexicon_client()

    assert client.get_entry("H1").lemma == "אָב"
    with pytest.raises(EntryNotFoundError):
        client.get_entry("G3056")
