"""RSN-2's reasoning loop, implemented: intent detection over the Knowledge
Graph, evidence gathering (with rejected evidence tracked, not discarded),
confidence calculation with a visible derivation, and an RSN-5-shaped trace.

v0.1 scope: this loop only handles concept/person questions the Knowledge
Graph actually has a node for (find_by_label matches a question token). It
is additive, not a replacement for pipeline.chat_pipeline's existing
reference/keyword-search handling — a question with no matching KG node
returns no trace, and the caller falls back to the existing pipeline
unchanged.
"""
