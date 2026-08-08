"""Unit tests for the context builder."""

from vahiy_engine.lexicon.models import LexiconEntry
from vahiy_engine.rag.context_builder import build_context
from vahiy_engine.rag.retrieval import Source
from vahiy_engine.reasoning.trace import EvidenceItem


def make_source(osis: str, text: str, score: int = 1) -> Source:
    book, chapter, verse = osis.split(".")
    return Source(
        osis=osis, book=book, chapter=int(chapter), verse=int(verse), text=text, score=score
    )


def make_lexicon_entry(
    strongs_number: str = "G3056", lemma: str = "λόγος", definition: str = "something said"
) -> LexiconEntry:
    return LexiconEntry(
        strongs_number=strongs_number,
        language="greek",
        lemma=lemma,
        transliteration="lógos",
        definition=definition,
    )


def test_build_context_returns_empty_string_for_empty_list() -> None:
    assert build_context([]) == ""


def test_build_context_includes_osis_reference_and_text() -> None:
    source = make_source("Gen.1.1", "In the beginning God created the heaven and the earth.")

    context = build_context([source])

    assert "Gen.1.1" in context
    assert "In the beginning God created the heaven and the earth." in context


def test_build_context_single_source_exact_format() -> None:
    source = make_source("Gen.1.1", "In the beginning God created the heaven and the earth.")

    context = build_context([source])

    assert context == "[Gen.1.1]\nIn the beginning God created the heaven and the earth."


def test_build_context_preserves_given_order_exactly() -> None:
    sources = [
        make_source("John.3.16", "For God so loved the world..."),
        make_source("Gen.1.1", "In the beginning God created the heaven and the earth."),
        make_source("Gen.1.2", "And the earth was without form..."),
    ]

    context = build_context(sources)

    assert context.index("John.3.16") < context.index("Gen.1.1") < context.index("Gen.1.2")


def test_build_context_separates_multiple_sources_with_blank_line() -> None:
    sources = [
        make_source("Gen.1.1", "In the beginning God created the heaven and the earth."),
        make_source("Gen.1.2", "And the earth was without form..."),
    ]

    context = build_context(sources)

    assert context == (
        "[Gen.1.1]\nIn the beginning God created the heaven and the earth."
        "\n\n"
        "[Gen.1.2]\nAnd the earth was without form..."
    )


def test_build_context_blocks_are_cleanly_splittable() -> None:
    sources = [
        make_source("Gen.1.1", "Text one."),
        make_source("Gen.1.2", "Text two."),
        make_source("Gen.1.3", "Text three."),
    ]

    blocks = build_context(sources).split("\n\n")

    assert len(blocks) == 3
    assert blocks == ["[Gen.1.1]\nText one.", "[Gen.1.2]\nText two.", "[Gen.1.3]\nText three."]


def test_build_context_returns_plain_string() -> None:
    context = build_context([make_source("Gen.1.1", "Text.")])

    assert isinstance(context, str)


def test_build_context_is_deterministic_across_repeated_calls() -> None:
    sources = [
        make_source("Gen.1.1", "In the beginning God created the heaven and the earth."),
        make_source("John.1.1", "In the beginning was the Word."),
    ]

    assert build_context(sources) == build_context(sources)


def test_build_context_does_not_reorder_sources_by_score() -> None:
    # A lower-score source placed first by the caller must stay first: ordering
    # is retrieval's responsibility, not the context builder's.
    sources = [
        make_source("Gen.1.3", "Low score first.", score=1),
        make_source("Gen.1.1", "High score second.", score=5),
    ]

    context = build_context(sources)

    assert context.index("Gen.1.3") < context.index("Gen.1.1")


def test_build_context_with_no_lexicon_entries_argument_is_unaffected() -> None:
    source = make_source("Gen.1.1", "In the beginning God created the heaven and the earth.")

    assert build_context([source]) == build_context([source], None)
    assert build_context([source]) == build_context([source], [])


def test_build_context_renders_lexicon_entries_after_verse_sources() -> None:
    source = make_source("John.1.1", "In the beginning was the Word.")
    entry = make_lexicon_entry()

    context = build_context([source], [entry])

    assert context.index("John.1.1") < context.index("Strong:G3056")


