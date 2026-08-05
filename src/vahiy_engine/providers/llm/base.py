"""Abstract LLM provider interface."""

from abc import ABC, abstractmethod


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider call fails.

    Covers configuration problems (missing API key), transport failures
    (network/timeout), API-side failures (auth, rate limit, server errors), and
    malformed responses — callers only need to catch this one type regardless
    of which provider is configured.
    """


class LLMProvider(ABC):
    """Common interface every LLM provider (OpenAI, Claude, Gemini, ...) must implement."""

    @abstractmethod
    def generate_answer(self, system_prompt: str, question: str, context: str) -> str:
        """Send the system prompt, user question, and retrieved context to the LLM
        and return only the generated answer text."""


def build_user_message(question: str, context: str) -> str:
    """Compose the context and question into a single user-turn message.

    Shared across providers so every LLM sees an identically structured prompt
    body regardless of which one is configured.
    """
    return f"Context:\n{context}\n\nQuestion:\n{question}"
