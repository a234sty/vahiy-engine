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


# --- Modifier-letter stripping (Hebrew aleph/ayin markers) ---


def test_plain_ascii_query_matches_a_transliteration_with_a_leading_modifier_letter() -> None:
    # AB's transliteration is "ʼâb" — the leading "ʼ" is a spacing modifier
    # letter (aleph marker), not a combining diacritic, so it needs its own
    # stripping rule; a plain "ab" (no marker, no accent) must still match.
    client = FakeLexiconClient([AB])

    match = find_lexicon_term(client, "What does ab mean?")

    assert match is not None
    assert match.strongs_number == "H1"


# --- COMMON_ALIASES: established English loanword spellings ---


def test_elohim_alias_resolves_to_h430() -> None:
    # "Elohim" is the established English spelling; the entry's own
    # transliteration ("ʼĕlôhîym") differs by more than diacritics/markers
    # (it spells the Hebrew mater lectionis yod as a literal "y"), so this
    # can only resolve via the curated alias, not the transliteration index.
    elohim = LexiconEntry(
        strongs_number="H430",
        language="hebrew",
        lemma="אֱלֹהִים",
        transliteration="ʼĕlôhîym",
        pronunciation="el-o-heem'",
        definition="gods, God",
    )
    client = FakeLexiconClient([elohim])

    match = find_lexicon_term(client, "What does Elohim mean?")

    assert match is not None
    assert match.strongs_number == "H430"


def test_elohim_alias_is_case_insensitive() -> None:
    elohim = LexiconEntry(
        strongs_number="H430", language="hebrew", lemma="אֱלֹהִים", definition="gods, God"
    )
    client = FakeLexiconClient([elohim])

    assert find_lexicon_term(client, "ELOHIM") is not None
    assert find_lexicon_term(client, "elohim") is not None


def test_alias_falls_through_when_its_number_is_not_registered_on_the_client() -> None:
    # The Hebrew lexicon isn't loaded on this client at all — H430 doesn't
    # exist here, so the alias must fail gracefully (None), not raise.
    client = FakeLexiconClient([LOGOS])

    assert find_lexicon_term(client, "What does Elohim mean?") is None
