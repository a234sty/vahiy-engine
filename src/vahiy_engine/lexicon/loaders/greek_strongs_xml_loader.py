"""Loader for ahit-corpus's Greek Strong's dictionary (lexicon/greek/strongsgreek.xml).

Source: the public-domain Strong's Exhaustive Concordance Greek dictionary,
XML edition prepared by Ulrik Petersen. It uses its own small DTD, not
OSIS — each entry is a flat `<entry strongs="00001">` with a fixed set of
possible children:

- <strongs> repeats the entry's own number as plain text (redundant with
  the `strongs` attribute; not used here).
- <greek unicode="..." translit="..." BETA="..."/> is the headword, always
  the first <greek> child of the entry. `unicode` is the real Greek word;
  `translit` is its transliteration. (Later <greek> elements can appear
  inside <strongs_derivation> or loose entry text as inline references to
  *other* words — those are ignored; only the first one, the entry's own
  headword, is used.)
- <pronunciation strongs="..."/> gives the pronunciation guide.
- <strongs_derivation> and <strongs_def> hold etymology and definition
  prose respectively, and may contain nested <greek>, <latin>, or
  <strongsref> elements inline. Only <strongs_def> is kept, as the
  entry's `definition` — except for a small number of entries (verified:
  19 in ahit-corpus's copy) that have a real headword but no <strongs_def>
  at all, only a <kjv_def>; for those, <kjv_def>'s text is used as the
  definition too, since it's the only prose available.
- <kjv_def> holds the KJV-translation gloss, kept as `kjv_translation`.
- <see language="..." strongs=".../> and <strongsref language="..."
  strongs="..."/> are empty elements marking a cross-reference to another
  entry. Neither carries display text of its own, so — like every loader
  in this codebase — they contribute nothing to the reconstructed prose
  rather than being resolved or smoothed over; any stray punctuation the
  source text built around them (e.g. "akin to the base of );") is kept
  exactly as written, since fixing it would mean editing the source, not
  transcribing it.

A small number of Strong's numbers (verified: 101 in ahit-corpus's copy)
were reserved but never assigned to a word — Strong's own edition marks
these with the entry's whole content being the plain text "Not Used" and
no <greek> headword, <strongs_def>, or <kjv_def> at all. These aren't
real dictionary entries, so they're skipped entirely rather than
producing a LexiconEntry with fabricated content for a word that was
never assigned one.

<strongs_def> and <kjv_def> prose is extracted with ElementTree's
`itertext()` (every descendant text and tail node, in document order),
then whitespace-collapsed to a single line, since the source file wraps
prose across lines purely for readability of the XML itself.
"""

from pathlib import Path
from xml.etree import ElementTree

from vahiy_engine.lexicon.loaders.base import LexiconLoader
from vahiy_engine.lexicon.models import LexiconEntry


class GreekStrongsXmlLoader(LexiconLoader):
    """Loads every entry from ahit-corpus's Greek Strong's dictionary XML file."""

    language = "greek"

    def load(self, lexicon_path: Path) -> dict[str, LexiconEntry]:
        root = ElementTree.parse(lexicon_path).getroot()

        entries: dict[str, LexiconEntry] = {}
        for entry_element in root.iter("entry"):
            raw_number = entry_element.get("strongs")
            if not raw_number:
                continue

            strongs_number = f"G{int(raw_number)}"

            greek = entry_element.find("greek")
            if greek is None:
                # A reserved-but-unassigned "Not Used" number — not a real entry.
                continue

            strongs_def = entry_element.find("strongs_def")
            kjv_def = entry_element.find("kjv_def")
            definition_source = strongs_def if strongs_def is not None else kjv_def
            if definition_source is None:
                raise ValueError(
                    f"Entry strongs='{raw_number}' in {lexicon_path} has a <greek> headword "
                    "but neither a <strongs_def> nor a <kjv_def> to use as its definition"
                )

            pronunciation = entry_element.find("pronunciation")

            entries[strongs_number] = LexiconEntry(
                strongs_number=strongs_number,
                language=self.language,
                lemma=greek.get("unicode", ""),
                transliteration=greek.get("translit"),
                pronunciation=(pronunciation.get("strongs") if pronunciation is not None else None),
                definition=_collapse_whitespace(_text_of(definition_source)),
                kjv_translation=(
                    _collapse_whitespace(_text_of(kjv_def)) if kjv_def is not None else None
                ),
            )

        return entries


def _text_of(element: ElementTree.Element) -> str:
    return "".join(element.itertext())


def _collapse_whitespace(text: str) -> str:
    return " ".join(text.split())
