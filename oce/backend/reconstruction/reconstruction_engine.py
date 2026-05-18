"""
V3 Phase 2 — Reconstruction Engine
Rebuilds continuity from partial state, sparse memory, topology overlap, and attractor proximity.

THIS is the true core of Phase 2.
Not storage — reconstruction. Not retrieval — inference.

Continuity is inferred, not replayed linearly.
This is contour completion mechanics — the system fills in gaps
from fragments, like completing a partially drawn shape.
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional

from .causal_geometry import CausalGeometryEngine, CausalEdge, ContinuityLineage
from .attractor_memory import AttractorMemory, Attractor


@dataclass
class ReconstructionResult:
    """Result of a continuity reconstruction operation."""
    target_state: str
    reconstructed: bool
    confidence: float           # 0.0-1.0
    method: str                 # "attractor", "lineage", "overlap", "inference"
    source_attractor: Optional[str] = None
    lineage_depth: int = 0
    entropy_cost: float = 0.0
    timestamp: float = field(default_factory=time.time)
    details: dict = field(default_factory=dict)

    @property
    def is_reliable(self) -> bool:
        """Reconstruction is reliable if confidence > 0.7."""
        return self.confidence > 0.7

    def to_dict(self) -> dict:
        return {
            "target_state": self.target_state,
            "reconstructed": self.reconstructed,
            "confidence": round(self.confidence, 4),
            "method": self.method,
            "source_attractor": self.source_attractor,
            "lineage_depth": self.lineage_depth,
            "is_reliable": self.is_reliable,
        }


class ReconstructionEngine:
    """
    Reconstructs continuity from partial information.
    
    Reconstruction methods (in priority order):
    1. Attractor proximity — find nearest stored attractor
    2. Lineage tracing — follow causal chain backward
    3. Overlap inference — use shared state from other observers
    4. Constraint inference — deduce from known constraints
    
    The engine tries each method in order until confidence > 0.7
    or all methods are exhausted.
    """

    def __init__(self):
        self.causal_geometry = CausalGeometryEngine()
        self.attractor_memory = AttractorMemory()
        self._reconstruction_count = 0
        self._success_count = 0

    def reconstruct(
        self, target_state: str,
        known_observers: list[str] = None,
        known_coherence: float = None,
        partial_context: dict = None,
    ) -> ReconstructionResult:
        """
        Attempt to reconstruct a target state from available information.
        
        Tries multiple reconstruction methods in priority order:
        1. Attractor proximity (fastest, most reliable)
        2. Lineage tracing (follows causal chain)
        3. Overlap inference (uses observer overlap)
        4. Constraint inference (deduces from constraints)
        """
        self._reconstruction_count += 1
        partial_context = partial_context or {}

        # Method 1: Attractor proximity
        result = self._reconstruct_from_attractor(target_state, known_observers, known_coherence)
        if result.is_reliable:
            self._success_count += 1
            return result

        # Method 2: Lineage tracing
        result = self._reconstruct_from_lineage(target_state)
        if result.is_reliable:
            self._success_count += 1
            return result

        # Method 3: Overlap inference
        result = self._reconstruct_from_overlap(target_state, known_observers)
        if result.is_reliable:
            self._success_count += 1
            return result

        # Method 4: Constraint inference (fallback)
        result = self._reconstruct_from_constraints(target_state, partial_context)
        if result.is_reliable:
            self._success_count += 1
            return result

        # If nothing worked, return best attempt
        return ReconstructionResult(
            target_state=target_state,
            reconstructed=False,
            confidence=0.1,
            method="failed",
            details={"message": "All reconstruction methods exhausted"},
        )

    def _reconstruct_from_attractor(
        self, target_state: str, observers: list[str], coherence: float,
    ) -> ReconstructionResult:
        """Reconstruct by finding the nearest stored attractor."""
        nearest = self.attractor_memory.find_nearest(
            coherence=coherence or 0.5,
            observers=observers,
        )
        if nearest:
            confidence = nearest.stability * nearest.coherence
            return ReconstructionResult(
                target_state=target_state,
                reconstructed=confidence > 0.5,
                confidence=confidence,
                method="attractor",
                source_attractor=nearest.attractor_id,
                details={"attractor_state": nearest.state_id},
            )
        return ReconstructionResult(target_state=target_state, reconstructed=False, confidence=0.0, method="attractor")

    def _reconstruct_from_lineage(self, target_state: str) -> ReconstructionResult:
        """Reconstruct by tracing the causal lineage backward."""
        lineage = self.causal_geometry.get_lineage(target_state)
        if lineage and lineage.is_intact:
            chain = self.causal_geometry.get_ancestor_chain(target_state)
            confidence = lineage.total_continuity * (1.0 / (1.0 + lineage.depth * 0.1))
            return ReconstructionResult(
                target_state=target_state,
                reconstructed=confidence > 0.5,
                confidence=confidence,
                method="lineage",
                lineage_depth=lineage.depth,
                details={"ancestor_chain": chain},
            )
        return ReconstructionResult(target_state=target_state, reconstructed=False, confidence=0.0, method="lineage")

    def _reconstruct_from_overlap(self, target_state: str, observers: list[str]) -> ReconstructionResult:
        """Reconstruct using observer overlap zones."""
        if not observers:
            return ReconstructionResult(target_state=target_state, reconstructed=False, confidence=0.0, method="overlap")

        # Find attractors involving the same observers
        overlapping = set()
        for obs in observers:
            for attractor in self.attractor_memory.find_by_observer(obs):
                overlapping.add(attractor.attractor_id)

        if overlapping:
            # Use the most stable overlapping attractor
            best = max(
                [self.attractor_memory.recall(aid) for aid in overlapping if self.attractor_memory.recall(aid)],
                key=lambda a: a.stability,
                default=None,
            )
            if best:
                overlap_ratio = len(set(best.observer_cluster) & set(observers)) / max(len(observers), 1)
                confidence = best.stability * overlap_ratio
                return ReconstructionResult(
                    target_state=target_state,
                    reconstructed=confidence > 0.5,
                    confidence=confidence,
                    method="overlap",
                    source_attractor=best.attractor_id,
                    details={"overlap_ratio": overlap_ratio},
                )
        return ReconstructionResult(target_state=target_state, reconstructed=False, confidence=0.0, method="overlap")

    def _reconstruct_from_constraints(self, target_state: str, context: dict) -> ReconstructionResult:
        """Reconstruct by inferring from known constraints."""
        # Fallback: use whatever context is available
        if context:
            confidence = min(0.5, len(context) * 0.1)
            return ReconstructionResult(
                target_state=target_state,
                reconstructed=confidence > 0.3,
                confidence=confidence,
                method="inference",
                details={"context_keys": list(context.keys())},
            )
        return ReconstructionResult(target_state=target_state, reconstructed=False, confidence=0.0, method="inference")

    def record_state_transition(
        self, source_state: str, target_state: str,
        influence_weight: float = 0.5, continuity_strength: float = 0.5,
        entropy_delta: float = 0.0, tags: list[str] = None,
    ) -> CausalEdge:
        """Record a state transition as a causal edge."""
        return self.causal_geometry.create_edge(
            source_state=source_state,
            target_state=target_state,
            influence_weight=influence_weight,
            continuity_strength=continuity_strength,
            entropy_delta=entropy_delta,
            tags=tags,
        )

    def store_attractor(self, attractor: Attractor) -> str:
        """Store a stable attractor."""
        return self.attractor_memory.store(attractor)

    @property
    def success_rate(self) -> float:
        """Reconstruction success rate."""
        if self._reconstruction_count == 0:
            return 1.0
        return self._success_count / self._reconstruction_count

    @property
    def stats(self) -> dict:
        """Reconstruction engine statistics."""
        return {
            "reconstructions": self._reconstruction_count,
            "successes": self._success_count,
            "success_rate": round(self.success_rate, 4),
            "causal_geometry": self.causal_geometry.stats,
            "attractor_memory": self.attractor_memory.stats,
        }

    def __repr__(self) -> str:
        return (
            f"ReconstructionEngine(success_rate={self.success_rate:.2f}, "
            f"attractors={len(self.attractor_memory.attractors)})"
        )
