"""
Recursive Compute Graph (RCG)

Nodes compute through recursive stabilization.
Computation emerges from field perturbation → recursive stabilization → solution state.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import hashlib


class ComputeState(Enum):
    """State of a compute node in the recursive process."""
    PERTURBED = "perturbed"
    STABILIZING = "stabilizing"
    STABLE = "stable"
    CONVERGED = "converged"


@dataclass
class StabilizationResult:
    """Result of a stabilization cycle."""
    node_id: str
    iterations: int
    converged: bool
    final_state: Dict[str, Any]
    coherence_score: float


@dataclass
class ComputeNode:
    """A node in the recursive compute graph."""
    node_id: str
    initial_state: Dict[str, Any]
    compute_function: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    neighbors: List[str] = field(default_factory=list)
    state: ComputeState = ComputeState.PERTURBED
    iteration_count: int = 0
    max_iterations: int = 100
    stability_threshold: float = 0.99
    
    def compute(self) -> Dict[str, Any]:
        """Execute compute function if available."""
        if self.compute_function:
            return self.compute_function(self.initial_state)
        return self.initial_state.copy()
    
    def update_state(self, new_state: Dict[str, Any]) -> None:
        """Update node state."""
        self.initial_state = new_state
        self.iteration_count += 1
    
    def is_stable(self) -> bool:
        """Check if node has reached stability threshold."""
        return self.state == ComputeState.STABLE or self.state == ComputeState.CONVERGED


class RecursiveComputeGraph:
    """
    A compute graph where nodes stabilize through recursive interaction.
    
    Computation proceeds through:
    1. Field perturbation (initial state)
    2. Recursive stabilization (neighbor influence)
    3. Emergent solution (converged state)
    """
    
    def __init__(self, name: str = "rcg"):
        self.name = name
        self.nodes: Dict[str, ComputeNode] = {}
        self.edges: Dict[str, List[str]] = {}  # node_id -> neighbor_ids
        self.global_coherence: float = 0.0
        self.iteration: int = 0
        self.max_global_iterations: int = 500
    
    def add_node(self, node: ComputeNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.node_id] = node
        self.edges[node.node_id] = node.neighbors.copy()
    
    def connect(self, node_id1: str, node_id2: str) -> None:
        """Create bidirectional connection between nodes."""
        if node_id1 in self.nodes and node_id2 in self.nodes:
            if node_id2 not in self.edges[node_id1]:
                self.edges[node_id1].append(node_id2)
            if node_id1 not in self.edges[node_id2]:
                self.edges[node_id2].append(node_id1)
    
    def compute_coherence(self, node_id: str) -> float:
        """Compute coherence score for a node based on neighbor alignment."""
        if node_id not in self.nodes:
            return 0.0
        
        node = self.nodes[node_id]
        neighbors = self.edges.get(node_id, [])
        
        if not neighbors:
            return 1.0  # Isolated node is trivially coherent
        
        # Compute similarity to neighbors
        similarities = []
        for neighbor_id in neighbors:
            if neighbor_id in self.nodes:
                neighbor = self.nodes[neighbor_id]
                similarity = self._state_similarity(
                    node.initial_state, 
                    neighbor.initial_state
                )
                similarities.append(similarity)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _state_similarity(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> float:
        """Compute similarity between two states."""
        if not state1 or not state2:
            return 0.0
        
        common_keys = set(state1.keys()) & set(state2.keys())
        if not common_keys:
            return 0.0
        
        matches = sum(1 for k in common_keys if state1[k] == state2[k])
        return matches / len(common_keys)
    
    def stabilize_node(self, node_id: str) -> StabilizationResult:
        """Run stabilization for a single node."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        node = self.nodes[node_id]
        coherence = self.compute_coherence(node_id)
        
        # Update state based on neighbors
        neighbors = self.edges.get(node_id, [])
        if neighbors:
            neighbor_states = [
                self.nodes[n].initial_state 
                for n in neighbors 
                if n in self.nodes
            ]
            if neighbor_states:
                # Average neighbor states as influence
                averaged = self._average_states(neighbor_states)
                node.update_state(averaged)
        
        # Check stability
        if coherence >= node.stability_threshold:
            node.state = ComputeState.STABLE
        elif node.iteration_count >= node.max_iterations:
            node.state = ComputeState.CONVERGED
        
        return StabilizationResult(
            node_id=node_id,
            iterations=node.iteration_count,
            converged=node.state in (ComputeState.STABLE, ComputeState.CONVERGED),
            final_state=node.initial_state.copy(),
            coherence_score=coherence
        )
    
    def _average_states(self, states: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Average multiple states together."""
        if not states:
            return {}
        
        result = {}
        all_keys = set()
        for s in states:
            all_keys.update(s.keys())
        
        for key in all_keys:
            values = [s.get(key) for s in states if key in s]
            if values and all(isinstance(v, (int, float)) for v in values):
                result[key] = sum(values) / len(values)
            elif values:
                result[key] = values[0]  # Take first non-numeric value
        
        return result
    
    def compute(self) -> Dict[str, StabilizationResult]:
        """
        Run the full recursive compute cycle.
        
        Returns results for all nodes after stabilization.
        """
        results = {}
        
        for _ in range(self.max_global_iterations):
            self.iteration += 1
            all_stable = True
            
            for node_id in self.nodes:
                if self.nodes[node_id].state not in (ComputeState.STABLE, ComputeState.CONVERGED):
                    result = self.stabilize_node(node_id)
                    results[node_id] = result
                    if not result.converged:
                        all_stable = False
            
            # Update global coherence
            coherences = [self.compute_coherence(n) for n in self.nodes]
            self.global_coherence = sum(coherences) / len(coherences) if coherences else 0.0
            
            if all_stable:
                break
        
        return results
    
    def get_solution(self) -> Dict[str, Any]:
        """Extract the converged solution from all nodes."""
        return {
            node_id: node.initial_state.copy()
            for node_id, node in self.nodes.items()
            if node.state in (ComputeState.STABLE, ComputeState.CONVERGED)
        }