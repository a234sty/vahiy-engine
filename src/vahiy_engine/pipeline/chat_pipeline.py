"""Orchestrates the chat pipeline."""

from dataclasses import dataclass

from vahiy_engine.providers.llm.base import LLMProvider
from vahiy_engine.rag.context_builder import build_context
from vahiy_engine.rag.retrieval import Source, retrieve
from vahiy_engine.sources.client import CorpusClient

DEFAULT_LIMIT = 5

DEFAULT_SYSTEM_PROMPT = (
    "You are Vahiy Engine, a neutral, source-first assistant. Answer only using "
    "the provided context. If the context does not contain the answer, say so "
    "instead of guessing. Never favor any religion, denomination, sect, "
    "ideology, or theological position."
)


@dataclass(frozen=True)
class ChatResult:
    answer: str
    sources: list[Source]


def run_chat_pipeline(
    corpus: CorpusClient,
    provider: LLMProvider,
    question: str,
    limit: int = DEFAULT_LIMIT,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> ChatResult:
    """Answer `question` using retrieval-augmented generation over `corpus`.

    Orchestrates the existing components in a fixed sequence: retrieve ranked
    sources, build a plain-text context from them, then ask `provider` to
    generate an answer grounded in that context. Returns the answer together
    with the sources it was grounded in.

    Has no FastAPI dependency and carries no state between calls — each call is
    independent, with no conversation memory.
    """
    sources = retrieve(corpus, question, limit)
    context = build_context(sources)
    answer = provider.generate_answer(system_prompt, question, context)

    return ChatResult(answer=answer, sources=sources)
