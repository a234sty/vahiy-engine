"""Unit tests for LLM provider selection (get_llm_provider)."""

import pytest

from vahiy_engine.config import settings
from vahiy_engine.providers.llm import get_llm_provider
from vahiy_engine.providers.llm.base import LLMProviderError
from vahiy_engine.providers.llm.gemini_provider import GeminiProvider
from vahiy_engine.providers.llm.openai_provider import OpenAIProvider


@pytest.fixture(autouse=True)
def clear_provider_cache():
    get_llm_provider.cache_clear()
    yield
    get_llm_provider.cache_clear()


def test_selects_gemini_by_default_when_no_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "gemini_api_key", "fake-gemini-key")

    provider = get_llm_provider()

    assert isinstance(provider, GeminiProvider)


def test_selects_openai_when_openai_key_is_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "openai_api_key", "fake-openai-key")
    monkeypatch.setattr(settings, "gemini_api_key", None)

    provider = get_llm_provider()

    assert isinstance(provider, OpenAIProvider)


def test_openai_takes_priority_when_both_keys_are_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "openai_api_key", "fake-openai-key")
    monkeypatch.setattr(settings, "gemini_api_key", "fake-gemini-key")

    provider = get_llm_provider()

    assert isinstance(provider, OpenAIProvider)


def test_get_llm_provider_is_a_cached_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "gemini_api_key", "fake-gemini-key")

    first = get_llm_provider()
    second = get_llm_provider()

    assert first is second


def test_raises_llm_provider_error_when_neither_key_is_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "gemini_api_key", None)

    with pytest.raises(LLMProviderError):
        get_llm_provider()
