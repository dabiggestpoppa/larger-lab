"""
9_emergence.field_drift_correction
===================================
Detects and corrects field-wide parameter drift over time.

Monitors key field metrics for gradual drift away from optimal
operating points. When drift exceeds configurable thresholds,
generates correction signals to bring the field back into alignment.

Drift types:
- baseline_drift: gradual shift in baseline metrics
- variance_drift: change in metric volatility
- correlation_drift: breakdown in expected correlations between metrics
- boundary_drift: field operating near or beyond safe boundaries

The module maintains a drift model for each tracked metric and
applies exponential smoothing to distinguish genuine drift from
normal fluctuation.
"""

import logging
import math
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger("field.emergence.drift_correction")


class DriftSignal(BaseModel):
    """A detected drift signal."""
    signal_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    metric_name: str
    drift_type: str  # baseline, variance, correlation, boundary
    severity: float = 0.0  # 0=none, 1=critical
    direction: str = "positive"  # positive, negative
    current_value: float = 0.0
    expected_value: float = 0.0
    correction_delta: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    corrected: bool = False


class MetricModel(BaseModel):
    """Drift model for a single metric."""
    metric_name: str
    baseline: float = 0.0
    variance: float = 0.0
    sample_count: int = 0
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    drift_detected: bool = False


class FieldDriftCorrectionConfig(BaseModel):
    """Configuration for field_drift_correction."""
    enabled: bool = True
    baseline_window: int = 200
    variance_window: int = 100
    drift_threshold: float = 0.15
    critical_threshold: float = 0.4
    correction_strength: float = 0.3
    smoothing_factor: float = 0.05
    max_signals: int = 5000
    boundary_margin: float = 0.1


