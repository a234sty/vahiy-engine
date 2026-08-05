"""OpenAI LLM provider."""

import os

from openai import APIError as OpenAIAPIError
from openai import OpenAI

from vahiy_engine.providers.llm.base import LLMProvider, LLMProviderError

DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider(LLMProvider):
    """Sends context to OpenAI's Chat Completions API and returns the answer text."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        client: OpenAI | None = None,
    ) -> None:
        self._model = model

        if client is not None:
            self._client = client
            return

        resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved_key:
            raise LLMProviderError("OPENAI_API_KEY is not set")

        self._client = OpenAI(api_key=resolved_key)

    def generate_answer(self, system_prompt: str, question: str, context: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": _build_user_message(question, context)},
                ],
            )
        except OpenAIAPIError as exc:
            raise LLMProviderError(f"OpenAI request failed: {exc}") from exc

        answer = response.choices[0].message.content
        if not answer:
            raise LLMProviderError("OpenAI response did not contain an answer")

        return answer


def _build_user_message(question: str, context: str) -> str:
    return f"Context:\n{context}\n\nQuestion:\n{question}"
