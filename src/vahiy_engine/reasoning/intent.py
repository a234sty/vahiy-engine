"""Question analysis: what is the user actually asking, in what language, and
how much work does answering it honestly require.

This is the "what is the user really trying to learn" layer, in code rather
than in prompt text alone. It runs before retrieval and shapes three
downstream decisions the engine otherwise has to guess at:

- `intent` selects the answer shape (a verse question and a comparative
  doctrinal question must not receive the same template),
- `depth` selects how much evidence to gather (a broad concept question
  earns a passage-rich answer; "what does John 3:16 say" does not),
- `complexity` selects how much compute to spend, so an expensive reasoning
  model is not billed for "Yuhanna 3:16 ne diyor?".

Deliberately rule-based and deterministic rather than a model call. Three
reasons, in order of weight: an LLM classifier would make every answer
depend on a second non-reproducible inference, breaking the reproducibility
guarantee the whole trace design exists to provide; it would add latency and
cost to the very path whose job is to *reduce* cost; and a rule set is
auditable -- you can read why a question was classified the way it was,
which a hidden classifier does not permit.

The rules are bilingual (Turkish and English) because those are the two
languages the corpus and the user base actually use. Markers are matched
against `normalize()`d text, so Turkish casing (İ/ı) folds correctly.
"""

from dataclasses import dataclass
from enum import StrEnum

from vahiy_engine.search.index import normalize, tokenize
from vahiy_engine.search.reference_parser import find_chapter_references, find_references


class IntentType(StrEnum):
    """What kind of answer the question calls for.

    Values match the `answer_type` vocabulary in the engine's output
    contract, so a classified intent can be reported to the caller without
    translation between two parallel enumerations that could drift apart.
    """

    VERSE_EXPLANATION = "verse_explanation"
    WORD_MEANING = "word_meaning"
    DOCTRINAL_EXPLANATION = "doctrinal_explanation"
    COMPARISON = "comparison"
    HISTORICAL_EXPLANATION = "historical_explanation"
    TRANSLATION_HELP = "translation_help"
    CROSS_REFERENCE = "cross_reference"
    SUMMARY = "summary"
    CLARIFICATION = "clarification"
    UNKNOWN = "unknown"


class Depth(StrEnum):
    """How much evidence an honest answer needs."""

    NARROW = "narrow"
    STANDARD = "standard"
    BROAD = "broad"


