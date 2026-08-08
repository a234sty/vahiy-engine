"""Builds the final AI-ready context from ranked sources and reasoning evidence.

The context is deliberately *tiered and labeled* rather than a flat list of
verse text. The system prompt instructs the model to separate direct textual
evidence from interpretation, to weigh primary sources above incidental
matches, and to disclose what the corpus does not cover -- none of which the
model can do honestly if every retrieved line arrives looking identical.
So this module marks, structurally:

- which evidence came from a curated Knowledge Graph edge (primary: a
  citation someone verified as being *about* the matched concept), versus
  which came from keyword retrieval (supporting: a passage whose words
  happened to rank, which may or may not be on-topic),
- which corpus each citation came from (Bible / Qur'an / lexicon), so the
  model never silently presents a Qur'anic ayah as biblical or vice versa
  ("source mixing"),
- what is knowably absent, so a gap is reported as a gap rather than filled
  in from the model's own background knowledge.
"""

from vahiy_engine.lexicon.models import LexiconEntry
from vahiy_engine.rag.retrieval import Source
from vahiy_engine.reasoning.trace import EvidenceItem

_CORPUS_LABELS = {
    "osis": "Bible",
    "quran": "Qur'an",
    "strongs": "Lexicon (Strong's)",
}


def build_context(
    sources: list[Source],
    lexicon_entries: list[LexiconEntry] | None = None,
    primary_evidence: list[EvidenceItem] | None = None,
    coverage_notes: list[str] | None = None,
    retrieved_evidence: tuple[EvidenceItem, ...] | None = None,
) -> str:
    """Render retrieved sources and reasoning evidence into a single,
    provider-independent plain-text context.

    Preserves the exact order of `sources` as given -- this function never
    re-sorts or re-ranks; ordering is retrieval's responsibility.

    `primary_evidence`, when given, holds the Knowledge Graph's resolved
    citations for the concept the question was matched to (Bible, Qur'an and
    Strong's alike). It is rendered first and labeled as primary, because a
    curated citation about the matched concept is stronger evidence than a
    keyword hit, and the model should be able to tell them apart.

    `lexicon_entries` are rendered as their own labeled block: a dictionary
    entry is lexical evidence, not a scriptural claim, and the prompt asks
    the model never to present one as the other.

    `coverage_notes`, when given, state what the currently configured corpus
    does *not* contain. This is evidence about the absence of evidence, and
    it is included on purpose: it is what lets the model say "no Qur'anic
    parallel is available here" instead of inventing one.

    Called with only `sources` (and optionally `lexicon_entries`), the output
    is exactly what it always was -- an untiered context stays untiered, so
    no existing caller changes behavior.
    """
    blocks: list[str] = []

    if primary_evidence:
        blocks.append(_render_primary_evidence(primary_evidence))

    if retrieved_evidence:
        blocks.append(_render_retrieved_evidence(retrieved_evidence))

    if sources:
        supporting = [_render_source(source) for source in sources]
        if primary_evidence:
            heading = "=== SUPPORTING EVIDENCE (keyword retrieval; relevance not verified) ==="
            blocks.append(heading + "\n\n" + "\n\n".join(supporting))
        else:
            # No reasoning layer ran, so there is nothing to contrast against
            # and a heading would imply a tier distinction that wasn't made.
            blocks.extend(supporting)

    blocks.extend(_render_lexicon_entry(entry) for entry in lexicon_entries or [])

    if coverage_notes:
        blocks.append(
            "=== COVERAGE LIMITS (state these rather than filling the gap) ===\n"
            + "\n".join(f"- {note}" for note in coverage_notes)
        )

    return "\n\n".join(blocks)


def _render_primary_evidence(evidence: list[EvidenceItem]) -> str:
    lines = ["=== PRIMARY EVIDENCE (curated citations for the matched concept) ==="]
    for item in evidence:
        corpus = _CORPUS_LABELS.get(item.citation_type, item.citation_type)
        lines.append(f"\n[{item.citation}] ({corpus})\n{item.text}")
        if item.original_text:
            language = item.original_language or "original language"
            lines.append(f"  {language} (source text): {item.original_text}")
        if item.transliteration:
            lines.append(f"  Transliteration: {item.transliteration}")
        elif item.original_language:
            # The quoted text above *is* the source-language witness; say so,
            # so the model doesn't present it as a translation.
            lines.append(
                f"  (The text above is the {item.original_language} source text; "
                "no translation of this verse is configured here.)"
            )
        if item.note:
            lines.append(f"  Why this citation is attached: {item.note}")
    return "\n".join(lines)


def _render_retrieved_evidence(evidence: tuple[EvidenceItem, ...]) -> str:
    """Passages found by the planned sub-questions.

    Labeled separately from both tiers around it: unlike primary evidence
    nobody verified these are about the concept, and unlike the flat keyword
    block each one records which sub-question found it and in which corpus,
    so a comparative answer can tell its Qur'anic evidence from its biblical
    evidence without inferring it from the citation format.
    """
    lines = ["=== RETRIEVED EVIDENCE (found by the planned sub-questions) ==="]
    for item in evidence:
        corpus = _CORPUS_LABELS.get(item.citation_type, item.citation_type)
        lines.append(f"\n[{item.citation}] ({corpus})\n{item.text}")
        if item.note:
            lines.append(f"  {item.note}")
    return "\n".join(lines)


def _render_source(source: Source) -> str:
    return f"[{source.osis}]\n{source.text}"


def _render_lexicon_entry(entry: LexiconEntry) -> str:
    return (
        f"[Strong:{entry.strongs_number}] {entry.lemma} "
        f"({entry.transliteration}): {entry.definition}"
    )
