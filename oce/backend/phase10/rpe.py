"""
Resonance Propagation Engine (RPE)

Propagate coherence and constraints through the field.
Resonance spreads through the topology, carrying information and influence.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import math


class PropagationMode(Enum):
    """How resonance propagates through the field."""
    DIFFUSIVE = "diffusive"  # Spreads outward
    DIRECTED = "directed"   # Follows specific paths
    SELECTIVE = "selective" # Only to resonant nodes


@dataclass
class PropagationResult:
    """Result of a resonance propagation cycle."""
    source_id: str
    affected_nodes: List[str]
    coherence_delta: Dict[str, float]  # node_id -> coherence change
    constraint_updates: Dict[str, Any]  # node_id -> constraint changes
    total_propagation: float


class ResonancePropagationEngine:
    """
    Propagates resonance (coherence) and constraints through the field.
    
    Resonance is the alignment between nodes. When one node becomes
    coherent, it influences neighbors to align, propagating the coherence.
    """
    
    def __init__(self, name: str = "rpe"):
        self.name = name
        self.nodes: Dict[str, Dict[str, Any]] = {}  # node_id -> state
        self.edges: Dict[str, List[str]] = {}  # adjacency list
        self.constraints: Dict[str, Dict[str, Any]] = {}  # node_id -> constraints
        self.propagation_history: List[PropagationResult] = []
    
    def register_node(self, node_id: str, initial_state: Optional[Dict[str, Any]] = None) -> None:
        """Register a node with the propagation engine."""
        self.nodes[node_id] = initial_state or {}
        self.edges[node_id] = []
        self.constraints[node_id] = {}
    
    def connect(self, node_id1: str, node_id2: str) -> None:
        """Create bidirectional connection for propagation."""
        if node_id1 in self.nodes and node_id2 in self.nodes:
            if node_id2 not in self.edges[node_id1]:
                self.edges[node_id1].append(node_id2)
            if node_id1 not in self.edges[node_id2]:
                self.edges[node_id2].append(node_id1)
    
    def set_constraint(self, node_id: str, constraint_name: str, value: Any) -> None:
        """Set a constraint on a node."""
        if node_id in self.nodes:
            self.constraints[node_id][constraint_name] = value
    
    def compute_coherence(self, node_id: str) -> float:
        """Compute coherence score for a node."""
        if node_id not in self.nodes:
            return 0.0
        
        state = self.nodes[node_id]
        if not state:
            return 0.0
        
        # Coherence based on constraint satisfaction
        satisfied = sum(
            1 for k, v in self.constraints.get(node_id, {}).items()
            if state.get(k) == v
        )
        total = len(self.constraints.get(node_id, {}))
        
        return satisfied / total if total > 0 else 1.0
    
    def propagate(
        self,
        source_id: str,
        mode: PropagationMode = PropagationMode.DIFFUSIVE,
        strength: float = 1.0,
        max_depth: int = 3
    ) -> PropagationResult:
        """
        Propagate resonance from a source node.
        
        Args:
            source_id: Node to propagate from
            mode: How to propagate (diffusive, directed, selective)
            strength: Initial propagation strength
            max_depth: Maximum propagation depth
        
        Returns:
            PropagationResult with affected nodes and coherence changes
        """
        if source_id not in self.nodes:
            return PropagationResult(
                source_id=source_id,
                affected_nodes=[],
                coherence_delta={},
                constraint_updates={},
                total_propagation=0.0
            )
        
        source_coherence = self.compute_coherence(source_id)
        affected = []
        coherence_delta = {}
        constraint_updates = {}
        
        # BFS propagation
        visited = {source_id}
        queue = [(source_id, 0, strength)]
        
        while queue:
            current_id, depth, current_strength = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            for neighbor_id in self.edges.get(current_id, []):
                if neighbor_id in visited:
                    continue
                
                visited.add(neighbor_id)
                affected.append(neighbor_id)
                
                # Compute coherence influence
                neighbor_coherence = self.compute_coherence(neighbor_id)
                influence = current_strength * source_coherence * 0.5
                
                # Update coherence delta
                coherence_delta[neighbor_id] = influence
                
                # Apply constraint updates based on mode
                if mode == PropagationMode.DIFFUSIVE:
                    # Spread constraints
                    for c_name, c_value in self.constraints.get(current_id, {}).items():
                        if c_name not in self.constraints.get(neighbor_id, {}):
                            constraint_updates[neighbor_id] = {
                                c_name: c_value
                            }
                
                # Continue propagation with decayed strength
                new_strength = current_strength * 0.7
                queue.append((neighbor_id, depth + 1, new_strength))
        
        result = PropagationResult(
            source_id=source_id,
            affected_nodes=affected,
            coherence_delta=coherence_delta,
            constraint_updates=constraint_updates,
            total_propagation=sum(coherence_delta.values())
        )
        
        self.propagation_history.append(result)
        return result
    
    def apply_propagation(self, result: PropagationResult) -> None:
        """Apply the results of a propagation to the nodes."""
        for node_id, delta in result.coherence_delta.items():
            if node_id in self.nodes:
                # Apply coherence as a state update
                self.nodes[node_id]["coherence"] = self.nodes[node_id].get("coherence", 0) + delta
        
        for node_id, updates in result.constraint_updates.items():
            if node_id in self.constraints:
                self.constraints[node_id].update(updates)
    
    def get_field_coherence(self) -> float:
        """Get average coherence across all nodes."""
        if not self.nodes:
            return 0.0
        
        coherences = [self.compute_coherence(n) for n in self.nodes]
        return sum(coherences) / len(coherences)
    
    def find_resonant_clusters(self, threshold: float = 0.7) -> List[List[str]]:
        """Find clusters of highly resonant nodes."""
        clusters = []
        visited = set()
        
        for node_id in self.nodes:
            if node_id in visited:
                continue
            
            # BFS to find cluster
            cluster = []
            queue = [node_id]
            
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                
                visited.add(current)
                if self.compute_coherence(current) >= threshold:
                    cluster.append(current)
                    
                    for neighbor in self.edges.get(current, []):
                        if neighbor not in visited:
                            queue.append(neighbor)
            
            if len(cluster) >= 2:
                clusters.append(cluster)
        
        return clusters