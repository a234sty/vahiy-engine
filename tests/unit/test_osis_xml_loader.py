"""Unit tests for OsisXmlLoader (Hebrew OT OSIS-XML / WLC).

Fragments marked "real ahit-corpus data" below were captured verbatim from
the actual WLC XML files in ahit-corpus (bible/ot/books/Gen.xml, Ps.xml) to
exercise the loader against real-world markup, not just simplified cases.
"""

from pathlib import Path

import pytest

from vahiy_engine.sources.loaders.osis_xml_loader import OsisXmlLoader

OSIS_NAMESPACE = "http://www.bibletechnologies.net/2003/OSIS/namespace"


def _write_book(directory: Path, book: str, chapter: int, verse_xml: str) -> Path:
    doc = f"""<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="{OSIS_NAMESPACE}" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="{OSIS_NAMESPACE} http://www.bibletechnologies.net/osisCore.2.1.1.xsd">
  <osisText xml:lang="he" osisIDWork="OSHB" osisRefWork="Bible">
    <header></header>
    <div type="book" osisID="{book}">
      <chapter osisID="{book}.{chapter}">
        {verse_xml}
      </chapter>
    </div>
  </osisText>
</osis>
"""
    path = directory / f"{book}.xml"
    path.write_text(doc, encoding="utf-8")
    return path


def test_file_extension_is_xml() -> None:
    assert OsisXmlLoader().file_extension == "xml"


def test_reconstructs_simple_verse_with_no_special_markup(tmp_path: Path) -> None:
    verse = (
        '<verse osisID="Gen.1.1">'
        "<w>בְּ/רֵאשִׁ֖ית</w>"
        "<w>בָּרָ֣א</w>"
        "<w>אֱלֹהִ֑ים</w>"
        "<w>אֵ֥ת</w>"
        "<w>הַ/שָּׁמַ֖יִם</w>"
        "<w>וְ/אֵ֥ת</w>"
        "<w>הָ/אָֽרֶץ</w>"
        '<seg type="x-sof-pasuq">׃</seg>'
        "</verse>"
    )
    _write_book(tmp_path, "Gen", 1, verse)

    chapters = OsisXmlLoader().load(tmp_path, "Gen")

    assert chapters[1][1] == (
        "בְּ/רֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַ/שָּׁמַ֖יִם וְ/אֵ֥ת הָ/אָֽרֶץ׃"
    )


def test_maqqef_glues_words_with_no_space_on_either_side(tmp_path: Path) -> None:
    # Real ahit-corpus data: Gen.1.2, containing two maqqef-joined pairs
    # ("עַל־פְּנֵ֣י") and a trailing sof-pasuq.
    verse = (
        '<verse osisID="Gen.1.2">\n'
        '          <w lemma="c/d/776" n="1.1.1" morph="HC/Td/Ncbsa" id="01LN3">וְ/הָ/אָ֗רֶץ</w>\n'
        '          <w lemma="1961" morph="HVqp3fs" id="01Qzf">הָיְתָ֥ה</w>\n'
        '          <w lemma="8414" n="1.1.0" morph="HNcmsa" id="01aPd">תֹ֨הוּ֙</w>\n'
        '          <w lemma="c/922" n="1.1" morph="HC/Ncmsa" id="01eYX">וָ/בֹ֔הוּ</w>\n'
        '          <w lemma="c/2822" n="1.0" morph="HC/Ncmsa" id="01C5U">וְ/חֹ֖שֶׁךְ</w>\n'
        '          <w lemma="5921 a" morph="HR" id="01qNN">עַל</w>'
        '<seg type="x-maqqef">־</seg>'
        '<w lemma="6440" morph="HNcbpc" id="01EVS">פְּנֵ֣י</w>\n'
        '          <w lemma="8415" n="1" morph="HNcbsa" id="01PB6">תְה֑וֹם</w>\n'
        '          <w lemma="c/7307" morph="HC/Ncbsc" id="0137c">וְ/ר֣וּחַ</w>\n'
        '          <w lemma="430" n="0.1" morph="HNcmpa" id="01x9c">אֱלֹהִ֔ים</w>\n'
        '          <w lemma="7363 b" n="0.0" morph="HVprfsa" id="01yNB">מְרַחֶ֖פֶת</w>\n'
        '          <w lemma="5921 a" morph="HR" id="0129t">עַל</w>'
        '<seg type="x-maqqef">־</seg>'
        '<w lemma="6440" morph="HNcbpc" id="01KZG">פְּנֵ֥י</w>\n'
        '          <w lemma="d/4325" n="0" morph="HTd/Ncmpa" id="01TZE">הַ/מָּֽיִם</w>'
        '<seg type="x-sof-pasuq">׃</seg>\n'
        "        </verse>"
    )
    _write_book(tmp_path, "Gen", 1, verse)

    text = OsisXmlLoader().load(tmp_path, "Gen")[1][2]

    assert "עַל־פְּנֵ֣י" in text
    assert "עַל־פְּנֵ֥י" in text
    assert "עַל ־" not in text
    assert " ׃" not in text
    assert text.endswith("הַ/מָּֽיִם׃")


