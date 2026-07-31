"""
Long-Term Drift Tracker
========================
Phase 5: Tracks slow divergence from stabilized continuity over time.

Drift types:
- Constraint Drift: priorities silently shift
- Identity Drift: continuity changes unexpectedly
- Synchronization Drift: patches desynchronize
- Memory Drift: reconstruction diverges
- Entropy Drift: redundancy accumulates

Uses slow-moving stabilization windows to detect gradual changes.
"""

import json
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict


class DriftSignal:
    """A detected drift signal."""

    def __init__(self, drift_type: str, severity: float, description: str,
                 source: str = "system"):
        self.drift_type = drift_type
        self.severity = max(0.0, min(1.0, severity))
        self.description = description
        self.source = source
        self.detected_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "drift_type": self.drift_type,
            "severity": round(self.severity, 3),
            "description": self.description,
            "source": self.source,
            "detected_at": self.detected_at,
        }


class LongTermDriftTracker:
    """
    Tracks slow divergence from stabilized continuity over extended time horizons.

    Uses exponential moving averages (EMA) to detect gradual shifts that
    would be invisible to short-term drift detection.
    """

    def __init__(self, window_size: int = 100, sensitivity: float = 0.1):
        self.window_size = window_size
        self.sensitivity = sensitivity
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._ema: Dict[str, float] = {}
        self._signals: List[DriftSignal] = []

    def record(self, metric_name: str, value: float):
        """Record a metric observation."""
        history = self._history[metric_name]
        history.append(value)

        # Update EMA
        if metric_name not in self._ema:
            self._ema[metric_name] = value
        else:
            alpha = 2.0 / (self.window_size + 1)
            self._ema[metric_name] = alpha * value + (1 - alpha) * self._ema[metric_name]

        # Trim history
        if len(history) > self.window_size * 2:
            self._history[metric_name] = history[-self.window_size:]

    def check_drift(self, metric_name: str) -> Optional[DriftSignal]:
        """Check if a metric has drifted significantly from its EMA."""
        history = self._history.get(metric_name, [])
        if len(history) < self.window_size // 2:
            return None  # Not enough data

        ema = self._ema.get(metric_name)
        if ema is None:
            return None

        # Compare recent average to EMA
        recent = history[-self.window_size // 4:]
        recent_avg = sum(recent) / len(recent)

        # Drift = deviation from EMA normalized by EMA
        if abs(ema) < 0.001:
            drift_magnitude = abs(recent_avg - ema)
        else:
            drift_magnitude = abs(recent_avg - ema) / abs(ema)

        if drift_magnitude > self.sensitivity:
            direction = "increasing" if recent_avg > ema else "decreasing"
            return DriftSignal(
                drift_type=f"{metric_name}_drift",
                severity=min(1.0, drift_magnitude / (self.sensitivity * 3)),
                description=f"{metric_name} {direction}: EMA={ema:.3f}, recent={recent_avg:.3f}",
                source="drift_tracker"
            )
        return None

    def check_all(self) -> List[DriftSignal]:
        """Check all tracked metrics for drift."""
        signals = []
        for metric_name in self._history:
            signal = self.check_drift(metric_name)
            if signal:
                signals.append(signal)
                self._signals.append(signal)
        return signals

    def get_trend(self, metric_name: str) -> Optional[dict]:
        """Get the trend for a metric."""
        history = self._history.get(metric_name, [])
        if len(history) < 2:
            return None

        # Simple linear regression
        n = len(history)
        x_mean = (n - 1) / 2
        y_mean = sum(history) / n

        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(history))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        return {
            "metric": metric_name,
            "slope": round(slope, 6),
            "ema": round(self._ema.get(metric_name, 0), 3),
            "samples": n,
            "direction": "increasing" if slope > 0.001 else ("decreasing" if slope < -0.001 else "stable"),
        }

    def get_stats(self) -> dict:
        return {
            "tracked_metrics": list(self._history.keys()),
            "total_observations": sum(len(h) for h in self._history.values()),
            "total_signals": len(self._signals),
            "recent_signals": [s.to_dict() for s in self._signals[-5:]],
        }


if __name__ == "__main__":
    tracker = LongTermDriftTracker(window_size=50, sensitivity=0.15)

    # Simulate gradual drift
    import random
    for i in range(100):
        # Stable metric
        tracker.record("anchor_weight", 0.7 + random.gauss(0, 0.05))
        # Drifting metric (gradually increasing)
        tracker.record("entropy_load", 0.1 + i * 0.005 + random.gauss(0, 0.02))

    signals = tracker.check_all()
    print(f"Drift signals: {len(signals)}")
    for s in signals:
        print(f"  {s.to_dict()}")

    print(f"\nTrends:")
    for metric in tracker._history:
        trend = tracker.get_trend(metric)
        if trend:
            print(f"  {trend}")

    print(f"\nStats: {json.dumps(tracker.get_stats(), indent=2)}")
