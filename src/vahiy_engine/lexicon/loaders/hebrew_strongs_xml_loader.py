"""Loader for ahit-corpus's Hebrew Strong's dictionary (lexicon/hebrew/StrongHebrewG.xml).

Source: "A Concise Dictionary of the Words in the Hebrew Bible" (David
Troidl / David Instone-Brewer's cleaned-up edition of Strong's Hebrew
dictionary), in OSIS-XML glossary form — a different dialect from
GreekStrongsXmlLoader's flat DTD format, and also different from
OsisXmlLoader's Bible-text OSIS (this is an OSIS *glossary*, not Bible
text: <div type="entry"> instead of <verse>).

Each entry is a `<div type="entry">` whose relevant direct children are:

- <w ID="H1" lemma="..." xlit="..." .../> is the entry's own headword,
  always the first <w> child of the entry div. `ID` is the entry's Strong's
  number, already in the spec's own citation form ("H1") with no
  reformatting needed. `lemma` is the vocalized Hebrew word; `xlit` is its
  transliteration. (A `<foreign>` sibling, when present, nests further
  <w> elements for cross-referenced Greek equivalents — not the entry's
  own headword, and not read here.)
- <list><item>1) ...</item>...</list> holds the numbered dictionary senses;
  joined with "; " to form `definition`.
- <note type="translation"> holds the KJV-rendering gloss, kept as
  `kjv_translation`. (Sibling <note type="exegesis"> and <note
  type="explanation"> notes carry etymology/gloss information not modeled
  by LexiconEntry today, and are not read here.)

There is no separate pronunciation guide in this format (unlike Greek's
<pronunciation>), so `pronunciation` is always None for Hebrew entries.

<item> and <note type="translation"> text is extracted with
ElementTree's `itertext()` and whitespace-collapsed, the same as
GreekStrongsXmlLoader: some entries' translation notes contain nested
empty <w src="..." .../> cross-reference elements (e.g. "Compare <w
src="369" .../>."), which — like Greek's <strongsref> — carry no display
text of their own and so contribute nothing but their surrounding prose,
exactly as OsisXmlLoader and GreekStrongsXmlLoader already treat their
own cross-reference markup.
"""

from pathlib import Path
from xml.etree import ElementTree

from vahiy_engine.lexicon.loaders.base import LexiconLoader
from vahiy_engine.lexicon.models import LexiconEntry


class HebrewStrongsXmlLoader(LexiconLoader):
    """Loads every entry from ahit-corpus's Hebrew Strong's dictionary XML file."""

    language = "hebrew"

    def load(self, lexicon_path: Path) -> dict[str, LexiconEntry]:
        root = ElementTree.parse(lexicon_path).getroot()

        entries: dict[str, LexiconEntry] = {}
        for entry_div in root.iter():
            if _local_name(entry_div.tag) != "div" or entry_div.get("type") != "entry":
                continue

            headword = _direct_child(entry_div, "w")
            list_element = _direct_child(entry_div, "list")
            if headword is None or list_element is None:
                raise ValueError(
                    f"Entry n='{entry_div.get('n')}' in {lexicon_path} is missing its "
                    "required <w> headword or <list> of definitions"
                )

            strongs_number = headword.get("ID")
            if not strongs_number:
                raise ValueError(
                    f"Entry n='{entry_div.get('n')}' in {lexicon_path} has a <w> headword "
                    "with no ID attribute"
                )

            translation_note = _find_note(entry_div, "translation")

            entries[strongs_number] = LexiconEntry(
                strongs_number=strongs_number,
                language=self.language,
                lemma=headword.get("lemma", ""),
                transliteration=headword.get("xlit"),
                pronunciation=None,
                definition=_join_items(list_element),
                kjv_translation=(
                    _collapse_whitespace(_text_of(translation_note))
                    if translation_note is not None
                    else None
                ),
            )

        return entries


def _direct_child(element: ElementTree.Element, name: str) -> ElementTree.Element | None:
    for child in element:
        if _local_name(child.tag) == name:
            return child
    return None


def _find_note(element: ElementTree.Element, note_type: str) -> ElementTree.Element | None:
    for child in element:
        if _local_name(child.tag) == "note" and child.get("type") == note_type:
            return child
    return None


def _join_items(list_element: ElementTree.Element) -> str:
    items = [
        _collapse_whitespace(_text_of(child))
        for child in list_element
        if _local_name(child.tag) == "item"
    ]
    return "; ".join(items)


def _text_of(element: ElementTree.Element) -> str:
    return "".join(element.itertext())


def _collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
