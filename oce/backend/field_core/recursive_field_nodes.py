"""
V3 Phase 9 — Recursive Field Nodes
Field participants with local awareness.
Each node maintains local field state and participates in coherence propagation.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FieldTopology:
    """Topology information for a field node."""
    node_id: str
    parent_id: Optional[str] = None
    children: list[str] = field(default_factory=list)
    depth: int = 0
    is_leaf: bool = True
    is_root: bool = False

    def add_child(self, child_id: str) -> None:
        if child_id not in self.children:
            self.children.append(child_id)
            self.is_leaf = False

    def remove_child(self, child_id: str) -> None:
        if child_id in self.children:
            self.children.remove(child_id)
            self.is_leaf = len(self.children) == 0


@dataclass
class RecursiveFieldNode:
    """A field participant with local awareness."""
    node_id: str
    local_state: dict = field(default_factory=dict)
    coherence: float = 0.5
    active: bool = True
    topology: FieldTopology = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if self.topology is None:
            self.topology = FieldTopology(node_id=self.node_id)

    def update_state(self, key: str, value) -> None:
        self.local_state[key] = value
        self.updated_at = time.time()

    def get_state(self, key: str, default=None):
        return self.local_state.get(key, default)

    def propagate_coherence(self, neighbor_coherence: float, weight: float = 0.3) -> float:
        """Propagate coherence from a neighbor. Returns new coherence."""
        self.coherence = (1 - weight) * self.coherence + weight * neighbor_coherence
        self.updated_at = time.time()
        return self.coherence

    @property
    def is_healthy(self) -> bool:
        return self.active and self.coherence > 0.2

    @property
    def state_size(self) -> int:
        return len(self.local_state)


class FieldNodeRegistry:
    """Registry of all field nodes."""

    def __init__(self):
        self._nodes: dict[str, RecursiveFieldNode] = {}

    def register(self, node_id: str, **kwargs) -> RecursiveFieldNode:
        """Register a new field node."""
        node = RecursiveFieldNode(node_id=node_id, **kwargs)
        self._nodes[node_id] = node
        return node

    def get(self, node_id: str) -> Optional[RecursiveFieldNode]:
        return self._nodes.get(node_id)

    def remove(self, node_id: str) -> bool:
        if node_id in self._nodes:
            del self._nodes[node_id]
            return True
        return False

    def get_active_nodes(self) -> list[RecursiveFieldNode]:
        return [n for n in self._nodes.values() if n.active]

    def get_healthy_nodes(self) -> list[RecursiveFieldNode]:
        return [n for n in self._nodes.values() if n.is_healthy]

    def propagate_all(self, weight: float = 0.3) -> int:
        """Propagate coherence across all connected nodes. Returns count updated."""
        updated = 0
        for node in self._nodes.values():
            if not node.active:
                continue
            for child_id in node.topology.children:
                child = self._nodes.get(child_id)
                if child and child.active:
                    child.propagate_coherence(node.coherence, weight)
                    updated += 1
        return updated

    @property
    def stats(self) -> dict:
        active = sum(1 for n in self._nodes.values() if n.active)
        healthy = sum(1 for n in self._nodes.values() if n.is_healthy)
        avg_coherence = (
            sum(n.coherence for n in self._nodes.values()) / len(self._nodes)
            if self._nodes else 0.0
        )
        return {
            "total_nodes": len(self._nodes),
            "active_nodes": active,
            "healthy_nodes": healthy,
            "avg_coherence": round(avg_coherence, 4),
        }
