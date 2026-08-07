"""100 historical questions, organized into ten sub-themes of ten.

Gold cases are limited to Abraham's historical narrative, since that's the
person-node the Knowledge Graph actually covers.
"""

from tests.benchmark.question_bank.schema import BenchmarkQuestion
from vahiy_engine.reasoning.trace import ConfidenceTier

HISTORICAL_QUESTIONS: list[BenchmarkQuestion] = [
    # --- 1. Abraham's historical narrative (gold) ---
    BenchmarkQuestion(
        id="hist-001",
        category="historical",
        question="What does Genesis record about Abraham's call to leave his homeland?",
        coverage_status="gold",
        expected_node_id="abraham",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Gen.12.1",),
    ),
    BenchmarkQuestion(
        id="hist-002",
        category="historical",
        question="When and why was Abram's name changed to Abraham?",
        coverage_status="gold",
        expected_node_id="abraham",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Gen.17.5",),
    ),
    BenchmarkQuestion(
        id="hist-003",
        category="historical",
        question="What does the narrative of the binding of Isaac record?",
        coverage_status="gold",
        expected_node_id="abraham",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Gen.22.2",),
    ),
    BenchmarkQuestion(
        id="hist-004",
        category="historical",
        question="İbrahim'in tarihte çağrılması hakkında Tekvin ne kaydeder?",
        language="tr",
        coverage_status="gold",
        expected_node_id="abraham",
        expected_min_confidence=ConfidenceTier.HIGH,
        expected_evidence_citations=("Gen.12.1",),
    ),
    BenchmarkQuestion(
        id="hist-005",
        category="historical",
        question="What archaeological evidence, if any, bears on the historicity of the patriarchal narratives?",
    ),
    BenchmarkQuestion(
        id="hist-006",
        category="historical",
        question="What was the historical and geographic setting of Ur of the Chaldees?",
    ),
    BenchmarkQuestion(
        id="hist-007",
        category="historical",
        question="What is the estimated historical period traditionally assigned to Abraham?",
    ),
    BenchmarkQuestion(
        id="hist-008",
        category="historical",
        question="What historical customs of the ancient Near East illuminate the covenant-making practices in Genesis?",
    ),
    BenchmarkQuestion(
        id="hist-009",
        category="historical",
        question="How do Nuzi tablets inform historical scholarship on patriarchal-era social customs?",
    ),
    BenchmarkQuestion(
        id="hist-010",
        category="historical",
        question="What is the historical relationship between Haran and Abraham's migration route?",
    ),
    # --- 2. Exodus dating and archaeology ---
    BenchmarkQuestion(
        id="hist-011",
        category="historical",
        question="What are the two major scholarly positions on the date of the Exodus?",
    ),
    BenchmarkQuestion(
        id="hist-012",
        category="historical",
        question="What archaeological evidence exists, or is debated, for the Exodus narrative?",
    ),
    BenchmarkQuestion(
        id="hist-013",
        category="historical",
        question="Who was the historical pharaoh most commonly associated with the Exodus narrative?",
    ),
    BenchmarkQuestion(
        id="hist-014",
        category="historical",
        question="What is the Merneptah Stele and why is it historically significant to Exodus studies?",
    ),
    BenchmarkQuestion(
        id="hist-015",
        category="historical",
        question="What historical route theories exist for the wilderness wandering?",
    ),
    BenchmarkQuestion(
        id="hist-016",
        category="historical",
        question="What is the historical population estimate debate surrounding the Exodus numbers?",
    ),
    BenchmarkQuestion(
        id="hist-017",
        category="historical",
        question="How does Egyptian historical record (or silence) bear on the Exodus account?",
    ),
    BenchmarkQuestion(
        id="hist-018",
        category="historical",
        question="What is the historical significance of the Ipuwer Papyrus in Exodus debates?",
    ),
    BenchmarkQuestion(
        id="hist-019",
        category="historical",
        question="What historical evidence exists for Semitic presence in Egypt during the second millennium BCE?",
    ),
    BenchmarkQuestion(
        id="hist-020",
        category="historical",
        question="How is Mount Sinai's historical/geographic location debated among scholars?",
    ),
    # --- 3. Second Temple period ---
    BenchmarkQuestion(
        id="hist-021",
        category="historical",
        question="What historical events led to the Second Temple's construction?",
    ),
    BenchmarkQuestion(
        id="hist-022",
        category="historical",
        question="Who were the major Jewish sects of the Second Temple period?",
    ),
    BenchmarkQuestion(
        id="hist-023",
        category="historical",
        question="What was the historical significance of the Maccabean revolt?",
    ),
    BenchmarkQuestion(
        id="hist-024",
        category="historical",
        question="How did Hellenistic culture historically influence Second Temple Judaism?",
    ),
    BenchmarkQuestion(
        id="hist-025",
        category="historical",
        question="What is the historical origin of the Sanhedrin?",
    ),
    BenchmarkQuestion(
        id="hist-026",
        category="historical",
        question="What historical role did the Herodian dynasty play in Second Temple Judea?",
    ),
    BenchmarkQuestion(
        id="hist-027",
        category="historical",
        question="What is the historical significance of the Qumran community?",
    ),
    BenchmarkQuestion(
        id="hist-028",
        category="historical",
        question="How did Roman rule historically shape religious life in first-century Judea?",
    ),
    BenchmarkQuestion(
        id="hist-029",
        category="historical",
        question="What historical events led to the Temple's destruction in 70 CE?",
    ),
    BenchmarkQuestion(
        id="hist-030",
        category="historical",
        question="What is the historical significance of the Bar Kokhba revolt?",
    ),
    # --- 4. Canon formation history ---
    BenchmarkQuestion(
        id="hist-031",
        category="historical",
        question="What is the historical process by which the Hebrew Bible's canon was formed?",
    ),
    BenchmarkQuestion(
        id="hist-032",
        category="historical",
        question="What historical councils are associated with New Testament canon formation?",
    ),
    BenchmarkQuestion(
        id="hist-033",
        category="historical",
        question="What is the historical status of the Apocrypha in different canonical traditions?",
    ),
    BenchmarkQuestion(
        id="hist-034",
        category="historical",
        question="What is the historical process of the Quran's compilation under Uthman?",
    ),
    BenchmarkQuestion(
        id="hist-035",
        category="historical",
        question="What historical criteria were used to determine New Testament canonicity?",
    ),
    BenchmarkQuestion(
        id="hist-036",
        category="historical",
        question="What is the historical relationship between the Septuagint and the Hebrew canon?",
    ),
    BenchmarkQuestion(
        id="hist-037",
        category="historical",
        question="What is the historical timeline of Hadith collection and compilation?",
    ),
    BenchmarkQuestion(
        id="hist-038",
        category="historical",
        question="What historical debates surrounded the inclusion of the book of Esther in the canon?",
    ),
    BenchmarkQuestion(
        id="hist-039",
        category="historical",
        question="What is the historical origin of the Masoretic textual tradition?",
    ),
    BenchmarkQuestion(
        id="hist-040",
        category="historical",
        question="What historical role did the Council of Jamnia play, if any, in Jewish canon formation?",
    ),
    # --- 5. Manuscript history / textual transmission ---
    BenchmarkQuestion(
        id="hist-041",
        category="historical",
        question="What is the historical significance of the Dead Sea Scrolls for biblical textual criticism?",
    ),
    BenchmarkQuestion(
        id="hist-042",
        category="historical",
        question="What is the historical dating of the earliest complete Hebrew Bible manuscripts?",
    ),
    BenchmarkQuestion(
        id="hist-043",
        category="historical",
        question="What is the historical significance of Codex Sinaiticus?",
    ),
    BenchmarkQuestion(
        id="hist-044",
        category="historical",
        question="How did historical scribal practices affect textual transmission of the Hebrew Bible?",
    ),
    BenchmarkQuestion(
        id="hist-045",
        category="historical",
        question="What is the historical relationship between the Samaritan Pentateuch and the Masoretic Text?",
    ),
    BenchmarkQuestion(
        id="hist-046",
        category="historical",
        question="What historical evidence exists for the earliest Quranic manuscripts (e.g. the Sanaa manuscript)?",
    ),
    BenchmarkQuestion(
        id="hist-047",
        category="historical",
        question="What is the historical process of vocalization (niqqud) added to the Hebrew text?",
    ),
    BenchmarkQuestion(
        id="hist-048",
        category="historical",
        question="What historical factors explain New Testament textual variants across manuscript families?",
    ),
    BenchmarkQuestion(
        id="hist-049",
        category="historical",
        question="What is the historical origin of the Peshitta translation?",
    ),
    BenchmarkQuestion(
        id="hist-050",
        category="historical",
        question="What historical printing milestones shaped the standardized Hebrew and Greek texts used today?",
    ),
    # --- 6. Early Islamic history ---
    BenchmarkQuestion(
        id="hist-051",
        category="historical",
        question="What is the historical context of the Meccan period of Quranic revelation?",
    ),
    BenchmarkQuestion(
        id="hist-052",
        category="historical",
        question="What is the historical significance of the Hijra?",
    ),
    BenchmarkQuestion(
        id="hist-053",
        category="historical",
        question="What historical events characterize the early Rashidun Caliphate?",
    ),
    BenchmarkQuestion(
        id="hist-054",
        category="historical",
        question="What is the historical background of the split between Sunni and Shia traditions?",
    ),
    BenchmarkQuestion(
        id="hist-055",
        category="historical",
        question="What was the historical significance of the Constitution of Medina?",
    ),
    BenchmarkQuestion(
        id="hist-056",
        category="historical",
        question="What historical relationship existed between early Muslim communities and Jewish tribes in Medina?",
    ),
    BenchmarkQuestion(
        id="hist-057",
        category="historical",
        question="What is the historical significance of the conquest of Mecca?",
    ),
    BenchmarkQuestion(
        id="hist-058",
        category="historical",
        question="What historical factors shaped the early Islamic expansion outside Arabia?",
    ),
    BenchmarkQuestion(
        id="hist-059",
        category="historical",
        question="What is the historical role of the Umayyad dynasty in early Islamic history?",
    ),
    BenchmarkQuestion(
        id="hist-060",
        category="historical",
        question="What historical sources exist for reconstructing pre-Islamic Arabian religious practice?",
    ),
    # --- 7. Church history / councils ---
    BenchmarkQuestion(
        id="hist-061",
        category="historical",
        question="What historical debates led to the Council of Nicaea?",
    ),
    BenchmarkQuestion(
        id="hist-062",
        category="historical",
        question="What is the historical significance of the Council of Chalcedon?",
    ),
    BenchmarkQuestion(
        id="hist-063",
        category="historical",
        question="What historical events led to the Great Schism between Eastern and Western Christianity?",
    ),
    BenchmarkQuestion(
        id="hist-064",
        category="historical",
        question="What is the historical background of the Protestant Reformation?",
    ),
    BenchmarkQuestion(
        id="hist-065",
        category="historical",
        question="What historical role did Constantine play in Christianity's institutional development?",
    ),
    BenchmarkQuestion(
        id="hist-066",
        category="historical",
        question="What is the historical origin of monasticism in early Christianity?",
    ),
    BenchmarkQuestion(
        id="hist-067",
        category="historical",
        question="What historical factors led to the persecution of early Christians under Rome?",
    ),
    BenchmarkQuestion(
        id="hist-068",
        category="historical",
        question="What is the historical significance of the Edict of Milan?",
    ),
    BenchmarkQuestion(
        id="hist-069",
        category="historical",
        question="What historical developments shaped the early papacy?",
    ),
    BenchmarkQuestion(
        id="hist-070",
        category="historical",
        question="What is the historical background of the Council of Jerusalem in Acts 15?",
    ),
    # --- 8. Ancient Near Eastern context ---
    BenchmarkQuestion(
        id="hist-071",
        category="historical",
        question="What historical parallels exist between the Code of Hammurabi and biblical law?",
    ),
    BenchmarkQuestion(
        id="hist-072",
        category="historical",
        question="What is the historical relationship between the Epic of Gilgamesh and the biblical flood narrative?",
    ),
    BenchmarkQuestion(
        id="hist-073",
        category="historical",
        question="What historical role did the Canaanite pantheon play in the religious environment surrounding early Israel?",
    ),
    BenchmarkQuestion(
        id="hist-074",
        category="historical",
        question="What is the historical significance of the Amarna letters for understanding Canaan before the Israelite settlement?",
    ),
    BenchmarkQuestion(
        id="hist-075",
        category="historical",
        question="What historical evidence exists for the united monarchy under David and Solomon?",
    ),
    BenchmarkQuestion(
        id="hist-076",
        category="historical",
        question="What is the historical significance of the Tel Dan Stele?",
    ),
    BenchmarkQuestion(
        id="hist-077",
        category="historical",
        question="What historical context surrounds the Assyrian conquest of the northern kingdom of Israel?",
    ),
    BenchmarkQuestion(
        id="hist-078",
        category="historical",
        question="What is the historical background of the Babylonian exile?",
    ),
    BenchmarkQuestion(
        id="hist-079",
        category="historical",
        question="What historical role did the Cyrus Cylinder play in the return from exile?",
    ),
    BenchmarkQuestion(
        id="hist-080",
        category="historical",
        question="What historical evidence exists for the Philistines as a distinct Iron Age people group?",
    ),
    # --- 9. Historical figures ---
    BenchmarkQuestion(
        id="hist-081",
        category="historical",
        question="What historical evidence, if any, exists outside scripture for Moses as a historical figure?",
    ),
    BenchmarkQuestion(
        id="hist-082",
        category="historical",
        question="What is the historical scholarly debate over the united versus divided kingdom under David?",
    ),
    BenchmarkQuestion(
        id="hist-083",
        category="historical",
        question="What historical sources describe Solomon's reign beyond the biblical account?",
    ),
    BenchmarkQuestion(
        id="hist-084",
        category="historical",
        question="What is the historical background of Paul's life prior to his conversion?",
    ),
    BenchmarkQuestion(
        id="hist-085",
        category="historical",
        question="What historical Roman administrative context shaped Pontius Pilate's governorship?",
    ),
    BenchmarkQuestion(
        id="hist-086",
        category="historical",
        question="What is the historical evidence for John the Baptist outside the New Testament?",
    ),
    BenchmarkQuestion(
        id="hist-087",
        category="historical",
        question="What historical sources exist for Herod the Great's reign?",
    ),
    BenchmarkQuestion(
        id="hist-088",
        category="historical",
        question="What is the historical relationship between Josephus's writings and New Testament history?",
    ),
    BenchmarkQuestion(
        id="hist-089",
        category="historical",
        question="What historical context surrounds the life of the prophet Jeremiah?",
    ),
    BenchmarkQuestion(
        id="hist-090",
        category="historical",
        question="What is the historical background of Ezra and Nehemiah's reforms?",
    ),
    # --- 10. Archaeological corroboration ---
    BenchmarkQuestion(
        id="hist-091",
        category="historical",
        question="What archaeological findings corroborate the existence of the Hittite civilization mentioned in the Bible?",
    ),
    BenchmarkQuestion(
        id="hist-092",
        category="historical",
        question="What archaeological evidence exists for the historical city of Jericho's destruction layers?",
    ),
    BenchmarkQuestion(
        id="hist-093",
        category="historical",
        question="What is the archaeological status of the search for Noah's Ark?",
    ),
    BenchmarkQuestion(
        id="hist-094",
        category="historical",
        question="What archaeological evidence bears on the historical existence of Nazareth in the first century?",
    ),
    BenchmarkQuestion(
        id="hist-095",
        category="historical",
        question="What is the archaeological evidence for the pool of Siloam mentioned in the Gospel of John?",
    ),
    BenchmarkQuestion(
        id="hist-096",
        category="historical",
        question="What archaeological findings relate to the historical city of Petra and the Nabateans?",
    ),
    BenchmarkQuestion(
        id="hist-097",
        category="historical",
        question="What is the archaeological evidence for ancient Ebla and its relevance to biblical studies?",
    ),
    BenchmarkQuestion(
        id="hist-098",
        category="historical",
        question="What archaeological evidence exists for the historical synagogue at Capernaum?",
    ),
    BenchmarkQuestion(
        id="hist-099",
        category="historical",
        question="What is the archaeological status of the City of David excavations in Jerusalem?",
    ),
    BenchmarkQuestion(
        id="hist-100",
        category="historical",
        question="What archaeological evidence bears on the historical accuracy of the census under Quirinius mentioned in Luke?",
    ),
]

assert len(HISTORICAL_QUESTIONS) == 100
