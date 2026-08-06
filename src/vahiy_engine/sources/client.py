"""Generic corpus access interface."""

from abc import ABC, abstractmethod
from collections.abc import Iterator

from vahiy_engine.sources.models import Verse
from vahiy_engine.sources.osis import OsisReference


class CorpusClient(ABC):
    """Common interface every corpus (Ahit and future corpora) must implement.

    `translation` is optional on both methods: omitting it (or passing None)
    means "this implementation's own default translation" — every existing
    caller that doesn't care which translation it's reading keeps working
    unchanged as new translations are registered on a given client.
    """

    @abstractmethod
    def get_verse(self, reference: OsisReference, translation: str | None = None) -> Verse:
        """Return a single verse for the given OSIS reference."""

    @abstractmethod
    def iter_verses(self, translation: str | None = None) -> Iterator[Verse]:
        """Yield every verse in the corpus, in a fixed deterministic order."""