def test_reconstructs_verse_with_maqqef_paseq_note_and_sof_pasuq(tmp_path: Path) -> None:
    # Real ahit-corpus data: Ps.1.1, the richest single example — a maqqef
    # pair, a mid-verse editorial <note>, a paseq, and a trailing sof-pasuq
    # all in one verse.
    verse = (
        '<verse osisID="Ps.1.1">\n'
        '          <w lemma="835" morph="HNcmpa" id="19xeN">אַ֥שְֽׁרֵי</w>'
        '<seg type="x-maqqef">־</seg>'
        '<w lemma="d/376" n="2.1" morph="HTd/Ncmsa" id="19Nvk">הָ/אִ֗ישׁ</w>\n'
        '          <note n="c">We read one or more accents in L differently than BHS. '
        "Often this notation indicates a typographical error in BHS. </note>\n"
        '          <w lemma="834 a" n="2.0.0" morph="HTr" id="19TyA">אֲשֶׁ֤ר</w>\n'
        '          <seg type="x-paseq">׀</seg>\n'
        '          <w lemma="3808" morph="HTn" id="19vuQ">לֹ֥א</w>\n'
        '          <w lemma="1980" n="2.0" morph="HVqp3ms" id="19TSc">הָלַךְ֮</w>\n'
        '          <w lemma="b/6098" morph="HR/Ncfsc" id="19k5P">בַּ/עֲצַ֪ת</w>\n'
        '          <w lemma="7563" n="2" morph="HAampa" id="19nPh">רְשָׁ֫עִ֥ים</w>\n'
        '          <w lemma="c/b/1870" morph="HC/R/Ncbsc" id="19LN3">וּ/בְ/דֶ֣רֶךְ</w>\n'
        '          <w lemma="2400" n="1.0" morph="HAampa" id="19Qzf">חַ֭טָּאִים</w>\n'
        '          <w lemma="3808" morph="HTn" id="19aPd">לֹ֥א</w>\n'
        '          <w lemma="5975" n="1" morph="HVqp3ms" id="19eYX">עָמָ֑ד</w>\n'
        '          <w lemma="c/b/4186" morph="HC/R/Ncmsc" id="19C5U">וּ/בְ/מוֹשַׁ֥ב</w>\n'
        '          <w lemma="3887" n="0.0" morph="HAampa" id="19qNN">לֵ֝צִ֗ים</w>\n'
        '          <w lemma="3808" morph="HTn" id="19EVS">לֹ֣א</w>\n'
        '          <w lemma="3427" n="0" morph="HVqp3ms" id="19PB6">יָשָֽׁב</w>'
        '<seg type="x-sof-pasuq">׃</seg>\n'
        "        </verse>"
    )
    _write_book(tmp_path, "Ps", 1, verse)

    text = OsisXmlLoader().load(tmp_path, "Ps")[1][1]

    assert text == (
        "אַ֥שְֽׁרֵי־הָ/אִ֗ישׁ אֲשֶׁ֤ר׀ לֹ֥א הָלַךְ֮ בַּ/עֲצַ֪ת רְשָׁ֫עִ֥ים וּ/בְ/דֶ֣רֶךְ "
        "חַ֭טָּאִים לֹ֥א עָמָ֑ד וּ/בְ/מוֹשַׁ֥ב לֵ֝צִ֗ים לֹ֣א יָשָֽׁב׃"
    )


