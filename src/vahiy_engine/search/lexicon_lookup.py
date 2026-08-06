"""Detects a Strong's-lexicon term named in a chat question.

Distinct from reference_parser (which recognizes a Bible *reference*, e.g.
"Gen 1:1") and from search/engine.py (which ranks *verses* by relevance):
this recognizes when the question itself names a specific Greek or Hebrew
word — e.g. "What does Logos mean in John 1:1?" — so that word's lexicon
entry can be cited as a source and its definition given to the LLM as
context, alongside whatever verses are retrieved.

Matching is intentionally simple and literal, in keeping with "Deterministic
Retrieval": a question token must equal a lexicon entry's lemma (the
original-language word) or transliteration exactly, after normalizing case
and stripping diacritics/vowel-pointing (so a plain-ASCII "logos" matches
the entry transliterated "lógos", and a plain Hebrew consonantal query
matches an entry's vocalized lemma). Standalone Unicode modifier letters
used by the Hebrew transliteration scheme to mark aleph/ayin (ʼ, ʻ) are
stripped too — verified via unicodedata.combining() that these are NOT
combining marks (they're spacing letters), so a plain-ASCII "Elohim" still
needs them stripped separately to reach "elohim" from the entry's own
transliteration "ʼĕlôhîym" -> "ʼelohiym" -> "elohiym". This is not fuzzy
matching and does not try to lemmatize inflected forms.

Academic transliteration and common English spelling can still diverge
beyond what stripping fixes — "elohiym" (from "ʼĕlôhîym") vs. "elohim" is a
genuine spelling difference (the source transliterates the Hebrew mater
lectionis yod as a literal "y"), not a diacritic. COMMON_ALIASES is a small,
explicit table for well-known English loanwords like this, the same kind of
curated exception list reference_parser.py already uses for book names.
"""

import unicodedata

from vahiy_engine.lexicon.client import LexiconClient
from vahiy_engine.lexicon.models import LexiconEntry
from vahiy_engine.search.index import STOPWORDS, normalize, tokenize

COMMON_ALIASES: dict[str, str] = {
    "elohim": "H430",
}
"""Maps a lowercased common English spelling to the Strong's number it names,
for well-known loanwords whose established English spelling doesn't literally
match any registered entry's lemma or transliteration."""

_SILENT_MODIFIER_LETTERS = frozenset({"ʼ", "ʻ"})
"""Hebrew aleph/ayin markers (U+02BC, U+02BB): spacing modifier letters, not
combining marks, so unicodedata.combining() alone won't strip them — but
they're routinely dropped in casual English spelling all the same."""


def find_lexicon_term(client: LexiconClient, question: str) -> LexiconEntry | None:
    """Return the first lexicon entry named in `question`, or None if none is.

    Question tokens are checked in the order they appear in `question`, so
    the earliest-named term wins when more than one lexicon term is present.
    When multiple registered entries share a matchable form (lemma or
    transliteration), the first one encountered in `client.iter_entries()`'s
    own deterministic order wins — both ties are resolved consistently, not
    by incidental dict/set ordering. COMMON_ALIASES is checked before the
    transliteration index for each token; if an alias's Strong's number isn't
    registered on `client` (e.g. its language's lexicon wasn't loaded), that
    token falls through to the normal index lookup rather than erroring.
    """
    index = _build_form_index(client)

    for token in tokenize(normalize(question)):
        if token in STOPWORDS:
            continue

        alias_number = COMMON_ALIASES.get(token)
        if alias_number is not None:
            try:
                return client.get_entry(alias_number)
            except LookupError:
                pass

        match = index.get(_strip_diacritics(token))
        if match is not None:
            return match

    return None


def _build_form_index(client: LexiconClient) -> dict[str, LexiconEntry]:
    index: dict[str, LexiconEntry] = {}
    for entry in client.iter_entries():
        for form in (entry.lemma, entry.transliteration):
            if not form:
                continue
            key = _strip_diacritics(normalize(form))
            if key and key not in index:
                index[key] = entry
    return index


def _strip_diacritics(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(
        ch
        for ch in decomposed
        if not unicodedata.combining(ch) and ch not in _SILENT_MODIFIER_LETTERS
    )
