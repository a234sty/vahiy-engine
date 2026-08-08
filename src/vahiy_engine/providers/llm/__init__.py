"""Large language model provider integrations."""

from functools import lru_cache

from vahiy_engine.config import settings
from vahiy_engine.providers.llm.base import LLMProvider
from vahiy_engine.reasoning.intent import Complexity


@lru_cache
def get_llm_provider(complexity: Complexity | None = None) -> LLMProvider:
    """Select the configured LLM provider, optionally tiered by question complexity.

    OpenAI is used when OPENAI_API_KEY is configured; otherwise Gemini is used
    by default. Each provider's SDK is imported only on the branch that needs
    it, so an environment with only one of the two packages installed still
    works, as long as the matching key (or no key, since Gemini is default) is
    set.

    `complexity` selects a cheaper or stronger model within the chosen
    provider when the deployment configures one. A SIMPLE question -- a verse
    lookup, a single lexicon entry -- does not need the model that a DEEP
    cross-scripture comparison needs, and paying deep-tier rates for every
    question is the largest avoidable cost on this path. When no tier is
    configured the provider's default model is used, so an unconfigured
    deployment behaves exactly as it did before tiering existed.

    Cached per complexity, so at most one client per tier is constructed.
    """
    model = tier_model_for(complexity)

    if settings.openai_api_key:
        from vahiy_engine.providers.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(model=model)

    from vahiy_engine.providers.llm.gemini_provider import GeminiProvider

    return GeminiProvider(model=model)


def tier_model_for(complexity: Complexity | None) -> str | None:
    """The configured model for `complexity`, or None when this deployment
    has not configured a tier for it.

    Public so callers can ask whether tiering is configured at all before
    deciding to bypass an already-selected provider.
    """
    if complexity is None:
        return None

    using_openai = bool(settings.openai_api_key)
    if complexity is Complexity.SIMPLE:
        return settings.openai_model_fast if using_openai else settings.gemini_model_fast
    if complexity is Complexity.DEEP:
        return settings.openai_model_deep if using_openai else settings.gemini_model_deep
    return None
