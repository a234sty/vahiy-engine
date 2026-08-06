"""Loader for ahit-corpus's Hebrew Old Testament OSIS-XML text (WLC).

Source: the OpenScriptures Hebrew Bible (github.com/openscriptures/morphhb),
the Westminster Leningrad Codex in OSIS-XML with word-level morphological
tagging. Only the Bible text itself is reconstructed here — the lemma/morph
attributes on each <w> belong to a future morphology feature, not retrieval.

Verse text is rebuilt from each <verse>'s direct children, in document order:

- <w> is a word; consecutive words are separated by a single space, unless a
  maqqef binds them (see below).
- <seg type="x-maqqef"> is the maqqef (a hyphen-like connector): it attaches
  directly to the preceding word with no space, and also suppresses the
  space before the *next* word, since maqqef binds both sides.
- <seg> of any other type (e.g. "x-sof-pasuq", the verse-final punctuation
  mark; "x-paseq", a disjunctive stroke) attaches directly to the preceding
  word with no space, but does not affect the word that follows it.
- <note> (editorial/text-critical footnotes) is skipped entirely, along with
  everything nested inside it.

Ketiv/qere: where the Masoretic tradition marks a word as "written" one way
but "read" another, ahit-corpus's source data represents the ketiv (written
form) as an ordinary <w> in the verse's main flow, and the qere (read form)
nested inside a sibling <note><rdg type="x-qere"><w>...</w></rdg></note>.
Since <note> is skipped entirely, this loader always reconstructs the ketiv
form. This is a deliberate, documented choice to do plain, faithful text
extraction rather than an editorial ketiv/qere selection — not currently
configurable.

Word text includes the source's own morpheme-boundary "/" markers (e.g.
"הָ/אִישׁ" for "the man") exactly as written — these are not stripped, since
doing so would mean editing rather than transcribing the source.
"""

from pathlib import Path
from xml.etree import ElementTree

from vahiy_engine.sources.loaders.base import BookLoader


class OsisXmlLoader(BookLoader):
    """Loads a book from ahit-corpus's per-book OSIS-XML files (Hebrew OT / WLC)."""

    file_extension = "xml"

    def load(self, corpus_path: Path, book: str) -> dict[int, dict[int, str]]:
        book_file = corpus_path / f"{book}.xml"
        if not book_file.is_file():
            raise FileNotFoundError(f"No corpus file found for book '{book}' at {book_file}")

        root = ElementTree.parse(book_file).getroot()

        chapters: dict[int, dict[int, str]] = {}
        for verse_element in root.iter():
            if _local_name(verse_element.tag) != "verse":
                continue

            osis_id = verse_element.get("osisID")
            if not osis_id:
                continue

            parts = osis_id.split(".")
            if len(parts) != 3 or parts[0] != book:
                continue

            chapter_number = int(parts[1])
            verse_number = int(parts[2])
            chapters.setdefault(chapter_number, {})[verse_number] = _reconstruct_verse_text(
                verse_element
            )

        if not chapters:
            raise ValueError(
                f"{book_file} contained no verses recognized as book '{book}' — is this really "
                "a per-book OSIS file, and not e.g. a versification map?"
            )

        return chapters


def _reconstruct_verse_text(verse_element: ElementTree.Element) -> str:
    parts: list[str] = []
    suppress_leading_space = True

    for child in verse_element:
        tag = _local_name(child.tag)
        text = child.text or ""

        if tag == "w":
            if parts and not suppress_leading_space:
                parts.append(" ")
            parts.append(text)
            suppress_leading_space = False
        elif tag == "seg":
            parts.append(text)
            suppress_leading_space = child.get("type") == "x-maqqef"
        # <note> and anything else are skipped entirely — no text, no effect
        # on spacing.

    return "".join(parts)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
