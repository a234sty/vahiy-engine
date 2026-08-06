"""Unit tests for GreekStrongsXmlLoader.

Fragments marked "real ahit-corpus data" were captured verbatim from the
actual lexicon/greek/strongsgreek.xml file, and expected field values were
computed by running the loader's own extraction algorithm (itertext +
whitespace-collapse) against them directly, not hand-typed.
"""

from pathlib import Path

import pytest

from vahiy_engine.lexicon.loaders.greek_strongs_xml_loader import GreekStrongsXmlLoader

# Real ahit-corpus data: G3056 (λόγος / "logos"), ENGINE_SPEC.md's own
# worked example of a "Strong:G3056" source.
G3056 = (
    '<entry strongs="03056">\n'
    ' <strongs>3056</strongs>   <greek BETA="LO/GOS" unicode="λόγος" translit="lógos"/>   '
    '<pronunciation strongs="log\'-os"/>\n\n'
    ' <strongs_derivation>from <strongsref language="GREEK" strongs="3004"/>;</strongs_derivation>'
    "<strongs_def> something said (including the thought); by implication, a\n"
    " topic (subject of discourse), also reasoning (the mental faculty) or\n"
    " motive; by extension, a computation; specially, (with the article in\n"
    " John) the Divine Expression (i.e. Christ)</strongs_def>"
    "<kjv_def>:--account, cause,\n"
    " communication, X concerning, doctrine, fame, X have to do, intent,\n"
    " matter, mouth, preaching, question, reason, + reckon, remove,\n"
    " say(-ing), shew, X speaker, speech, talk, thing, + none of these\n"
    " things move me, tidings, treatise, utterance, word, work.</kjv_def>\n"
    '<see language="GREEK" strongs="3004"/>\n'
    "</entry>"
)

# Real ahit-corpus data: G1, with two trailing <see> cross-references and
# loose prose after </kjv_def> (both should contribute nothing beyond
# what strongs_def/kjv_def already captured).
G1 = (
    '<entry strongs="00001">\n\n'
    ' <strongs>1</strongs>   <greek BETA="*A" unicode="Α" translit="A"/>   '
    '<pronunciation strongs="al\'-fah"/>\n\n'
    " <strongs_derivation>of Hebrew origin;</strongs_derivation>"
    "<strongs_def> the first letter of the alphabet; figuratively, only\n"
    " (from its use as a numeral) the first: </strongs_def>"
    "<kjv_def>--Alpha.</kjv_def> Often used (usually\n"
    ' <greek BETA="A)/N" unicode="ἄν" translit="án"/>, before a vowel) also in composition '
    '(as a contraction from <strongsref language="GREEK" strongs="427"/>) in\n'
    " the sense of privation; so, in many words, beginning with this letter;\n"
    " occasionally in the sense of union (as a contraction of "
    '<strongsref language="GREEK" strongs="260"/>).\n'
    '<see language="GREEK" strongs="427"/>\n'
    '<see language="GREEK" strongs="260"/>\n'
    "</entry>"
)

# Real ahit-corpus data: G23, whose <strongs_def> contains a nested
# <strongsref> (an empty cross-reference element with no display text of
# its own).
G23 = (
    '<entry strongs="00023">\n'
    ' <strongs>23</strongs>   <greek BETA="A)GANAKTE/W" unicode="ἀγανακτέω" translit="aganaktéō"/>'
    '   <pronunciation strongs="ag-an-ak-teh\'-o"/>\n\n'
    ' <strongs_derivation>from <greek BETA="A)/GAN" unicode="ἄγαν" translit="ágan"/> (much) and '
    '<greek BETA="A)/XQOS" unicode="ἄχθος" translit="áchthos"/> '
    "(grief;</strongs_derivation>"
    '<strongs_def> akin to the base of <strongsref language="GREEK" strongs="43"/>); to be\n'
    " greatly afflicted, i.e. (figuratively) indignant</strongs_def>"
    "<kjv_def>:--be much (sore)\n"
    " displeased, have (be moved with, with) indignation.</kjv_def>\n"
    '<see language="GREEK" strongs="43"/>\n'
    "</entry>"
)


def _write_dictionary(directory: Path, *entries: str) -> Path:
    doc = f"<strongsdictionary><entries>{''.join(entries)}</entries></strongsdictionary>"
    path = directory / "strongsgreek.xml"
    path.write_text(doc, encoding="utf-8")
    return path


def test_language_is_greek() -> None:
    assert GreekStrongsXmlLoader().language == "greek"


