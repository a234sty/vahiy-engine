"""Builds the final AI-ready context from ranked sources."""

from vahiy_engine.rag.retrieval import Source


def build_context(sources: list[Source]) -> str:
    """Render retrieved sources into a single, provider-independent plain-text context.

    Preserves the exact order of `sources` as given — this function never
    re-sorts or re-ranks; ordering is retrieval's responsibility. Each source is
    rendered as its OSIS reference followed by its verse text, with a blank line
    clearly separating one source from the next. The output is plain text with
    no provider-specific structure (no OpenAI/Claude/Gemini message format), so
    any LLM provider can consume it as-is.
    """
    return "\n\n".join(_render_source(source) for source in sources)


def _render_source(source: Source) -> str:
    return f"[{source.osis}]\n{source.text}"
