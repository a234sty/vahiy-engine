"""Turns one question into several explicit, source-targeted sub-queries.

A question like "Mesih ne demek?" is not one retrieval. It is at least four:
what the term means lexically, where it occurs in the biblical text, where it
occurs in the Qur'an, and what the original-language wording is. Issuing a
single keyword search for the whole sentence answers none of them well --
it searches one corpus, in one language, for a string that includes the
question words themselves.

This module produces the decomposition as data: each sub-query names the
facet it answers, the concrete corpus and translation it targets, and the
reason it was planned. The plan is inspectable before it is executed, and it
is recorded alongside the answer, so "which sub-questions did the engine
actually ask" is a question with a checkable answer rather than a guess.

Source selection is driven by the question's language and by what the
configured corpus actually contains, not by assumption. A translation with
no meaningful coverage is not planned against, and the plan says so.
"""

from dataclasses import dataclass
from enum import StrEnum

from vahiy_engine.reasoning.intent import Depth, IntentType, QuestionAnalysis
from vahiy_engine.search.index import STOPWORDS, get_index, normalize, tokenize
from vahiy_engine.search.reference_parser import find_references
from vahiy_engine.sources.client import CorpusClient
from vahiy_engine.sources.quran.client import QuranClient

# A translation with fewer verses than this is a sample, not a corpus. The
# repository ships a 17-verse KJV sample for offline tests; planning searches
# against it would return nothing while looking like retrieval ran.
_MINIMUM_USABLE_VERSES = 100

# Latin-script questions cannot match Hebrew or Greek text, so an
# original-language sub-query is only planned when the question actually
# carries non-Latin characters. Planning one anyway would burn an index build
# to guarantee zero hits.
_ORIGINAL_SCRIPT_RANGES = (
    (0x0370, 0x03FF),  # Greek and Coptic
    (0x0590, 0x05FF),  # Hebrew
    (0x0600, 0x06FF),  # Arabic
    (0x1F00, 0x1FFF),  # Greek Extended
)


class Facet(StrEnum):
    """The sub-question a retrieval answers."""

    SCRIPTURE_USAGE = "scripture_usage"
    QURAN_USAGE = "quran_usage"
    ORIGINAL_LANGUAGE = "original_language"
    CITED_PASSAGE = "cited_passage"


class SourceKind(StrEnum):
    BIBLE = "bible"
    QURAN = "quran"


@dataclass(frozen=True)
class SubQuery:
    id: str
    facet: Facet
    query: str
    source: SourceKind
    edition: str | None
    limit: int
    rationale: str


@dataclass(frozen=True)
class RetrievalPlan:
    question: str
    search_terms: tuple[str, ...]
    subqueries: tuple[SubQuery, ...]
    skipped: tuple[str, ...]
    """Sub-queries deliberately not planned, each with its reason. Recorded
    because "the Qur'an was not searched" and "the Qur'an had nothing" are
    different facts and must not look alike."""


# Question words and framing vocabulary that name the *task* rather than the
# subject. Searching a corpus for them matches nothing useful and dilutes the
# terms that do matter.
_FRAMING_TERMS = frozenset(
    {
        "mean",
        "means",
        "meaning",
        "define",
        "definition",
        "explain",
        "compare",
        "comparison",
        "contrast",
        "difference",
        "differences",
        "differ",
        "differs",
        "versus",
        "vs",
        "concept",
        "term",
        "word",
        "verse",
        "passage",
        "chapter",
        "according",
        "teach",
        "teaches",
        "teaching",
        "kavram",
        "kavrami",
        "anlam",
        "anlami",
        "anlamina",
        "anlama",
        "kelime",
        "kelimesi",
        "fark",
        "farki",
        "farklari",
        "farkli",
        "karsilastir",
        "karsilastirma",
        "aciklama",
        "acikla",
        "ayet",
        "ayeti",
        "pasaj",
        "bolum",
        "gore",
        # "ne demek" is the commonest Turkish way to ask what a term
        # means. Left out of this list it becomes a search term, and
        # "demek" appears in ordinary narration ("... demek mi") often
        # enough to outrank the actual subject: asking "Mesih ne demek?"
        # returned Luke 5:23 and Mark 2:9, neither about the Messiah.
        "demek",
        "demektir",
        "denir",
        "denmek",
        "denilen",
        "diyor",
        "der",
        "soyler",
        "gelir",
        "hakkinda",
        "ilgili",
        "nasil",
        "hangi",
    }
)

# Corpus names identify *where* to look, not *what* to look for.
_CORPUS_NAME_TERMS = frozenset(
    {
        "bible",
        "biblical",
        "quran",
        "quranic",
        "torah",
        "tanakh",
        "gospel",
        "testament",
        "scripture",
        "kuran",
        "kur",
        "incil",
        "tevrat",
        "zebur",
        "ahit",
        "ahitte",
        "ahitteki",
        "kitap",
        "kitapta",
        "yeni",
        "eski",
        "kutsal",
        "sure",
        "surah",
    }
)


def extract_search_terms(question: str) -> tuple[str, ...]:
    """The content terms of `question`: what to look for, minus how it was asked.

    Drops stopwords, task-framing vocabulary ("ne demek", "compare") and
    corpus names ("Kur'an", "Yeni Ahit"). What remains is the subject the
    corpora should be searched for. Order is preserved and duplicates are
    removed, so the result is deterministic.
    """
    seen: dict[str, None] = {}
    for token in tokenize(normalize(question)):
        if token in STOPWORDS or token in _FRAMING_TERMS or token in _CORPUS_NAME_TERMS:
            continue
        if len(token) < 2 or token.isdigit():
            continue
        seen.setdefault(token, None)
    return tuple(seen)