def test_ketiv_form_is_used_and_qere_note_is_skipped(tmp_path: Path) -> None:
    # Real ahit-corpus data: Ps.5.9, a ketiv/qere pair — the written form
    # "הושר" is an ordinary <w>, while the read form "הַיְשַׁ֖ר" is nested
    # inside a sibling <note>, which this loader always skips.
    verse = (
        '<verse osisID="Ps.5.9">\n'
        "          <note>KJV:Ps.5.8</note>\n"
        '          <w lemma="3068" n="1.0.0" morph="HNp" id="19vpK">יְהוָ֤ה</w>\n'
        '          <seg type="x-paseq">׀</seg>\n'
        '          <w lemma="5148" morph="HVqv2ms/Sp1cs" id="19G6E">נְחֵ֬/נִי</w>\n'
        '          <w lemma="b/6666" n="1.0" morph="HR/Ncfsc/Sp2ms" id="194vX">בְ/צִדְקָתֶ֗/ךָ</w>\n'
        '          <w lemma="4616" morph="HR" id="19X1R">לְמַ֥עַן</w>\n'
        '          <w lemma="8324" n="1" morph="HNcmpc/Sp1cs" id="19bsu">שׁוֹרְרָ֑/י</w>\n'
        '          <w type="x-ketiv" lemma="3474" morph="HVhv2ms" id="19Ygn">הושר</w>'
        '<note type="variant"><catchWord>הושר</catchWord>'
        '<rdg type="x-qere"><w lemma="3474" morph="HVhv2ms" id="192gM">הַיְשַׁ֖ר</w></rdg>'
        "</note>\n"
        '          <w lemma="l/6440" morph="HR/Ncbpc/Sp1cs" id="19pAw">לְ/פָנַ֣/י</w>\n'
        '          <w lemma="1870" n="0" morph="HNcbsc/Sp2ms" id="19mVV">דַּרְכֶּֽ/ךָ</w>'
        '<seg type="x-sof-pasuq">׃</seg>\n'
        "        </verse>"
    )
    _write_book(tmp_path, "Ps", 5, verse)

    text = OsisXmlLoader().load(tmp_path, "Ps")[5][9]

    assert "הושר" in text
    assert "הַיְשַׁ֖ר" not in text
    assert "KJV:Ps.5.8" not in text


def test_raises_file_not_found_for_missing_book(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        OsisXmlLoader().load(tmp_path, "Gen")


def test_raises_value_error_when_file_has_no_matching_osis_ids(tmp_path: Path) -> None:
    # Simulates VerseMap.xml: it has <verse> elements, but keyed by wlc/kjv
    # attributes rather than osisID, so none of them match book "Gen".
    doc = """<?xml version="1.0" encoding="UTF-8"?>
<verseMap xmlns="http://www.APTBibleTools.com/namespace">
  <book osisID="Gen">
    <verse wlc="Gen.32.1" kjv="Gen.31.55" type="full"/>
  </book>
</verseMap>
"""
    (tmp_path / "Gen.xml").write_text(doc, encoding="utf-8")

    with pytest.raises(ValueError, match="no verses recognized"):
        OsisXmlLoader().load(tmp_path, "Gen")
