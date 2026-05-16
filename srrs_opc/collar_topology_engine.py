"""
Collar Topology Engine
========================
Phase 6 Refinement: Overlap-centric cognition.

The overlap itself (not the observers) is the cognitive substrate.
Cognition emerges in the overlap between observer fields.

Key metrics:
- Overlap density (cognitive coupling)
- Collar entropy (instability in overlap)
- Reconstruction viability (continuity recoverability)
- Attractor pressure (directional coherence)
- Repair propagation (stabilization efficiency)
- Sovereignty entropy (dependency growth)
"""

import json
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class CollarMetrics:
    """Metrics for a single overlap collar."""

    def __init__(self, collar_id: str, observers: List[str]):
        self.collar_id = collar_id
        self.observers = observers
        self.overlap_density = 0.0  # Cognitive coupling strength
        self.collar_entropy = 0.0   # Instability in overlap
        self.reconstruction_viability = 1.0  # Continuity recoverability
        self.attractor_pressure = 0.0  # Directional coherence
        self.repair_propagation = 0.0  # Stabilization efficiency
        self.sovereignty_entropy = 0.0  # Dependency growth
        self.event_count = 0
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "collar_id": self.collar_id,
            "observers": self.observers,
            "overlap_density": round(self.overlap_density, 3),
            "collar_entropy": round(self.collar_entropy, 3),
            "reconstruction_viability": round(self.reconstruction_viability, 3),
            "attractor_pressure": round(self.attractor_pressure, 3),
            "repair_propagation": round(self.repair_propagation, 3),
            "sovereignty_entropy": round(self.sovereignty_entropy, 3),
            "event_count": self.event_count,
        }


