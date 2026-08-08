"""Renders the user turn from the engine's prompt contract files.

The prompt text itself lives in providers/llm/prompts/*.txt rather than in
Python string literals, so the contract governing every answer can be read,
reviewed and changed as a document instead of being buried in code.

Three files compose the user turn:
- chat_user_prompt.txt   the frame: question, language, intent, evidence, filters
- response_contract_*.txt the output shape, selected per request

The rendered frame is handed to the provider as the context, and the raw
question is passed alongside it, so the provider's `build_user_message`
places the full frame first and the bare question last. That ordering is
deliberate rather than incidental: the frame supplies everything needed to
answer, and ending on the question itself keeps it in the model's most
recent attention rather than buried a thousand tokens up.
"""

import importlib.resources
from dataclasses import dataclass, field
from enum import StrEnum

from vahiy_engine.reasoning.intent import QuestionAnalysis

_PROMPT_PACKAGE = "vahiy_engine.providers.llm"

_NOT_PROVIDED = "(none provided)"


class AnswerFormat(StrEnum):
    """Which output contract the caller wants back.

    MARKDOWN is the human-facing contract (Direct Answer / Evidence /
    Explanation / Original Text / Comparison / Confidence / Takeaway).
    JSON is the machine-readable contract, for callers that need to render
    the parts themselves rather than display prose.
    """

    MARKDOWN = "markdown"
    JSON = "json"


class Corpus(StrEnum):
    """Source families a caller may restrict an answer to."""

    BIBLE = "bible"
    QURAN = "quran"
    LEXICON = "lexicon"


# Which citation types each corpus filter admits. Used to make a source
# preference actually filter evidence rather than merely appear in a menu.
CORPUS_CITATION_TYPES: dict[Corpus, frozenset[str]] = {
    Corpus.BIBLE: frozenset({"osis"}),
    Corpus.QURAN: frozenset({"quran"}),
    Corpus.LEXICON: frozenset({"strongs"}),
}


@dataclass(frozen=True)
class UserPreferences:
    """Caller-supplied filters that must reach retrieval, not just the prompt.

    `corpora` restricts which source families may be cited at all. An empty
    tuple means no restriction. When a restriction is applied the engine
    still reports what it excluded, so a filtered answer is distinguishable
    from a corpus that simply had nothing to say.

    `traditions` and `translation` are declarative: they are passed to the
    model as instructions because the engine has no tradition-specific or
    translation-specific corpora to filter on yet. They are kept separate
    from `corpora` for exactly that reason -- one changes what is retrieved,
    the others change how it is discussed, and conflating them would be the
    "fake option" failure this field exists to avoid.
    """

    corpora: tuple[Corpus, ...] = ()
    traditions: tuple[str, ...] = ()
    translation: str | None = None
    source_priority: tuple[str, ...] = ()
    notes: str | None = None

    def allows(self, citation_type: str) -> bool:
        if not self.corpora:
            return True
        return any(citation_type in CORPUS_CITATION_TYPES[c] for c in self.corpora)

    def describe(self) -> str:
        lines: list[str] = []
        if self.corpora:
            lines.append(
                "Restrict citations to these source families: "
                + ", ".join(c.value for c in self.corpora)
                + ". Evidence from other corpora has already been withheld from the "
                "evidence block; do not supply it from your own knowledge."
            )
        if self.traditions:
            lines.append("Compare these traditions specifically: " + ", ".join(self.traditions))
        if self.translation:
            lines.append(f"Prefer this translation when quoting: {self.translation}")
        if self.notes:
            lines.append(self.notes)
        return "\n".join(lines) if lines else _NOT_PROVIDED


@dataclass(frozen=True)
class PromptInputs:
    question: str
    analysis: QuestionAnalysis
    evidence: str
    preferences: UserPreferences = field(default_factory=UserPreferences)
    conversation_context: str | None = None
    answer_format: AnswerFormat = AnswerFormat.MARKDOWN


def load_prompt(filename: str) -> str:
    prompt_dir = importlib.resources.files(_PROMPT_PACKAGE) / "prompts"
    return (prompt_dir / filename).read_text(encoding="utf-8").strip()


def load_response_contract(answer_format: AnswerFormat) -> str:
    return load_prompt(f"response_contract_{answer_format.value}.txt")


def build_user_prompt(inputs: PromptInputs) -> str:
    """Render the user-turn frame for one request."""
    template = load_prompt("chat_user_prompt.txt")
    analysis = inputs.analysis

    return template.format(
        user_question=inputs.question,
        conversation_context=inputs.conversation_context or _NOT_PROVIDED,
        user_language=_describe_language(analysis.language),
        detected_intent=_describe_intent(analysis),
        user_preferences=inputs.preferences.describe(),
        retrieved_evidence=inputs.evidence or "(no evidence was retrieved for this question)",
        source_priority=(
            ", ".join(inputs.preferences.source_priority)
            if inputs.preferences.source_priority
            else _NOT_PROVIDED
        ),
        response_contract=load_response_contract(inputs.answer_format),
    )


def _describe_language(code: str) -> str:
    return {"tr": "Turkish (tr) — answer in Turkish first", "en": "English (en)"}.get(code, code)


def _describe_intent(analysis: QuestionAnalysis) -> str:
    """State the classification as guidance, not as a verdict.

    The classifier is a deterministic rule set, not an oracle; telling the
    model it may override a misclassification is more useful than having it
    force a comparative answer onto a question the rules mislabeled.
    """
    return (
        f"intent={analysis.intent.value}; depth={analysis.depth.value}; "
        f"complexity={analysis.complexity.value}\n"
        "This classification comes from a deterministic rule set and is guidance, "
        "not a constraint. If the question is plainly something else, answer what "
        "was actually asked."
    )
