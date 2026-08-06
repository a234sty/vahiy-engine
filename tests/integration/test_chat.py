"""Integration tests for the /chat endpoint. No real network/LLM calls are made."""

import pytest
from fastapi.testclient import TestClient

from vahiy_engine.api.routes.chat import get_llm_provider
from vahiy_engine.config import settings
from vahiy_engine.main import app
from vahiy_engine.providers.llm.base import LLMProvider, LLMProviderError

client = TestClient(app)


class FakeProvider(LLMProvider):
    """Records calls instead of contacting a real LLM."""

    def __init__(self, answer: str = "fake answer", raise_error: bool = False) -> None:
        self.answer = answer
        self.raise_error = raise_error
        self.calls: list[tuple[str, str, str]] = []

    def generate_answer(self, system_prompt: str, question: str, context: str) -> str:
        self.calls.append((system_prompt, question, context))
        if self.raise_error:
            raise LLMProviderError("simulated provider failure")
        return self.answer


@pytest.fixture(autouse=True)
def clear_provider_override():
    yield
    app.dependency_overrides.pop(get_llm_provider, None)


def use_provider(provider: FakeProvider) -> None:
    app.dependency_overrides[get_llm_provider] = lambda: provider


def test_post_chat_returns_answer_and_sources() -> None:
    use_provider(FakeProvider("Genesis 1:1 describes the creation of the heavens and the earth."))

    response = client.post("/chat", json={"message": "beginning"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Genesis 1:1 describes the creation of the heavens and the earth."
    assert {s["osis"] for s in body["sources"]} == {"Gen.1.1", "John.1.1"}


def test_post_chat_source_items_have_required_fields() -> None:
    use_provider(FakeProvider())

    response = client.post("/chat", json={"message": "beginning"})

    for item in response.json()["sources"]:
        assert set(item.keys()) == {"osis", "chapter", "verse", "text", "score", "translation"}


def test_post_chat_passes_message_through_as_the_question() -> None:
    provider = FakeProvider()
    use_provider(provider)

    client.post("/chat", json={"message": "What is logos?"})

    assert provider.calls[0][1] == "What is logos?"


def test_post_chat_returns_empty_sources_when_no_matches() -> None:
    use_provider(FakeProvider("I don't know."))

    response = client.post("/chat", json={"message": "xyznonexistentword"})

    assert response.status_code == 200
    assert response.json()["sources"] == []
    assert response.json()["answer"] == "I don't know."


def test_post_chat_requires_message_field() -> None:
    # A working provider is configured so this exercises body validation in
    # isolation, not provider-configuration failure (also a 4xx/5xx path).
    use_provider(FakeProvider())

    response = client.post("/chat", json={})

    assert response.status_code == 422


def test_post_chat_returns_502_as_json_when_provider_fails() -> None:
    use_provider(FakeProvider(raise_error=True))

    response = client.post("/chat", json={"message": "beginning"})

    assert response.status_code == 502
    assert "error" in response.json()


def test_post_chat_returns_502_when_no_api_key_is_configured() -> None:
    # No dependency override here: exercises the real get_llm_provider(), which
    # falls back to Gemini (the default) and raises LLMProviderError when
    # neither settings.openai_api_key nor settings.gemini_api_key is set.
    original_openai_key = settings.openai_api_key
    original_gemini_key = settings.gemini_api_key
    settings.openai_api_key = None
    settings.gemini_api_key = None
    get_llm_provider.cache_clear()
    try:
        response = client.post("/chat", json={"message": "beginning"})
    finally:
        settings.openai_api_key = original_openai_key
        settings.gemini_api_key = original_gemini_key
        get_llm_provider.cache_clear()

    assert response.status_code == 502
    assert "error" in response.json()