def test_build_context_lexicon_entry_exact_format() -> None:
    entry = make_lexicon_entry()

    context = build_context([], [entry])

    assert context == "[Strong:G3056] λόγος (lógos): something said"


def test_build_context_with_only_lexicon_entries_and_no_sources() -> None:
    entry = make_lexicon_entry()

    context = build_context([], [entry])

    assert "Strong:G3056" in context


def test_build_context_multiple_lexicon_entries_each_get_their_own_block() -> None:
    logos = make_lexicon_entry("G3056", "λόγος", "something said")
    ab = make_lexicon_entry("H1", "אָב", "father")

    blocks = build_context([], [logos, ab]).split("\n\n")

    assert len(blocks) == 2
    assert "G3056" in blocks[0]
    assert "H1" in blocks[1]


# --- Evidence tiering, original-language rendering, and coverage limits ---


def make_evidence(
    citation: str = "Exod.3.14",
    citation_type: str = "osis",
    text: str = "I AM THAT I AM",
    **kwargs: object,
) -> EvidenceItem:
    return EvidenceItem(citation=citation, citation_type=citation_type, text=text, **kwargs)


def test_primary_evidence_is_labeled_and_rendered_before_keyword_sources() -> None:
    context = build_context(
        [make_source("Gen.1.1", "keyword hit")],
        primary_evidence=[make_evidence()],
    )

    assert context.index("PRIMARY EVIDENCE") < context.index("SUPPORTING EVIDENCE")
    assert context.index("I AM THAT I AM") < context.index("keyword hit")


def test_keyword_sources_are_not_labeled_supporting_when_no_reasoning_ran() -> None:
    # Without primary evidence there is no tier to contrast against, and a
    # "supporting" heading would imply a distinction that was never made.
    context = build_context([make_source("Gen.1.1", "text")])

    assert "SUPPORTING EVIDENCE" not in context
    assert "PRIMARY EVIDENCE" not in context


def test_each_primary_citation_is_labeled_with_its_corpus() -> None:
    context = build_context(
        [],
        primary_evidence=[
            make_evidence(citation="Gen.12.1", citation_type="osis", text="bible text"),
            make_evidence(citation="Quran.14.35", citation_type="quran", text="ayah text"),
            make_evidence(citation="Strong:H3068", citation_type="strongs", text="lemma"),
        ],
    )

    assert "[Gen.12.1] (Bible)" in context
    assert "[Quran.14.35] (Qur'an)" in context
    assert "[Strong:H3068] (Lexicon (Strong's))" in context


def test_original_language_is_rendered_alongside_the_translation() -> None:
    context = build_context(
        [],
        primary_evidence=[
            make_evidence(
                text="Tanrı Moşe'ye dedi",
                original_text="אֶֽהְיֶ֖ה אֲשֶׁ֣ר אֶֽהְיֶ֑ה",
                original_language="Hebrew",
            )
        ],
    )

    assert "Tanrı Moşe'ye dedi" in context
    assert "Hebrew (source text): אֶֽהְיֶ֖ה אֲשֶׁ֣ר אֶֽהְיֶ֑ה" in context


def test_source_language_only_evidence_is_flagged_as_not_a_translation() -> None:
    # When the corpus has no translation, the quoted text *is* the Hebrew;
    # saying so keeps the model from presenting it as a rendering.
    context = build_context(
        [],
        primary_evidence=[make_evidence(text="וַ/יֹּ֤אמֶר", original_language="Hebrew")],
    )

    assert "the Hebrew source text" in context
    assert "source text): " not in context


def test_coverage_notes_are_rendered_as_their_own_labeled_block() -> None:
    context = build_context([], coverage_notes=["No hadith corpus is configured."])

    assert "COVERAGE LIMITS" in context
    assert "- No hadith corpus is configured." in context


def test_context_is_unchanged_when_no_reasoning_arguments_are_passed() -> None:
    # The reasoning layer is additive: existing callers must get byte-identical
    # output, not merely equivalent output.
    sources = [make_source("Gen.1.1", "In the beginning")]
    entries = [make_lexicon_entry()]

    assert build_context(sources, entries) == build_context(
        sources, entries, primary_evidence=None, coverage_notes=None
    )