class FieldDriftCorrectionModule:
    """Detects and corrects field-wide parameter drift."""

    def __init__(self):
        self.config = FieldDriftCorrectionConfig()
        self.running = False
        self._lock = Lock()
        self._metric_models: Dict[str, MetricModel] = {}
        self._observations: Dict[str, List[float]] = defaultdict(list)
        self._signals: List[DriftSignal] = []
        self._corrections_applied: int = 0
        self._total_observations: int = 0

    def start(self) -> None:
        self.running = True
        logger.info("FieldDriftCorrection started")

    def stop(self) -> None:
        self.running = False
        logger.info("FieldDriftCorrection stopped — %d corrections applied from %d signals",
                     self._corrections_applied, len(self._signals))

    def observe(self, metric_name: str, value: float) -> Optional[DriftSignal]:
        """
        Submit a metric observation for drift detection.

        Maintains a running baseline and variance model for each metric.
        When a new observation deviates significantly from the model,
        a drift signal is generated with a correction delta.

        Args:
            metric_name: Name of the metric.
            value: Observed value.

        Returns:
            DriftSignal if drift detected, None otherwise.
        """
        with self._lock:
            self._total_observations += 1

            # Initialize model if new metric
            if metric_name not in self._metric_models:
                self._metric_models[metric_name] = MetricModel(
                    metric_name=metric_name,
                    baseline=value,
                    variance=0.0,
                    sample_count=1,
                )
                self._observations[metric_name].append(value)
                return None

            model = self._metric_models[metric_name]
            self._observations[metric_name].append(value)

            # Trim observations
            max_win = max(self.config.baseline_window, self.config.variance_window) * 2
            if len(self._observations[metric_name]) > max_win:
                self._observations[metric_name] = self._observations[metric_name][-max_win:]

            # Update baseline with exponential smoothing
            alpha = self.config.smoothing_factor
            old_baseline = model.baseline
            model.baseline = alpha * value + (1 - alpha) * old_baseline

            # Update variance
            recent = self._observations[metric_name][-self.config.variance_window:]
            if len(recent) >= 5:
                mean = sum(recent) / len(recent)
                model.variance = sum((x - mean) ** 2 for x in recent) / len(recent)

            model.sample_count += 1
            model.last_updated = datetime.now(timezone.utc).isoformat()

            # Detect drift
            if model.sample_count < 10:
                return None

            deviation = abs(value - old_baseline)
            std_dev = math.sqrt(model.variance) if model.variance > 0 else 1e-10
            normalized_drift = deviation / (std_dev + 1e-10)

            if normalized_drift < self.config.drift_threshold:
                model.drift_detected = False
                return None

            # Classify drift type
            drift_type = self._classify_drift(metric_name, value, old_baseline, model)

            # Determine severity
            if normalized_drift >= self.config.critical_threshold:
                severity = min(1.0, normalized_drift / (self.config.critical_threshold * 2))
            else:
                severity = normalized_drift / self.config.critical_threshold * 0.5

            # Compute correction
            direction = "positive" if value > old_baseline else "negative"
            correction_delta = -self.config.correction_strength * (value - old_baseline)

            signal = DriftSignal(
                metric_name=metric_name,
                drift_type=drift_type,
                severity=round(severity, 4),
                direction=direction,
                current_value=round(value, 6),
                expected_value=round(old_baseline, 6),
                correction_delta=round(correction_delta, 6),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            self._signals.append(signal)
            model.drift_detected = True

            # Trim signals
            if len(self._signals) > self.config.max_signals:
                self._signals = self._signals[-self.config.max_signals:]

            logger.info("Drift detected: %s — type=%s severity=%.3f correction=%.6f",
                        metric_name, drift_type, severity, correction_delta)
            return signal

    def _classify_drift(self, metric_name: str, value: float,
                        baseline: float, model: MetricModel) -> str:
        """Classify the type of drift."""
        name_lower = metric_name.lower()

        # Boundary drift: value near 0 or 1 for normalized metrics
        if any(w in name_lower for w in ["ratio", "rate", "score", "utilization", "load"]):
            if value > (1.0 - self.config.boundary_margin) or value < self.config.boundary_margin:
                return "boundary"

        # Variance drift: check if variance itself has changed significantly
        if model.sample_count > 50:
            recent = self._observations[metric_name][-50:]
            older = self._observations[metric_name][-100:-50] if len(self._observations[metric_name]) >= 100 else []
            if older:
                old_mean = sum(older) / len(older)
                old_var = sum((x - old_mean) ** 2 for x in older) / len(older)
                new_mean = sum(recent) / len(recent)
                new_var = sum((x - new_mean) ** 2 for x in recent) / len(recent)
                if old_var > 0 and abs(new_var - old_var) / old_var > 0.5:
                    return "variance"

        # Correlation drift: check for breakdown in expected relationships
        if any(w in name_lower for w in ["correlation", "covariance", "sync"]):
            return "correlation"

        return "baseline"

    def apply_correction(self, signal_id: str) -> Optional[float]:
        """
        Mark a drift signal as corrected and return the correction delta.

        Args:
            signal_id: The signal to apply correction for.

        Returns:
            The correction delta, or None if signal not found.
        """
        with self._lock:
            for signal in self._signals:
                if signal.signal_id == signal_id and not signal.corrected:
                    signal.corrected = True
                    self._corrections_applied += 1
                    logger.info("Correction applied for %s: delta=%.6f",
                                signal.metric_name, signal.correction_delta)
                    return signal.correction_delta
        return None

    def get_signals(self, drift_type: Optional[str] = None,
                    min_severity: float = 0.0,
                    uncorrected_only: bool = False,
                    limit: int = 100) -> List[Dict]:
        """
        Get drift signals, optionally filtered.

        Args:
            drift_type: Filter by drift type.
            min_severity: Minimum severity threshold.
            uncorrected_only: Only return uncorrected signals.
            limit: Max signals to return.

        Returns:
            List of signal dicts, most recent first.
        """
        with self._lock:
            signals = list(reversed(self._signals))
            if drift_type:
                signals = [s for s in signals if s.drift_type == drift_type]
            signals = [s for s in signals if s.severity >= min_severity]
            if uncorrected_only:
                signals = [s for s in signals if not s.corrected]
            return [s.model_dump() for s in signals[:limit]]

    def get_metric_status(self, metric_name: str) -> Optional[Dict]:
        """
        Get the drift model status for a metric.

        Returns:
            Dict with baseline, variance, sample_count, drift_detected.
        """
        with self._lock:
            model = self._metric_models.get(metric_name)
            if not model:
                return None
            return {
                "metric_name": model.metric_name,
                "baseline": round(model.baseline, 6),
                "variance": round(model.variance, 6),
                "sample_count": model.sample_count,
                "drift_detected": model.drift_detected,
                "last_updated": model.last_updated,
            }

    def get_all_metric_statuses(self) -> List[Dict]:
        """Get drift model status for all tracked metrics."""
        with self._lock:
            return [
                {
                    "metric_name": m.metric_name,
                    "baseline": round(m.baseline, 6),
                    "variance": round(m.variance, 6),
                    "sample_count": m.sample_count,
                    "drift_detected": m.drift_detected,
                }
                for m in self._metric_models.values()
            ]

    def get_drift_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current drift landscape.

        Returns:
            Dict with total metrics, drifting metrics, total signals,
            uncorrected signals, and corrections applied.
        """
        with self._lock:
            drifting = sum(1 for m in self._metric_models.values() if m.drift_detected)
            uncorrected = sum(1 for s in self._signals if not s.corrected)
            type_counts: Dict[str, int] = defaultdict(int)
            for s in self._signals:
                type_counts[s.drift_type] += 1
            return {
                "total_metrics": len(self._metric_models),
                "drifting_metrics": drifting,
                "total_signals": len(self._signals),
                "uncorrected_signals": uncorrected,
                "corrections_applied": self._corrections_applied,
                "total_observations": self._total_observations,
                "drift_type_counts": dict(type_counts),
            }
