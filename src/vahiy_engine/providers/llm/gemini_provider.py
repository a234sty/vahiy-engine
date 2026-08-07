"""Gemini LLM provider."""

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from vahiy_engine.config import settings
from vahiy_engine.providers.llm.base import LLMProvider, LLMProviderError, build_user_message


class GeminiProvider(LLMProvider):
    """Sends context to Google's Gemini API and returns the answer text."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: genai.Client | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._model = model or settings.gemini_model

        if client is not None:
            self._client = client
            return

        resolved_key = api_key or settings.gemini_api_key
        if not resolved_key:
            raise LLMProviderError("GEMINI_API_KEY is not set")

        resolved_timeout = (
            timeout_seconds if timeout_seconds is not None else settings.llm_request_timeout_seconds
        )
        self._client = genai.Client(
            api_key=resolved_key,
            http_options=types.HttpOptions(timeout=round(resolved_timeout * 1000)),
        )

    def generate_answer(self, system_prompt: str, question: str, context: str) -> str:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=build_user_message(question, context),
                config=types.GenerateContentConfig(system_instruction=system_prompt),
            )
        except genai_errors.APIError as exc:
            raise LLMProviderError(f"Gemini request failed: {exc}") from exc
        except httpx.TimeoutException as exc:
            # A request timeout isn't wrapped in APIError by the SDK — it's
            # re-raised as the underlying httpx exception, since the SDK's
            # retry logic (disabled here, as we set no retry_options) reraises
            # whatever it caught once attempts are exhausted.
            raise LLMProviderError(f"Gemini request timed out: {exc}") from exc

        answer = response.text
        if not answer:
            raise LLMProviderError("Gemini response did not contain an answer")

        return answer
