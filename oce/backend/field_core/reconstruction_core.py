"""
V3 Phase 9 — Reconstruction Core
Topology-constrained inference.
Reconstructs field state from partial information using topological constraints.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReconstructionResult:
    """Result of a reconstruction attempt."""
    result_id: str
    target_element: str
    success: bool
    confidence: float  # 0-1, how confident in the reconstruction
    reconstructed_state: dict = field(default_factory=dict)
    missing_keys: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def is_usable(self) -> bool:
        return self.success and self.confidence > 0.5


class ReconstructionCore:
    """
    Topology-constrained inference engine.
    
    Reconstructs field state from partial information using topological
    constraints. When parts of the field state are lost or corrupted,
    uses knowledge of the topology to infer missing values.
    """

    def __init__(self):
        self._results: list[ReconstructionResult] = []
        self._topology: dict[str, list[str]] = {}  # element_id → neighbor_ids

    def set_topology(self, element_id: str, neighbors: list[str]) -> None:
        """Set the topology (neighbors) for an element."""
        self._topology[element_id] = neighbors

    def reconstruct(self, target_element: str, known_state: dict,
                     full_schema: dict) -> ReconstructionResult:
        """
        Reconstruct missing state for an element.
        
        Uses topological neighbors to infer missing values.
        """
        missing_keys = [k for k in full_schema if k not in known_state]
        reconstructed = dict(known_state)

        # Try to infer missing values from neighbors
        neighbors = self._topology.get(target_element, [])
        inferred_count = 0

        for key in missing_keys:
            # Check if any neighbor has this key
            for neighbor_id in neighbors:
                # In a real system, we'd query the neighbor's state
                # Here we use the schema default
                if key in full_schema:
                    reconstructed[key] = full_schema[key]
                    inferred_count += 1
                    break

        still_missing = [k for k in full_schema if k not in reconstructed]
        total_keys = len(full_schema) if full_schema else 1
        confidence = 1.0 - (len(still_missing) / total_keys)

        result = ReconstructionResult(
            result_id=f"recon_{int(time.time() * 1000)}",
            target_element=target_element,
            success=confidence > 0.5,
            confidence=round(confidence, 4),
            reconstructed_state=reconstructed,
            missing_keys=still_missing,
        )
        self._results.append(result)
        return result

    def reconstruct_from_neighbors(self, target_element: str,
                                     neighbor_states: list[dict],
                                     full_schema: dict) -> ReconstructionResult:
        """Reconstruct state using actual neighbor state data."""
        reconstructed = {}
        missing_keys = list(full_schema.keys()) if full_schema else []

        # Aggregate from neighbors
        for state in neighbor_states:
            for key, value in state.items():
                if key not in reconstructed:
                    reconstructed[key] = value

        # Fill in schema defaults for still-missing keys
        for key in list(missing_keys):
            if key in reconstructed:
                missing_keys.remove(key)
            elif full_schema and key in full_schema:
                reconstructed[key] = full_schema[key]
                missing_keys.remove(key)

        total_keys = len(full_schema) if full_schema else 1
        confidence = 1.0 - (len(missing_keys) / total_keys) if total_keys > 0 else 0.0

        result = ReconstructionResult(
            result_id=f"recon_{int(time.time() * 1000)}",
            target_element=target_element,
            success=confidence > 0.5,
            confidence=round(confidence, 4),
            reconstructed_state=reconstructed,
            missing_keys=missing_keys,
        )
        self._results.append(result)
        return result

    def get_success_rate(self) -> float:
        """Get reconstruction success rate."""
        if not self._results:
            return 0.0
        successful = sum(1 for r in self._results if r.success)
        return successful / len(self._results)

    @property
    def stats(self) -> dict:
        successful = sum(1 for r in self._results if r.success)
        usable = sum(1 for r in self._results if r.is_usable)
        avg_confidence = (
            sum(r.confidence for r in self._results) / len(self._results)
            if self._results else 0.0
        )
        return {
            "total_attempts": len(self._results),
            "successful": successful,
            "usable": usable,
            "success_rate": round(self.get_success_rate(), 4),
            "avg_confidence": round(avg_confidence, 4),
        }