def _has_original_script(text: str) -> bool:
    return any(any(low <= ord(ch) <= high for low, high in _ORIGINAL_SCRIPT_RANGES) for ch in text)


def usable_translations(corpus: CorpusClient, candidates: tuple[str, ...]) -> tuple[str, ...]:
    """Those of `candidates` that actually carry a corpus worth searching.

    Checked against the real index rather than assumed from configuration:
    a translation can be registered and still be a 17-verse sample, and
    planning a search against it produces the appearance of retrieval with
    none of the substance.
    """
    usable: list[str] = []
    for translation in candidates:
        try:
            if len(get_index(corpus, translation)) >= _MINIMUM_USABLE_VERSES:
                usable.append(translation)
        except (LookupError, FileNotFoundError, ValueError):
            continue
    return tuple(usable)


def _readable_bible_translations(corpus: CorpusClient, language: str) -> tuple[str, ...]:
    preferred = ("YTC", "KJV") if language == "tr" else ("KJV", "YTC")
    return usable_translations(corpus, preferred)


def _quran_editions(quran: QuranClient, language: str) -> tuple[str, ...]:
    available = set(quran.available_editions())
    preferred = ("tr", "en") if language == "tr" else ("en", "tr")
    return tuple(edition for edition in preferred if edition in available)


def _limit_for(depth: Depth) -> int:
    """How many candidates a single sub-query may contribute.

    Broad questions earn a passage-rich answer and narrow ones must not be
    flooded, so the budget is set by the analyzed depth rather than fixed.
    """
    return {Depth.NARROW: 3, Depth.STANDARD: 6, Depth.BROAD: 10}[depth]


def plan_retrieval(
    question: str,
    analysis: QuestionAnalysis,
    corpus: CorpusClient,
    quran: QuranClient | None = None,
) -> RetrievalPlan:
    """Decompose `question` into source-targeted sub-queries."""
    terms = extract_search_terms(question)
    query = " ".join(terms)
    limit = _limit_for(analysis.depth)
    subqueries: list[SubQuery] = []
    skipped: list[str] = []

    references = find_references(question)
    for index, (book, chapter, verse) in enumerate(references, start=1):
        subqueries.append(
            SubQuery(
                id=f"cited-{index}",
                facet=Facet.CITED_PASSAGE,
                query=f"{book}.{chapter}.{verse}",
                source=SourceKind.BIBLE,
                edition=None,
                limit=1,
                rationale="The question cites this passage directly.",
            )
        )

    if not query:
        skipped.append(
            "No content terms remained after removing question framing, so no "
            "keyword sub-query was planned."
        )
        return RetrievalPlan(
            question=question,
            search_terms=terms,
            subqueries=tuple(subqueries),
            skipped=tuple(skipped),
        )

    bible_translations = _readable_bible_translations(corpus, analysis.language)
    if bible_translations:
        primary = bible_translations[0]
        subqueries.append(
            SubQuery(
                id="bible-usage",
                facet=Facet.SCRIPTURE_USAGE,
                query=query,
                source=SourceKind.BIBLE,
                edition=primary,
                limit=limit,
                rationale=(
                    f"Where the biblical text uses these terms, read in {primary} "
                    f"(selected for question language '{analysis.language}')."
                ),
            )
        )
    else:
        skipped.append(
            "No Bible translation in this deployment carries enough text to search; "
            "the biblical corpus was not keyword-searched."
        )

    wants_quran = analysis.intent is IntentType.COMPARISON or analysis.depth is not Depth.NARROW
    if quran is None:
        skipped.append("No Qur'an client is wired up, so the Qur'an was not searched.")
    elif not wants_quran:
        skipped.append(
            "The question is narrow and not comparative, so the Qur'an was not "
            "searched; this is a scope decision, not a finding about the Qur'an."
        )
    else:
        editions = _quran_editions(quran, analysis.language)
        if not editions:
            skipped.append(
                "No Qur'an edition is configured in this deployment, so the Qur'an "
                "was not searched."
            )
        else:
            subqueries.append(
                SubQuery(
                    id="quran-usage",
                    facet=Facet.QURAN_USAGE,
                    query=query,
                    source=SourceKind.QURAN,
                    edition=editions[0],
                    limit=limit,
                    rationale=(
                        f"Where the Qur'an uses these terms, read in the "
                        f"'{editions[0]}' edition."
                    ),
                )
            )

    if _has_original_script(question):
        for edition in usable_translations(corpus, ("WLC", "SBLGNT")):
            subqueries.append(
                SubQuery(
                    id=f"original-{edition.lower()}",
                    facet=Facet.ORIGINAL_LANGUAGE,
                    query=query,
                    source=SourceKind.BIBLE,
                    edition=edition,
                    limit=limit,
                    rationale=(
                        f"The question contains non-Latin script, so {edition} was "
                        "searched for the original wording."
                    ),
                )
            )
    else:
        skipped.append(
            "The question is written in Latin script, which cannot match Hebrew or "
            "Greek text, so the original-language corpora were not keyword-searched. "
            "Original wording still reaches the answer through resolved citations."
        )

    return RetrievalPlan(
        question=question,
        search_terms=terms,
        subqueries=tuple(subqueries),
        skipped=tuple(skipped),
    )
