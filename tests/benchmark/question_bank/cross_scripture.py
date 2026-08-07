"""100 cross-scripture reasoning questions, organized into ten sub-themes of
ten.

Gold cases (real expected node + verified evidence) are limited to what
knowledge_graph/seed_data.py actually covers for cross-scripture comparison:
Abraham/İbrahim, whose node carries both Torah citations (Gen.12.1, Gen.17.5,
Gen.22.2) and Qur'an citations (Quran.14.35, Quran.2.124, Quran.21.51) —
the only concept in the seed graph with genuine structural parity across
traditions right now. Everything else is a real question with
coverage_status="not_yet_covered" — honest about the gap rather than padded
with invented expectations.
"""

from tests.benchmark.question_bank.schema import BenchmarkQuestion
from vahiy_engine.reasoning.trace import ConfidenceTier

CROSS_SCRIPTURE_QUESTIONS: list[BenchmarkQuestion] = [
    # --- 1. Abraham across Torah and Qur'an (gold) ---
    BenchmarkQuestion(
        id="cross-001",
        category="cross_scripture",
        question="How is Abraham/İbrahim depicted in both the Torah and the Qur'an?",
        coverage_status="gold",
        expected_node_id="abraham",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Gen.12.1", "Quran.14.35"),
    ),
    BenchmarkQuestion(
        id="cross-002",
        category="cross_scripture",
        question="İbrahim hem Tevrat'ta hem Kur'an'da nasıl anlatılır?",
        language="tr",
        coverage_status="gold",
        expected_node_id="abraham",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Gen.17.5", "Quran.2.124"),
    ),
    BenchmarkQuestion(
        id="cross-003",
        category="cross_scripture",
        question="Does the Qur'an's idol-breaking narrative about Ibrahim appear anywhere in the Torah?",
        coverage_status="gold",
        expected_node_id="abraham",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Quran.21.51",),
        notes="Gold on retrieval; the graph does not itself adjudicate whether the Torah lacks a parallel narrative.",
    ),
    BenchmarkQuestion(
        id="cross-004",
        category="cross_scripture",
        question="How does Genesis 22's binding of Isaac compare to the Qur'an's account of the near-sacrifice in Surah 37?",
        notes="Requires Quran.37 coverage not yet in the seed graph; not yet gold.",
    ),
    BenchmarkQuestion(
        id="cross-005",
        category="cross_scripture",
        question="What covenant language is shared between Genesis 17 and Quran 2:124 regarding Abraham?",
        coverage_status="gold",
        expected_node_id="abraham",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Gen.17.5", "Quran.2.124"),
    ),
    BenchmarkQuestion(
        id="cross-006",
        category="cross_scripture",
        question="Why do Jewish, Christian, and Muslim traditions all claim Abraham as a founding patriarch?",
    ),
    BenchmarkQuestion(
        id="cross-007",
        category="cross_scripture",
        question="Does the Qur'an ever directly quote or paraphrase a specific Torah verse about Abraham?",
    ),
    BenchmarkQuestion(
        id="cross-008",
        category="cross_scripture",
        question="How does the identity of the son nearly sacrificed (Isaac vs. Ishmael) differ between Jewish and Islamic tradition?",
    ),
    BenchmarkQuestion(
        id="cross-009",
        category="cross_scripture",
        question="What does the Qur'an say about Abraham's relationship to Mecca that has no Torah parallel?",
        coverage_status="gold",
        expected_node_id="abraham",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Quran.14.35",),
    ),
    BenchmarkQuestion(
        id="cross-010",
        category="cross_scripture",
        question="How many times is Abraham/İbrahim mentioned across the Torah versus the Qur'an?",
        notes="Requires a full-corpus mention count, not a single-node lookup; not yet gold.",
    ),
    # --- 2. Divine names across traditions ---
    BenchmarkQuestion(
        id="cross-011",
        category="cross_scripture",
        question="Is the God of the Qur'an (Allah) the same referent as YHWH in the Hebrew Bible?",
    ),
    BenchmarkQuestion(
        id="cross-012",
        category="cross_scripture",
        question="How does the Qur'anic concept of tawhid compare to the Shema's declaration of God's oneness?",
    ),
    BenchmarkQuestion(
        id="cross-013",
        category="cross_scripture",
        question="Does the New Testament's application of kyrios to Jesus have any parallel treatment in the Qur'an's Christology?",
        coverage_status="gold",
        expected_node_id="yhwh",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Rom.10.13",),
        notes="Gold on the New Testament side of the retrieval only; the graph has no Qur'anic Christology citations to compare against.",
    ),
    BenchmarkQuestion(
        id="cross-014",
        category="cross_scripture",
        question="What names or titles for God appear in both the Hebrew Bible and the Qur'an?",
    ),
    BenchmarkQuestion(
        id="cross-015",
        category="cross_scripture",
        question="How does the Qur'an's 99 names of Allah compare structurally to Jewish traditions of divine names?",
    ),
    BenchmarkQuestion(
        id="cross-016",
        category="cross_scripture",
        question="Does the Qur'an ever use a term structurally equivalent to the Tetragrammaton?",
    ),
    BenchmarkQuestion(
        id="cross-017",
        category="cross_scripture",
        question="How do Trinitarian and strictly monotheistic readings of divine unity diverge across the New Testament and the Qur'an?",
    ),
    BenchmarkQuestion(
        id="cross-018",
        category="cross_scripture",
        question="What is the Islamic doctrine regarding the Christian use of 'Son of God' language, and where does the Qur'an address it?",
    ),
    BenchmarkQuestion(
        id="cross-019",
        category="cross_scripture",
        question="How does Deuteronomy 6:4 relate conceptually to Quran 112?",
    ),
    BenchmarkQuestion(
        id="cross-020",
        category="cross_scripture",
        question="Is there a shared root or borrowing history between 'Elohim' and 'Allah'?",
    ),
    # --- 3. Sabbath and its cross-tradition analogues ---
    BenchmarkQuestion(
        id="cross-021",
        category="cross_scripture",
        question="Does the Qur'an have any commandment analogous to the Sabbath?",
        coverage_status="gold",
        expected_node_id="sabbath",
        expected_min_confidence=ConfidenceTier.MEDIUM,
        expected_evidence_citations=("Exod.20.8",),
        notes="Gold on the biblical Sabbath retrieval only; the graph has no Qur'anic Sabbath citation to compare against, and that absence is itself informative.",
    ),
    BenchmarkQuestion(
        id="cross-022",
        category="cross_scripture",
        question="How does Islamic Jumu'ah (Friday prayer) compare functionally to the Jewish Sabbath?",
    ),
    BenchmarkQuestion(
        id="cross-023",
        category="cross_scripture",
        question="Does the Qur'an criticize or address the Sabbath practices of the Children of Israel?",
    ),
    BenchmarkQuestion(
        id="cross-024",
        category="cross_scripture",
        question="How does Hebrews 4:9's 'sabbath rest' typology get received or reinterpreted in later Christian tradition versus how rest is framed in the Qur'an?",
        coverage_status="gold",
        expected_node_id="sabbath",
        expected_min_confidence=ConfidenceTier.MEDIUM,
        expected_evidence_citations=("Heb.4.9",),
    ),
    BenchmarkQuestion(
        id="cross-025",
        category="cross_scripture",
        question="What day of the week does each Abrahamic tradition treat as sacred, and why?",
    ),
    BenchmarkQuestion(
        id="cross-026",
        category="cross_scripture",
        question="Is Sunday observance in Christianity a continuation, replacement, or rejection of the Sabbath commandment?",
    ),
    BenchmarkQuestion(
        id="cross-027",
        category="cross_scripture",
        question="How does the concept of sacred time differ structurally between the Hebrew Bible and the Qur'an?",
    ),
    BenchmarkQuestion(
        id="cross-028",
        category="cross_scripture",
        question="What does Quran 16:124 say about disputes over the Sabbath?",
        notes="Requires Quran.16.124 coverage not yet in the seed graph; not yet gold.",
    ),
    BenchmarkQuestion(
        id="cross-029",
        category="cross_scripture",
        question="How does rabbinic halakha on Sabbath labor compare to Islamic fiqh on Friday obligations?",
    ),
    BenchmarkQuestion(
        id="cross-030",
        category="cross_scripture",
        question="Is there a Sabbath-keeping tradition within any Christian denomination that mirrors Jewish practice?",
    ),
    # --- 4. Shared prophetic and patriarchal narratives ---
    BenchmarkQuestion(
        id="cross-031",
        category="cross_scripture",
        question="How does the Qur'an's account of Moses compare to the Exodus narrative?",
    ),
    BenchmarkQuestion(
        id="cross-032",
        category="cross_scripture",
        question="How does the Qur'an's account of Noah compare to Genesis 6-9?",
    ),
    BenchmarkQuestion(
        id="cross-033",
        category="cross_scripture",
        question="How does the Qur'an's account of Joseph in Surah Yusuf compare to Genesis 37-50?",
    ),
    BenchmarkQuestion(
        id="cross-034",
        category="cross_scripture",
        question="Does the Qur'an narrate the story of David and Goliath, and how does it compare to 1 Samuel 17?",
    ),
    BenchmarkQuestion(
        id="cross-035",
        category="cross_scripture",
        question="How does the Qur'an's treatment of Solomon compare to 1 Kings' account?",
    ),
    BenchmarkQuestion(
        id="cross-036",
        category="cross_scripture",
        question="Does the Qur'an mention Jonah, and how closely does it follow the book of Jonah's plot?",
    ),
    BenchmarkQuestion(
        id="cross-037",
        category="cross_scripture",
        question="How does the Qur'an's nativity narrative of Jesus compare to the Gospel of Luke's?",
    ),
    BenchmarkQuestion(
        id="cross-038",
        category="cross_scripture",
        question="Are Job's narrative and theological arc treated similarly in the Qur'an and the Hebrew Bible?",
    ),
    BenchmarkQuestion(
        id="cross-039",
        category="cross_scripture",
        question="How does Ishmael's role in Genesis compare to his role in Islamic tradition?",
    ),
    BenchmarkQuestion(
        id="cross-040",
        category="cross_scripture",
        question="Does the Qur'an mention Lot's narrative, and how does it align with Genesis 19?",
    ),
    # --- 5. Canon, scripture-of-scripture claims ---
    BenchmarkQuestion(
        id="cross-041",
        category="cross_scripture",
        question="What does the Qur'an claim about its relationship to the Torah and the Gospel (Injil)?",
    ),
    BenchmarkQuestion(
        id="cross-042",
        category="cross_scripture",
        question="What is the Islamic doctrine of tahrif (textual corruption) as applied to prior scriptures?",
    ),
    BenchmarkQuestion(
        id="cross-043",
        category="cross_scripture",
        question="Does the New Testament ever claim continuity with or fulfillment of the Hebrew Bible in ways structurally comparable to the Qur'an's claims about prior scripture?",
    ),
    BenchmarkQuestion(
        id="cross-044",
        category="cross_scripture",
        question="How do 'People of the Book' (Ahl al-Kitab) references in the Qur'an characterize Jewish and Christian scripture?",
    ),
    BenchmarkQuestion(
        id="cross-045",
        category="cross_scripture",
        question="Is there manuscript or historical evidence for a distinct 'Injil' text the Qur'an refers to?",
    ),
    BenchmarkQuestion(
        id="cross-046",
        category="cross_scripture",
        question="How does supersessionist theology in Christianity compare structurally to the Islamic doctrine of Qur'anic finality?",
    ),
    BenchmarkQuestion(
        id="cross-047",
        category="cross_scripture",
        question="What does 'naskh' (abrogation) mean within the Qur'an, and is there a structurally similar concept applied to the Hebrew Bible in Christian theology?",
    ),
    BenchmarkQuestion(
        id="cross-048",
        category="cross_scripture",
        question="How do the three traditions differ in defining what counts as canonical scripture?",
    ),
    BenchmarkQuestion(
        id="cross-049",
        category="cross_scripture",
        question="Does the Qur'an quote or closely paraphrase any Psalms text?",
    ),
    BenchmarkQuestion(
        id="cross-050",
        category="cross_scripture",
        question="What extra-canonical or intertestamental texts inform both Second Temple Judaism and early Qur'anic exegesis?",
    ),
    # --- 6. Law and ethics across traditions ---
    BenchmarkQuestion(
        id="cross-051",
        category="cross_scripture",
        question="How does the Decalogue compare structurally to the core ethical commands in the Qur'an?",
    ),
    BenchmarkQuestion(
        id="cross-052",
        category="cross_scripture",
        question="How do dietary laws (kashrut) in the Torah compare to halal regulations in Islamic law?",
    ),
    BenchmarkQuestion(
        id="cross-053",
        category="cross_scripture",
        question="Is there a shared prohibition on usury (riba/neshekh) across the Torah and the Qur'an?",
    ),
    BenchmarkQuestion(
        id="cross-054",
        category="cross_scripture",
        question="How does the lex talionis in Exodus compare to retributive justice principles in the Qur'an?",
    ),
    BenchmarkQuestion(
        id="cross-055",
        category="cross_scripture",
        question="How do inheritance laws compare between the Torah and the Qur'an?",
    ),
    BenchmarkQuestion(
        id="cross-056",
        category="cross_scripture",
        question="Do the Gospels' teachings on divorce align more closely with Deuteronomy or with Qur'anic divorce law?",
    ),
    BenchmarkQuestion(
        id="cross-057",
        category="cross_scripture",
        question="How does the concept of sin and atonement differ across the Levitical sacrificial system, the New Testament, and the Qur'an?",
    ),
    BenchmarkQuestion(
        id="cross-058",
        category="cross_scripture",
        question="How do circumcision requirements compare between Genesis 17 and Islamic practice?",
        coverage_status="gold",
        expected_node_id="abraham",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Gen.17.5",),
        notes="Gold on the Genesis 17 retrieval only; the graph has no citation for Islamic circumcision practice to compare against.",
    ),
    BenchmarkQuestion(
        id="cross-059",
        category="cross_scripture",
        question="How does almsgiving (tzedakah, zakat) compare across Jewish and Islamic law?",
    ),
    BenchmarkQuestion(
        id="cross-060",
        category="cross_scripture",
        question="What ethical commands in the Sermon on the Mount have direct parallels in the Qur'an?",
    ),
    # --- 7. Eschatology across traditions ---
    BenchmarkQuestion(
        id="cross-061",
        category="cross_scripture",
        question="How does the Islamic concept of Yawm al-Qiyamah compare to Jewish and Christian last-judgment eschatology?",
    ),
    BenchmarkQuestion(
        id="cross-062",
        category="cross_scripture",
        question="Do the Qur'an and the book of Revelation share any apocalyptic imagery?",
    ),
    BenchmarkQuestion(
        id="cross-063",
        category="cross_scripture",
        question="How does the Islamic figure of the Mahdi compare to Jewish messianic expectation?",
    ),
    BenchmarkQuestion(
        id="cross-064",
        category="cross_scripture",
        question="Does the Qur'an's description of paradise (Jannah) share imagery with Genesis 2's Eden?",
    ),
    BenchmarkQuestion(
        id="cross-065",
        category="cross_scripture",
        question="How does the return of Jesus (Isa) in Islamic eschatology compare to Christian second-coming theology?",
    ),
    BenchmarkQuestion(
        id="cross-066",
        category="cross_scripture",
        question="What resurrection-of-the-body language is shared between Daniel 12 and the Qur'an?",
    ),
    BenchmarkQuestion(
        id="cross-067",
        category="cross_scripture",
        question="How does Gehenna in the New Testament compare structurally to Jahannam in the Qur'an?",
    ),
    BenchmarkQuestion(
        id="cross-068",
        category="cross_scripture",
        question="Is there a shared concept of a heavenly book of deeds across the Qur'an and Jewish apocalyptic literature?",
    ),
    BenchmarkQuestion(
        id="cross-069",
        category="cross_scripture",
        question="How does the Antichrist figure in Christian eschatology compare to Dajjal in Islamic tradition?",
    ),
    BenchmarkQuestion(
        id="cross-070",
        category="cross_scripture",
        question="What differences exist between Jewish, Christian, and Islamic views on the intermediate state between death and resurrection?",
    ),
    # --- 8. Methodological questions about cross-scripture comparison ---
    BenchmarkQuestion(
        id="cross-071",
        category="cross_scripture",
        question="What methodological safeguards prevent a cross-scripture comparison from flattening real theological differences?",
    ),
    BenchmarkQuestion(
        id="cross-072",
        category="cross_scripture",
        question="Is textual parallel evidence of literary dependence, shared oral tradition, or independent development — how should each be distinguished?",
    ),
    BenchmarkQuestion(
        id="cross-073",
        category="cross_scripture",
        question="What is the difference between typological and historical-critical approaches to cross-scripture comparison?",
    ),
    BenchmarkQuestion(
        id="cross-074",
        category="cross_scripture",
        question="How should a research engine present a cross-scripture comparison without implying that one tradition's reading adjudicates the others?",
        coverage_status="gold",
        expects_no_match=True,
        notes="A meta-methodological question about the engine's own neutrality posture, not a lookup the Knowledge Graph resolves; correctly returning no match is the honest outcome.",
    ),
    BenchmarkQuestion(
        id="cross-075",
        category="cross_scripture",
        question="What is 'parallelomania' as a scholarly caution in comparative scripture study?",
    ),
    BenchmarkQuestion(
        id="cross-076",
        category="cross_scripture",
        question="How does source-critical theory (e.g., the documentary hypothesis) complicate claims of direct Qur'an-Torah dependence?",
    ),
    BenchmarkQuestion(
        id="cross-077",
        category="cross_scripture",
        question="What role does shared Ancient Near Eastern or Late Antique context play versus direct textual borrowing in explaining parallels?",
    ),
    BenchmarkQuestion(
        id="cross-078",
        category="cross_scripture",
        question="How should confidence be scored differently for a direct textual citation versus a thematic parallel across scriptures?",
    ),
    BenchmarkQuestion(
        id="cross-079",
        category="cross_scripture",
        question="What does structural parity mean as a design principle for comparing scriptures without asserting equivalence of truth-claims?",
    ),
    BenchmarkQuestion(
        id="cross-080",
        category="cross_scripture",
        question="Why is it important that a cross-scripture answer disclose which citations came from which corpus and translation?",
    ),
    # --- 9. Ritual, liturgy, and sacred geography ---
    BenchmarkQuestion(
        id="cross-081",
        category="cross_scripture",
        question="How does the Islamic Hajj relate to the Abrahamic narrative shared with Genesis?",
        coverage_status="gold",
        expected_node_id="abraham",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Quran.14.35", "Quran.2.124"),
    ),
    BenchmarkQuestion(
        id="cross-082",
        category="cross_scripture",
        question="How does the Jewish Passover Seder liturgy compare structurally to the Islamic Eid celebrations?",
    ),
    BenchmarkQuestion(
        id="cross-083",
        category="cross_scripture",
        question="What is the shared and divergent significance of Jerusalem across Jewish, Christian, and Islamic tradition?",
    ),
    BenchmarkQuestion(
        id="cross-084",
        category="cross_scripture",
        question="How does the Islamic qibla toward Mecca compare historically to earlier Jewish and Christian prayer-direction practices?",
    ),
    BenchmarkQuestion(
        id="cross-085",
        category="cross_scripture",
        question="What is the shared significance of the number forty across flood, wilderness, and fasting narratives in these traditions?",
    ),
    BenchmarkQuestion(
        id="cross-086",
        category="cross_scripture",
        question="How does ritual purity law in Leviticus compare to Islamic concepts of ritual purity (taharah)?",
    ),
    BenchmarkQuestion(
        id="cross-087",
        category="cross_scripture",
        question="Is there a shared tradition behind the practice of pilgrimage across these three traditions?",
    ),
    BenchmarkQuestion(
        id="cross-088",
        category="cross_scripture",
        question="How does the Christian Eucharist relate historically to Passover practice?",
    ),
    BenchmarkQuestion(
        id="cross-089",
        category="cross_scripture",
        question="What is the shared and divergent theological function of fasting across these traditions?",
    ),
    BenchmarkQuestion(
        id="cross-090",
        category="cross_scripture",
        question="How does the sanctity of the Kaaba relate to pre-Islamic Arabian religious practice and to the Abrahamic narrative?",
    ),
    # --- 10. Historical relationship between the traditions ---
    BenchmarkQuestion(
        id="cross-091",
        category="cross_scripture",
        question="What historical contact existed between Jewish communities in Arabia and the emergence of the Qur'an?",
    ),
    BenchmarkQuestion(
        id="cross-092",
        category="cross_scripture",
        question="What historical contact existed between Christian communities and the emergence of the Qur'an?",
    ),
    BenchmarkQuestion(
        id="cross-093",
        category="cross_scripture",
        question="How did the Cairo Genizah documents inform understanding of Judeo-Arabic textual exchange?",
    ),
    BenchmarkQuestion(
        id="cross-094",
        category="cross_scripture",
        question="What role did Syriac Christian literature play in transmitting biblical narratives into a pre-Islamic Arabian context?",
    ),
    BenchmarkQuestion(
        id="cross-095",
        category="cross_scripture",
        question="How did medieval Jewish-Muslim philosophical exchange (e.g., Maimonides and Islamic philosophy) shape textual interpretation?",
    ),
    BenchmarkQuestion(
        id="cross-096",
        category="cross_scripture",
        question="What is the historical relationship between Ahitçilik's Ehl-i Vahiy branch and mainstream Jewish and Christian scripture traditions?",
    ),
    BenchmarkQuestion(
        id="cross-097",
        category="cross_scripture",
        question="How did the translation movement (Bayt al-Hikma) affect the transmission of biblical and classical texts into the Islamic world?",
    ),
    BenchmarkQuestion(
        id="cross-098",
        category="cross_scripture",
        question="What do the Dead Sea Scrolls reveal about textual plurality in the Second Temple period relevant to later cross-scripture comparison?",
    ),
    BenchmarkQuestion(
        id="cross-099",
        category="cross_scripture",
        question="How did interfaith polemical literature in the medieval period shape later cross-scripture scholarship?",
    ),
    BenchmarkQuestion(
        id="cross-100",
        category="cross_scripture",
        question="What general principle should govern citing a historical-contact hypothesis as an explanation for a cross-scripture parallel, without overclaiming direct dependence?",
    ),
]

assert len(CROSS_SCRIPTURE_QUESTIONS) == 100
