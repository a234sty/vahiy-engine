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
matches an entry's vocalized lemma). This is not fuzzy matching and does not
try to lemmatize inflected forms.
"""

import unicodedata

from vahiy_engine.lexicon.client import LexiconClient
from vahiy_engine.lexicon.models import LexiconEntry
from vahiy_engine.search.index import STOPWORDS, normalize, tokenize


def find_lexicon_term(client: LexiconClient, question: str) -> LexiconEntry | None:
    """Return the first lexicon entry named in `question`, or None if none is.

    Question tokens are checked in the order they appear in `question`, so
    the earliest-named term wins when more than one lexicon term is present.
    When multiple registered entries share a matchable form (lemma or
    transliteration), the first one encountered in `client.iter_entries()`'s
    own deterministic order wins — both ties are resolved consistently, not
    by incidental dict/set ordering.
    """
    index = _build_form_index(client)

    for token in tokenize(normalize(question)):
        if token in STOPWORDS:
            continue
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
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))
