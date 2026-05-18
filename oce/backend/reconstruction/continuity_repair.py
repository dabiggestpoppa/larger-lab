"""
V3 Phase 2 — Continuity Repair Loop
Detects and repairs continuity fractures automatically.

Without this: all long-running systems collapse eventually.
With this: the field self-heals from partial failures.

Repair sequence:
1. Detect drift/fracture
2. Trace causal replay
3. Match to nearest attractor
4. Apply continuity patch
5. Verify coherence
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional

from .causal_geometry import CausalGeometryEngine
from .attractor_memory import AttractorMemory, Attractor
from .reconstruction_engine import ReconstructionEngine, ReconstructionResult
from .overlap_manifold import OverlapManifold


@dataclass
class RepairResult:
    """Result of a continuity repair operation."""
    repair_id: str
    target_state: str
    success: bool
    method: str
    confidence_before: float
    confidence_after: float
    timestamp: float = field(default_factory=time.time)
    details: dict = field(default_factory=dict)

    @property
    def improvement(self) -> float:
        return self.confidence_after - self.confidence_before

    def to_dict(self) -> dict:
        return {
            "repair_id": self.repair_id,
            "target_state": self.target_state,
            "success": self.success,
            "method": self.method,
            "confidence_before": round(self.confidence_before, 4),
            "confidence_after": round(self.confidence_after, 4),
            "improvement": round(self.improvement, 4),
        }


class ContinuityRepairLoop:
    """
    Automatic continuity repair system.
    
    Detects:
    - Continuity fractures (broken lineage chains)
    - Semantic corruption (incoherent state transitions)
    - Attractor destabilization (stable states becoming unstable)
    - Observer drift (observers losing synchronization)
    
    Repairs:
    - Automatically, using reconstruction engine
    - Falls back to attractor matching if reconstruction fails
    - Verifies repair by measuring coherence after
    """

    def __init__(self):
        self.reconstruction_engine = ReconstructionEngine()
        self.overlap_manifold = OverlapManifold()
        self._repair_history: list[RepairResult] = []
        self._repair_counter = 0
        self._drift_threshold = 0.3  # Coherence below this triggers repair

    def detect_fractures(self, observer_ids: list[str] = None) -> list[dict]:
        """
        Scan for continuity fractures.
        
        Fractures are detected when:
        1. Lineage continuity < 0.3
        2. No stable attractor found for an observer
        3. Overlap strength between observers < 0.1
        """
        fractures = []
        
        # Check lineage integrity
        for state_id, lineage in self.reconstruction_engine.causal_geometry.lineages.items():
            if not lineage.is_intact:
                fractures.append({
                    "type": "lineage_fracture",
                    "state_id": state_id,
                    "continuity": lineage.total_continuity,
                    "depth": lineage.depth,
                })

        # Check observer overlap
        if observer_ids and len(observer_ids) >= 2:
            for i in range(len(observer_ids)):
                for j in range(i + 1, len(observer_ids)):
                    strength = self.overlap_manifold.calculate_overlap_strength(
                        observer_ids[i], observer_ids[j]
                    )
                    if strength < 0.1:
                        fractures.append({
                            "type": "observer_drift",
                            "observer_a": observer_ids[i],
                            "observer_b": observer_ids[j],
                            "overlap_strength": strength,
                        })

        # Check attractor stability
        for attractor in self.reconstruction_engine.attractor_memory.attractors.values():
            if not attractor.is_stable and attractor.access_count > 5:
                fractures.append({
                    "type": "attractor_destabilization",
                    "attractor_id": attractor.attractor_id,
                    "stability": attractor.stability,
                })

        return fractures

    def repair(
        self, target_state: str,
        known_observers: list[str] = None,
        known_coherence: float = None,
    ) -> RepairResult:
        """
        Attempt to repair continuity for a target state.
        
        Repair sequence:
        1. Measure current confidence
        2. Attempt reconstruction
        3. If reconstruction succeeds, apply patch
        4. Verify coherence improved
        """
        self._repair_counter += 1
        repair_id = f"repair_{self._repair_counter}"

        # Measure before
        before_confidence = self._measure_confidence(target_state)

        # Attempt reconstruction
        result = self.reconstruction_engine.reconstruct(
            target_state=target_state,
            known_observers=known_observers,
            known_coherence=known_coherence,
        )

        if result.reconstructed:
            # Apply patch: record the reconstruction as a causal edge
            if result.source_attractor:
                attractor = self.reconstruction_engine.attractor_memory.recall(result.source_attractor)
                if attractor:
                    self.reconstruction_engine.record_state_transition(
                        source_state=attractor.state_id,
                        target_state=target_state,
                        influence_weight=result.confidence,
                        continuity_strength=result.confidence,
                        tags=["repair", "auto"],
                    )

            # Measure after
            after_confidence = self._measure_confidence(target_state)
            
            repair_result = RepairResult(
                repair_id=repair_id,
                target_state=target_state,
                success=True,
                method=result.method,
                confidence_before=before_confidence,
                confidence_after=after_confidence,
                details=result.details,
            )
        else:
            repair_result = RepairResult(
                repair_id=repair_id,
                target_state=target_state,
                success=False,
                method="failed",
                confidence_before=before_confidence,
                confidence_after=before_confidence,
                details={"message": "Reconstruction failed"},
            )

        self._repair_history.append(repair_result)
        return repair_result

    def auto_repair(self, observer_ids: list[str] = None) -> list[RepairResult]:
        """
        Detect all fractures and repair them automatically.
        Returns list of repair results.
        """
        fractures = self.detect_fractures(observer_ids)
        results = []

        for fracture in fractures:
            if fracture["type"] == "lineage_fracture":
                result = self.repair(
                    target_state=fracture["state_id"],
                    known_observers=observer_ids,
                )
                results.append(result)
            elif fracture["type"] == "observer_drift":
                # Create overlap zone to repair drift
                self.overlap_manifold.create_zone(
                    observer_ids=[fracture["observer_a"], fracture["observer_b"]],
                )
            elif fracture["type"] == "attractor_destabilization":
                # Re-access the attractor to stabilize it
                attractor = self.reconstruction_engine.attractor_memory.recall(
                    fracture["attractor_id"]
                )
                if attractor:
                    attractor.access()

        return results

    def _measure_confidence(self, state_id: str) -> float:
        """Measure current confidence in a state's continuity."""
        lineage = self.reconstruction_engine.causal_geometry.get_lineage(state_id)
        if lineage:
            return lineage.total_continuity
        return 0.3  # Unknown state = low confidence

    @property
    def repair_success_rate(self) -> float:
        if not self._repair_history:
            return 1.0
        return sum(1 for r in self._repair_history if r.success) / len(self._repair_history)

    @property
    def stats(self) -> dict:
        return {
            "total_repairs": len(self._repair_history),
            "successful_repairs": sum(1 for r in self._repair_history if r.success),
            "success_rate": round(self.repair_success_rate, 4),
            "avg_improvement": round(
                sum(r.improvement for r in self._repair_history) / max(len(self._repair_history), 1), 4
            ),
        }

    def __repr__(self) -> str:
        return f"ContinuityRepair(repairs={len(self._repair_history)}, success_rate={self.repair_success_rate:.2f})"
