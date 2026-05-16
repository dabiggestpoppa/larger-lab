"""
Long-Horizon Operator Continuity Tracking
===========================================
Phase 8: Track operator identity across sessions (not just within one session).

Reconstructs operator's "strategic trajectory" from sparse evidence.
Links to trajectory_fields.py (Phase 5) for cross-session continuity.

No global state — self-stabilizing continuity tracker.
"""

import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class SessionAnchor:
    """A sparse evidence point from a single operator session."""

    def __init__(self, session_id: str, operator_id: str,
                 evidence: Dict[str, Any], timestamp: Optional[str] = None):
        self.anchor_id = hashlib.sha256(
            f"{session_id}:{operator_id}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]
        self.session_id = session_id
        self.operator_id = operator_id
        self.evidence = evidence
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.weight: float = 0.5

    def to_dict(self) -> dict:
        return {
            "anchor_id": self.anchor_id,
            "session_id": self.session_id,
            "operator_id": self.operator_id,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
            "weight": round(self.weight, 3),
        }


class StrategicTrajectory:
    """
    Reconstructed strategic trajectory of an operator across sessions.

    Built from sparse session anchors — doesn't require complete history.
    """

    def __init__(self, operator_id: str):
        self.operator_id = operator_id
        self._anchors: List[SessionAnchor] = []
        self._sessions: List[str] = []
        self._trajectory_segments: List[Dict[str, Any]] = []

    def add_anchor(self, anchor: SessionAnchor):
        """Add a session anchor to the trajectory."""
        self._anchors.append(anchor)
        if anchor.session_id not in self._sessions:
            self._sessions.append(anchor.session_id)
        self._anchors.sort(key=lambda a: a.timestamp)
        self._rebuild_segments()

    def _rebuild_segments(self):
        """Rebuild trajectory segments from anchors."""
        self._trajectory_segments = []
        for i in range(len(self._anchors) - 1):
            current = self._anchors[i]
            next_anchor = self._anchors[i + 1]
            segment = {
                "from_session": current.session_id,
                "to_session": next_anchor.session_id,
                "from_time": current.timestamp,
                "to_time": next_anchor.timestamp,
                "evidence_delta": self._compute_evidence_delta(
                    current.evidence, next_anchor.evidence
                ),
                "continuity_score": self._compute_continuity(
                    current.evidence, next_anchor.evidence
                ),
            }
            self._trajectory_segments.append(segment)

    def _compute_evidence_delta(self, evidence1: Dict, evidence2: Dict) -> Dict[str, float]:
        """Compute the change in evidence between two anchors."""
        delta = {}
        all_keys = set(evidence1.keys()) | set(evidence2.keys())
        for key in all_keys:
            v1 = evidence1.get(key, 0)
            v2 = evidence2.get(key, 0)
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                delta[key] = round(v2 - v1, 3)
            else:
                delta[key] = 1.0 if v1 != v2 else 0.0
        return delta

    def _compute_continuity(self, evidence1: Dict, evidence2: Dict) -> float:
        """
        Compute continuity score between two evidence sets.
        1.0 = perfect continuity, 0.0 = complete discontinuity.
        """
        if not evidence1 or not evidence2:
            return 0.5

        common_keys = set(evidence1.keys()) & set(evidence2.keys())
        if not common_keys:
            return 0.3  # Some baseline continuity from same operator

        matches = 0
        total = 0
        for key in common_keys:
            v1 = evidence1[key]
            v2 = evidence2[key]
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                # Numeric: compute similarity
                max_val = max(abs(v1), abs(v2), 0.01)
                similarity = 1.0 - abs(v1 - v2) / max_val
                matches += max(0, similarity)
            else:
                # Categorical: exact match
                matches += 1.0 if v1 == v2 else 0.0
            total += 1

        return round(matches / max(total, 1), 3)

    def get_continuity_score(self) -> float:
        """Get overall trajectory continuity score."""
        if not self._trajectory_segments:
            return 1.0  # Single session = perfect continuity
        scores = [s["continuity_score"] for s in self._trajectory_segments]
        return round(sum(scores) / len(scores), 3)

    def get_strategic_drift(self) -> Dict[str, Any]:
        """
        Detect strategic drift across the trajectory.
        Returns drift magnitude and direction per evidence dimension.
        """
        if len(self._anchors) < 2:
            return {"drift_detected": False, "dimensions": {}}

        first = self._anchors[0].evidence
        last = self._anchors[-1].evidence
        delta = self._compute_evidence_delta(first, last)

        drift_detected = any(abs(v) > 0.2 for v in delta.values() if isinstance(v, (int, float)))

        return {
            "drift_detected": drift_detected,
            "dimensions": delta,
            "session_span": len(self._sessions),
            "anchor_count": len(self._anchors),
        }

    def reconstruct_from_sparse(self, min_anchors: int = 2) -> Dict[str, Any]:
        """
        Reconstruct operator's strategic trajectory from sparse anchors.

        Even with gaps, we can reconstruct a plausible trajectory
        by interpolating between known anchor points.
        """
        if len(self._anchors) < min_anchors:
            return {
                "reconstructable": False,
                "reason": f"Need at least {min_anchors} anchors, have {len(self._anchors)}",
            }

        return {
            "reconstructable": True,
            "operator_id": self.operator_id,
            "session_count": len(self._sessions),
            "anchor_count": len(self._anchors),
            "continuity_score": self.get_continuity_score(),
            "trajectory_segments": self._trajectory_segments,
            "strategic_drift": self.get_strategic_drift(),
            "first_seen": self._anchors[0].timestamp if self._anchors else None,
            "last_seen": self._anchors[-1].timestamp if self._anchors else None,
        }

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "sessions": self._sessions,
            "anchor_count": len(self._anchors),
            "continuity_score": self.get_continuity_score(),
            "segments": self._trajectory_segments,
        }


class OperatorContinuityTracker:
    """
    Tracks operator identity across sessions using sparse evidence.

    Links to Phase 5 trajectory_fields for cross-session continuity.
    Each operator gets their own StrategicTrajectory.
    """

    def __init__(self):
        self._trajectories: Dict[str, StrategicTrajectory] = {}

    def get_or_create_trajectory(self, operator_id: str) -> StrategicTrajectory:
        if operator_id not in self._trajectories:
            self._trajectories[operator_id] = StrategicTrajectory(operator_id)
        return self._trajectories[operator_id]

    def record_session(self, operator_id: str, session_id: str,
                       evidence: Dict[str, Any]):
        """Record a session anchor for an operator."""
        trajectory = self.get_or_create_trajectory(operator_id)
        anchor = SessionAnchor(
            session_id=session_id,
            operator_id=operator_id,
            evidence=evidence,
        )
        trajectory.add_anchor(anchor)

    def get_continuity_report(self, operator_id: str) -> Dict[str, Any]:
        """Get continuity report for an operator."""
        if operator_id not in self._trajectories:
            return {"operator_id": operator_id, "found": False}
        traj = self._trajectories[operator_id]
        return {
            "operator_id": operator_id,
            "found": True,
            **traj.reconstruct_from_sparse(min_anchors=1),
        }

    def to_dict(self) -> dict:
        return {
            "tracked_operators": list(self._trajectories.keys()),
            "operator_count": len(self._trajectories),
        }
