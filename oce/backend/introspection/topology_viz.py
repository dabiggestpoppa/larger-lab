"""
V3 Phase 6 — Topology Visualization
Generates live topology maps of the cognitive field.

Produces data structures that can be rendered as visual graphs
showing observer connections, cluster health, and field structure.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional

from topology.collar_field import CollarFieldEngine


@dataclass
class TopologyMap:
    """A visualizable topology map."""
    map_id: str
    timestamp: float
    nodes: list[dict] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)
    clusters: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "map_id": self.map_id,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "clusters": len(self.clusters),
        }


class TopologyVisualization:
    """
    Generates live topology maps of the cognitive field.
    
    Produces data structures for visualizing:
    - Observer nodes (sized by health)
    - Connection edges (weighted by resonance)
    - Cluster groupings (colored by coherence)
    - Field boundaries (showing scope)
    """

    def __init__(self, collar_engine: CollarFieldEngine = None):
        self.collar_engine = collar_engine or CollarFieldEngine()

    def generate_map(self) -> TopologyMap:
        """Generate a topology map of the current field."""
        collars = self.collar_engine.collars

        nodes = []
        edges = []
        clusters = []

        # Generate nodes from observers
        for obs_id, collar in collars.items():
            nodes.append({
                "id": obs_id,
                "health": round(collar.avg_resonance, 4),
                "connections": collar.connection_count,
                "type": "observer",
            })

        # Generate edges from resonance map
        seen_edges = set()
        for obs_id, collar in collars.items():
            for target_id, resonance in collar.resonance_map.items():
                edge_key = tuple(sorted([obs_id, target_id]))
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges.append({
                        "source": obs_id,
                        "target": target_id,
                        "weight": round(resonance, 4),
                        "type": "strong" if resonance > 0.6 else "weak",
                    })

        # Simple clustering: group observers with strong mutual resonance
        clustered = set()
        for obs_id, collar in collars.items():
            if obs_id in clustered:
                continue
            cluster_members = [obs_id]
            for target_id, resonance in collar.resonance_map.items():
                if resonance > 0.7 and target_id not in clustered:
                    cluster_members.append(target_id)
                    clustered.add(target_id)
            if len(cluster_members) > 1:
                clusters.append({
                    "members": cluster_members,
                    "coherence": round(collar.avg_resonance, 4),
                })
            clustered.add(obs_id)

        return TopologyMap(
            map_id=f"map_{int(time.time())}",
            timestamp=time.time(),
            nodes=nodes,
            edges=edges,
            clusters=clusters,
        )

    def get_field_summary(self) -> dict:
        """Get a summary of the field's visual topology."""
        map_data = self.generate_map()
        return {
            "observers": len(map_data.nodes),
            "connections": len(map_data.edges),
            "clusters": len(map_data.clusters),
            "strong_connections": sum(1 for e in map_data.edges if e["type"] == "strong"),
            "weak_connections": sum(1 for e in map_data.edges if e["type"] == "weak"),
        }

    @property
    def stats(self) -> dict:
        return self.get_field_summary()
