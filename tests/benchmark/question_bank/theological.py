"""100 theological questions, organized into ten sub-themes of ten.

Gold cases (real expected node + verified evidence) are limited to what
knowledge_graph/seed_data.py actually covers: YHWH and Sabbath. Everything
else is a real question with coverage_status="not_yet_covered" — honest
about the gap rather than padded with invented expectations.
"""

from tests.benchmark.question_bank.schema import BenchmarkQuestion
from vahiy_engine.reasoning.trace import ConfidenceTier

THEOLOGICAL_QUESTIONS: list[BenchmarkQuestion] = [
    # --- 1. Names and nature of God (YHWH is covered; gold) ---
    BenchmarkQuestion(
        id="theo-001",
        category="theological",
        question="What does the divine name YHWH mean?",
        coverage_status="gold",
        expected_node_id="yhwh",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Exod.3.14", "Strong:H3068"),
    ),
    BenchmarkQuestion(
        id="theo-002",
        category="theological",
        question="YHWH ismi ne anlama gelir?",
        language="tr",
        coverage_status="gold",
        expected_node_id="yhwh",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Exod.3.14", "Strong:H3068"),
    ),
    BenchmarkQuestion(
        id="theo-003",
        category="theological",
        question="How does Exodus 3:14 explain the meaning of God's name?",
        coverage_status="gold",
        expected_node_id="yhwh",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Exod.3.14",),
    ),
    BenchmarkQuestion(
        id="theo-004",
        category="theological",
        question="Is God's essence static or dynamic according to the etymology of YHWH?",
        notes="Interpretive question about the hayah root; not yet gold since it requires synthesis beyond a single citation lookup.",
    ),
    BenchmarkQuestion(
        id="theo-005",
        category="theological",
        question="What are the seventy names of God in Jewish tradition?",
    ),
    BenchmarkQuestion(
        id="theo-006",
        category="theological",
        question="What are the 99 names of Allah in Islamic tradition?",
    ),
    BenchmarkQuestion(
        id="theo-007",
        category="theological",
        question="Is the name Elohim singular or plural in form, and what does that imply?",
    ),
    BenchmarkQuestion(
        id="theo-008",
        category="theological",
        question="What is the theological significance of God being unnameable versus God revealing a personal name?",
    ),
    BenchmarkQuestion(
        id="theo-009",
        category="theological",
        question="How do Jewish traditions treat the pronunciation of the Tetragrammaton?",
    ),
    BenchmarkQuestion(
        id="theo-010",
        category="theological",
        question="What does it mean theologically that YHWH is translated as Kyrios (Lord) in the New Testament?",
        coverage_status="gold",
        expected_node_id="yhwh",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Rom.10.13",),
    ),
    # --- 2. Sabbath / rest theology (gold) ---
    BenchmarkQuestion(
        id="theo-011",
        category="theological",
        question="What is the theological basis for the Sabbath commandment?",
        coverage_status="gold",
        expected_node_id="sabbath",
        expected_min_confidence=ConfidenceTier.MEDIUM,
        expected_evidence_citations=("Gen.2.3", "Exod.20.8"),
    ),
    BenchmarkQuestion(
        id="theo-012",
        category="theological",
        question="Şabat neden kutsaldır?",
        language="tr",
        coverage_status="gold",
        expected_node_id="sabbath",
        expected_min_confidence=ConfidenceTier.MEDIUM,
        expected_evidence_citations=("Gen.2.3", "Exod.20.8"),
    ),
    BenchmarkQuestion(
        id="theo-013",
        category="theological",
        question="How is the Sabbath a sign of the covenant between God and Israel?",
        coverage_status="gold",
        expected_node_id="sabbath",
        expected_min_confidence=ConfidenceTier.MEDIUM,
        expected_evidence_citations=("Exod.31.13",),
    ),
    BenchmarkQuestion(
        id="theo-014",
        category="theological",
        question="What does Isaiah 58 teach about the proper spirit of Sabbath observance?",
        coverage_status="gold",
        expected_node_id="sabbath",
        expected_min_confidence=ConfidenceTier.MEDIUM,
        expected_evidence_citations=("Isa.58.13",),
    ),
    BenchmarkQuestion(
        id="theo-015",
        category="theological",
        question="What does Hebrews 4 mean by a 'sabbath rest' that remains for the people of God?",
        coverage_status="gold",
        expected_node_id="sabbath",
        expected_min_confidence=ConfidenceTier.MEDIUM,
        expected_evidence_citations=("Heb.4.9",),
    ),
    BenchmarkQuestion(
        id="theo-016",
        category="theological",
        question="Is Sabbath rest a creation ordinance binding on all humanity or a sign specific to Israel?",
        notes="Genuinely disputed across traditions; correct engine behavior is attributed presentation, not resolution.",
    ),
    BenchmarkQuestion(
        id="theo-017",
        category="theological",
        question="How does the concept of Jumu'ah (Friday congregational prayer) in Islam relate theologically to the Sabbath?",
    ),
    BenchmarkQuestion(
        id="theo-018",
        category="theological",
        question="What theological weight does rest carry as an attribute of divine character?",
    ),
    BenchmarkQuestion(
        id="theo-019",
        category="theological",
        question="Why might work be considered spiritually significant enough to warrant a commanded cessation?",
    ),
    BenchmarkQuestion(
        id="theo-020",
        category="theological",
        question="How do Reform, Conservative, and Orthodox Judaism differ in their theology of Sabbath observance?",
    ),
    # --- 3. Covenant theology ---
    BenchmarkQuestion(
        id="theo-021",
        category="theological",
        question="What is the theological significance of the Abrahamic covenant?",
    ),
    BenchmarkQuestion(
        id="theo-022",
        category="theological",
        question="How does the Mosaic covenant differ theologically from the Abrahamic covenant?",
    ),
    BenchmarkQuestion(
        id="theo-023",
        category="theological",
        question="What is meant by the 'New Covenant' in Christian theology?",
    ),
    BenchmarkQuestion(
        id="theo-024",
        category="theological",
        question="Is circumcision primarily a covenantal sign or a legal requirement?",
    ),
    BenchmarkQuestion(
        id="theo-025",
        category="theological",
        question="What role does covenant faithfulness (hesed) play in the character of God?",
    ),
    BenchmarkQuestion(
        id="theo-026",
        category="theological",
        question="How does the concept of covenant in the Hebrew Bible compare to the Islamic concept of mithaq (primordial covenant)?",
    ),
    BenchmarkQuestion(
        id="theo-027",
        category="theological",
        question="What theological implications follow from describing Israel as a covenant people?",
    ),
    BenchmarkQuestion(
        id="theo-028",
        category="theological",
        question="Is covenant conditional or unconditional in Reformed theology?",
    ),
    BenchmarkQuestion(
        id="theo-029",
        category="theological",
        question="What is the theological meaning of the covenant sign of the rainbow after the Flood?",
    ),
    BenchmarkQuestion(
        id="theo-030",
        category="theological",
        question="How do dispensationalist and covenant theologians differ on the relationship between Israel and the Church?",
    ),
    # --- 4. Sin and atonement ---
    BenchmarkQuestion(
        id="theo-031",
        category="theological",
        question="What is the theological concept of original sin, and is it universally accepted across Christian traditions?",
    ),
    BenchmarkQuestion(
        id="theo-032",
        category="theological",
        question="How does Judaism understand sin differently from the Christian doctrine of original sin?",
    ),
    BenchmarkQuestion(
        id="theo-033",
        category="theological",
        question="What is the Islamic concept of fitrah and how does it relate to human sinfulness?",
    ),
    BenchmarkQuestion(
        id="theo-034",
        category="theological",
        question="What is the theological function of animal sacrifice in atoning for sin in the Torah?",
    ),
    BenchmarkQuestion(
        id="theo-035",
        category="theological",
        question="How do different Christian traditions understand the atonement accomplished by Christ's death?",
    ),
    BenchmarkQuestion(
        id="theo-036",
        category="theological",
        question="What is the Day of Atonement (Yom Kippur) and its theological purpose?",
    ),
    BenchmarkQuestion(
        id="theo-037",
        category="theological",
        question="Is repentance (teshuvah) sufficient for atonement in Jewish theology without sacrifice?",
    ),
    BenchmarkQuestion(
        id="theo-038",
        category="theological",
        question="What theological distinctions exist between guilt, shame, and sin across these traditions?",
    ),
    BenchmarkQuestion(
        id="theo-039",
        category="theological",
        question="How does the concept of a scapegoat function theologically in Leviticus 16?",
    ),
    BenchmarkQuestion(
        id="theo-040",
        category="theological",
        question="What is the theological relationship between sin and death in Pauline theology?",
    ),
    # --- 5. Salvation / soteriology ---
    BenchmarkQuestion(
        id="theo-041",
        category="theological",
        question="What are the major differences between the doctrines of salvation by faith and salvation by works?",
    ),
    BenchmarkQuestion(
        id="theo-042",
        category="theological",
        question="How does Islam understand salvation in relation to submission (islam) to God's will?",
    ),
    BenchmarkQuestion(
        id="theo-043",
        category="theological",
        question="What is the Jewish theological understanding of the afterlife and reward?",
    ),
    BenchmarkQuestion(
        id="theo-044",
        category="theological",
        question="What is meant by 'justification by faith' in Protestant theology?",
    ),
    BenchmarkQuestion(
        id="theo-045",
        category="theological",
        question="How does Catholic theology understand the role of grace and works together in salvation?",
    ),
    BenchmarkQuestion(
        id="theo-046",
        category="theological",
        question="What is the theological concept of election or predestination, and how is it debated?",
    ),
    BenchmarkQuestion(
        id="theo-047",
        category="theological",
        question="Is universal salvation (apokatastasis) a minority or majority position historically?",
    ),
    BenchmarkQuestion(
        id="theo-048",
        category="theological",
        question="What does the concept of 'being born again' mean theologically?",
    ),
    BenchmarkQuestion(
        id="theo-049",
        category="theological",
        question="How central is the concept of intercession to different views of salvation?",
    ),
    BenchmarkQuestion(
        id="theo-050",
        category="theological",
        question="What theological role does divine mercy play relative to divine justice in salvation?",
    ),
    # --- 6. Messiah / eschatology ---
    BenchmarkQuestion(
        id="theo-051",
        category="theological",
        question="What are the major Jewish expectations for the coming of the Messiah?",
    ),
    BenchmarkQuestion(
        id="theo-052",
        category="theological",
        question="How does the Christian understanding of the Messiah differ from the Jewish expectation?",
    ),
    BenchmarkQuestion(
        id="theo-053",
        category="theological",
        question="What role does Isa (Jesus) play in Islamic eschatology?",
    ),
    BenchmarkQuestion(
        id="theo-054",
        category="theological",
        question="What is the theological significance of the 'Day of the Lord' in prophetic literature?",
    ),
    BenchmarkQuestion(
        id="theo-055",
        category="theological",
        question="What are the differing millennial views (premillennial, amillennial, postmillennial) in Christian eschatology?",
    ),
    BenchmarkQuestion(
        id="theo-056",
        category="theological",
        question="What is the concept of the Mahdi in Islamic eschatology?",
    ),
    BenchmarkQuestion(
        id="theo-057",
        category="theological",
        question="How is bodily resurrection understood theologically across these traditions?",
    ),
    BenchmarkQuestion(
        id="theo-058",
        category="theological",
        question="What is the theological meaning of the phrase 'Kingdom of God'?",
    ),
    BenchmarkQuestion(
        id="theo-059",
        category="theological",
        question="What signs are theologically associated with the end times in apocalyptic literature?",
    ),
    BenchmarkQuestion(
        id="theo-060",
        category="theological",
        question="Is the Messianic age understood as a political restoration or a spiritual transformation?",
    ),
    # --- 7. Angels and spiritual beings ---
    BenchmarkQuestion(
        id="theo-061",
        category="theological",
        question="What is the theological role of angels as messengers in these traditions?",
    ),
    BenchmarkQuestion(
        id="theo-062",
        category="theological",
        question="Who is the angel Gabriel (Jibril) and what is his theological significance across traditions?",
    ),
    BenchmarkQuestion(
        id="theo-063",
        category="theological",
        question="What is the theological status of Satan/Iblis across Jewish, Christian, and Islamic thought?",
    ),
    BenchmarkQuestion(
        id="theo-064",
        category="theological",
        question="Are angels considered to have free will theologically?",
    ),
    BenchmarkQuestion(
        id="theo-065",
        category="theological",
        question="What are cherubim theologically, and what is their function in the Hebrew Bible?",
    ),
    BenchmarkQuestion(
        id="theo-066",
        category="theological",
        question="What is the theological concept of the 'sons of God' in Genesis 6?",
    ),
    BenchmarkQuestion(
        id="theo-067",
        category="theological",
        question="How do jinn function theologically in Islamic cosmology?",
    ),
    BenchmarkQuestion(
        id="theo-068",
        category="theological",
        question="What is the theological distinction between angels and demons?",
    ),
    BenchmarkQuestion(
        id="theo-069",
        category="theological",
        question="What role does the Angel of the LORD play theologically in the Hebrew Bible?",
    ),
    BenchmarkQuestion(
        id="theo-070",
        category="theological",
        question="Is angelic worship or veneration theologically permitted in any of these traditions?",
    ),
    # --- 8. Worship and ritual law ---
    BenchmarkQuestion(
        id="theo-071",
        category="theological",
        question="What is the theological purpose of dietary law (kashrut) in Judaism?",
    ),
    BenchmarkQuestion(
        id="theo-072",
        category="theological",
        question="What is the theological rationale for halal dietary law in Islam?",
    ),
    BenchmarkQuestion(
        id="theo-073",
        category="theological",
        question="What is the theological significance of the Eucharist/Communion in Christian worship?",
    ),
    BenchmarkQuestion(
        id="theo-074",
        category="theological",
        question="What is the theological meaning of the five daily prayers (salat) in Islam?",
    ),
    BenchmarkQuestion(
        id="theo-075",
        category="theological",
        question="What is the theological purpose of the Passover meal (Pesach)?",
    ),
    BenchmarkQuestion(
        id="theo-076",
        category="theological",
        question="What is the theological significance of baptism?",
    ),
    BenchmarkQuestion(
        id="theo-077",
        category="theological",
        question="Why is the Temple central to biblical theology even after its destruction?",
    ),
    BenchmarkQuestion(
        id="theo-078",
        category="theological",
        question="What is the theological purpose of fasting during Ramadan?",
    ),
    BenchmarkQuestion(
        id="theo-079",
        category="theological",
        question="How does theology explain the shift from Temple sacrifice to synagogue prayer in Judaism?",
    ),
    BenchmarkQuestion(
        id="theo-080",
        category="theological",
        question="What is the theological significance of pilgrimage (Hajj) in Islam?",
    ),
    # --- 9. Divine attributes ---
    BenchmarkQuestion(
        id="theo-081",
        category="theological",
        question="How is divine omniscience theologically reconciled with human free will?",
    ),
    BenchmarkQuestion(
        id="theo-082",
        category="theological",
        question="What does divine holiness mean theologically, distinct from moral perfection?",
    ),
    BenchmarkQuestion(
        id="theo-083",
        category="theological",
        question="How is God's justice theologically balanced with God's mercy?",
    ),
    BenchmarkQuestion(
        id="theo-084",
        category="theological",
        question="What does divine immutability mean theologically, and is it debated?",
    ),
    BenchmarkQuestion(
        id="theo-085",
        category="theological",
        question="What is the theological problem of evil, and how is it addressed across traditions?",
    ),
    BenchmarkQuestion(
        id="theo-086",
        category="theological",
        question="What does divine transcendence mean as distinct from divine immanence?",
    ),
    BenchmarkQuestion(
        id="theo-087",
        category="theological",
        question="What is the theological concept of divine simplicity?",
    ),
    BenchmarkQuestion(
        id="theo-088",
        category="theological",
        question="How is God's wrath theologically understood in relation to God's love?",
    ),
    BenchmarkQuestion(
        id="theo-089",
        category="theological",
        question="What does it mean theologically that God is described as jealous?",
    ),
    BenchmarkQuestion(
        id="theo-090",
        category="theological",
        question="Is divine impassibility (that God does not suffer) a shared or contested doctrine?",
    ),
    # --- 10. Comparative doctrine, phrased neutrally ---
    BenchmarkQuestion(
        id="theo-091",
        category="theological",
        question="What are the major interpretive positions on the nature of God's unity across these traditions?",
    ),
    BenchmarkQuestion(
        id="theo-092",
        category="theological",
        question="How do different traditions theologically understand the concept of divine revelation?",
    ),
    BenchmarkQuestion(
        id="theo-093",
        category="theological",
        question="What are the major positions on whether prophecy continues after a closed canon?",
    ),
    BenchmarkQuestion(
        id="theo-094",
        category="theological",
        question="How is the concept of 'chosenness' theologically understood and debated?",
    ),
    BenchmarkQuestion(
        id="theo-095",
        category="theological",
        question="What theological role does free will play across these traditions' understanding of moral responsibility?",
    ),
    BenchmarkQuestion(
        id="theo-096",
        category="theological",
        question="How do these traditions theologically understand the purpose of suffering?",
    ),
    BenchmarkQuestion(
        id="theo-097",
        category="theological",
        question="What are the major theological positions on the relationship between faith and reason?",
    ),
    BenchmarkQuestion(
        id="theo-098",
        category="theological",
        question="How is the concept of sacred text's own authority theologically grounded in each tradition?",
    ),
    BenchmarkQuestion(
        id="theo-099",
        category="theological",
        question="What theological positions exist on whether God can be known directly or only through mediation?",
    ),
    BenchmarkQuestion(
        id="theo-100",
        category="theological",
        question="How do these traditions theologically understand the relationship between law and love?",
    ),
]

assert len(THEOLOGICAL_QUESTIONS) == 100
