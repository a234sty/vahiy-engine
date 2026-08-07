"""Loader for ahit-corpus's Qur'an JSON editions.

All four files ahit-corpus ships (quran.json/Arabic, quran-en.json,
quran-tr.json, quran-transliteration.json) share one shape:
`{"<surah>": [{"chapter": N, "verse": M, "text": "..."}, ...]}` — a dict
keyed by surah number, each value a flat list of ayah objects for that
surah. One loader handles all four; only which file it's pointed at
determines the edition's language.
"""

import json
from pathlib import Path

from vahiy_engine.sources.quran.models import Ayah


class QuranJsonLoader:
    """Loads one whole Qur'an edition file into every ayah it contains."""

    def load(self, file_path: Path, edition: str) -> dict[tuple[int, int], Ayah]:
        with file_path.open(encoding="utf-8") as f:
            raw = json.load(f)

        ayat: dict[tuple[int, int], Ayah] = {}
        for entries in raw.values():
            for entry in entries:
                surah = int(entry["chapter"])
                ayah_number = int(entry["verse"])
                ayat[(surah, ayah_number)] = Ayah(
                    surah=surah, ayah=ayah_number, text=entry["text"], edition=edition
                )
        return ayat
