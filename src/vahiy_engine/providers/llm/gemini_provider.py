"""Gemini LLM provider."""

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
    ) -> None:
        self._model = model or settings.gemini_model

        if client is not None:
            self._client = client
            return

        resolved_key = api_key or settings.gemini_api_key
        if not resolved_key:
            raise LLMProviderError("GEMINI_API_KEY is not set")

        self._client = genai.Client(api_key=resolved_key)

    def generate_answer(self, system_prompt: str, question: str, context: str) -> str:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=build_user_message(question, context),
                config=types.GenerateContentConfig(system_instruction=system_prompt),
            )
        except genai_errors.APIError as exc:
            raise LLMProviderError(f"Gemini request failed: {exc}") from exc

        answer = response.text
        if not answer:
            raise LLMProviderError("Gemini response did not contain an answer")

        return answer
