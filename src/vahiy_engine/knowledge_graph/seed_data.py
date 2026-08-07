"""Seed data for v0.1's three validation concepts: YHWH, Sabbath, Abraham.

Every citation below was individually resolved against a real ahit-corpus
clone before being written here — Exod.3.14, Gen.2.3, Exod.20.8, Exod.31.13,
Isa.58.13 against WLC; Heb.4.9, Rom.10.13 against SBLGNT; Gen.12.1, Gen.17.5,
Gen.22.2 against WLC; Quran.14.35, Quran.2.124, Quran.21.51 against the real
Qur'an corpus; H3068, H1961, G2962 against the real Strong's lexicons. None
of this is illustrative or invented — it is deliberately small and populated
only where a citation is real and checked, per `ID-5`'s no-fabrication rule.

Two things are conspicuously absent from Abraham's node, and that absence is
itself the point: Hadith and Tafsir citations. ahit-corpus has no Hadith or
Tafsir corpus ingested as of this phase, so none are cited — a KG-instructed
GRAND claim about "Abraham in Hadith tradition" without a real, resolvable
source would be exactly the invented-attribution failure `ID-5` and `FND-4`
exist to prevent. When that corpus exists, this seed data grows to cite it;
until then, the gap is disclosed, not papered over.
"""

from vahiy_engine.knowledge_graph.graph import KnowledgeGraph
from vahiy_engine.knowledge_graph.models import Edge, Node


def build_seed_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()

    # --- Supporting word nodes ---

    graph.add_node(Node(id="hayah", type="word", labels={"en": "to be, become", "he": "הָיָה"}))
    graph.add_edge(
        Edge(
            source_id="hayah",
            type="attributed_to",
            citation="Strong:H1961",
            citation_type="strongs",
        )
    )

    graph.add_node(Node(id="kyrios", type="word", labels={"en": "Lord", "grc": "κύριος"}))
    graph.add_edge(
        Edge(
            source_id="kyrios",
            type="attributed_to",
            citation="Strong:G2962",
            citation_type="strongs",
        )
    )

    # --- YHWH ---

    graph.add_node(
        Node(
            id="yhwh",
            type="concept",
            labels={"en": "YHWH", "he": "יהוה", "tr": "YHWH"},
            notes="The Tetragrammaton, the proper name of God in the Hebrew Bible.",
        )
    )
    graph.add_edge(
        Edge(
            source_id="yhwh",
            type="explains",
            citation="Exod.3.14",
            citation_type="osis",
            note="The name's own scriptural self-disclosure to Moses ('I AM THAT I AM').",
        )
    )
    graph.add_edge(
        Edge(
            source_id="yhwh",
            type="derives_from",
            target_id="hayah",
            citation="Exod.3.14",
            citation_type="osis",
            note="Traditionally connected to the Hebrew verb 'to be'.",
        )
    )
    graph.add_edge(
        Edge(
            source_id="yhwh", type="attributed_to", citation="Strong:H3068", citation_type="strongs"
        )
    )
    graph.add_edge(
        Edge(
            source_id="yhwh",
            type="translates_to",
            target_id="kyrios",
            citation="Rom.10.13",
            citation_type="osis",
            note=(
                "The New Testament applies kyrios ('Lord') from Joel 2:32 (a YHWH "
                "passage) to Jesus in this verse — a translation/typological "
                "correspondence, not a claim this graph adjudicates theologically."
            ),
        )
    )

    # --- Sabbath / Şabat ---

    graph.add_node(
        Node(
            id="sabbath",
            type="concept",
            labels={"en": "Sabbath", "he": "שַׁבָּת", "tr": "Şabat"},
        )
    )
    graph.add_edge(
        Edge(
            source_id="sabbath",
            type="explains",
            citation="Gen.2.3",
            citation_type="osis",
            note="Establishment: God blesses and sanctifies the seventh day at creation.",
        )
    )
    graph.add_edge(
        Edge(
            source_id="sabbath",
            type="explains",
            citation="Exod.20.8",
            citation_type="osis",
            note="Commandment: 'Remember the sabbath day, to keep it holy.'",
        )
    )
    graph.add_edge(
        Edge(
            source_id="sabbath",
            type="explains",
            citation="Exod.31.13",
            citation_type="osis",
            note="Sign of the covenant between YHWH and Israel.",
        )
    )
    graph.add_edge(
        Edge(
            source_id="sabbath",
            type="explains",
            citation="Isa.58.13",
            citation_type="osis",
            note="Prophetic exhortation: the sabbath as delight, not burden.",
        )
    )
    graph.add_edge(
        Edge(
            source_id="sabbath",
            type="cross_references",
            citation="Heb.4.9",
            citation_type="osis",
            note="New Testament rest typology: 'a sabbath rest remains for the people of God.'",
        )
    )

    # --- Abraham / İbrahim ---

    graph.add_node(
        Node(
            id="abraham",
            type="person",
            labels={
                "en": "Abraham",
                "he": "אַבְרָהָם",
                "ar": "إبراهيم",
                "tr": "İbrahim",
            },
        )
    )
    graph.add_edge(
        Edge(
            source_id="abraham",
            type="cross_references",
            citation="Gen.12.1",
            citation_type="osis",
            note="The call: 'Get thee out of thy country... unto a land that I will shew thee.'",
        )
    )
    graph.add_edge(
        Edge(
            source_id="abraham",
            type="cross_references",
            citation="Gen.17.5",
            citation_type="osis",
            note="Renaming from Abram to Abraham.",
        )
    )
    graph.add_edge(
        Edge(
            source_id="abraham",
            type="cross_references",
            citation="Gen.22.2",
            citation_type="osis",
            note="The binding of Isaac.",
        )
    )
    graph.add_edge(
        Edge(
            source_id="abraham",
            type="cross_references",
            citation="Quran.14.35",
            citation_type="quran",
            note="Ibrahim's prayer for the security of Mecca and for his descendants.",
        )
    )
    graph.add_edge(
        Edge(
            source_id="abraham",
            type="cross_references",
            citation="Quran.2.124",
            citation_type="quran",
            note="Ibrahim tried by his Lord's commands; the covenant.",
        )
    )
    graph.add_edge(
        Edge(
            source_id="abraham",
            type="cross_references",
            citation="Quran.21.51",
            citation_type="quran",
            note="The idol-breaking narrative.",
        )
    )

    return graph
