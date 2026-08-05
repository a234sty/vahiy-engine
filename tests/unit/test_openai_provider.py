"""Unit tests for the OpenAI LLM provider. No real network calls are made."""

from unittest.mock import MagicMock, patch

import httpx
import openai
import pytest

from vahiy_engine.config import settings
from vahiy_engine.providers.llm.base import LLMProviderError
from vahiy_engine.providers.llm.openai_provider import OpenAIProvider


def make_fake_client(answer: str = "The answer.") -> MagicMock:
    client = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=answer))]
    client.chat.completions.create.return_value = response
    return client


def test_generate_answer_returns_text_from_response() -> None:
    client = make_fake_client("In the beginning God created the heaven and the earth.")
    provider = OpenAIProvider(client=client)

    answer = provider.generate_answer("system prompt", "What does Gen.1.1 say?", "[Gen.1.1]\ntext")

    assert answer == "In the beginning God created the heaven and the earth."


def test_generate_answer_sends_system_prompt_unchanged() -> None:
    client = make_fake_client()
    provider = OpenAIProvider(client=client)

    provider.generate_answer("You are neutral and source-first.", "question", "context")

    messages = client.chat.completions.create.call_args.kwargs["messages"]
    assert messages[0] == {"role": "system", "content": "You are neutral and source-first."}


def test_generate_answer_combines_context_and_question_in_user_message() -> None:
    client = make_fake_client()
    provider = OpenAIProvider(client=client)

    provider.generate_answer("system", "What is logos?", "[John.1.1]\nIn the beginning...")

    messages = client.chat.completions.create.call_args.kwargs["messages"]
    user_content = messages[1]["content"]
    assert messages[1]["role"] == "user"
    assert "[John.1.1]\nIn the beginning..." in user_content
    assert "What is logos?" in user_content
    assert user_content.index("[John.1.1]") < user_content.index("What is logos?")


def test_generate_answer_uses_model_from_config_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "openai_model", "gpt-4o-mini-from-config")
    client = make_fake_client()
    provider = OpenAIProvider(client=client)

    provider.generate_answer("system", "question", "context")

    assert client.chat.completions.create.call_args.kwargs["model"] == "gpt-4o-mini-from-config"


def test_generate_answer_uses_explicit_model_over_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "openai_model", "gpt-4o-mini-from-config")
    client = make_fake_client()
    provider = OpenAIProvider(client=client, model="gpt-4o-explicit")

    provider.generate_answer("system", "question", "context")

    assert client.chat.completions.create.call_args.kwargs["model"] == "gpt-4o-explicit"


def test_constructor_raises_when_no_api_key_in_config_and_no_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "openai_api_key", None)

    with pytest.raises(LLMProviderError):
        OpenAIProvider()


def test_constructor_reads_api_key_from_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "openai_api_key", "key-from-config")

    with patch("vahiy_engine.providers.llm.openai_provider.OpenAI") as mock_openai_cls:
        OpenAIProvider()

    mock_openai_cls.assert_called_once_with(api_key="key-from-config")


def test_constructor_prefers_explicit_api_key_over_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "openai_api_key", "key-from-config")

    with patch("vahiy_engine.providers.llm.openai_provider.OpenAI") as mock_openai_cls:
        OpenAIProvider(api_key="explicit-key")

    mock_openai_cls.assert_called_once_with(api_key="explicit-key")


def test_generate_answer_wraps_connection_error() -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = openai.APIConnectionError(
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    )
    provider = OpenAIProvider(client=client)

    with pytest.raises(LLMProviderError):
        provider.generate_answer("system", "question", "context")


def test_generate_answer_wraps_rate_limit_error() -> None:
    client = MagicMock()
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    response = httpx.Response(429, request=request)
    client.chat.completions.create.side_effect = openai.RateLimitError(
        "Rate limit exceeded", response=response, body=None
    )
    provider = OpenAIProvider(client=client)

    with pytest.raises(LLMProviderError):
        provider.generate_answer("system", "question", "context")


def test_generate_answer_raises_when_response_has_no_content() -> None:
    client = make_fake_client(answer=None)
    provider = OpenAIProvider(client=client)

    with pytest.raises(LLMProviderError):
        provider.generate_answer("system", "question", "context")


def test_generate_answer_raises_when_response_content_is_empty_string() -> None:
    client = make_fake_client(answer="")
    provider = OpenAIProvider(client=client)

    with pytest.raises(LLMProviderError):
        provider.generate_answer("system", "question", "context")
