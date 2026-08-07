"""OpenAI LLM provider."""

from openai import APIError as OpenAIAPIError
from openai import OpenAI

from vahiy_engine.config import settings
from vahiy_engine.providers.llm.base import LLMProvider, LLMProviderError, build_user_message


class OpenAIProvider(LLMProvider):
    """Sends context to OpenAI's Chat Completions API and returns the answer text."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: OpenAI | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._model = model or settings.openai_model

        if client is not None:
            self._client = client
            return

        resolved_key = api_key or settings.openai_api_key
        if not resolved_key:
            raise LLMProviderError("OPENAI_API_KEY is not set")

        resolved_timeout = (
            timeout_seconds if timeout_seconds is not None else settings.llm_request_timeout_seconds
        )
        self._client = OpenAI(api_key=resolved_key, timeout=resolved_timeout)

    def generate_answer(self, system_prompt: str, question: str, context: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": build_user_message(question, context)},
                ],
            )
        except OpenAIAPIError as exc:
            raise LLMProviderError(f"OpenAI request failed: {exc}") from exc

        answer = response.choices[0].message.content
        if not answer:
            raise LLMProviderError("OpenAI response did not contain an answer")

        return answer
