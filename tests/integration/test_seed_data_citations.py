"""Integration tests proving every citation in the seed Knowledge Graph
resolves against the real corpus — nothing in seed_data.py is invented.

Requires AHIT_CORPUS_ROOT to point at a real ahit-corpus checkout; skipped
automatically when it isn't, consistent with the rest of this suite, which
never depends on a live network clone to pass in a clean environment. This
module's real verification happened once, manually, against a live clone
during development (every citation in seed_data.py was checked before being
written) — these tests are a regression guard for environments where the
corpus happens to be present (Docker, CI with setup_corpus.sh run), not the
primary proof of correctness.
"""

import pytest

from vahiy_engine.knowledge_graph.seed_data import build_seed_graph
from vahiy_engine.lexicon.ahit.client import EntryNotFoundError, get_lexicon_client
from vahiy_engine.sources.ahit.client import VerseNotFoundError, get_ahit_client
from vahiy_engine.sources.osis import parse_osis
from vahiy_engine.sources.quran.client import AyahNotFoundError, get_quran_client
from vahiy_engine.sources.quran.models import QuranReference

# OSIS citations in seed_data.py that live in the Greek NT (SBLGNT) rather
# than the Hebrew OT (WLC).
_SBLGNT_CITATIONS = {"Heb.4.9", "Rom.10.13"}


def _requires_real_corpus() -> None:
    corpus = get_ahit_client()
    try:
        corpus.get_verse(parse_osis("Exod.3.14"), translation="WLC")
    except Exception:
        pytest.skip("AHIT_CORPUS_ROOT not pointed at a real ahit-corpus checkout")


def test_every_osis_citation_resolves_against_the_real_corpus() -> None:
    _requires_real_corpus()
    corpus = get_ahit_client()
    graph = build_seed_graph()

    for node_id in ("yhwh", "sabbath", "abraham"):
        for edge in graph.edges_from(node_id):
            if edge.citation_type != "osis":
                continue
            translation = "SBLGNT" if edge.citation in _SBLGNT_CITATIONS else "WLC"
            try:
                verse = corpus.get_verse(parse_osis(edge.citation), translation=translation)
            except VerseNotFoundError:
                pytest.fail(
                    f"{edge.citation} ({translation}) does not resolve — seed data is stale"
                )
            assert verse.text.strip()


def test_every_quran_citation_resolves_against_the_real_corpus() -> None:
    _requires_real_corpus()
    quran = get_quran_client()
    graph = build_seed_graph()

    quran_edges = [e for e in graph.edges_from("abraham") if e.citation_type == "quran"]
    if not quran_edges:
        pytest.fail("expected at least one Quran citation on the Abraham node")

    for edge in quran_edges:
        _, surah, ayah = edge.citation.split(".")
        try:
            ayah_obj = quran.get_ayah(QuranReference(surah=int(surah), ayah=int(ayah)))
        except AyahNotFoundError:
            pytest.fail(f"{edge.citation} does not resolve — seed data is stale")
        assert ayah_obj.text.strip()


def test_every_strongs_citation_resolves_against_the_real_lexicon() -> None:
    _requires_real_corpus()
    lexicon = get_lexicon_client()
    graph = build_seed_graph()

    for node_id in ("yhwh", "hayah", "kyrios"):
        for edge in graph.edges_from(node_id):
            if edge.citation_type != "strongs":
                continue
            number = edge.citation.removeprefix("Strong:")
            try:
                entry = lexicon.get_entry(number)
            except EntryNotFoundError:
                pytest.fail(f"{edge.citation} does not resolve — seed data is stale")
            assert entry.lemma
