"""Unit tests for HebrewStrongsXmlLoader.

Fragments marked "real ahit-corpus data" were captured verbatim from the
actual lexicon/hebrew/StrongHebrewG.xml file, and expected field values
were computed by running the loader's own extraction algorithm against
them directly, not hand-typed.
"""

from pathlib import Path

import pytest

from vahiy_engine.lexicon.loaders.hebrew_strongs_xml_loader import HebrewStrongsXmlLoader

OSIS_NAMESPACE = "http://www.bibletechnologies.net/2003/OSIS/namespace"

# Real ahit-corpus data: H1 (אָב / "ab", father) — has a <foreign> sibling
# nesting cross-referenced Greek <w> elements (not the entry's own
# headword), an 11-item <list>, and all three <note> types.
H1 = """<div type="entry" n="1">
        <w gloss="4a" lemma="אָב" morph="n-m" POS="awb" xlit="ʼâb" ID="H1" xml:lang="heb">אב</w>
        <foreign xml:lang="grc">
          <w gloss="G:1118" />
          <w gloss="G:2730" />
        </foreign>
        <list>
          <item>1) father of an individual</item>
          <item>2) of God as father of his people</item>
          <item>3) head or founder of a household,  group,  family,  or clan</item>
          <item>4) ancestor</item>
          <item>4a) grandfather,  forefathers — of person</item>
          <item>4b) of people</item>
          <item>5) originator or patron of a class,  profession,  or art</item>
          <item>6) of producer,  generator (fig.)</item>
          <item>7) of benevolence and protection (fig.)</item>
          <item>8) term of respect and honour</item>
          <item>9) ruler or chief (spec.)</item>
        </list>
        <note type="exegesis">a primitive word;</note>
        <note type="explanation"><hi>father</hi>, in a literal and immediate, or figurative \
and remote application</note>
        <note type="translation">chief, (fore-) father(-less), [idiom] patrimony, principal. \
Compare names in 'Abi-'.</note>
      </div>"""

# Real ahit-corpus data: H165 (אֱהִי), no <foreign> sibling, single-item
# <list>, and a <note type="translation"> containing a nested empty <w
# src="..."/> cross-reference — proving those contribute no display text,
# the same way GreekStrongsXmlLoader's <strongsref> elements don't.
H165 = """<div type="entry" n="165">
        <w gloss="31" lemma="אֱהִי" morph="adv" POS="e-hee'" xlit="ʼĕhîy" ID="H165" xml:lang="heb">\
אהי</w>
        <list>
          <item>1) where</item>
        </list>
        <note type="exegesis">apparently an orthographical variation for <w lemma="אַיֵּה" \
POS="ah-yay'" src="346" xlit="ʼayêh"/>;</note>
        <note type="explanation"><hi>where</hi></note>
        <note type="translation">I will be (Hosea 13:10,14) (which is often the rendering of \
the same Hebrew form from <w lemma="הָיָה" POS="haw-yaw" src="1961" xlit="hâyâh"/>).</note>
      </div>"""


# Real ahit-corpus data: H430 (אֱלֹהִים / "Elohim") — its POS attribute
# ("el-o-heem'") is a phonetic pronunciation guide, not a part-of-speech
# tag (morph="n-m" already carries that).
H430 = """<div type="entry" n="430">
        <w gloss="93c" lemma="אֱלֹהִים" morph="n-m" POS="el-o-heem'" xlit="ʼĕlôhîym" ID="H430" \
xml:lang="heb">אלהים</w>
        <foreign xml:lang="grc">
          <w gloss="G:2304" />
          <w gloss="G:2316" />
        </foreign>
        <list>
          <item>1) (plural)</item>
          <item>2e) God</item>
        </list>
        <note type="exegesis">plural of <w lemma="אֱלוֹהַּ" POS="el-o'-ah" src="433" \
xlit="ʼĕlôwahh"/>;</note>
        <note type="explanation"><hi>gods</hi> in the ordinary sense</note>
        <note type="translation">angels, [idiom] exceeding, God (gods) (-dess, -ly), [idiom] \
(very) great, judges, [idiom] mighty.</note>
      </div>"""


def _write_dictionary(directory: Path, *entries: str) -> Path:
    doc = (
        f'<osis xmlns="{OSIS_NAMESPACE}"><osisText>'
        f'<div type="glossary">{"".join(entries)}</div>'
        "</osisText></osis>"
    )
    path = directory / "StrongHebrewG.xml"
    path.write_text(doc, encoding="utf-8")
    return path


def test_language_is_hebrew() -> None:
    assert HebrewStrongsXmlLoader().language == "hebrew"


def test_parses_h1_with_its_numbered_senses_and_kjv_gloss(tmp_path: Path) -> None:
    path = _write_dictionary(tmp_path, H1)

    entries = HebrewStrongsXmlLoader().load(path)

    ab = entries["H1"]
    assert ab.strongs_number == "H1"
    assert ab.language == "hebrew"
    assert ab.lemma == "אָב"
    assert ab.transliteration == "ʼâb"
    assert ab.pronunciation == "awb"
    assert ab.definition == (
        "1) father of an individual; 2) of God as father of his people; "
        "3) head or founder of a household, group, family, or clan; 4) ancestor; "
        "4a) grandfather, forefathers — of person; 4b) of people; "
        "5) originator or patron of a class, profession, or art; "
        "6) of producer, generator (fig.); 7) of benevolence and protection (fig.); "
        "8) term of respect and honour; 9) ruler or chief (spec.)"
    )
    assert ab.kjv_translation == (
        "chief, (fore-) father(-less), [idiom] patrimony, principal. Compare names in 'Abi-'."
    )


def test_foreign_sibling_w_elements_are_not_mistaken_for_the_headword(tmp_path: Path) -> None:
    path = _write_dictionary(tmp_path, H1)

    entry = HebrewStrongsXmlLoader().load(path)["H1"]

    # The headword is the entry's own <w>, not one of the cross-referenced
    # Greek <w gloss="G:..."/> elements nested inside <foreign>.
    assert entry.lemma == "אָב"


def test_nested_w_cross_reference_inside_translation_note_contributes_no_text(
    tmp_path: Path,
) -> None:
    path = _write_dictionary(tmp_path, H165)

    entry = HebrewStrongsXmlLoader().load(path)["H165"]

    assert entry.definition == "1) where"
    assert entry.kjv_translation == (
        "I will be (Hosea 13:10,14) (which is often the rendering of the same "
        "Hebrew form from )."
    )


def test_pos_attribute_is_read_as_pronunciation_not_discarded(tmp_path: Path) -> None:
    path = _write_dictionary(tmp_path, H430)

    entry = HebrewStrongsXmlLoader().load(path)["H430"]

    assert entry.pronunciation == "el-o-heem'"
    assert entry.lemma == "אֱלֹהִים"
    assert entry.transliteration == "ʼĕlôhîym"


def test_parses_multiple_entries_from_one_file(tmp_path: Path) -> None:
    path = _write_dictionary(tmp_path, H1, H165)

    entries = HebrewStrongsXmlLoader().load(path)

    assert set(entries) == {"H1", "H165"}


def test_raises_value_error_when_entry_is_missing_required_elements(tmp_path: Path) -> None:
    path = _write_dictionary(tmp_path, '<div type="entry" n="99999"></div>')

    with pytest.raises(ValueError, match="99999"):
        HebrewStrongsXmlLoader().load(path)
