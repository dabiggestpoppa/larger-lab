"""
9.5 Emergence Monitor
======================
Monitors the field for emergent behaviors and patterns.

Detects when new behaviors arise that were not explicitly programmed,
tracks their stability, and reports on the emergence landscape.

Emergence types:
- behavioral: new agent behavior patterns
- structural: new connection patterns in the agent network
- functional: new capabilities arising from composition
- informational: new knowledge patterns in the resonance bus
"""

import logging
import math
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.emergence.monitor")


class EmergenceEvent(BaseModel):
    """A detected emergence event."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    emergence_type: str  # behavioral, structural, functional, informational
    description: str
    confidence: float = 0.0
    stability: float = 0.0  # 0.0 = fleeting, 1.0 = persistent
    source_agents: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EmergenceMonitorConfig(BaseModel):
    """Configuration for emergence_monitor."""
    enabled: bool = True
    detection_window: int = 100
    confidence_threshold: float = 0.6
    stability_threshold: float = 0.5
    max_events: int = 5000
    baseline_decay: float = 0.995


class EmergenceMonitorModule:
    """Monitors the field for emergent behaviors and patterns."""

    def __init__(self):
        self.config = EmergenceMonitorConfig()
        self.running = False
        self._lock = Lock()
        self._events: List[EmergenceEvent] = []
        self._baselines: Dict[str, float] = {}  # metric_name -> baseline value
        self._observations: Dict[str, List[float]] = defaultdict(list)
        self._type_counts: Dict[str, int] = defaultdict(int)
        self._stable_events: Dict[str, EmergenceEvent] = {}  # description -> event

    def start(self) -> None:
        """Start the emergence monitor."""
        self.running = True
        logger.info("EmergenceMonitor started")

    def stop(self) -> None:
        """Stop the emergence monitor."""
        self.running = False
        logger.info("EmergenceMonitor stopped")

    def observe(self, metric_name: str, value: float, source_agents: Optional[List[str]] = None) -> Optional[EmergenceEvent]:
        """
        Submit an observation for emergence detection.

        Tracks the metric over time and detects when values deviate
        significantly from the established baseline, signaling potential emergence.

        Args:
            metric_name: Name of the metric being observed.
            value: Observed value.
            source_agents: Agents involved in this observation.

        Returns:
            EmergenceEvent if emergence detected, None otherwise.
        """
        with self._lock:
            self._observations[metric_name].append(value)

            # Trim observations
            if len(self._observations[metric_name]) > self.config.detection_window * 2:
                self._observations[metric_name] = self._observations[metric_name][-self.config.detection_window:]

            # Update baseline with exponential decay
            if metric_name in self._baselines:
                self._baselines[metric_name] = (
                    self.config.baseline_decay * self._baselines[metric_name]
                    + (1 - self.config.baseline_decay) * value
                )
            else:
                self._baselines[metric_name] = value

            # Detect emergence: significant deviation from baseline
            baseline = self._baselines[metric_name]
            if baseline == 0:
                baseline = 1e-10

            deviation = abs(value - baseline) / abs(baseline)

            # Compute confidence from recent observations
            recent = self._observations[metric_name][-self.config.detection_window:]
            if len(recent) >= 10:
                mean_recent = sum(recent) / len(recent)
                variance = sum((x - mean_recent) ** 2 for x in recent) / len(recent)
                std_dev = math.sqrt(variance) if variance > 0 else 1e-10
                confidence = min(1.0, deviation / (std_dev / abs(baseline) + 1e-10))
            else:
                confidence = 0.0

            if confidence >= self.config.confidence_threshold:
                # Determine emergence type from metric name
                em_type = self._classify_emergence(metric_name)

                event = EmergenceEvent(
                    emergence_type=em_type,
                    description=f"Emergence detected in '{metric_name}': value={value:.4f}, baseline={baseline:.4f}, deviation={deviation:.4f}",
                    confidence=round(confidence, 4),
                    stability=0.0,
                    source_agents=source_agents or [],
                    metadata={"metric": metric_name, "value": value, "baseline": baseline, "deviation": deviation},
                )

                # Check stability: has similar emergence been seen before?
                existing = self._stable_events.get(metric_name)
                if existing:
                    existing.stability = min(1.0, existing.stability + 0.1)
                    existing.confidence = max(existing.confidence, confidence)
                    event.stability = existing.stability
                    event.event_id = existing.event_id
                else:
                    self._stable_events[metric_name] = event

                self._events.append(event)
                self._type_counts[em_type] += 1

                # Trim events
                if len(self._events) > self.config.max_events:
                    self._events = self._events[-self.config.max_events:]

                logger.info("Emergence detected: %s (confidence=%.3f)", metric_name, confidence)
                return event

        return None

    def _classify_emergence(self, metric_name: str) -> str:
        """Classify the emergence type from metric name."""
        name_lower = metric_name.lower()
        if any(w in name_lower for w in ["behavior", "action", "response", "decision"]):
            return "behavioral"
        elif any(w in name_lower for w in ["connection", "link", "network", "topology", "graph"]):
            return "structural"
        elif any(w in name_lower for w in ["capability", "function", "compose", "synthesis"]):
            return "functional"
        elif any(w in name_lower for w in ["knowledge", "info", "pattern", "insight", "message"]):
            return "informational"
        return "behavioral"  # default

    def get_events(self, emergence_type: Optional[str] = None,
                   min_confidence: float = 0.0, limit: int = 100) -> List[Dict]:
        """Get emergence events, optionally filtered.

        Args:
            emergence_type: Filter by type.
            min_confidence: Minimum confidence threshold.
            limit: Max events to return.

        Returns:
            List of event dicts, most recent first.
        """
        with self._lock:
            events = list(reversed(self._events))
            if emergence_type:
                events = [e for e in events if e.emergence_type == emergence_type]
            events = [e for e in events if e.confidence >= min_confidence]
            return [e.model_dump() for e in events[:limit]]

    def get_stable_emergences(self, min_stability: Optional[float] = None) -> List[Dict]:
        """Get emergences that have become stable (persistent).

        Args:
            min_stability: Minimum stability threshold (default from config).

        Returns:
            List of stable emergence event dicts.
        """
        threshold = min_stability if min_stability is not None else self.config.stability_threshold
        with self._lock:
            return [e.model_dump() for e in self._stable_events.values() if e.stability >= threshold]

    def get_emergence_landscape(self) -> Dict[str, Any]:
        """Get a summary of the emergence landscape.

        Returns high-level view of what's emerging in the field.
        """
        with self._lock:
            total = len(self._events)
            stable = len([e for e in self._stable_events.values()
                         if e.stability >= self.config.stability_threshold])
            return {
                "total_events": total,
                "stable_emergences": stable,
                "by_type": dict(self._type_counts),
                "tracked_metrics": len(self._observations),
                "baselines_established": len(self._baselines),
                "confidence_threshold": self.config.confidence_threshold,
                "most_recent": self._events[-1].model_dump() if self._events else None,
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get module statistics."""
        return self.get_emergence_landscape()
