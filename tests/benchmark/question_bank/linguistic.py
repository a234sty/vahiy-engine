"""100 linguistic questions, organized into ten sub-themes of ten.

Gold cases (real expected node + verified evidence) are limited to what
knowledge_graph/seed_data.py actually covers for word-level and etymological
claims: the hayah/YHWH root connection (Strong:H1961, Strong:H3068,
Exod.3.14) and the kyrios/YHWH translation correspondence (Strong:G2962,
Rom.10.13). Everything else is a real question with
coverage_status="not_yet_covered" — honest about the gap rather than padded
with invented expectations.
"""

from tests.benchmark.question_bank.schema import BenchmarkQuestion
from vahiy_engine.reasoning.trace import ConfidenceTier

LINGUISTIC_QUESTIONS: list[BenchmarkQuestion] = [
    # --- 1. Hebrew root hayah / YHWH etymology (gold) ---
    BenchmarkQuestion(
        id="ling-001",
        category="linguistic",
        question="What Hebrew verb root is YHWH traditionally connected to?",
        coverage_status="gold",
        expected_node_id="yhwh",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Exod.3.14", "Strong:H3068"),
    ),
    BenchmarkQuestion(
        id="ling-002",
        category="linguistic",
        question="What does the Hebrew word hayah mean?",
        coverage_status="gold",
        expected_node_id="hayah",
        expected_min_confidence=ConfidenceTier.LOW,
        expected_evidence_citations=("Strong:H1961",),
    ),
    BenchmarkQuestion(
        id="ling-003",
        category="linguistic",
        question="hayah kelimesi ne anlama gelir?",
        language="tr",
        coverage_status="gold",
        expected_node_id="hayah",
        expected_min_confidence=ConfidenceTier.LOW,
        expected_evidence_citations=("Strong:H1961",),
    ),
    BenchmarkQuestion(
        id="ling-004",
        category="linguistic",
        question="Is the Tetragrammaton morphologically an imperfect or causative form of the verb 'to be'?",
        notes="Requires grammatical synthesis beyond a single Strong's entry; not yet gold.",
    ),
    BenchmarkQuestion(
        id="ling-005",
        category="linguistic",
        question="What is the difference between the qal and hiphil stems in Biblical Hebrew?",
    ),
    BenchmarkQuestion(
        id="ling-006",
        category="linguistic",
        question="How many consonants does the Hebrew alphabet have?",
    ),
    BenchmarkQuestion(
        id="ling-007",
        category="linguistic",
        question="What is the significance of vowel pointing (niqqud) in the Masoretic Text?",
    ),
    BenchmarkQuestion(
        id="ling-008",
        category="linguistic",
        question="How does Biblical Hebrew mark verb tense compared to aspect?",
    ),
    BenchmarkQuestion(
        id="ling-009",
        category="linguistic",
        question="What is a Qere-Ketiv reading tradition?",
    ),
    BenchmarkQuestion(
        id="ling-010",
        category="linguistic",
        question="What Semitic languages is Hebrew most closely related to?",
    ),
    # --- 2. Kyrios / Greek NT terminology (gold) ---
    BenchmarkQuestion(
        id="ling-011",
        category="linguistic",
        question="What does the Greek word kyrios mean?",
        coverage_status="gold",
        expected_node_id="kyrios",
        expected_min_confidence=ConfidenceTier.LOW,
        expected_evidence_citations=("Strong:G2962",),
    ),
    BenchmarkQuestion(
        id="ling-012",
        category="linguistic",
        question="kyrios kelimesi Yunancada ne anlama gelir?",
        language="tr",
        coverage_status="gold",
        expected_node_id="kyrios",
        expected_min_confidence=ConfidenceTier.LOW,
        expected_evidence_citations=("Strong:G2962",),
    ),
    BenchmarkQuestion(
        id="ling-013",
        category="linguistic",
        question="Why does Romans 10:13 use kyrios where the Hebrew original had YHWH?",
        coverage_status="gold",
        expected_node_id="yhwh",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Rom.10.13",),
    ),
    BenchmarkQuestion(
        id="ling-014",
        category="linguistic",
        question="How did the Septuagint translators render YHWH into Greek?",
        notes="Requires LXX-specific corpus not yet ingested; not yet gold.",
    ),
    BenchmarkQuestion(
        id="ling-015",
        category="linguistic",
        question="What is Koine Greek and how does it differ from Classical Greek?",
    ),
    BenchmarkQuestion(
        id="ling-016",
        category="linguistic",
        question="What is the Greek definite article's role in identifying kyrios as a title versus a name?",
    ),
    BenchmarkQuestion(
        id="ling-017",
        category="linguistic",
        question="How many cases does Koine Greek have and what are they?",
    ),
    BenchmarkQuestion(
        id="ling-018",
        category="linguistic",
        question="What is the aorist tense and why is it significant for New Testament exegesis?",
    ),
    BenchmarkQuestion(
        id="ling-019",
        category="linguistic",
        question="What manuscript families inform the critical Greek New Testament text?",
    ),
    BenchmarkQuestion(
        id="ling-020",
        category="linguistic",
        question="How does Greek grammatical gender affect theological translation choices?",
    ),
    # --- 3. Arabic and Qur'anic linguistics ---
    BenchmarkQuestion(
        id="ling-021",
        category="linguistic",
        question="What is the root meaning of the Arabic word 'Islam'?",
    ),
    BenchmarkQuestion(
        id="ling-022",
        category="linguistic",
        question="What is a triliteral root in Arabic morphology?",
    ),
    BenchmarkQuestion(
        id="ling-023",
        category="linguistic",
        question="What is the difference between Classical Arabic and Modern Standard Arabic?",
    ),
    BenchmarkQuestion(
        id="ling-024",
        category="linguistic",
        question="What does the word 'Qur'an' itself mean in Arabic?",
    ),
    BenchmarkQuestion(
        id="ling-025",
        category="linguistic",
        question="What are the seven canonical qira'at (recitation readings) of the Qur'an?",
    ),
    BenchmarkQuestion(
        id="ling-026",
        category="linguistic",
        question="What is i'jaz al-Qur'an (the inimitability of the Qur'an) as a linguistic claim?",
    ),
    BenchmarkQuestion(
        id="ling-027",
        category="linguistic",
        question="How does Arabic verb conjugation mark person, gender, and number?",
    ),
    BenchmarkQuestion(
        id="ling-028",
        category="linguistic",
        question="What is the significance of Arabic diacritical marks (tashkeel) for Qur'anic recitation?",
    ),
    BenchmarkQuestion(
        id="ling-029",
        category="linguistic",
        question="What loanwords does Arabic share with Hebrew and Aramaic?",
    ),
    BenchmarkQuestion(
        id="ling-030",
        category="linguistic",
        question="How is the Arabic word 'Rabb' related in meaning to Hebrew 'Adon' and Greek 'kyrios'?",
        notes="Cross-lingual comparison touching the kyrios node but requiring an Arabic lexicon not yet ingested; not yet gold.",
    ),
    # --- 4. Turkish translation and terminology ---
    BenchmarkQuestion(
        id="ling-031",
        category="linguistic",
        question="Şabat kelimesinin İbranice kökeni nedir?",
        language="tr",
    ),
    BenchmarkQuestion(
        id="ling-032",
        category="linguistic",
        question="Türkçe Kutsal Kitap çevirilerinde 'YHWH' nasıl karşılanır?",
        language="tr",
    ),
    BenchmarkQuestion(
        id="ling-033",
        category="linguistic",
        question="What challenges arise when translating Hebrew tense/aspect into Turkish?",
    ),
    BenchmarkQuestion(
        id="ling-034",
        category="linguistic",
        question="How does Turkish vowel harmony affect the transliteration of Semitic names?",
    ),
    BenchmarkQuestion(
        id="ling-035",
        category="linguistic",
        question="What is the history of Turkish-language Qur'an translation (meal)?",
    ),
    BenchmarkQuestion(
        id="ling-036",
        category="linguistic",
        question="Kitabı Mukaddes ile Tevrat kelimeleri arasındaki fark nedir?",
        language="tr",
    ),
    BenchmarkQuestion(
        id="ling-037",
        category="linguistic",
        question="How do Ottoman Turkish religious texts differ linguistically from modern Turkish translations?",
    ),
    BenchmarkQuestion(
        id="ling-038",
        category="linguistic",
        question="What Persian and Arabic loanwords dominate Turkish religious vocabulary?",
    ),
    BenchmarkQuestion(
        id="ling-039",
        category="linguistic",
        question="How does agglutination in Turkish affect the rendering of construct-state Hebrew phrases?",
    ),
    BenchmarkQuestion(
        id="ling-040",
        category="linguistic",
        question="What is the difference between 'Tanrı' and 'Allah' as used in Turkish religious discourse?",
    ),
    # --- 5. Textual criticism and manuscript terminology ---
    BenchmarkQuestion(
        id="ling-041",
        category="linguistic",
        question="What is a variant reading in textual criticism?",
    ),
    BenchmarkQuestion(
        id="ling-042",
        category="linguistic",
        question="What does the term 'lectio difficilior' mean and how is it used?",
    ),
    BenchmarkQuestion(
        id="ling-043",
        category="linguistic",
        question="What is the difference between an autograph and an apograph in manuscript studies?",
    ),
    BenchmarkQuestion(
        id="ling-044",
        category="linguistic",
        question="What is a scribal gloss and how is it distinguished from original text?",
    ),
    BenchmarkQuestion(
        id="ling-045",
        category="linguistic",
        question="What does 'stemma codicum' mean in manuscript genealogy?",
    ),
    BenchmarkQuestion(
        id="ling-046",
        category="linguistic",
        question="What is the difference between a codex and a scroll as manuscript formats?",
    ),
    BenchmarkQuestion(
        id="ling-047",
        category="linguistic",
        question="What is haplography and how does it produce textual variants?",
    ),
    BenchmarkQuestion(
        id="ling-048",
        category="linguistic",
        question="What is dittography as a scribal error?",
    ),
    BenchmarkQuestion(
        id="ling-049",
        category="linguistic",
        question="What does 'terminus ante quem' mean when dating a manuscript?",
    ),
    BenchmarkQuestion(
        id="ling-050",
        category="linguistic",
        question="What is the difference between eclectic and diplomatic critical editions?",
    ),
    # --- 6. Semantic range and word-study method ---
    BenchmarkQuestion(
        id="ling-051",
        category="linguistic",
        question="What is a 'semantic range' in lexical study of Biblical Hebrew?",
    ),
    BenchmarkQuestion(
        id="ling-052",
        category="linguistic",
        question="Why is it a methodological error to import a word's full semantic range into every occurrence (illegitimate totality transfer)?",
    ),
    BenchmarkQuestion(
        id="ling-053",
        category="linguistic",
        question="What is a hapax legomenon and why is it difficult to translate?",
    ),
    BenchmarkQuestion(
        id="ling-054",
        category="linguistic",
        question="How do concordance-based word studies differ from discourse-based lexical semantics?",
    ),
    BenchmarkQuestion(
        id="ling-055",
        category="linguistic",
        question="What is diachronic versus synchronic analysis in Biblical Hebrew lexicography?",
    ),
    BenchmarkQuestion(
        id="ling-056",
        category="linguistic",
        question="What is a cognate language argument in reconstructing an obscure Hebrew word's meaning?",
    ),
    BenchmarkQuestion(
        id="ling-057",
        category="linguistic",
        question="What is the etymological fallacy in word-study exegesis?",
    ),
    BenchmarkQuestion(
        id="ling-058",
        category="linguistic",
        question="How does collocation analysis help determine a word's meaning in context?",
    ),
    BenchmarkQuestion(
        id="ling-059",
        category="linguistic",
        question="What is the difference between denotation and connotation in theological word studies?",
    ),
    BenchmarkQuestion(
        id="ling-060",
        category="linguistic",
        question="Why do Strong's numbers group multiple distinct senses of a word under one entry, and what risk does that create?",
        coverage_status="gold",
        expected_node_id="hayah",
        expected_min_confidence=ConfidenceTier.LOW,
        expected_evidence_citations=("Strong:H1961",),
        notes="Gold on retrieval of the hayah Strong's entry itself; the methodological claim in the question is not adjudicated by the graph.",
    ),
    # --- 7. Translation theory ---
    BenchmarkQuestion(
        id="ling-061",
        category="linguistic",
        question="What is the difference between formal equivalence and dynamic equivalence in Bible translation?",
    ),
    BenchmarkQuestion(
        id="ling-062",
        category="linguistic",
        question="What is a paraphrase translation and how does it differ from a literal translation?",
    ),
    BenchmarkQuestion(
        id="ling-063",
        category="linguistic",
        question="What is 'translation drift' across successive editions of a Bible version?",
    ),
    BenchmarkQuestion(
        id="ling-064",
        category="linguistic",
        question="How do interlinear translations attempt to preserve source-language word order?",
    ),
    BenchmarkQuestion(
        id="ling-065",
        category="linguistic",
        question="What is a targum and how does it function as translation-plus-commentary?",
    ),
    BenchmarkQuestion(
        id="ling-066",
        category="linguistic",
        question="Why can no translation of the Qur'an be considered the Qur'an itself in classical Islamic doctrine?",
    ),
    BenchmarkQuestion(
        id="ling-067",
        category="linguistic",
        question="What is skopos theory and how does it apply to sacred text translation?",
    ),
    BenchmarkQuestion(
        id="ling-068",
        category="linguistic",
        question="What ethical obligations does a translator have when a source term is genuinely ambiguous?",
    ),
    BenchmarkQuestion(
        id="ling-069",
        category="linguistic",
        question="How do committee translations differ methodologically from single-translator versions?",
    ),
    BenchmarkQuestion(
        id="ling-070",
        category="linguistic",
        question="What is back-translation and how is it used to check translation accuracy?",
    ),
    # --- 8. Phonology and script ---
    BenchmarkQuestion(
        id="ling-071",
        category="linguistic",
        question="What is the difference between an abjad and an alphabet as writing systems?",
    ),
    BenchmarkQuestion(
        id="ling-072",
        category="linguistic",
        question="How did paleo-Hebrew script differ from the square Aramaic script used today?",
    ),
    BenchmarkQuestion(
        id="ling-073",
        category="linguistic",
        question="What are begadkefat consonants in Hebrew phonology?",
    ),
    BenchmarkQuestion(
        id="ling-074",
        category="linguistic",
        question="What is the emphatic ayin sound in Semitic languages and how is it transliterated?",
    ),
    BenchmarkQuestion(
        id="ling-075",
        category="linguistic",
        question="How does Arabic script's contextual letter forms differ from Hebrew's fixed forms?",
    ),
    BenchmarkQuestion(
        id="ling-076",
        category="linguistic",
        question="What is the significance of matres lectionis in reconstructing pre-Masoretic pronunciation?",
    ),
    BenchmarkQuestion(
        id="ling-077",
        category="linguistic",
        question="What is cantillation (te'amim) and what linguistic information does it encode?",
    ),
    BenchmarkQuestion(
        id="ling-078",
        category="linguistic",
        question="How do Samaritan Hebrew pronunciation traditions differ from Masoretic Hebrew?",
    ),
    BenchmarkQuestion(
        id="ling-079",
        category="linguistic",
        question="What is the phonetic difference between Ashkenazi and Sephardi Hebrew pronunciation?",
    ),
    BenchmarkQuestion(
        id="ling-080",
        category="linguistic",
        question="What is emphasis (tafkhim) in Qur'anic Arabic phonology?",
    ),
    # --- 9. Syntax and discourse grammar ---
    BenchmarkQuestion(
        id="ling-081",
        category="linguistic",
        question="What is the waw-consecutive construction in Biblical Hebrew narrative?",
    ),
    BenchmarkQuestion(
        id="ling-082",
        category="linguistic",
        question="How does Biblical Hebrew poetry use parallelism as a structural device?",
    ),
    BenchmarkQuestion(
        id="ling-083",
        category="linguistic",
        question="What is a construct chain (smikhut) in Hebrew grammar?",
    ),
    BenchmarkQuestion(
        id="ling-084",
        category="linguistic",
        question="What is chiasm and how is it used as a literary-structural marker in Scripture?",
    ),
    BenchmarkQuestion(
        id="ling-085",
        category="linguistic",
        question="How does Greek word order convey emphasis differently than English?",
    ),
    BenchmarkQuestion(
        id="ling-086",
        category="linguistic",
        question="What is asyndeton and what rhetorical effect does it create in Koine Greek prose?",
    ),
    BenchmarkQuestion(
        id="ling-087",
        category="linguistic",
        question="What is the function of the Hebrew particle 'hinneh' in narrative discourse?",
    ),
    BenchmarkQuestion(
        id="ling-088",
        category="linguistic",
        question="How does discourse analysis identify paragraph and pericope boundaries in ancient texts?",
    ),
    BenchmarkQuestion(
        id="ling-089",
        category="linguistic",
        question="What is topicalization and how is it marked in Biblical Hebrew word order?",
    ),
    BenchmarkQuestion(
        id="ling-090",
        category="linguistic",
        question="What syntactic features distinguish Qur'anic Arabic rhetorical style from Arabic prose of its era?",
    ),
    # --- 10. Comparative Semitic and cross-tradition terminology ---
    BenchmarkQuestion(
        id="ling-091",
        category="linguistic",
        question="What is comparative Semitic linguistics and how does it aid interpretation of obscure terms?",
    ),
    BenchmarkQuestion(
        id="ling-092",
        category="linguistic",
        question="Are the Hebrew 'El' and Arabic 'Allah' etymologically related?",
    ),
    BenchmarkQuestion(
        id="ling-093",
        category="linguistic",
        question="What is the linguistic relationship between Hebrew 'shalom' and Arabic 'salaam'?",
    ),
    BenchmarkQuestion(
        id="ling-094",
        category="linguistic",
        question="How is the name 'Abraham/İbrahim' rendered across Hebrew, Greek, Arabic, and Turkish, and what does each form preserve or lose?",
        coverage_status="gold",
        expected_node_id="abraham",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Gen.17.5", "Quran.14.35"),
        notes="Gold on cross-lingual name retrieval via the multi-language labels on the abraham node; full etymological comparison beyond scope.",
    ),
    BenchmarkQuestion(
        id="ling-095",
        category="linguistic",
        question="What is Proto-Semitic and how is it reconstructed from daughter languages?",
    ),
    BenchmarkQuestion(
        id="ling-096",
        category="linguistic",
        question="How does Aramaic function as a bridge language between Hebrew and later Jewish and Christian texts?",
    ),
    BenchmarkQuestion(
        id="ling-097",
        category="linguistic",
        question="What Akkadian cognates inform the interpretation of rare Biblical Hebrew vocabulary?",
    ),
    BenchmarkQuestion(
        id="ling-098",
        category="linguistic",
        question="How do Ge'ez (Ethiopic) terms illuminate textual questions in the Book of Enoch tradition?",
    ),
    BenchmarkQuestion(
        id="ling-099",
        category="linguistic",
        question="What is the significance of shared vocabulary between Ugaritic and Biblical Hebrew for lexicography?",
    ),
    BenchmarkQuestion(
        id="ling-100",
        category="linguistic",
        question="What general principle should govern citing a cognate language to fill a gap in Hebrew lexicography, without overclaiming certainty?",
    ),
]

assert len(LINGUISTIC_QUESTIONS) == 100
