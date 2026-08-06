"""Large language model provider integrations."""

from functools import lru_cache

from vahiy_engine.config import settings
from vahiy_engine.providers.llm.base import LLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Select the configured LLM provider.

    OpenAI is used when OPENAI_API_KEY is configured; otherwise Gemini is used
    by default. Each provider's SDK is imported only on the branch that needs
    it, so an environment with only one of the two packages installed still
    works, as long as the matching key (or no key, since Gemini is default) is
    set.
    """
    if settings.openai_api_key:
        from vahiy_engine.providers.llm.openai_provider import OpenAIProvider

        return OpenAIProvider()

    from vahiy_engine.providers.llm.gemini_provider import GeminiProvider

    return GeminiProvider()
