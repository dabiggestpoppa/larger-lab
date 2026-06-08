"""
5_continuity.temporal_reasoner
=================================
Temporal reasoning over field events — sequences, trends, periodicity.

Analyzes event streams across time to detect patterns, trends,
and periodic behaviors in field activity.
"""

import logging
import math
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.temporal_reasoner")


class TemporalReasonerConfig(BaseModel):
    """Configuration for temporal_reasoner."""
    enabled: bool = True
    max_events: int = 100000
    trend_window_sec: float = 3600.0
    min_events_for_trend: int = 10


class TemporalEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    data: Dict[str, Any] = Field(default_factory=dict)


class TrendInfo(BaseModel):
    event_type: str
    direction: str  # "increasing", "decreasing", "stable"
    slope: float  # events per second change
    r_squared: float  # goodness of fit
    window_start: str
    window_end: str
    event_count: int


class PeriodInfo(BaseModel):
    event_type: str
    period_seconds: Optional[float] = None
    confidence: float = 0.0
    sample_count: int = 0


class TemporalReasonerModule:
    """Temporal reasoning over field events."""

    def __init__(self):
        self.config = TemporalReasonerConfig()
        self.running = False
        self._events: List[TemporalEvent] = []
        self._event_counts: Dict[str, int] = defaultdict(int)
        self._lock = Lock()

    def start(self) -> None:
        """Start the module."""
        self.running = True
        logger.info("TemporalReasoner started")

    def stop(self) -> None:
        """Stop the module."""
        self.running = False
        logger.info("TemporalReasoner stopped")

    def record_event(self, event_id: str, event_type: str,
                     timestamp: Optional[str] = None,
                     data: Optional[Dict[str, Any]] = None) -> None:
        """Record a temporal event."""
        with self._lock:
            event = TemporalEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
                data=data or {},
            )
            self._events.append(event)
            self._event_counts[event_type] += 1
            # Evict oldest if over max
            if len(self._events) > self.config.max_events:
                removed = self._events.pop(0)
                self._event_counts[removed.event_type] -= 1

    def get_sequence(self, event_type: str,
                     since: Optional[str] = None,
                     until: Optional[str] = None) -> List[TemporalEvent]:
        """Get event sequence for a type within time range."""
        with self._lock:
            filtered = [e for e in self._events if e.event_type == event_type]
            if since:
                filtered = [e for e in filtered if e.timestamp >= since]
            if until:
                filtered = [e for e in filtered if e.timestamp <= until]
            return filtered

    def detect_trend(self, event_type: str,
                     window: Optional[float] = None) -> TrendInfo:
        """Detect trend for an event type using simple linear regression."""
        window = window or self.config.trend_window_sec
        with self._lock:
            events = [e for e in self._events if e.event_type == event_type]

        if len(events) < self.config.min_events_for_trend:
            return TrendInfo(
                event_type=event_type, direction="stable", slope=0.0,
                r_squared=0.0, window_start="", window_end="",
                event_count=len(events),
            )

        # Bin events into time buckets (10 buckets across window)
        now = datetime.now(timezone.utc)
        window_start_ts = now.timestamp() - window
        buckets = [0] * 10
        bucket_size = window / 10

        for e in events:
            try:
                e_ts = datetime.fromisoformat(e.timestamp).timestamp()
                if e_ts >= window_start_ts:
                    bucket_idx = int((e_ts - window_start_ts) / bucket_size)
                    if 0 <= bucket_idx < 10:
                        buckets[bucket_idx] += 1
            except (ValueError, OSError):
                continue

        # Simple linear regression on bucket counts
        n = len(buckets)
        if n == 0:
            return TrendInfo(
                event_type=event_type, direction="stable", slope=0.0,
                r_squared=0.0, window_start="", window_end="",
                event_count=len(events),
            )

        x_mean = (n - 1) / 2.0
        y_mean = sum(buckets) / n

        numerator = sum((i - x_mean) * (b - y_mean) for i, b in enumerate(buckets))
        denom_x = sum((i - x_mean) ** 2 for i in range(n))
        denom_y = sum((b - y_mean) ** 2 for b in buckets)

        if denom_x == 0:
            slope = 0.0
        else:
            slope = numerator / denom_x

        if denom_x == 0 or denom_y == 0:
            r_squared = 0.0
        else:
            r_squared = (numerator ** 2) / (denom_x * denom_y)

        # Classify direction
        if abs(slope) < 0.01:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        return TrendInfo(
            event_type=event_type,
            direction=direction,
            slope=round(slope, 6),
            r_squared=round(r_squared, 4),
            window_start=datetime.fromtimestamp(window_start_ts, tz=timezone.utc).isoformat(),
            window_end=now.isoformat(),
            event_count=sum(buckets),
        )

    def detect_periodicity(self, event_type: str) -> PeriodInfo:
        """Detect periodicity in event occurrences."""
        with self._lock:
            events = [e for e in self._events if e.event_type == event_type]

        if len(events) < 20:
            return PeriodInfo(event_type=event_type, sample_count=len(events))

        # Compute inter-event intervals
        timestamps = []
        for e in events:
            try:
                timestamps.append(datetime.fromisoformat(e.timestamp).timestamp())
            except (ValueError, OSError):
                continue

        timestamps.sort()
        intervals = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]

        if not intervals:
            return PeriodInfo(event_type=event_type, sample_count=len(events))

        # Check for periodicity: low variance in intervals suggests periodicity
        mean_interval = sum(intervals) / len(intervals)
        if mean_interval == 0:
            return PeriodInfo(event_type=event_type, sample_count=len(events))

        variance = sum((i - mean_interval) ** 2 for i in intervals) / len(intervals)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean_interval if mean_interval > 0 else float('inf')

        # Low coefficient of variation = periodic
        confidence = max(0.0, 1.0 - cv)

        return PeriodInfo(
            event_type=event_type,
            period_seconds=round(mean_interval, 2) if confidence > 0.5 else None,
            confidence=round(confidence, 4),
            sample_count=len(events),
        )

    def get_temporal_stats(self) -> Dict[str, Any]:
        """Get temporal reasoning statistics."""
        with self._lock:
            return {
                "total_events": len(self._events),
                "event_types": dict(self._event_counts),
                "unique_types": len(self._event_counts),
                "capacity_used_pct": round(len(self._events) / self.config.max_events * 100, 2),
            }
