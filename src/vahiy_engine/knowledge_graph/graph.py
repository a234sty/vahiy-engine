"""In-memory Knowledge Graph store.

No external graph database: consistent with the rest of this codebase (search
is in-memory keyword matching, not a vector store), and right-sized for a
v0.1 prototype's node count. Revisit only if scale actually demands it.
"""

from vahiy_engine.knowledge_graph.models import Edge, Node
from vahiy_engine.search.index import normalize


class NodeNotFoundError(LookupError):
    """Raised when a requested node id isn't registered on this graph."""


class KnowledgeGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []

    def add_node(self, node: Node) -> None:
        if node.id in self._nodes:
            raise ValueError(f"Node '{node.id}' is already registered")
        self._nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        for node_id in (edge.source_id, edge.target_id):
            if node_id is not None and node_id not in self._nodes:
                raise ValueError(f"Edge references unknown node '{node_id}'")
        self._edges.append(edge)

    def get_node(self, node_id: str) -> Node:
        try:
            return self._nodes[node_id]
        except KeyError as exc:
            raise NodeNotFoundError(f"Node '{node_id}' not found") from exc

    def edges_from(self, node_id: str, type: str | None = None) -> list[Edge]:
        return [
            edge
            for edge in self._edges
            if edge.source_id == node_id and (type is None or edge.type == type)
        ]

    def nodes_by_type(self, type: str) -> list[Node]:
        return [node for node in self._nodes.values() if node.type == type]

    def find_by_label(self, label: str) -> list[Node]:
        """Find every node with a label matching `label` in any language, case-insensitively.

        This is how a user's question token (e.g. "YHWH", "Şabat", "İbrahim")
        gets mapped to a graph node. Uses the same `normalize()` search
        already uses for verse text, not bare `.casefold()` — Python's plain
        casefold turns "İ" into "i̇" (i + a combining dot, two characters),
        not plain ASCII "i", so a query already folded by `normalize()`
        (which does apply the Turkish-specific fold) would silently fail to
        match a label compared with bare `.casefold()` instead. Confirmed
        against real data: "İbrahim kimdir?" didn't match the Abraham node
        until both sides went through the same normalization.
        """
        normalized = normalize(label)
        return [
            node
            for node in self._nodes.values()
            if any(normalize(value) == normalized for value in node.labels.values())
        ]
