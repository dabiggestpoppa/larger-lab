"""
DSPy Observer Configuration Pipeline — OCE Phase 3
===================================================
Auto-configures observer parameters from event patterns.

Uses DSPy signatures and teleprompters to optimize observer
configuration for maximum throughput and minimum entropy cost.

Gracefully degrades to heuristic-based configuration when DSPy
is not installed.

Task: OCE-3.19
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from srrs_opc import (
    EntropyBudgetManager,
    CoherenceYieldAnalyzer,
    AdaptiveCompressionEngine,
    SyncCostOptimizer,
)

logger = logging.getLogger("oce.dspy.observer_config")

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    dspy = None


class ObserverConfigHeuristic:
    """Rule-based observer configuration (no DSPy required)."""

    @staticmethod
    def recommend(
        event_history: List[Dict],
        current_config: Dict[str, Any],
        performance_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate observer config recommendations from heuristics."""
        recommendations = {}

        # Analyze event throughput
        event_count = len(event_history)
        if event_count > 100:
            recommendations["recommended_event_types"] = _narrow_subscriptions(event_history)
            recommendations["recommended_priority"] = 2  # HIGH
        elif event_count > 20:
            recommendations["recommended_event_types"] = _current_or_expand(event_history)
            recommendations["recommended_priority"] = 1  # NORMAL
        else:
            recommendations["recommended_event_types"] = "observer.*, system.*"
            recommendations["recommended_priority"] = 0  # LOW

        # Analyze entropy consumption
        entropy_used = performance_metrics.get("entropy_consumed", 0)
        entropy_budget = performance_metrics.get("entropy_budget", 500)
        if entropy_budget > 0:
            usage_ratio = entropy_used / entropy_budget
            if usage_ratio > 0.8:
                recommendations["recommended_budget_allocation"] = 0.5  # Reduce
                recommendations["recommended_sync_frequency"] = 30  # Slow down
            elif usage_ratio < 0.2:
                recommendations["recommended_budget_allocation"] = 1.0  # Can use more
                recommendations["recommended_sync_frequency"] = 5   # Speed up
            else:
                recommendations["recommended_budget_allocation"] = 0.75
                recommendations["recommended_sync_frequency"] = 10

        # Analyze error rate
        error_rate = performance_metrics.get("error_rate", 0)
        if error_rate > 0.1:
            recommendations["recommended_event_types"] = _narrow_subscriptions(event_history)
            recommendations["recommended_priority"] = 3  # CRITICAL — focus on reliability

        # Analyze latency
        avg_latency = performance_metrics.get("avg_latency_ms", 0)
        if avg_latency > 1000:
            recommendations["recommended_sync_frequency"] = max(
                recommendations.get("recommended_sync_frequency", 10) * 2, 60
            )

        return recommendations


def _narrow_subscriptions(event_history: List[Dict]) -> str:
    """Narrow event subscriptions to only the most frequent types."""
    type_counts: Dict[str, int] = {}
    for event in event_history:
        etype = event.get("event_type", "unknown")
        # Group by prefix (e.g., "observer.state_change" -> "observer.*")
        prefix = ".".join(etype.split(".")[:2]) + ".*"
        type_counts[prefix] = type_counts.get(prefix, 0) + 1

    # Return top 3 most frequent
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    return ", ".join(t[0] for t in sorted_types[:3])


def _current_or_expand(event_history: List[Dict]) -> str:
    """Keep current subscriptions or slightly expand."""
    types = set()
    for event in event_history:
        etype = event.get("event_type", "")
        if etype:
            types.add(etype)
    if len(types) <= 5:
        return ", ".join(sorted(types))
    return _narrow_subscriptions(event_history)


if DSPY_AVAILABLE:
    class ObserverConfigSignature(dspy.Signature):
        """Optimize observer configuration from event patterns and performance data."""
        event_history = dspy.InputField(
            desc="Last 100 events processed by this observer (JSON)"
        )
        current_config = dspy.InputField(
            desc="Current observer configuration (JSON)"
        )
        performance_metrics = dspy.InputField(
            desc="Latency, accuracy, entropy consumption metrics (JSON)"
        )

        recommended_event_types = dspy.OutputField(
            desc="Optimal event type subscriptions (comma-separated, e.g., 'observer.*, system.*')"
        )
        recommended_priority = dspy.OutputField(
            desc="Optimal priority level (0=low, 1=normal, 2=high, 3=critical)"
        )
        recommended_budget_allocation = dspy.OutputField(
            desc="Entropy budget share (0.0-1.0, where 1.0 = full budget)"
        )
        recommended_sync_frequency = dspy.OutputField(
            desc="Sync interval in seconds (integer)"
        )


    class DSPyObserverConfigOptimizer(dspy.Module):
        """DSPy module for optimizing observer configuration."""

        def __init__(self):
            self.optimize = dspy.ChainOfThought(ObserverConfigSignature)

        def forward(
            self,
            event_history: List[Dict],
            current_config: Dict[str, Any],
            performance_metrics: Dict[str, Any],
        ) -> Dict[str, Any]:
            result = self.optimize(
                event_history=str(event_history[-100:]),
                current_config=str(current_config),
                performance_metrics=str(performance_metrics),
            )
            return {
                "recommended_event_types": result.recommended_event_types,
                "recommended_priority": int(result.recommended_priority),
                "recommended_budget_allocation": float(result.recommended_budget_allocation),
                "recommended_sync_frequency": int(result.recommended_sync_frequency),
            }


class ObserverConfigPipeline:
    """
    Observer configuration pipeline.
    Uses DSPy when available, falls back to heuristics.
    """

    def __init__(self, lm: Optional[Any] = None):
        self._dspy_available = DSPY_AVAILABLE
        self._heuristic = ObserverConfigHeuristic()
        self._optimizer = None
        if self._dspy_available:
            try:
                self._optimizer = DSPyObserverConfigOptimizer()
                if lm:
                    dspy.configure(lm=lm)
            except Exception as e:
                logger.warning(f"DSPy optimizer init failed, using heuristics: {e}")
                self._dspy_available = False

        # SRRA-OPH components for context
        self._entropy_budget = EntropyBudgetManager(global_budget=500.0)
        self._coherence_analyzer = CoherenceYieldAnalyzer()
        self._compression = AdaptiveCompressionEngine()
        self._sync_optimizer = SyncCostOptimizer()

    def recommend(
        self,
        event_history: List[Dict],
        current_config: Dict[str, Any],
        performance_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate observer configuration recommendations."""
        if self._dspy_available and self._optimizer:
            try:
                return self._optimizer(event_history, current_config, performance_metrics)
            except Exception as e:
                logger.warning(f"DSPy optimization failed, using heuristics: {e}")

        return self._heuristic.recommend(event_history, current_config, performance_metrics)

    def get_status(self) -> Dict[str, Any]:
        return {
            "dspy_available": self._dspy_available,
            "method": "dspy" if self._dspy_available else "heuristic",
            "components": {
                "entropy_budget": "active",
                "coherence_analyzer": "active",
                "compression": "active",
                "sync_optimizer": "active",
            },
        }
