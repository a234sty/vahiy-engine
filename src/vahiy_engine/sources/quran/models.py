"""Qur'an domain models.

Deliberately not reusing `sources.models.Verse` or `sources.osis.OsisReference`:
the Qur'an has no "book" concept — one continuous text divided into surahs and
ayat — so forcing it into Bible's book.chapter.verse shape would mean either a
fake book code or a lossy reuse of a reference type that doesn't fit. Giving it
its own reference shape is the same choice already made for every other
resource in this corpus (Strong's numbers over OSIS references, Hebrew's own
OSIS-glossary shape over the Bible-text OSIS shape): match the source's own
structure rather than the first abstraction that happened to exist already.
"""

from pydantic import BaseModel


class Ayah(BaseModel):
    surah: int
    ayah: int
    text: str
    edition: str = "arabic"


class QuranReference(BaseModel):
    surah: int
    ayah: int

    @property
    def citation(self) -> str:
        return f"Quran.{self.surah}.{self.ayah}"
