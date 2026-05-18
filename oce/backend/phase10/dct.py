"""
Dynamic Constraint Topology (DCT)

Adaptive topology rewiring based on coherence feedback.
The field topology changes as coherence patterns evolve.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import math


class TopologyChange(Enum):
    """Types of topology changes."""
    EDGE_ADDED = "edge_added"
    EDGE_REMOVED = "edge_removed"
    NODE_ADDED = "node_added"
    NODE_REMOVED = "node_removed"
    WEIGHT_UPDATED = "weight_updated"


@dataclass
class ConstraintEdge:
    """An edge in the constraint topology."""
    source: str
    target: str
    weight: float = 1.0
    constraint_type: str = "resonance"
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "weight": self.weight,
            "constraint_type": self.constraint_type,
            "active": self.active
        }


class DynamicConstraintTopology:
    """
    Manages a dynamic topology that rewires based on coherence feedback.
    
    The topology adapts to maintain and enhance coherence flow through
    the field. Edges are added/removed based on resonance patterns.
    """
    
    def __init__(self, name: str = "dct"):
        self.name = name
        self.nodes: Set[str] = set()
        self.edges: Dict[tuple, ConstraintEdge] = {}  # (source, target) -> edge
        self.change_history: List[TopologyChange] = []
        self.coherence_scores: Dict[str, float] = {}
    
    def add_node(self, node_id: str) -> None:
        """Add a node to the topology."""
        if node_id not in self.nodes:
            self.nodes.add(node_id)
            self.coherence_scores[node_id] = 0.0
            self.change_history.append(TopologyChange.NODE_ADDED)
    
    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its edges."""
        if node_id in self.nodes:
            self.nodes.remove(node_id)
            # Remove all edges involving this node
            edges_to_remove = [
                (s, t) for (s, t) in self.edges
                if s == node_id or t == node_id
            ]
            for edge_key in edges_to_remove:
                del self.edges[edge_key]
            self.change_history.append(TopologyChange.NODE_REMOVED)
    
    def add_edge(
        self, 
        source: str, 
        target: str, 
        weight: float = 1.0,
        constraint_type: str = "resonance"
    ) -> None:
        """Add an edge to the topology."""
        if source not in self.nodes:
            self.add_node(source)
        if target not in self.nodes:
            self.add_node(target)
        
        edge_key = (source, target)
        if edge_key not in self.edges:
            self.edges[edge_key] = ConstraintEdge(
                source=source,
                target=target,
                weight=weight,
                constraint_type=constraint_type
            )
            self.change_history.append(TopologyChange.EDGE_ADDED)
    
    def remove_edge(self, source: str, target: str) -> None:
        """Remove an edge from the topology."""
        edge_key = (source, target)
        if edge_key in self.edges:
            del self.edges[edge_key]
            self.change_history.append(TopologyChange.EDGE_REMOVED)
    
    def update_edge_weight(self, source: str, target: str, new_weight: float) -> None:
        """Update the weight of an edge."""
        edge_key = (source, target)
        if edge_key in self.edges:
            self.edges[edge_key].weight = new_weight
            self.change_history.append(TopologyChange.WEIGHT_UPDATED)
    
    def set_coherence(self, node_id: str, coherence: float) -> None:
        """Set coherence score for a node."""
        self.coherence_scores[node_id] = coherence
    
    def get_neighbors(self, node_id: str) -> List[str]:
        """Get all neighbors of a node."""
        neighbors = []
        for (s, t), edge in self.edges.items():
            if s == node_id and edge.active:
                neighbors.append(t)
            elif t == node_id and edge.active:
                neighbors.append(s)
        return neighbors
    
    def rewire(
        self, 
        coherence_threshold: float = 0.8,
        min_coherence_diff: float = 0.2
    ) -> List[TopologyChange]:
        """
        Rewire the topology based on coherence patterns.
        
        - Add edges between high-coherence nodes
        - Remove edges between low-coherence nodes
        - Strengthen edges with similar coherence
        """
        changes = []
        
        # Find high-coherence nodes
        high_coherence = [
            n for n, c in self.coherence_scores.items()
            if c >= coherence_threshold
        ]
        
        # Add edges between high-coherence nodes
        for i, node1 in enumerate(high_coherence):
            for node2 in high_coherence[i+1:]:
                edge_key = (node1, node2)
                reverse_key = (node2, node1)
                
                if edge_key not in self.edges and reverse_key not in self.edges:
                    self.add_edge(node1, node2, weight=1.0)
                    changes.append(TopologyChange.EDGE_ADDED)
        
        # Remove edges between dissimilar coherence nodes
        for (s, t), edge in list(self.edges.items()):
            if not edge.active:
                continue
            
            s_coherence = self.coherence_scores.get(s, 0)
            t_coherence = self.coherence_scores.get(t, 0)
            diff = abs(s_coherence - t_coherence)
            
            if diff > min_coherence_diff and (s_coherence < coherence_threshold or t_coherence < coherence_threshold):
                self.remove_edge(s, t)
                changes.append(TopologyChange.EDGE_REMOVED)
        
        # Strengthen edges between similar coherence nodes
        for (s, t), edge in self.edges.items():
            if not edge.active:
                continue
            
            s_coherence = self.coherence_scores.get(s, 0)
            t_coherence = self.coherence_scores.get(t, 0)
            
            if abs(s_coherence - t_coherence) < 0.1:
                new_weight = min(edge.weight * 1.2, 2.0)
                if new_weight != edge.weight:
                    self.update_edge_weight(s, t, new_weight)
                    changes.append(TopologyChange.WEIGHT_UPDATED)
        
        return changes
    
    def get_topology_metrics(self) -> Dict[str, Any]:
        """Get metrics about the current topology."""
        num_nodes = len(self.nodes)
        num_edges = len([e for e in self.edges.values() if e.active])
        
        # Average degree
        degrees = [len(self.get_neighbors(n)) for n in self.nodes]
        avg_degree = sum(degrees) / len(degrees) if degrees else 0
        
        # Average coherence
        coherences = list(self.coherence_scores.values())
        avg_coherence = sum(coherences) / len(coherences) if coherences else 0
        
        return {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "avg_degree": avg_degree,
            "avg_coherence": avg_coherence,
            "density": num_edges / (num_nodes * (num_nodes - 1) / 2) if num_nodes > 1 else 0
        }
    
    def to_adjacency_list(self) -> Dict[str, List[str]]:
        """Convert topology to adjacency list representation."""
        adj = {n: [] for n in self.nodes}
        for (s, t), edge in self.edges.items():
            if edge.active:
                adj[s].append(t)
                adj[t].append(s)
        return adj