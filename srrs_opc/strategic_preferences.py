"""
Strategic Preference Modeling
==============================
Phase 8: Model operator's strategic preferences as weighted vectors.

Models preferences (e.g., mean-reversion vs momentum, asset class preferences)
as weighted vectors with confidence scores. Detects preference drift over time.

No global state — self-stabilizing preference model.
"""

import json
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class PreferenceVector:
    """
    A single strategic preference modeled as a weighted vector.

    Dimensions: strategy_type, asset_class, time_horizon, risk_profile
    Weight: strength of preference (0.0 to 1.0)
    Confidence: how confident we are in this preference (0.0 to 1.0)
    """

    def __init__(self, dimension: str, value: str, weight: float = 0.5,
                 confidence: float = 0.1):
        self.dimension = dimension
        self.value = value
        self.weight = max(0.0, min(1.0, weight))
        self.confidence = max(0.0, min(1.0, confidence))
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_updated = self.created_at
        self._update_count = 1

    def reinforce(self, strength: float = 0.1):
        """Strengthen preference when operator acts consistently with it."""
        self.weight = min(1.0, self.weight + strength * 0.5)
        self.confidence = min(1.0, self.confidence + strength)
        self._update_count += 1
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def weaken(self, strength: float = 0.05):
        """Weaken preference when operator acts against it."""
        self.weight = max(0.0, self.weight - strength * 0.5)
        self.confidence = max(0.05, self.confidence - strength * 0.3)
        self._update_count += 1
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "value": self.value,
            "weight": round(self.weight, 3),
            "confidence": round(self.confidence, 3),
            "update_count": self._update_count,
            "last_updated": self.last_updated,
        }


class PreferenceDriftSignal:
    """Detected shift in operator's strategic preferences."""

    def __init__(self, dimension: str, old_value: str, new_value: str,
                 severity: float, description: str = ""):
        self.dimension = dimension
        self.old_value = old_value
        self.new_value = new_value
        self.severity = max(0.0, min(1.0, severity))
        self.description = description
        self.detected_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "severity": round(self.severity, 3),
            "description": self.description,
            "detected_at": self.detected_at,
        }


class StrategicPreferenceModel:
    """
    Models operator's strategic preferences as weighted vectors with confidence.

    Supports:
    - Preference reinforcement/weakening based on operator actions
    - Preference drift detection (when operator's strategy shifts)
    - Confidence scoring (more observations = higher confidence)
    """

    DRIFT_THRESHOLD = 0.3  # weight change that triggers drift signal

    def __init__(self, operator_id: str):
        self.operator_id = operator_id
        self._preferences: Dict[str, PreferenceVector] = {}
        self._drift_signals: List[PreferenceDriftSignal] = []
        self._history: List[Dict[str, Any]] = []

    def set_preference(self, dimension: str, value: str,
                       weight: float = 0.5, confidence: float = 0.1):
        """Set or update a strategic preference."""
        key = f"{dimension}:{value}"
        if key in self._preferences:
            old_weight = self._preferences[key].weight
            self._preferences[key].reinforce(weight)
            # Check for drift
            if abs(self._preferences[key].weight - old_weight) > self.DRIFT_THRESHOLD:
                self._drift_signals.append(PreferenceDriftSignal(
                    dimension=dimension,
                    old_value=value,
                    new_value=value,
                    severity=abs(self._preferences[key].weight - old_weight),
                    description=f"Significant weight change in {dimension}",
                ))
        else:
            self._preferences[key] = PreferenceVector(
                dimension=dimension, value=value,
                weight=weight, confidence=confidence
            )

    def record_action(self, dimension: str, chosen_value: str,
                      alternative_values: Optional[List[str]] = None):
        """
        Record an operator action to update preferences.

        Strengthens the chosen value's preference, weakens alternatives.
        """
        # Reinforce chosen
        key = f"{dimension}:{chosen_value}"
        if key not in self._preferences:
            self._preferences[key] = PreferenceVector(
                dimension=dimension, value=chosen_value,
                weight=0.3, confidence=0.1
            )
        else:
            self._preferences[key].reinforce(0.1)

        # Weaken alternatives
        if alternative_values:
            for alt in alternative_values:
                alt_key = f"{dimension}:{alt}"
                if alt_key in self._preferences:
                    self._preferences[alt_key].weaken(0.05)

        self._history.append({
            "dimension": dimension,
            "chosen": chosen_value,
            "alternatives": alternative_values or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def detect_drift(self) -> List[PreferenceDriftSignal]:
        """
        Detect preference drift by comparing recent history to established patterns.

        Drift is detected when:
        1. A preference's weight changes significantly
        2. A new preference emerges that contradicts an established one
        """
        new_signals = []

        # Group preferences by dimension
        by_dimension: Dict[str, List[PreferenceVector]] = defaultdict(list)
        for pv in self._preferences.values():
            by_dimension[pv.dimension].append(pv)

        for dim, prefs in by_dimension.items():
            if len(prefs) < 2:
                continue
            # Sort by weight descending
            prefs_sorted = sorted(prefs, key=lambda p: p.weight, reverse=True)
            top = prefs_sorted[0]
            second = prefs_sorted[1]

            # If top preference is losing ground to second, that's drift
            if top.confidence > 0.3 and second.weight > top.weight * 0.8:
                signal = PreferenceDriftSignal(
                    dimension=dim,
                    old_value=top.value,
                    new_value=second.value,
                    severity=round(second.weight / max(top.weight, 0.01) * 0.5, 3),
                    description=f"Preference shifting from '{top.value}' to '{second.value}' in {dim}",
                )
                new_signals.append(signal)

        self._drift_signals.extend(new_signals)
        return new_signals

    def get_top_preferences(self, dimension: Optional[str] = None,
                            min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """Get top preferences, optionally filtered by dimension and confidence."""
        results = []
        for key, pv in self._preferences.items():
            if dimension and pv.dimension != dimension:
                continue
            if pv.confidence < min_confidence:
                continue
            results.append(pv.to_dict())
        results.sort(key=lambda x: x["weight"] * x["confidence"], reverse=True)
        return results

    def get_preference_summary(self) -> Dict[str, Any]:
        """Get a summary of all strategic preferences."""
        by_dimension: Dict[str, List[dict]] = defaultdict(list)
        for pv in self._preferences.values():
            by_dimension[pv.dimension].append(pv.to_dict())

        # For each dimension, find the dominant preference
        dominant = {}
        for dim, prefs in by_dimension.items():
            if prefs:
                top = max(prefs, key=lambda p: p["weight"] * p["confidence"])
                dominant[dim] = {
                    "value": top["value"],
                    "weight": top["weight"],
                    "confidence": top["confidence"],
                }

        return {
            "operator_id": self.operator_id,
            "dimensions": dict(by_dimension),
            "dominant_preferences": dominant,
            "drift_signals": [s.to_dict() for s in self._drift_signals[-5:]],
            "total_preferences": len(self._preferences),
        }

    def to_dict(self) -> dict:
        return self.get_preference_summary()
