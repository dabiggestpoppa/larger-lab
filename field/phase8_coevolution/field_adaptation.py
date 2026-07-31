"""
8_coevolution.field_adaptation
===============================
Field Adaptation Engine — adjusts field parameters based on
operator feedback, environmental changes, and performance metrics.

The adaptation engine monitors field behavior and automatically tunes
configuration parameters to optimize for accuracy, speed, and relevance.
Supports multiple adaptation strategies:
- reactive: respond to explicit feedback signals
- proactive: anticipate needs from usage patterns
- conservative: small incremental changes with rollback capability
- aggressive: larger changes when confidence is high

Each adaptation is tracked with before/after values and can be rolled
back if performance degrades.
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger("field.coevolution.field_adaptation")


class AdaptationRecord(BaseModel):
    """Record of a single adaptation event."""
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    parameter: str
    old_value: float
    new_value: float
    strategy: str  # reactive, proactive, conservative, aggressive
    reason: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    rolled_back: bool = False
    performance_delta: float = 0.0  # measured after adaptation


class AdaptationRule(BaseModel):
    """Rule for when and how to adapt a parameter."""
    parameter: str
    strategy: str = "conservative"
    min_value: float = 0.0
    max_value: float = 1.0
    step_size: float = 0.05
    cooldown_seconds: int = 60
    requires_approval: bool = False


class FieldAdaptationConfig(BaseModel):
    """Configuration for field_adaptation."""
    enabled: bool = True
    max_records: int = 10000
    default_strategy: str = "conservative"
    performance_window: int = 50
    rollback_threshold: float = -0.1  # rollback if performance drops by this much
    max_adaptations_per_hour: int = 20


class FieldAdaptationModule:
    """Field Adaptation Engine — tunes field parameters automatically."""

    def __init__(self):
        self.config = FieldAdaptationConfig()
        self.running = False
        self._lock = Lock()
        self._parameters: Dict[str, float] = {}
        self._records: List[AdaptationRecord] = []
        self._rules: Dict[str, AdaptationRule] = {}
        self._performance_history: Dict[str, List[float]] = defaultdict(list)
        self._last_adaptation_time: Dict[str, str] = {}
        self._hourly_counts: Dict[str, int] = defaultdict(int)
        self._adjustment_functions: Dict[str, Callable[[float, float], float]] = {}

    def start(self) -> None:
        """Start the adaptation engine."""
        self.running = True
        logger.info("FieldAdaptationModule started (strategy=%s)", self.config.default_strategy)

    def stop(self) -> None:
        """Stop the adaptation engine."""
        self.running = False
        logger.info("FieldAdaptationModule stopped with %d adaptations", len(self._records))

    def register_parameter(self, name: str, initial_value: float,
                           rule: Optional[AdaptationRule] = None) -> None:
        """Register a tunable parameter.

        Args:
            name: Parameter name.
            initial_value: Starting value.
            rule: Optional adaptation rule for this parameter.
        """
        with self._lock:
            self._parameters[name] = initial_value
            if rule:
                self._rules[name] = rule
            else:
                self._rules[name] = AdaptationRule(parameter=name)
        logger.debug("Registered parameter: %s = %.4f", name, initial_value)

    def get_parameter(self, name: str) -> Optional[float]:
        """Get the current value of a parameter."""
        with self._lock:
            return self._parameters.get(name)

    def get_all_parameters(self) -> Dict[str, float]:
        """Get all registered parameter values."""
        with self._lock:
            return dict(self._parameters)

    def set_parameter(self, name: str, value: float, reason: str = "manual") -> bool:
        """Manually set a parameter value.

        Args:
            name: Parameter name.
            value: New value.
            reason: Reason for the change.

        Returns:
            True if the parameter was updated.
        """
        with self._lock:
            if name not in self._parameters:
                logger.warning("Unknown parameter: %s", name)
                return False

            rule = self._rules.get(name)
            if rule:
                value = max(rule.min_value, min(rule.max_value, value))

            old_value = self._parameters[name]
            self._parameters[name] = value

            record = AdaptationRecord(
                parameter=name,
                old_value=old_value,
                new_value=value,
                strategy="manual",
                reason=reason,
            )
            self._records.append(record)
            self._trim_records()

        logger.info("Parameter %s set: %.4f -> %.4f (%s)", name, old_value, value, reason)
        return True

    def adapt(self, parameter: str, feedback_signal: float,
              strategy: str = "") -> Optional[AdaptationRecord]:
        """
        Adapt a parameter based on a feedback signal.

        Args:
            parameter: Parameter to adapt.
            feedback_signal: Feedback value (-1.0 to 1.0, negative=decrease, positive=increase).
            strategy: Adaptation strategy override.

        Returns:
            AdaptationRecord if adaptation was made, None if skipped.
        """
        if not self.running:
            return None

        with self._lock:
            if parameter not in self._parameters:
                logger.warning("Cannot adapt unknown parameter: %s", parameter)
                return None

            rule = self._rules.get(parameter, AdaptationRule(parameter=parameter))
            strat = strategy or rule.strategy or self.config.default_strategy

            # Check cooldown
            last_time = self._last_adaptation_time.get(parameter)
            if last_time:
                try:
                    elapsed = (datetime.now(timezone.utc) -
                               datetime.fromisoformat(last_time)).total_seconds()
                    if elapsed < rule.cooldown_seconds:
                        logger.debug("Parameter %s in cooldown (%.0fs remaining)",
                                     parameter, rule.cooldown_seconds - elapsed)
                        return None
                except (ValueError, TypeError):
                    pass

            # Check hourly limit
            if self._hourly_counts[parameter] >= self.config.max_adaptations_per_hour:
                logger.warning("Hourly adaptation limit reached for %s", parameter)
                return None

            # Compute step
            step = rule.step_size
            if strat == "aggressive":
                step *= 3.0
            elif strat == "conservative":
                step *= 0.5

            delta = feedback_signal * step
            old_value = self._parameters[parameter]
            new_value = old_value + delta
            new_value = max(rule.min_value, min(rule.max_value, new_value))

            # Apply change
            self._parameters[parameter] = round(new_value, 6)
            self._last_adaptation_time[parameter] = datetime.now(timezone.utc).isoformat()
            self._hourly_counts[parameter] += 1

            record = AdaptationRecord(
                parameter=parameter,
                old_value=old_value,
                new_value=round(new_value, 6),
                strategy=strat,
                reason=f"feedback_signal={feedback_signal:.4f}",
            )
            self._records.append(record)
            self._trim_records()

        logger.info("Adapted %s: %.4f -> %.4f (strategy=%s, signal=%.4f)",
                     parameter, old_value, new_value, strat, feedback_signal)
        return record

    def record_performance(self, metric_name: str, value: float) -> None:
        """Record a performance metric for rollback evaluation.

        Args:
            metric_name: Name of the performance metric.
            value: Metric value (higher is better).
        """
        with self._lock:
            self._performance_history[metric_name].append(value)
            if len(self._performance_history[metric_name]) > self.config.performance_window:
                self._performance_history[metric_name] = \
                    self._performance_history[metric_name][-self.config.performance_window:]

            # Check if recent adaptations should be rolled back
            self._check_rollback(metric_name)

    def _check_rollback(self, metric_name: str) -> None:
        """Check if recent adaptations hurt performance and should be rolled back."""
        history = self._performance_history.get(metric_name, [])
        if len(history) < 10:
            return

        recent_avg = sum(history[-5:]) / 5
        older_avg = sum(history[-10:-5]) / 5

        if older_avg == 0:
            return

        delta = (recent_avg - older_avg) / abs(older_avg)

        if delta < self.config.rollback_threshold:
            # Find the most recent non-rolled-back adaptation
            for record in reversed(self._records):
                if not record.rolled_back:
                    # Roll back
                    self._parameters[record.parameter] = record.old_value
                    record.rolled_back = True
                    record.performance_delta = delta
                    logger.warning(
                        "Rolled back %s: %.4f -> %.4f (performance dropped %.1f%%)",
                        record.parameter, record.new_value, record.old_value, abs(delta) * 100
                    )
                    break

    def rollback(self, record_id: str) -> bool:
        """Roll back a specific adaptation by record ID.

        Args:
            record_id: The adaptation record to roll back.

        Returns:
            True if rolled back successfully.
        """
        with self._lock:
            for record in self._records:
                if record.record_id == record_id and not record.rolled_back:
                    self._parameters[record.parameter] = record.old_value
                    record.rolled_back = True
                    logger.info("Rolled back adaptation %s: %s -> %.4f",
                                record_id, record.parameter, record.old_value)
                    return True
        return False

    def get_adaptations(self, parameter: Optional[str] = None,
                        limit: int = 100) -> List[Dict]:
        """Get adaptation records, optionally filtered by parameter."""
        with self._lock:
            records = list(reversed(self._records))
            if parameter:
                records = [r for r in records if r.parameter == parameter]
            return [r.model_dump() for r in records[:limit]]

    def get_stats(self) -> Dict[str, Any]:
        """Get adaptation engine statistics."""
        with self._lock:
            total = len(self._records)
            rolled_back = sum(1 for r in self._records if r.rolled_back)
            strategy_counts: Dict[str, int] = defaultdict(int)
            for r in self._records:
                strategy_counts[r.strategy] += 1
            return {
                "total_adaptations": total,
                "rolled_back": rolled_back,
                "active_adaptations": total - rolled_back,
                "registered_parameters": len(self._parameters),
                "strategy_distribution": dict(strategy_counts),
                "current_parameters": dict(self._parameters),
            }

    def _trim_records(self) -> None:
        """Trim records to max limit."""
        if len(self._records) > self.config.max_records:
            self._records = self._records[-self.config.max_records:]
