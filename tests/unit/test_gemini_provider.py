"""Unit tests for the Gemini LLM provider. No real network calls are made."""

from unittest.mock import MagicMock, patch

import pytest
from google.genai import errors as genai_errors

from vahiy_engine.config import settings
from vahiy_engine.providers.llm.base import LLMProviderError
from vahiy_engine.providers.llm.gemini_provider import GeminiProvider


def make_fake_client(answer: str = "The answer.") -> MagicMock:
    client = MagicMock()
    response = MagicMock()
    response.text = answer
    client.models.generate_content.return_value = response
    return client


def test_generate_answer_returns_text_from_response() -> None:
    client = make_fake_client("In the beginning God created the heaven and the earth.")
    provider = GeminiProvider(client=client)

    answer = provider.generate_answer("system prompt", "What does Gen.1.1 say?", "[Gen.1.1]\ntext")

    assert answer == "In the beginning God created the heaven and the earth."


def test_generate_answer_sends_system_instruction_unchanged() -> None:
    client = make_fake_client()
    provider = GeminiProvider(client=client)

    provider.generate_answer("You are neutral and source-first.", "question", "context")

    config = client.models.generate_content.call_args.kwargs["config"]
    assert config.system_instruction == "You are neutral and source-first."


def test_generate_answer_combines_context_and_question_in_contents() -> None:
    client = make_fake_client()
    provider = GeminiProvider(client=client)

    provider.generate_answer("system", "What is logos?", "[John.1.1]\nIn the beginning...")

    contents = client.models.generate_content.call_args.kwargs["contents"]
    assert "[John.1.1]\nIn the beginning..." in contents
    assert "What is logos?" in contents
    assert contents.index("[John.1.1]") < contents.index("What is logos?")


def test_generate_answer_uses_model_from_config_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "gemini_model", "gemini-2.5-flash-from-config")
    client = make_fake_client()
    provider = GeminiProvider(client=client)

    provider.generate_answer("system", "question", "context")

    assert (
        client.models.generate_content.call_args.kwargs["model"] == "gemini-2.5-flash-from-config"
    )


def test_generate_answer_uses_explicit_model_over_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "gemini_model", "gemini-2.5-flash-from-config")
    client = make_fake_client()
    provider = GeminiProvider(client=client, model="gemini-explicit")

    provider.generate_answer("system", "question", "context")

    assert client.models.generate_content.call_args.kwargs["model"] == "gemini-explicit"


def test_constructor_raises_when_no_api_key_in_config_and_no_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "gemini_api_key", None)

    with pytest.raises(LLMProviderError):
        GeminiProvider()


def test_constructor_reads_api_key_from_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "gemini_api_key", "key-from-config")

    with patch("vahiy_engine.providers.llm.gemini_provider.genai.Client") as mock_client_cls:
        GeminiProvider()

    mock_client_cls.assert_called_once_with(api_key="key-from-config")


def test_constructor_prefers_explicit_api_key_over_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "gemini_api_key", "key-from-config")

    with patch("vahiy_engine.providers.llm.gemini_provider.genai.Client") as mock_client_cls:
        GeminiProvider(api_key="explicit-key")

    mock_client_cls.assert_called_once_with(api_key="explicit-key")


def test_generate_answer_wraps_client_error() -> None:
    client = MagicMock()
    client.models.generate_content.side_effect = genai_errors.ClientError(
        404, {"error": {"message": "not found"}}
    )
    provider = GeminiProvider(client=client)

    with pytest.raises(LLMProviderError):
        provider.generate_answer("system", "question", "context")


def test_generate_answer_wraps_server_error() -> None:
    client = MagicMock()
    client.models.generate_content.side_effect = genai_errors.ServerError(
        503, {"error": {"message": "unavailable"}}
    )
    provider = GeminiProvider(client=client)

    with pytest.raises(LLMProviderError):
        provider.generate_answer("system", "question", "context")


def test_generate_answer_raises_when_response_has_no_text() -> None:
    client = make_fake_client(answer=None)
    provider = GeminiProvider(client=client)

    with pytest.raises(LLMProviderError):
        provider.generate_answer("system", "question", "context")


def test_generate_answer_raises_when_response_text_is_empty_string() -> None:
    client = make_fake_client(answer="")
    provider = GeminiProvider(client=client)

    with pytest.raises(LLMProviderError):
        provider.generate_answer("system", "question", "context")