class CollarTopologyEngine:
    """
    Analyzes overlap geometry between observer fields.
    Cognition emerges in the overlap, not inside isolated observers.
    """

    def __init__(self):
        self._collars: Dict[str, CollarMetrics] = {}
        self._observer_collars: Dict[str, List[str]] = defaultdict(list)

    def _collar_id(self, obs_a: str, obs_b: str) -> str:
        return f"{min(obs_a, obs_b)}-{max(obs_a, obs_b)}"

    def register_overlap(self, obs_a: str, obs_b: str) -> CollarMetrics:
        """Register an overlap collar between two observers."""
        cid = self._collar_id(obs_a, obs_b)
        if cid not in self._collars:
            self._collars[cid] = CollarMetrics(cid, [obs_a, obs_b])
            self._observer_collars[obs_a].append(cid)
            self._observer_collars[obs_b].append(cid)
        return self._collars[cid]

    def record_overlap_event(self, obs_a: str, obs_b: str,
                              coherence_delta: float, entropy_delta: float):
        """Record an event in the overlap region."""
        collar = self.register_overlap(obs_a, obs_b)
        collar.event_count += 1

        # Overlap density: increases with coherent interactions
        collar.overlap_density = min(1.0,
            collar.overlap_density + max(0, coherence_delta) * 0.1)

        # Collar entropy: increases with instability
        collar.collar_entropy = min(1.0,
            collar.collar_entropy + max(0, entropy_delta) * 0.1)

        # Reconstruction viability: decreases with entropy (stronger impact)
        collar.reconstruction_viability = max(0.0,
            collar.reconstruction_viability - entropy_delta * 0.5)

        # Attractor pressure: directional coherence
        collar.attractor_pressure = min(1.0,
            collar.attractor_pressure + coherence_delta * 0.05)

        # Repair propagation: how well repairs stabilize
        if entropy_delta < 0:
            collar.repair_propagation = min(1.0,
                collar.repair_propagation + 0.1)

        # Sovereignty entropy: dependency growth
        collar.sovereignty_entropy = min(1.0,
            collar.sovereignty_entropy + 0.01)

        collar.last_updated = datetime.now(timezone.utc).isoformat()

    def get_collar_metrics(self, obs_a: str, obs_b: str) -> Optional[dict]:
        """Get metrics for a specific collar."""
        cid = self._collar_id(obs_a, obs_b)
        collar = self._collars.get(cid)
        return collar.to_dict() if collar else None

    def get_observer_collars(self, observer: str) -> List[dict]:
        """Get all collar metrics for an observer."""
        return [self._collars[cid].to_dict()
                for cid in self._observer_collars.get(observer, [])
                if cid in self._collars]

    def get_system_metrics(self) -> dict:
        """Get system-wide overlap metrics."""
        if not self._collars:
            return {"status": "no_collars"}

        collars = list(self._collars.values())
        return {
            "total_collars": len(collars),
            "avg_overlap_density": round(
                sum(c.overlap_density for c in collars) / len(collars), 3),
            "avg_collar_entropy": round(
                sum(c.collar_entropy for c in collars) / len(collars), 3),
            "avg_reconstruction_viability": round(
                sum(c.reconstruction_viability for c in collars) / len(collars), 3),
            "avg_attractor_pressure": round(
                sum(c.attractor_pressure for c in collars) / len(collars), 3),
            "avg_repair_propagation": round(
                sum(c.repair_propagation for c in collars) / len(collars), 3),
            "avg_sovereignty_entropy": round(
                sum(c.sovereignty_entropy for c in collars) / len(collars), 3),
            "total_events": sum(c.event_count for c in collars),
        }

    def identify_weak_collars(self, threshold: float = 0.3) -> List[dict]:
        """Identify collars with low reconstruction viability."""
        weak = []
        for collar in self._collars.values():
            if collar.reconstruction_viability < threshold:
                weak.append({
                    "collar_id": collar.collar_id,
                    "observers": collar.observers,
                    "reconstruction_viability": collar.reconstruction_viability,
                    "collar_entropy": collar.collar_entropy,
                    "recommendation": "strengthen" if collar.overlap_density > 0.5 else "isolate",
                })
        return weak

    def suggest_overlap_optimizations(self) -> List[dict]:
        """Suggest optimizations for overlap geometry."""
        suggestions = []
        for collar in self._collars.values():
            # High entropy + high density = unstable strong coupling
            if collar.collar_entropy > 0.6 and collar.overlap_density > 0.7:
                suggestions.append({
                    "type": "stabilize_strong_coupling",
                    "collar": collar.collar_id,
                    "reason": f"High entropy ({collar.collar_entropy:.2f}) with strong coupling ({collar.overlap_density:.2f})",
                    "action": "Add repair mediation or reduce sync frequency",
                })
            # Low viability + high sovereignty = dangerous dependency
            if collar.reconstruction_viability < 0.3 and collar.sovereignty_entropy > 0.7:
                suggestions.append({
                    "type": "reduce_dependency",
                    "collar": collar.collar_id,
                    "reason": f"Low viability ({collar.reconstruction_viability:.2f}) with high dependency ({collar.sovereignty_entropy:.2f})",
                    "action": "Decouple or add redundancy",
                })
        return suggestions


if __name__ == "__main__":
    engine = CollarTopologyEngine()

    # Simulate overlap events
    import random
    random.seed(42)

    for i in range(50):
        engine.record_overlap_event("planner", "execution",
                                     coherence_delta=random.gauss(0.1, 0.05),
                                     entropy_delta=random.gauss(0.02, 0.01))
        engine.record_overlap_event("execution", "memory",
                                     coherence_delta=random.gauss(0.05, 0.03),
                                     entropy_delta=random.gauss(0.05, 0.02))
        if i % 5 == 0:
            engine.record_overlap_event("memory", "repair",
                                         coherence_delta=random.gauss(-0.05, 0.02),
                                         entropy_delta=random.gauss(0.1, 0.03))

    print("System metrics:")
    print(json.dumps(engine.get_system_metrics(), indent=2))

    print("\nWeak collars:")
    for w in engine.identify_weak_collars():
        print(f"  {w}")

    print("\nOptimization suggestions:")
    for s in engine.suggest_overlap_optimizations():
        print(f"  {s}")
