"""
V3 Phase 2 — Causal Geometry Engine
Tracks influence relationships, continuity lineage, and synchronization ancestry.

NOT just chronology — tracks WHY state changes propagate, not just WHEN.
Without causal geometry: memory = dead archives.
With causal geometry: memory = recoverable dynamics.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CausalEdge:
    """
    Represents a causal relationship between two states.
    
    Causal edges track:
    - Which state influenced which (source -> target)
    - How strong the influence is (influence_weight)
    - How much continuity is preserved (continuity_strength)
    - How much entropy changed (entropy_delta)
    """
    source_state: str
    target_state: str
    influence_weight: float = 0.5       # 0.0-1.0, strength of causal link
    continuity_strength: float = 0.5    # 0.0-1.0, how much continuity preserved
    entropy_delta: float = 0.0          # Entropy change across this edge
    edge_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def is_strong(self) -> bool:
        """A strong causal edge has high influence and continuity."""
        return self.influence_weight > 0.7 and self.continuity_strength > 0.7

    @property
    def is_entropic(self) -> bool:
        """An entropic edge increases entropy significantly."""
        return self.entropy_delta > 0.5

    def to_dict(self) -> dict:
        return {
            "edge_id": self.edge_id,
            "source_state": self.source_state,
            "target_state": self.target_state,
            "influence_weight": round(self.influence_weight, 4),
            "continuity_strength": round(self.continuity_strength, 4),
            "entropy_delta": round(self.entropy_delta, 4),
            "timestamp": self.timestamp,
            "tags": self.tags,
            "is_strong": self.is_strong,
        }


@dataclass
class ContinuityLineage:
    """
    Tracks the lineage of continuity for a given state.
    
    A lineage is a chain of causal edges showing how a state
    evolved from previous states. This enables reconstruction
    of any state from its ancestors.
    """
    state_id: str
    ancestor_ids: list[str] = field(default_factory=list)
    edge_ids: list[str] = field(default_factory=list)
    depth: int = 0
    total_continuity: float = 1.0  # Product of continuity_strength along chain
    created_at: float = field(default_factory=time.time)

    def add_ancestor(self, ancestor_id: str, edge: CausalEdge) -> None:
        """Add an ancestor state and the causal edge connecting them."""
        self.ancestor_ids.append(ancestor_id)
        self.edge_ids.append(edge.edge_id)
        self.depth += 1
        self.total_continuity *= edge.continuity_strength

    @property
    def is_intact(self) -> bool:
        """Lineage is intact if total continuity > 0.3."""
        return self.total_continuity > 0.3

    def to_dict(self) -> dict:
        return {
            "state_id": self.state_id,
            "ancestor_count": len(self.ancestor_ids),
            "depth": self.depth,
            "total_continuity": round(self.total_continuity, 4),
            "is_intact": self.is_intact,
        }


class CausalGeometryEngine:
    """
    Manages the causal graph of the cognitive field.
    
    Tracks:
    - Causal edges between states
    - Continuity lineages
    - Influence propagation paths
    - Entropy flow through the graph
    """

    def __init__(self, max_edges: int = 50000, max_lineages: int = 10000):
        self.edges: dict[str, CausalEdge] = {}
        self.lineages: dict[str, ContinuityLineage] = {}
        self._state_edges: dict[str, list[str]] = {}  # state_id -> [edge_ids]
        self.max_edges = max_edges
        self.max_lineages = max_lineages

    def add_edge(self, edge: CausalEdge) -> str:
        """Add a causal edge to the geometry."""
        self.edges[edge.edge_id] = edge
        
        # Index by source and target
        for state_id in [edge.source_state, edge.target_state]:
            if state_id not in self._state_edges:
                self._state_edges[state_id] = []
            self._state_edges[state_id].append(edge.edge_id)
        
        # Update lineage for target state
        if edge.target_state not in self.lineages:
            self.lineages[edge.target_state] = ContinuityLineage(state_id=edge.target_state)
        self.lineages[edge.target_state].add_ancestor(edge.source_state, edge)
        
        # Evict old edges if over capacity
        if len(self.edges) > self.max_edges:
            self._evict_oldest(keep=self.max_edges * 8 // 10)
        
        return edge.edge_id

    def create_edge(
        self, source_state: str, target_state: str,
        influence_weight: float = 0.5, continuity_strength: float = 0.5,
        entropy_delta: float = 0.0, tags: list[str] = None,
    ) -> CausalEdge:
        """Create and add a causal edge."""
        edge = CausalEdge(
            source_state=source_state,
            target_state=target_state,
            influence_weight=influence_weight,
            continuity_strength=continuity_strength,
            entropy_delta=entropy_delta,
            tags=tags or [],
        )
        self.add_edge(edge)
        return edge

    def get_lineage(self, state_id: str) -> Optional[ContinuityLineage]:
        """Get the continuity lineage for a state."""
        return self.lineages.get(state_id)

    def get_edges_from(self, state_id: str) -> list[CausalEdge]:
        """Get all causal edges originating from a state."""
        edge_ids = self._state_edges.get(state_id, [])
        return [self.edges[eid] for eid in edge_ids if eid in self.edges]

    def get_edges_to(self, state_id: str) -> list[CausalEdge]:
        """Get all causal edges targeting a state."""
        edge_ids = self._state_edges.get(state_id, [])
        return [self.edges[eid] for eid in edge_ids if eid in self.edges and self.edges[eid].target_state == state_id]

    def get_strongest_path(self, source: str, target: str) -> list[CausalEdge]:
        """
        Find the strongest causal path from source to target.
        Uses modified Dijkstra where edge weight = 1 / influence_weight.
        """
        if source not in self._state_edges or target not in self._state_edges:
            return []

        # Simple BFS with priority on influence weight
        import heapq
        visited = set()
        # (negative_weight, current_node, path)
        heap = [(-1.0, source, [])]

        while heap:
            neg_weight, current, path = heapq.heappop(heap)
            if current in visited:
                continue
            visited.add(current)

            if current == target:
                return path

            for edge in self.get_edges_from(current):
                if edge.target_state not in visited:
                    new_weight = neg_weight * edge.influence_weight
                    heapq.heappush(heap, (new_weight, edge.target_state, path + [edge]))

        return []

    def get_influence_score(self, state_id: str) -> float:
        """
        Calculate how much influence a state has on the field.
        = sum of influence_weights of all outgoing edges.
        """
        edges = self.get_edges_from(state_id)
        if not edges:
            return 0.0
        return min(1.0, sum(e.influence_weight for e in edges) / max(len(edges), 1))

    def get_continuity_score(self, state_id: str) -> float:
        """
        Calculate how well a state preserves continuity.
        Based on its lineage's total_continuity.
        """
        lineage = self.lineages.get(state_id)
        if not lineage:
            return 0.5  # Unknown state = neutral
        return lineage.total_continuity

    def get_ancestor_chain(self, state_id: str, max_depth: int = 10) -> list[str]:
        """Get the chain of ancestor states up to max_depth."""
        chain = []
        current = state_id
        for _ in range(max_depth):
            lineage = self.lineages.get(current)
            if not lineage or not lineage.ancestor_ids:
                break
            parent = lineage.ancestor_ids[-1]  # Most recent ancestor
            chain.append(parent)
            current = parent
        return chain

    def _evict_oldest(self, keep: int) -> None:
        """Evict oldest edges to stay under capacity."""
        if len(self.edges) <= keep:
            return
        sorted_edges = sorted(self.edges.values(), key=lambda e: e.timestamp)
        to_remove = sorted_edges[:len(self.edges) - keep]
        for edge in to_remove:
            del self.edges[edge.edge_id]
            for state_id in [edge.source_state, edge.target_state]:
                if state_id in self._state_edges:
                    self._state_edges[state_id] = [
                        eid for eid in self._state_edges[state_id] if eid != edge.edge_id
                    ]

    @property
    def stats(self) -> dict:
        """Causal geometry statistics."""
        intact = sum(1 for l in self.lineages.values() if l.is_intact)
        return {
            "total_edges": len(self.edges),
            "total_lineages": len(self.lineages),
            "intact_lineages": intact,
            "broken_lineages": len(self.lineages) - intact,
            "avg_depth": sum(l.depth for l in self.lineages.values()) / max(len(self.lineages), 1),
        }

    def __repr__(self) -> str:
        return f"CausalGeometry(edges={len(self.edges)}, lineages={len(self.lineages)})"
