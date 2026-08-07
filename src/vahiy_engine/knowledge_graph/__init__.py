"""In-memory Knowledge Graph: Vahiy Engine's Concept/Person/Word node network.

v0.1 scope, deliberately: nodes model concepts, people, and lexical items
(YHWH, Abraham, the root hayah); they do NOT duplicate verse or ayah text as
nodes of their own. Every existing corpus client (AhitCorpusClient,
QuranClient, AhitLexiconClient) already resolves a citation to real text —
duplicating that into graph nodes would mean two sources of truth for the
same verse. Instead, edges carry a `citation` (an OSIS reference, a
Quran surah:ayah, or a Strong's number) as the evidence for a relationship,
resolved on demand through the client that already owns that data.

This is a scoping decision, not the final shape: KM-1's fuller node
taxonomy (Verse/Ayah as first-class nodes, richer edge types) remains the
target once the graph needs verse-level traversal v0.1 doesn't yet need.
"""
