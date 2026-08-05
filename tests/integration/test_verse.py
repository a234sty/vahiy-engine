"""Integration tests for the /verse endpoint."""

from fastapi.testclient import TestClient

from vahiy_engine.main import app

client = TestClient(app)


def test_get_verse_returns_matching_verse() -> None:
    response = client.get("/verse", params={"osis": "Gen.1.1"})

    assert response.status_code == 200
    assert response.json() == {
        "osis": "Gen.1.1",
        "chapter": 1,
        "verse": 1,
        "text": "In the beginning God created the heaven and the earth.",
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
