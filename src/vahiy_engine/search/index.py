"""Search index build/lookup."""

import unicodedata
from dataclasses import dataclass

from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.models import Verse

_TURKISH_I_FOLD = str.maketrans({"İ": "i", "I": "i", "ı": "i"})


def normalize(text: str) -> str:
    """Normalize text for matching.

    Unicode NFKC-normalizes and casefolds text. Turkish letters that aren't part of
    the Latin I/i case pair (ç, ğ, ö, ş, ü) are preserved as distinct letters, never
    stripped to ASCII look-alikes. The four-way Turkish I/ı/İ/i case ambiguity — where
    plain casefold alone leaves ASCII "I" and Turkish "ı" as different letters — is
    folded to one form, so a plain-ASCII query like "TANRI" matches Turkish "Tanrı".
    """
    folded = text.translate(_TURKISH_I_FOLD)
    return unicodedata.normalize("NFKC", folded).casefold()


@dataclass(frozen=True)
class IndexedVerse:
    verse: Verse
    normalized_text: str


def build_index(corpus: CorpusClient) -> list[IndexedVerse]:
    """Build a normalized, deterministically ordered index of every verse in the corpus."""
    return [IndexedVerse(verse=v, normalized_text=normalize(v.text)) for v in corpus.iter_verses()]
