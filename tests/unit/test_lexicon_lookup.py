"""Unit tests for find_lexicon_term()."""

from collections.abc import Iterator

from vahiy_engine.lexicon.client import LexiconClient
from vahiy_engine.lexicon.models import LexiconEntry
from vahiy_engine.search.lexicon_lookup import find_lexicon_term

LOGOS = LexiconEntry(
    strongs_number="G3056",
    language="greek",
    lemma="λόγος",
    transliteration="lógos",
    definition="something said",
)

AB = LexiconEntry(
    strongs_number="H1",
    language="hebrew",
    lemma="אָב",
    transliteration="ʼâb",
    definition="father",
)


class FakeLexiconClient(LexiconClient):
    def __init__(self, entries: list[LexiconEntry]) -> None:
        self._entries = entries

    def get_entry(self, strongs_number: str) -> LexiconEntry:
        for entry in self._entries:
            if entry.strongs_number == strongs_number:
                return entry
        raise LookupError(strongs_number)

    def iter_entries(self, language: str | None = None) -> Iterator[LexiconEntry]:
        for entry in self._entries:
            if language is None or entry.language == language:
                yield entry


def test_finds_the_spec_example_term_by_transliteration() -> None:
    client = FakeLexiconClient([LOGOS])

    match = find_lexicon_term(client, "What does Logos mean in John 1:1?")

    assert match is not None
    assert match.strongs_number == "G3056"


def test_transliteration_match_ignores_diacritics() -> None:
    client = FakeLexiconClient([LOGOS])

    # The entry is transliterated with an accent ("lógos"); a plain ASCII
    # "logos" in the question still matches it.
    match = find_lexicon_term(client, "logos")

    assert match is not None
    assert match.strongs_number == "G3056"


def test_lemma_match_using_the_original_language_script() -> None:
    client = FakeLexiconClient([LOGOS])

    match = find_lexicon_term(client, "What does λόγος mean?")

    assert match is not None
    assert match.strongs_number == "G3056"


def test_returns_none_when_no_token_matches() -> None:
    client = FakeLexiconClient([LOGOS, AB])

    assert find_lexicon_term(client, "What is faith?") is None


def test_returns_none_for_empty_lexicon() -> None:
    client = FakeLexiconClient([])

    assert find_lexicon_term(client, "logos") is None


def test_stopwords_are_never_matched_even_if_present_in_a_lexicon() -> None:
    # A pathological lexicon entry whose transliteration collides with a
    # stopword must never surface — stopwords are excluded from matching
    # before the lexicon index is even consulted.
    collider = LexiconEntry(
        strongs_number="G1", language="greek", lemma="x", transliteration="is", definition="d"
    )
    client = FakeLexiconClient([collider])

    assert find_lexicon_term(client, "What is faith?") is None


def test_earliest_named_term_wins_when_question_has_more_than_one() -> None:
    client = FakeLexiconClient([LOGOS, AB])

    # "ʼâb" (father) appears in the question before "logos" — Hebrew
    # transliterations conventionally lead with the "ʼ" glottal marker, so
    # this token must be typed as it actually appears in the source data.
    match = find_lexicon_term(client, "ʼâb before logos")

    assert match is not None
    assert match.strongs_number == "H1"


def test_first_registered_entry_wins_on_a_duplicate_form() -> None:
    first = LexiconEntry(
        strongs_number="G1", language="greek", lemma="a", transliteration="dupe", definition="d1"
    )
    second = LexiconEntry(
        strongs_number="G2", language="greek", lemma="b", transliteration="dupe", definition="d2"
    )
    client = FakeLexiconClient([first, second])

    match = find_lexicon_term(client, "dupe")

    assert match is not None
    assert match.strongs_number == "G1"
