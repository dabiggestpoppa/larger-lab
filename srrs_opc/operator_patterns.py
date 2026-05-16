"""
Operator Pattern Stabilization
================================
Phase 8: Track operator decision patterns over time.

Tracks operator behavior (entry/exit preferences, risk tolerance, session timing)
from workspace activity logs. Patterns must persist across 3+ sessions to be "stable".

No global state — self-stabilizing per-operator model.
"""

import json
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class PatternObservation:
    """A single observed operator action."""

    def __init__(self, action_type: str, details: Dict[str, Any],
                 session_id: str, timestamp: Optional[str] = None):
        self.action_type = action_type
        self.details = details
        self.session_id = session_id
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type,
            "details": self.details,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
        }


class OperatorPatternModel:
    """
    Stabilized model of a single operator's decision patterns.

    Patterns are not "learned" from a single session — they must persist
    across 3+ sessions to be considered stable. This prevents overfitting
    to temporary behavior.
    """

    STABILITY_THRESHOLD = 3  # sessions required for pattern stability

    def __init__(self, operator_id: str):
        self.operator_id = operator_id
        self._observations: List[PatternObservation] = []
        self._sessions: set = set()
        self._stable_patterns: Dict[str, Dict[str, Any]] = {}
        self._pattern_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._session_pattern_sets: Dict[str, set] = defaultdict(set)

    def record_observation(self, observation: PatternObservation):
        """Record a single operator action observation."""
        self._observations.append(observation)
        self._sessions.add(observation.session_id)

        # Track pattern frequency per session
        key = observation.action_type
        detail_key = json.dumps(observation.details, sort_keys=True, default=str)
        self._pattern_counts[key][detail_key] += 1
        self._session_pattern_sets[observation.session_id].add((key, detail_key))

    def get_stable_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Return patterns that have persisted across STABILITY_THRESHOLD+ sessions.

        A pattern is "stable" if the same (action_type, details) tuple appears
        in at least STABILITY_THRESHOLD distinct sessions.
        """
        stable = {}
        session_count = len(self._sessions)

        if session_count < self.STABILITY_THRESHOLD:
            return stable  # Not enough data for any stable pattern

        # Count how many sessions each pattern appears in
        pattern_session_count: Dict[str, set] = defaultdict(set)
        for session_id, patterns in self._session_pattern_sets.items():
            for action_type, detail_key in patterns:
                composite_key = f"{action_type}:{detail_key}"
                pattern_session_count[composite_key].add(session_id)

        for composite_key, sessions in pattern_session_count.items():
            if len(sessions) >= self.STABILITY_THRESHOLD:
                action_type, detail_key = composite_key.split(":", 1)
                stable[composite_key] = {
                    "action_type": action_type,
                    "details": json.loads(detail_key),
                    "session_count": len(sessions),
                    "total_sessions": session_count,
                    "stability_ratio": round(len(sessions) / max(session_count, 1), 3),
                }

        self._stable_patterns = stable
        return stable

    def get_entry_preferences(self) -> Dict[str, float]:
        """Extract entry signal preferences from stable patterns."""
        prefs: Dict[str, int] = defaultdict(int)
        for obs in self._observations:
            if obs.action_type == "entry":
                signal = obs.details.get("signal", "unknown")
                prefs[signal] += 1
        total = sum(prefs.values()) or 1
        return {k: round(v / total, 3) for k, v in prefs.items()}

    def get_exit_preferences(self) -> Dict[str, float]:
        """Extract exit signal preferences from stable patterns."""
        prefs: Dict[str, int] = defaultdict(int)
        for obs in self._observations:
            if obs.action_type == "exit":
                reason = obs.details.get("reason", "unknown")
                prefs[reason] += 1
        total = sum(prefs.values()) or 1
        return {k: round(v / total, 3) for k, v in prefs.items()}

    def get_risk_tolerance_estimate(self) -> float:
        """
        Estimate risk tolerance from position sizing patterns.
        Returns 0.0 (very conservative) to 1.0 (very aggressive).
        """
        sizes = []
        for obs in self._observations:
            if obs.action_type == "entry":
                size = obs.details.get("position_size", 0)
                if size > 0:
                    sizes.append(size)
        if not sizes:
            return 0.5  # default: neutral
        avg_size = sum(sizes) / len(sizes)
        # Normalize: assume max reasonable size is 10x min
        return min(1.0, avg_size / 10.0)

    def get_session_timing_pattern(self) -> Dict[str, Any]:
        """Extract preferred session timing from observation timestamps."""
        hours = []
        for obs in self._observations:
            try:
                ts = datetime.fromisoformat(obs.timestamp.replace("Z", "+00:00"))
                hours.append(ts.hour)
            except (ValueError, AttributeError):
                continue
        if not hours:
            return {"peak_hour": None, "active_hours": [], "hour_distribution": {}}
        hour_dist: Dict[int, int] = defaultdict(int)
        for h in hours:
            hour_dist[h] += 1
        peak = max(hour_dist, key=hour_dist.get)
        active = sorted(h for h, c in hour_dist.items() if c >= max(hour_dist.values()) * 0.3)
        return {
            "peak_hour": peak,
            "active_hours": active,
            "hour_distribution": {str(k): v for k, v in sorted(hour_dist.items())},
        }

    @property
    def session_count(self) -> int:
        return len(self._sessions)

    @property
    def observation_count(self) -> int:
        return len(self._observations)

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "session_count": self.session_count,
            "observation_count": self.observation_count,
            "stable_patterns": self.get_stable_patterns(),
            "entry_preferences": self.get_entry_preferences(),
            "exit_preferences": self.get_exit_preferences(),
            "risk_tolerance": round(self.get_risk_tolerance_estimate(), 3),
            "timing": self.get_session_timing_pattern(),
        }
