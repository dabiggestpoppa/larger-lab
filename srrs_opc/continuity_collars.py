"""
Continuity Collars
===================
Phase 5: Long-horizon continuity emerges at overlap boundaries.

Continuity collars extend Phase 3 active collar fields with:
- Temporal overlap tracking (continuity intersection across time)
- Drift gradient measurement (divergence detection)
- Reconstruction confidence scoring (viability estimation)
- Attractor compatibility (directional stability)

Key insight: Long-horizon continuity emerges at overlap boundaries,
NOT at isolated memory stores.
"""

import json
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

from .active_collar_fields import ActiveCollarField, CollarFieldManager
from .drift_tracker import DriftSignal


class TemporalOverlap:
    """Tracks continuity intersection across time windows."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.snapshots: List[Dict[str, Any]] = []
        self.created_at = datetime.now(timezone.utc).isoformat()

    def add_snapshot(self, state: dict):
        """Add a state snapshot to the temporal window."""
        snapshot = {
            "state": state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.snapshots.append(snapshot)
        # Keep only recent window
        if len(self.snapshots) > self.window_size:
            self.snapshots = self.snapshots[-self.window_size:]

    def compute_overlap(self, other: 'TemporalOverlap') -> float:
        """Compute overlap score between two temporal windows."""
        if not self.snapshots or not other.snapshots:
            return 0.0

        # Compare recent snapshots
        recent_self = self.snapshots[-10:]
        recent_other = other.snapshots[-10:]

        matches = 0
        total = 0
        for s in recent_self:
            for o in recent_other:
                if s["state"] == o["state"]:
                    matches += 1
                total += 1

        return matches / max(1, total)

    def get_drift_gradient(self) -> float:
        """Measure how much the state has drifted over the window."""
        if len(self.snapshots) < 2:
            return 0.0

        # Simple drift: compare first and last snapshot
        first = self.snapshots[0]["state"]
        last = self.snapshots[-1]["state"]

        if not first or not last:
            return 0.0

        # Count changed keys
        all_keys = set(first.keys()) | set(last.keys())
        if not all_keys:
            return 0.0

        changed = sum(1 for k in all_keys if first.get(k) != last.get(k))
        return changed / len(all_keys)


class ContinuityCollar:
    """
    Extends ActiveCollarField with long-horizon continuity tracking.
    
    Maintains:
    - Temporal overlap (continuity intersection across time)
    - Drift gradients (divergence measurement)
    - Reconstruction confidence (viability estimation)
    - Attractor compatibility (directional stability)
    """

    def __init__(self, collar_id: str, observers: List[str], window_size: int = 100):
        self.collar_id = collar_id
        self.observers = observers
        self.temporal_overlap = TemporalOverlap(window_size)
        self.drift_signals: List[DriftSignal] = []
        self.reconstruction_confidence: float = 1.0
        self.attractor_compatibility: Dict[str, float] = {}
        self.entropy_score: float = 0.0
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_reconciled = None

    def reconcile_with_temporal(self, observer_id: str, state: dict) -> dict:
        """Reconcile state with temporal overlap tracking."""
        # Add to temporal window
        self.temporal_overlap.add_snapshot(state)

        # Compute drift gradient
        drift = self.temporal_overlap.get_drift_gradient()

        # Update reconstruction confidence
        self.reconstruction_confidence = max(0.0, 1.0 - drift)

        # Update entropy
        self.entropy_score = min(1.0, drift * 2)

        # Check for drift signals
        if drift > 0.3:
            signal = DriftSignal(
                drift_type="constraint_drift",
                severity=drift,
                description=f"Drift detected in {observer_id}: {drift:.2f}",
                source=observer_id,
            )
            self.drift_signals.append(signal)

        self.last_reconciled = datetime.now(timezone.utc).isoformat()

        return {
            "drift_gradient": round(drift, 3),
            "reconstruction_confidence": round(self.reconstruction_confidence, 3),
            "entropy_score": round(self.entropy_score, 3),
            "drift_signals": len(self.drift_signals),
        }

    def compute_continuity_score(self) -> float:
        """Compute overall continuity score for this collar."""
        if not self.temporal_overlap.snapshots:
            return 0.0

        drift_penalty = self.temporal_overlap.get_drift_gradient()
        signal_penalty = len(self.drift_signals) * 0.05
        confidence_bonus = self.reconstruction_confidence * 0.5

        score = max(0.0, 1.0 - drift_penalty - signal_penalty + confidence_bonus)
        return round(min(1.0, score), 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "collar_id": self.collar_id,
            "observers": self.observers,
            "temporal_snapshots": len(self.temporal_overlap.snapshots),
            "drift_signals": len(self.drift_signals),
            "reconstruction_confidence": round(self.reconstruction_confidence, 3),
            "entropy_score": round(self.entropy_score, 3),
            "continuity_score": self.compute_continuity_score(),
            "last_reconciled": self.last_reconciled,
        }


class ContinuityCollarManager:
    """Manages all continuity collars in the system."""

    def __init__(self):
        self.collars: Dict[str, ContinuityCollar] = {}

    def create_collar(self, collar_id: str, observers: List[str],
                      window_size: int = 100) -> ContinuityCollar:
        collar = ContinuityCollar(collar_id, observers, window_size)
        self.collars[collar_id] = collar
        return collar

    def get_collar(self, collar_id: str) -> Optional[ContinuityCollar]:
        return self.collars.get(collar_id)

    def get_system_continuity_report(self) -> Dict[str, Any]:
        """Get continuity report across all collars."""
        if not self.collars:
            return {"continuity_score": 0.0, "collar_count": 0}

        scores = [c.compute_continuity_score() for c in self.collars.values()]
        total_drift_signals = sum(len(c.drift_signals) for c in self.collars.values())

        return {
            "avg_continuity_score": round(sum(scores) / len(scores), 3),
            "min_continuity_score": round(min(scores), 3),
            "max_continuity_score": round(max(scores), 3),
            "collar_count": len(scores),
            "total_drift_signals": total_drift_signals,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
