"""Unit tests for the context builder."""

from vahiy_engine.lexicon.models import LexiconEntry
from vahiy_engine.rag.context_builder import build_context
from vahiy_engine.rag.retrieval import Source


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
