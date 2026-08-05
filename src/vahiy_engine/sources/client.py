"""Generic corpus access interface."""

from abc import ABC, abstractmethod
from collections.abc import Iterator

from vahiy_engine.sources.models import Verse
from vahiy_engine.sources.osis import OsisReference


class CorpusClient(ABC):
    """Common interface every corpus (Ahit and future corpora) must implement."""

    @abstractmethod
    def get_verse(self, reference: OsisReference) -> Verse:
        """Return a single verse for the given OSIS reference."""

    @abstractmethod
    def iter_verses(self) -> Iterator[Verse]:
        """Yield every verse in the corpus, in a fixed deterministic order."""