def test_parses_g3056_matching_the_spec_example(tmp_path: Path) -> None:
    path = _write_dictionary(tmp_path, G3056)

    entries = GreekStrongsXmlLoader().load(path)

    logos = entries["G3056"]
    assert logos.strongs_number == "G3056"
    assert logos.language == "greek"
    assert logos.lemma == "λόγος"
    assert logos.transliteration == "lógos"
    assert logos.pronunciation == "log'-os"
    assert logos.definition == (
        "something said (including the thought); by implication, a topic "
        "(subject of discourse), also reasoning (the mental faculty) or motive; "
        "by extension, a computation; specially, (with the article in John) the "
        "Divine Expression (i.e. Christ)"
    )
    assert logos.kjv_translation == (
        ":--account, cause, communication, X concerning, doctrine, fame, X have "
        "to do, intent, matter, mouth, preaching, question, reason, + reckon, "
        "remove, say(-ing), shew, X speaker, speech, talk, thing, + none of "
        "these things move me, tidings, treatise, utterance, word, work."
    )


def test_strongs_number_drops_leading_zeros_from_the_attribute(tmp_path: Path) -> None:
    path = _write_dictionary(tmp_path, G1)

    entries = GreekStrongsXmlLoader().load(path)

    assert "G1" in entries
    assert "G00001" not in entries


def test_ignores_trailing_see_cross_references_and_loose_prose(tmp_path: Path) -> None:
    path = _write_dictionary(tmp_path, G1)

    entry = GreekStrongsXmlLoader().load(path)["G1"]

    assert entry.lemma == "Α"
    assert entry.definition == (
        "the first letter of the alphabet; figuratively, only (from its use as "
        "a numeral) the first:"
    )
    assert entry.kjv_translation == "--Alpha."
    # The loose prose after </kjv_def> ("Often used...") and the <see>
    # cross-references are not part of any field.
    assert "Often used" not in entry.definition
    assert "Often used" not in entry.kjv_translation


def test_nested_strongsref_inside_strongs_def_contributes_no_text(tmp_path: Path) -> None:
    path = _write_dictionary(tmp_path, G23)

    entry = GreekStrongsXmlLoader().load(path)["G23"]

    assert entry.lemma == "ἀγανακτέω"
    assert entry.definition == (
        "akin to the base of ); to be greatly afflicted, i.e. (figuratively) indignant"
    )


def test_parses_multiple_entries_from_one_file(tmp_path: Path) -> None:
    path = _write_dictionary(tmp_path, G1, G23, G3056)

    entries = GreekStrongsXmlLoader().load(path)

    assert set(entries) == {"G1", "G23", "G3056"}


def test_raises_value_error_when_entry_has_a_headword_but_no_definition_source(
    tmp_path: Path,
) -> None:
    path = _write_dictionary(
        tmp_path, '<entry strongs="99999"><greek unicode="x" translit="x"/></entry>'
    )

    with pytest.raises(ValueError, match="99999"):
        GreekStrongsXmlLoader().load(path)


def test_not_used_entries_are_skipped_without_error(tmp_path: Path) -> None:
    # Real ahit-corpus data shape: a handful of Strong's numbers were
    # reserved but never assigned a word. The entry's whole content is the
    # plain text "Not Used" — no <greek>, <strongs_def>, or <kjv_def> at
    # all.
    not_used = '<entry strongs="02717">\n <strongs>2717</strongs>  Not Used\n</entry>'
    path = _write_dictionary(tmp_path, G3056, not_used)

    entries = GreekStrongsXmlLoader().load(path)

    assert set(entries) == {"G3056"}


def test_falls_back_to_kjv_def_when_strongs_def_is_absent(tmp_path: Path) -> None:
    # Real ahit-corpus data: G302 (ἄν) has a real headword but no
    # <strongs_def> at all — only a <strongs_derivation> and <kjv_def>.
    g302 = (
        '<entry strongs="00302">\n'
        ' <strongs>302</strongs>   <greek BETA="A)/N" unicode="ἄν" translit="án"/>   '
        '<pronunciation strongs="an"/>\n\n'
        " <strongs_derivation>a primary particle, denoting a supposition, wish, possibility or\n"
        " uncertainty</strongs_derivation>"
        "<kjv_def>:--(what-, where-, wither-, who-)soever.</kjv_def> Usually\n"
        " unexpressed except by the subjunctive or potential mood. Also\n"
        ' contracted for <strongsref language="GREEK" strongs="1437"/>.\n'
        '<see language="GREEK" strongs="1437"/>\n'
        "</entry>"
    )
    path = _write_dictionary(tmp_path, g302)

    entry = GreekStrongsXmlLoader().load(path)["G302"]

    assert entry.lemma == "ἄν"
    assert entry.definition == ":--(what-, where-, wither-, who-)soever."
    assert entry.kjv_translation == ":--(what-, where-, wither-, who-)soever."
