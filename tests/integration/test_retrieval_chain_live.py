"""End-to-end retrieval-chain tests against a real ahit-corpus checkout.

These assert on retrieval *quality*, not merely that the chain runs: that a
question about the Messiah returns passages containing the word, that a
comparative question returns both corpora, and that the previously dead
paths (31k-verse Turkish Bible, 6k-ayah Qur'an) are actually reached.

Skips cleanly without AHIT_CORPUS_ROOT, like every other live-corpus test
here.
"""

import pytest

from vahiy_engine.knowledge_graph.seed_data import get_knowledge_graph
from vahiy_engine.lexicon.ahit.client import get_lexicon_client
from vahiy_engine.pipeline.chat_pipeline import ChatResult, run_chat_pipeline
from vahiy_engine.rag.planner import Facet
from vahiy_engine.sources.ahit.client import get_ahit_client
from vahiy_engine.sources.osis import parse_osis
from vahiy_engine.sources.quran.client import get_quran_client


class CapturingProvider:
    def __init__(self) -> None:
        self.context = ""

    def generate_answer(self, system_prompt: str, question: str, context: str) -> str:
        self.context = context
        return "answer"


def _requires_real_corpus() -> None:
    try:
        get_ahit_client().get_verse(parse_osis("Exod.3.14"), translation="WLC")
    except Exception:
        pytest.skip("AHIT_CORPUS_ROOT not pointed at a real ahit-corpus checkout")


def _ask(question: str) -> ChatResult:
    return run_chat_pipeline(
        get_ahit_client(),
        CapturingProvider(),
        question,
        lexicon=get_lexicon_client(),
        quran=get_quran_client(),
        graph=get_knowledge_graph(),
    )


def test_the_full_turkish_bible_is_searched_not_the_bundled_sample() -> None:
    # The defect this pins: build_index() iterated the corpus default (a
    # 17-verse KJV sample), so every keyword question retrieved from 17
    # verses. "Pavlus" returned nothing at all.
    _requires_real_corpus()

    result = _ask("Pavlus ne diyor?")

    assert result.retrieved is not None
    citations = [item.citation for item in result.retrieved.items]
    assert citations, "no passage retrieved for a question about Paul"
    assert any(
        "pavlus" in item.text.casefold() for item in result.retrieved.items
    ), f"retrieved passages do not mention Paul: {citations}"


def test_a_messiah_question_retrieves_passages_that_actually_contain_the_term() -> None:
    _requires_real_corpus()

    result = _ask("Mesih ne demek?")

    assert result.retrieved is not None
    texts = [item.text.casefold() for item in result.retrieved.items]
    assert texts
    matching = [t for t in texts if "mesih" in t]
    # Not every slot need match -- a reserved facet slot may hold a weaker
    # hit -- but a majority that do not would mean the term extraction is
    # still searching for the wrong thing.
    assert len(matching) > len(texts) / 2, f"most retrieved passages lack the term: {texts[:3]}"


def test_a_comparative_question_returns_evidence_from_both_corpora() -> None:
    _requires_real_corpus()

    result = _ask("Mesih kavramı Kuran ve Yeni Ahitte nasıl farklı?")

    assert result.retrieved is not None
    kinds = {item.citation_type for item in result.retrieved.items}
    assert kinds == {"osis", "quran"}, f"one side of the comparison is missing: {kinds}"


def test_the_quran_corpus_is_reachable_by_topic_not_only_by_citation() -> None:
    _requires_real_corpus()

    result = _ask("Mesih kavramı Kuran ve Yeni Ahitte nasıl farklı?")

    assert result.retrieved is not None
    quran_items = [i for i in result.retrieved.items if i.citation_type == "quran"]
    assert quran_items
    # The seed graph holds only three Qur'anic citations, all about Abraham.
    # Anything else proves the corpus was searched, not looked up.
    seeded = {"Quran.14.35", "Quran.2.124", "Quran.21.51"}
    assert {i.citation for i in quran_items} - seeded


def test_the_plan_records_which_subquestions_were_asked() -> None:
    _requires_real_corpus()

    result = _ask("Mesih kavramı Kuran ve Yeni Ahitte nasıl farklı?")

    assert result.plan is not None
    assert result.plan.search_terms == ("mesih",)
    facets = {sq.facet for sq in result.plan.subqueries}
    assert Facet.SCRIPTURE_USAGE in facets
    assert Facet.QURAN_USAGE in facets


def test_retrieved_evidence_reaches_the_model_context_labeled_by_corpus() -> None:
    _requires_real_corpus()

    provider = CapturingProvider()
    run_chat_pipeline(
        get_ahit_client(),
        provider,
        "Mesih kavramı Kuran ve Yeni Ahitte nasıl farklı?",
        lexicon=get_lexicon_client(),
        quran=get_quran_client(),
        graph=get_knowledge_graph(),
    )

    assert "RETRIEVED EVIDENCE (found by the planned sub-questions)" in provider.context
    assert "(Qur'an)" in provider.context
    assert "(Bible)" in provider.context


def test_the_same_question_retrieves_the_same_evidence_twice() -> None:
    # Reproducibility applies to the retrieval chain too, not only the
    # knowledge-graph trace.
    _requires_real_corpus()

    first = _ask("Tanrı nedir?")
    second = _ask("Tanrı nedir?")

    assert first.retrieved is not None and second.retrieved is not None
    assert [i.citation for i in first.retrieved.items] == [
        i.citation for i in second.retrieved.items
    ]


def test_a_narrow_cited_question_stays_local() -> None:
    _requires_real_corpus()

    result = _ask("What does Genesis 1:1 mean?")

    assert result.retrieved is not None
    assert len(result.retrieved.items) <= 4
    assert any(item.citation == "Gen.1.1" for item in result.retrieved.items)
