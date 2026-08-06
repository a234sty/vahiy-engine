"""Search index build/lookup."""

import re
import unicodedata
from dataclasses import dataclass

from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.models import Verse

_TURKISH_I_FOLD = str.maketrans({"İ": "i", "I": "i", "ı": "i"})
_NON_WORD_PATTERN = re.compile(r"[^\w\s]+", re.UNICODE)
_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Normalize text for matching.

    Unicode NFKC-normalizes and casefolds text. Turkish letters that aren't part of
    the Latin I/i case pair (ç, ğ, ö, ş, ü) are preserved as distinct letters, never
    stripped to ASCII look-alikes. The four-way Turkish I/ı/İ/i case ambiguity — where
    plain casefold alone leaves ASCII "I" and Turkish "ı" as different letters — is
    folded to one form, so a plain-ASCII query like "TANRI" matches Turkish "Tanrı".

    Punctuation is replaced with whitespace (never deleted outright, so words
    never merge into one) and runs of whitespace collapse to a single space, so
    a query that differs from a verse only by punctuation — a comma the query
    omits, say — still matches as an exact phrase.
    """
    folded = text.translate(_TURKISH_I_FOLD)
    normalized = unicodedata.normalize("NFKC", folded).casefold()
    without_punctuation = _NON_WORD_PATTERN.sub(" ", normalized)
    return _WHITESPACE_PATTERN.sub(" ", without_punctuation).strip()


def tokenize(normalized_text: str) -> list[str]:
    """Split already-normalized text into word tokens."""
    return normalized_text.split()


# Common function/question words excluded from keyword-fallback matching, since
# they carry little search relevance on their own (English + Turkish; already
# spelled in their post-normalize() form, e.g. "nasil" not "nasıl").
STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "do",
        "does",
        "did",
        "what",
        "who",
        "whom",
        "whose",
        "which",
        "why",
        "how",
        "when",
        "where",
        "in",
        "on",
        "at",
        "to",
        "of",
        "for",
        "and",
        "or",
        "but",
        "with",
        "about",
        "say",
        "says",
        "said",
        "tell",
        "tells",
        "told",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "his",
        "her",
        "he",
        "she",
        "they",
        "them",
        "their",
        "i",
        "you",
        "we",
        "us",
        "our",
        "your",
        "my",
        "me",
        "mean",
        "meaning",
        "verse",
        "verses",
        "bible",
        "scripture",
        "ne",
        "nedir",
        "kim",
        "kimdir",
        "nasil",
        "neden",
        "niçin",
        "mi",
        "mu",
        "mü",
        "bir",
        "ve",
        "ile",
        "bu",
        "şu",
        "o",
        "için",
        "gibi",
        "de",
        "da",
    }
)


@dataclass(frozen=True)
class IndexedVerse:
    verse: Verse
    normalized_text: str


def build_index(corpus: CorpusClient) -> list[IndexedVerse]:
    """Build a normalized, deterministically ordered index of every verse in the corpus."""
    return [IndexedVerse(verse=v, normalized_text=normalize(v.text)) for v in corpus.iter_verses()]
