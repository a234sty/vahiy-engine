"""Integration tests for the /verse endpoint."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from vahiy_engine.config import settings
from vahiy_engine.main import app
from vahiy_engine.sources.ahit.client import get_ahit_client

client = TestClient(app)


def test_get_verse_returns_matching_verse() -> None:
    response = client.get("/verse", params={"osis": "Gen.1.1"})

    assert response.status_code == 200
    assert response.json() == {
        "osis": "Gen.1.1",
        "chapter": 1,
        "verse": 1,
        "text": "In the beginning God created the heaven and the earth.",
        "translation": "KJV",
    }


def test_get_verse_supports_other_books() -> None:
    response = client.get("/verse", params={"osis": "John.3.16"})

    assert response.status_code == 200
    assert response.json()["text"].startswith("For God so loved the world")


def test_get_verse_rejects_invalid_osis_reference() -> None:
    response = client.get("/verse", params={"osis": "not-a-reference"})

    assert response.status_code == 400


def test_get_verse_returns_404_for_unknown_book() -> None:
    response = client.get("/verse", params={"osis": "Exod.1.1"})

    assert response.status_code == 404


def test_get_verse_returns_404_for_unknown_verse() -> None:
    response = client.get("/verse", params={"osis": "Gen.99.99"})

    assert response.status_code == 404


def test_get_verse_defaults_to_kjv_when_translation_omitted() -> None:
    response = client.get("/verse", params={"osis": "Gen.1.1"})

    assert response.json()["translation"] == "KJV"


def test_get_verse_returns_404_for_unregistered_translation() -> None:
    response = client.get("/verse", params={"osis": "Gen.1.1", "translation": "YTC"})

    assert response.status_code == 404


def test_get_verse_serves_a_registered_translation_end_to_end(tmp_path: Path) -> None:
    ytc_dir = tmp_path / "bible" / "nt" / "translations" / "tr" / "ytc"
    ytc_dir.mkdir(parents=True)
    (ytc_dir / "John.json").write_text(
        json.dumps(
            {
                "metadata": {"osis": "John", "translation": "YTC"},
                "chapters": {
                    "1": [{"osis": "John.1.1", "chapter": 1, "verse": 1, "text": "Turkish text"}]
                },
            }
        ),
        encoding="utf-8",
    )

    original_root = settings.ahit_corpus_root
    settings.ahit_corpus_root = str(tmp_path)
    get_ahit_client.cache_clear()
    try:
        response = client.get("/verse", params={"osis": "John.1.1", "translation": "YTC"})
    finally:
        settings.ahit_corpus_root = original_root
        get_ahit_client.cache_clear()

    assert response.status_code == 200
    assert response.json() == {
        "osis": "John.1.1",
        "chapter": 1,
        "verse": 1,
        "text": "Turkish text",
        "translation": "YTC",
    }