class Complexity(StrEnum):
    """How much reasoning effort the question warrants."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    DEEP = "deep"


@dataclass(frozen=True)
class QuestionAnalysis:
    intent: IntentType
    depth: Depth
    complexity: Complexity
    language: str
    signals: tuple[str, ...]
    """Which rules fired, in order. Present so a classification can be
    explained and disputed rather than merely asserted."""


# Turkish letters outside the Latin I/i case pair. normalize() preserves
# these (it only folds the I/ı/İ/i ambiguity), so they survive as a reliable
# language signal.
_TURKISH_LETTERS = frozenset("çğöşü")

# High-signal Turkish function words, already in post-normalize() spelling.
_TURKISH_MARKERS = frozenset(
    {
        "nedir",
        "kimdir",
        "nasil",
        "neden",
        "hangi",
        "kelimesi",
        "anlami",
        "anlamina",
        "arasindaki",
        "arasinda",
        "midir",
        "gore",
        "ile",
        "icin",
        "ve",
        "bir",
        "bu",
        "ne",
        "kim",
        "farki",
        "fark",
        "gelir",
        "der",
        "diyor",
        "soyler",
        "ayet",
        "ayeti",
    }
)

_COMPARISON_MARKERS = frozenset(
    {
        "compare",
        "compared",
        "comparison",
        "versus",
        "vs",
        "difference",
        "differences",
        "differ",
        "differs",
        "contrast",
        "both",
        "karsilastir",
        "karsilastirma",
        "fark",
        "farki",
        "farklari",
        "arasindaki",
        "hem",
    }
)

_WORD_MEANING_MARKERS = frozenset(
    {
        "mean",
        "means",
        "meaning",
        "definition",
        "define",
        "etymology",
        "root",
        "lemma",
        "word",
        "term",
        "translated",
        "kelime",
        "kelimesi",
        "anlami",
        "anlamina",
        "anlam",
        "koku",
        "kokeni",
        "terim",
    }
)

_HISTORICAL_MARKERS = frozenset(
    {
        "history",
        "historical",
        "historically",
        "century",
        "dated",
        "dating",
        "archaeology",
        "archaeological",
        "manuscript",
        "manuscripts",
        "tarih",
        "tarihsel",
        "tarihi",
        "yuzyil",
        "donem",
        "doneminde",
        "elyazmasi",
    }
)

_TRANSLATION_MARKERS = frozenset(
    {
        "translate",
        "translated",
        "translation",
        "rendering",
        "renders",
        "ceviri",
        "cevirisi",
        "cevrilir",
        "meal",
        "tercume",
    }
)

_SUMMARY_MARKERS = frozenset({"summary", "summarize", "overview", "ozet", "ozetle", "genel"})

# Concepts that are genuinely broad: a one-line answer to any of these would
# be a worse answer, not a shorter one. Taken from the engine's own list of
# major theological concepts.
_BROAD_CONCEPTS = frozenset(
    {
        "god",
        "allah",
        "tanri",
        "yahve",
        "yhwh",
        "messiah",
        "mesih",
        "christ",
        "salvation",
        "kurtulus",
        "faith",
        "iman",
        "inanc",
        "covenant",
        "ahit",
        "antlasma",
        "law",
        "seriat",
        "kanun",
        "worship",
        "ibadet",
        "sabbath",
        "sabat",
        "spirit",
        "ruh",
        "kingdom",
        "kralligi",
        "revelation",
        "vahiy",
        "prophecy",
        "kehanet",
        "peygamberlik",
        "holiness",
        "kutsallik",
        "righteousness",
        "dogruluk",
        "forgiveness",
        "bagislanma",
        "trinity",
        "teslis",
        "sin",
        "gunah",
        "grace",
        "lutuf",
        "resurrection",
        "dirilis",
        "prayer",
        "dua",
        "namaz",
    }
)

# Corpus names: two or more distinct traditions named in one question is a
# strong comparative signal even without an explicit "compare".
_TRADITION_TERMS: dict[str, frozenset[str]] = {
    "bible": frozenset(
        {"bible", "biblical", "gospel", "torah", "tanakh", "incil", "tevrat", "kitap", "zebur"}
    ),
    "quran": frozenset({"quran", "quranic", "kuran", "kur", "surah", "sure", "ayah"}),
    "judaism": frozenset({"jewish", "judaism", "rabbinic", "yahudi", "yahudilik", "talmud"}),
    "christianity": frozenset(
        {"christian", "christianity", "church", "hristiyan", "hristiyanlik", "kilise"}
    ),
    "islam": frozenset({"islam", "islamic", "muslim", "islami", "musluman", "hadith", "hadis"}),
}

_PERSON_MARKERS = frozenset({"who", "whom", "kim", "kimdir", "kimdi"})

_DEEP_CONNECTIVES = frozenset(
    {
        "and",
        "but",
        "however",
        "whereas",
        "therefore",
        "because",
        "if",
        "whether",
        "ve",
        "ama",
        "fakat",
        "ancak",
        "cunku",
        "eger",
        "ise",
        "ayrica",
    }
)


_MIN_STEM_FOR_PREFIX_MATCH = 4
_MAX_SUFFIX_LENGTH = 5


def _has_marker(tokens: set[str], markers: frozenset[str]) -> bool:
    """Whether any token matches a marker exactly or as a suffixed form.

    Turkish is agglutinative, so exact set membership silently misses the
    forms users actually write: "ahit" is listed but the question says
    "Ahit'te", "fark" is listed but the question says "farklı", "Kuran" is
    listed but the question says "Kuran'daki". Both real misses, found by
    running the classifier on real questions rather than on the vocabulary
    it was written against.

    A token therefore also matches when it begins with a marker, provided
    the marker is long enough to be distinctive and the remainder is short
    enough to be an inflectional ending. Short markers keep exact-match-only
    semantics, so English "sin" never matches "single".
    """
    if tokens & markers:
        return True
    return any(
        token.startswith(marker) and 0 < len(token) - len(marker) <= _MAX_SUFFIX_LENGTH
        for marker in markers
        if len(marker) >= _MIN_STEM_FOR_PREFIX_MATCH
        for token in tokens
    )


def _matching_markers(tokens: set[str], markers: frozenset[str]) -> frozenset[str]:
    """The markers that matched, under the same rule as `_has_marker`."""
    return frozenset(
        marker
        for marker in markers
        if marker in tokens
        or (
            len(marker) >= _MIN_STEM_FOR_PREFIX_MATCH
            and any(
                token.startswith(marker) and 0 < len(token) - len(marker) <= _MAX_SUFFIX_LENGTH
                for token in tokens
            )
        )
    )


def analyze_question(question: str) -> QuestionAnalysis:
    """Classify `question` into intent, depth, complexity and language.

    Pure and deterministic: the same string always yields the same analysis,
    with no I/O and no model call.
    """
    normalized = normalize(question)
    tokens = tokenize(normalized)
    token_set = set(tokens)
    signals: list[str] = []

    language = _detect_language(question, token_set)
    signals.append(f"language:{language}")

    has_citation = bool(find_references(question)) or bool(find_chapter_references(question))
    traditions = _named_traditions(token_set)
    broad_concepts = _matching_markers(token_set, _BROAD_CONCEPTS)

    intent = _classify_intent(token_set, has_citation, traditions, broad_concepts, signals)
    depth = _classify_depth(intent, tokens, broad_concepts, has_citation, signals)
    complexity = _classify_complexity(intent, depth, tokens, token_set, traditions, signals)

    return QuestionAnalysis(
        intent=intent,
        depth=depth,
        complexity=complexity,
        language=language,
        signals=tuple(signals),
    )


def _detect_language(question: str, token_set: set[str]) -> str:
    """Turkish or English, defaulting to English.

    Two independent signals, either sufficient: a Turkish-specific letter
    (ç/ğ/ö/ş/ü, which normalize() preserves) or a Turkish function word.
    Deliberately two-way rather than general language identification -- the
    corpus, the translations and the benchmark all cover exactly these two,
    and claiming to detect more than the engine can actually serve would be
    the same overclaim this codebase avoids elsewhere.
    """
    if _TURKISH_LETTERS & set(question.casefold()):
        return "tr"
    if token_set & _TURKISH_MARKERS:
        return "tr"
    return "en"


def _named_traditions(token_set: set[str]) -> frozenset[str]:
    return frozenset(
        name for name, terms in _TRADITION_TERMS.items() if _has_marker(token_set, terms)
    )


def _classify_intent(
    token_set: set[str],
    has_citation: bool,
    traditions: frozenset[str],
    broad_concepts: frozenset[str],
    signals: list[str],
) -> IntentType:
    # Ordered most-specific-first. A question can carry several markers;
    # the first rule that fires wins, and `signals` records which one did.
    if _has_marker(token_set, _COMPARISON_MARKERS) or len(traditions) >= 2:
        signals.append(
            "comparison-markers"
            if _has_marker(token_set, _COMPARISON_MARKERS)
            else "two-traditions"
        )
        return IntentType.COMPARISON

    if _has_marker(token_set, _TRANSLATION_MARKERS):
        signals.append("translation-markers")
        return IntentType.TRANSLATION_HELP

    if _has_marker(token_set, _WORD_MEANING_MARKERS):
        signals.append("word-meaning-markers")
        return IntentType.WORD_MEANING

    if _has_marker(token_set, _HISTORICAL_MARKERS):
        signals.append("historical-markers")
        return IntentType.HISTORICAL_EXPLANATION

    if has_citation:
        signals.append("explicit-citation")
        return IntentType.VERSE_EXPLANATION

    if _has_marker(token_set, _SUMMARY_MARKERS):
        signals.append("summary-markers")
        return IntentType.SUMMARY

    if broad_concepts:
        signals.append("broad-concept")
        return IntentType.DOCTRINAL_EXPLANATION

    # "Who is X?" about a scriptural figure. Kept below the broad-concept
    # rule so "Who is the Messiah?" is classified by its subject rather than
    # by its interrogative, and given standard rather than broad depth --
    # "İsa kimdir?" deserves a scaled answer, not fourteen screens.
    if token_set & _PERSON_MARKERS:
        signals.append("person-question")
        return IntentType.DOCTRINAL_EXPLANATION

    signals.append("no-intent-marker")
    return IntentType.UNKNOWN


def _classify_depth(
    intent: IntentType,
    tokens: list[str],
    broad_concepts: frozenset[str],
    has_citation: bool,
    signals: list[str],
) -> Depth:
    # An explicit citation localizes a question no matter what else it
    # carries: "what does Genesis 1:1 mean" is narrow even though "mean" is
    # a word-meaning marker.
    if has_citation and intent in (IntentType.VERSE_EXPLANATION, IntentType.WORD_MEANING):
        signals.append("depth:citation-anchored")
        return Depth.NARROW

    if intent is IntentType.COMPARISON or broad_concepts:
        signals.append("depth:broad-subject")
        return Depth.BROAD

    if intent is IntentType.WORD_MEANING and len(tokens) <= 8:
        signals.append("depth:single-term")
        return Depth.NARROW

    signals.append("depth:default")
    return Depth.STANDARD


def _classify_complexity(
    intent: IntentType,
    depth: Depth,
    tokens: list[str],
    token_set: set[str],
    traditions: frozenset[str],
    signals: list[str],
) -> Complexity:
    connectives = len(_matching_markers(token_set, _DEEP_CONNECTIVES))

    if len(traditions) >= 2 or (intent is IntentType.COMPARISON and connectives >= 1):
        signals.append("complexity:multi-tradition")
        return Complexity.DEEP

    if len(tokens) >= 25 or connectives >= 3:
        signals.append("complexity:multi-clause")
        return Complexity.DEEP

    if depth is Depth.NARROW and len(tokens) <= 12:
        signals.append("complexity:localized")
        return Complexity.SIMPLE

    signals.append("complexity:default")
    return Complexity.MODERATE
