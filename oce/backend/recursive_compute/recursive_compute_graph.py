"""
V3 Phase 10 — Recursive Compute Graph (RCG)
Nodes compute through recursive stabilization.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional, Callable


@dataclass
class ComputeResult:
    """Result of a compute node execution."""
    node_id: str
    value: float
    converged: bool
    iterations: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class ComputeNode:
    """A node in the recursive compute graph."""
    node_id: str
    compute_fn: Optional[Callable] = None
    value: float = 0.0
    converged: bool = False
    iteration: int = 0
    max_iterations: int = 100
    tolerance: float = 0.001
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)

    def execute(self, input_values: list[float]) -> float:
        """Execute the compute function with given inputs."""
        if self.compute_fn:
            new_value = self.compute_fn(input_values)
        elif input_values:
            new_value = sum(input_values) / len(input_values)
        else:
            new_value = self.value

        # Check convergence
        delta = abs(new_value - self.value)
        self.converged = delta < self.tolerance
        self.value = new_value
        self.iteration += 1

        if self.iteration >= self.max_iterations:
            self.converged = True

        return self.value


class RecursiveComputeGraph:
    """
    Nodes compute through recursive stabilization.
    
    The graph stabilizes through iterative propagation until all
    nodes converge or max iterations are reached.
    """

    def __init__(self):
        self._nodes: dict[str, ComputeNode] = {}
        self._results: list[ComputeResult] = []

    def add_node(self, node_id: str, compute_fn: Callable = None,
                  initial_value: float = 0.0, **kwargs) -> ComputeNode:
        """Add a compute node to the graph."""
        node = ComputeNode(
            node_id=node_id, compute_fn=compute_fn,
            value=initial_value, **kwargs,
        )
        self._nodes[node_id] = node
        return node

    def connect(self, from_id: str, to_id: str) -> None:
        """Connect two nodes (from_id output → to_id input)."""
        if from_id in self._nodes and to_id in self._nodes:
            if to_id not in self._nodes[from_id].outputs:
                self._nodes[from_id].outputs.append(to_id)
            if from_id not in self._nodes[to_id].inputs:
                self._nodes[to_id].inputs.append(from_id)

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and its connections."""
        if node_id not in self._nodes:
            return False
        # Remove connections
        for n in self._nodes.values():
            if node_id in n.outputs:
                n.outputs.remove(node_id)
            if node_id in n.inputs:
                n.inputs.remove(node_id)
        del self._nodes[node_id]
        return True

    def execute_node(self, node_id: str) -> Optional[ComputeResult]:
        """Execute a single node."""
        node = self._nodes.get(node_id)
        if node is None:
            return None

        # Gather input values
        input_values = []
        for input_id in node.inputs:
            input_node = self._nodes.get(input_id)
            if input_node:
                input_node.execute([])
                input_values.append(input_node.value)

        value = node.execute(input_values)
        result = ComputeResult(
            node_id=node_id, value=value,
            converged=node.converged, iterations=node.iteration,
        )
        self._results.append(result)
        return result

    def stabilize(self, max_rounds: int = 100) -> bool:
        """
        Run the graph until all nodes converge or max rounds reached.
        Returns True if all nodes converged.
        """
        for _ in range(max_rounds):
            all_converged = True
            for node_id in self._nodes:
                result = self.execute_node(node_id)
                if result and not result.converged:
                    all_converged = False
            if all_converged:
                return True
        return False

    def get_node(self, node_id: str) -> Optional[ComputeNode]:
        return self._nodes.get(node_id)

    def get_converged_nodes(self) -> list[ComputeNode]:
        return [n for n in self._nodes.values() if n.converged]

    @property
    def stats(self) -> dict:
        converged = sum(1 for n in self._nodes.values() if n.converged)
        total_iterations = sum(n.iteration for n in self._nodes.values())
        return {
            "total_nodes": len(self._nodes),
            "converged_nodes": converged,
            "total_iterations": total_iterations,
            "total_results": len(self._results),
        }
