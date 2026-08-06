"""Generic lexicon access interface."""

from abc import ABC, abstractmethod
from collections.abc import Iterator

from vahiy_engine.lexicon.models import LexiconEntry


class LexiconClient(ABC):
    """Common interface every lexicon (Strong's and future lexicons) must implement.

    Unlike `CorpusClient`, entries are addressed by Strong's number rather
    than an OSIS reference, and there is no "default" language to fall back
    to — a lookup always names the number it wants (e.g. "G3056", "H1"), and
    the number's own letter prefix says which language it belongs to.
    """

    @abstractmethod
    def get_entry(self, strongs_number: str) -> LexiconEntry:
        """Return a single entry for the given Strong's number (e.g. "G3056")."""

    @abstractmethod
    def iter_entries(self, language: str | None = None) -> Iterator[LexiconEntry]:
        """Yield every entry in the lexicon, in a fixed deterministic order.

        `language` optionally restricts iteration to one language ("greek" or
        "hebrew"); omitting it yields every registered language's entries.
        """
