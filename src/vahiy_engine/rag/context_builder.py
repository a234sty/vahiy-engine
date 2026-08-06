"""Builds the final AI-ready context from ranked sources."""

from vahiy_engine.lexicon.models import LexiconEntry
from vahiy_engine.rag.retrieval import Source


def build_context(sources: list[Source], lexicon_entries: list[LexiconEntry] | None = None) -> str:
    """Render retrieved sources into a single, provider-independent plain-text context.

    Preserves the exact order of `sources` as given — this function never
    re-sorts or re-ranks; ordering is retrieval's responsibility. Each source is
    rendered as its OSIS reference followed by its verse text, with a blank line
    clearly separating one source from the next. The output is plain text with
    no provider-specific structure (no OpenAI/Claude/Gemini message format), so
    any LLM provider can consume it as-is.

    `lexicon_entries`, when given, are rendered after every verse source, each
    as its Strong's number followed by its lemma and definition — this is how
    a question naming a specific Greek/Hebrew word (e.g. "What does Logos
    mean?") gets that word's dictionary entry into the model's context, not
    just whichever verses happen to mention it.
    """
    blocks = [_render_source(source) for source in sources]
    blocks.extend(_render_lexicon_entry(entry) for entry in lexicon_entries or [])
    return "\n\n".join(blocks)


def _render_source(source: Source) -> str:
    return f"[{source.osis}]\n{source.text}"


def _render_lexicon_entry(entry: LexiconEntry) -> str:
    return (
        f"[Strong:{entry.strongs_number}] {entry.lemma} "
        f"({entry.transliteration}): {entry.definition}"
    )
