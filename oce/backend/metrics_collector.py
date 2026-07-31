"""
OCE Metrics Collector — Phase 5.1
=================================
Collects and aggregates metrics for all OCE subsystems:
- Event throughput (rates, latency, counts by type/source)
- Observer health (health_score, entropy, error rates)
- Memory usage (size, entry count, compression ratio)
- Entropy budget (consumed, remaining, burn rate)

Rolling windows: 1min, 5min, 1hr + SQLite for historical queries.
Singleton pattern consistent with existing OCE engines.
"""

import sqlite3
import json
import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("oce.metrics")

# ─── Constants ───────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "metrics.db"

# Window sizes in seconds
WINDOW_1MIN = 60
WINDOW_5MIN = 300
WINDOW_1HR = 3600


# ─── Data Models ─────────────────────────────────────────────────────────────

class MetricSnapshot(BaseModel):
    """A single metric data point."""
    metric_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RollingCounter:
    """Time-windowed counter that expires old entries."""

    def __init__(self, window_seconds: int):
        self.window = window_seconds
        self._entries: List[tuple] = []  # (timestamp_unix, value)

    def add(self, value: float = 1.0):
        now = time.time()
        self._entries.append((now, value))
        self._prune(now)

    def count(self) -> float:
        now = time.time()
        self._prune(now)
        return sum(v for _, v in self._entries)

    def rate_per_second(self) -> float:
        now = time.time()
        self._prune(now)
        if len(self._entries) < 2:
            return 0.0
        elapsed = self._entries[-1][0] - self._entries[0][0]
        if elapsed <= 0:
            return 0.0
        return sum(v for _, v in self._entries) / elapsed

    def _prune(self, now: float):
        cutoff = now - self.window
        self._entries = [(t, v) for t, v in self._entries if t >= cutoff]


class LatencyTracker:
    """Tracks latency statistics within a rolling window."""

    def __init__(self, window_seconds: int):
        self.window = window_seconds
        self._entries: List[tuple] = []  # (timestamp_unix, latency_ms)

    def record(self, latency_ms: float):
        now = time.time()
        self._entries.append((now, latency_ms))
        self._prune(now)

    def avg(self) -> float:
        now = time.time()
        self._prune(now)
        if not self._entries:
            return 0.0
        return sum(l for _, l in self._entries) / len(self._entries)

    def p95(self) -> float:
        now = time.time()
        self._prune(now)
        if not self._entries:
            return 0.0
        sorted_latencies = sorted(l for _, l in self._entries)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]

    def p99(self) -> float:
        now = time.time()
        self._prune(now)
        if not self._entries:
            return 0.0
        sorted_latencies = sorted(l for _, l in self._entries)
        idx = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]

    def count(self) -> int:
        now = time.time()
        self._prune(now)
        return len(self._entries)

    def _prune(self, now: float):
        cutoff = now - self.window
        self._entries = [(t, l) for t, l in self._entries if t >= cutoff]


# ─── Metrics Collector ───────────────────────────────────────────────────────

class MetricsCollector:
    """
    Singleton metrics collector for OCE.

    Tracks:
    - Event metrics: throughput, latency, counts by type/source
    - Observer metrics: health scores, entropy, error rates
    - Memory metrics: usage by layer, entry counts, compression ratios
    - Entropy metrics: budget consumption, burn rate

    All counters use rolling windows (1min, 5min, 1hr).
    Historical data persisted to SQLite.
    """

    _instance: Optional["MetricsCollector"] = None
    _lock = Lock()

    def __new__(cls) -> "MetricsCollector":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        # Event metrics
        self._event_counters: Dict[str, RollingCounter] = defaultdict(
            lambda: RollingCounter(WINDOW_1HR)
        )
        self._event_latency = LatencyTracker(WINDOW_1HR)
        self._event_type_counters: Dict[str, RollingCounter] = defaultdict(
            lambda: RollingCounter(WINDOW_1HR)
        )
        self._event_source_counters: Dict[str, RollingCounter] = defaultdict(
            lambda: RollingCounter(WINDOW_1HR)
        )

        # Observer metrics
        self._observer_health: Dict[str, float] = {}
        self._observer_entropy: Dict[str, float] = {}
        self._observer_error_counters: Dict[str, RollingCounter] = defaultdict(
            lambda: RollingCounter(WINDOW_1HR)
        )
        self._observer_event_counters: Dict[str, RollingCounter] = defaultdict(
            lambda: RollingCounter(WINDOW_1HR)
        )

        # Memory metrics
        self._memory_layer_size: Dict[str, int] = {}
        self._memory_layer_entries: Dict[str, int] = {}
        self._memory_compression_ratio: Dict[str, float] = {}

        # Entropy metrics
        self._entropy_consumed = RollingCounter(WINDOW_1HR)
        self._entropy_total: float = 1000.0  # configurable
        self._entropy_remaining: float = 1000.0

        # Snapshot history
        self._snapshots: List[Dict[str, Any]] = []
        self._max_snapshots = 1000

        # Initialize SQLite
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info("MetricsCollector initialized")

    def _init_db(self):
        """Initialize SQLite database for historical metrics."""
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metric_snapshots (
                    id TEXT PRIMARY KEY,
                    snapshot_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_created
                ON metric_snapshots(created_at)
            """)
            conn.commit()

    # ─── Event Metrics ────────────────────────────────────────────────────

    def record_event(self, event_type: str, source: str, latency_ms: float = 0.0):
        """Record an event passing through the fabric."""
        self._event_counters["total"].add(1)
        self._event_type_counters[event_type].add(1)
        self._event_source_counters[source].add(1)
        if latency_ms > 0:
            self._event_latency.record(latency_ms)

    def get_event_rate(self, window: str = "total") -> float:
        """Get event rate (events/sec) for a given counter."""
        counter = self._event_counters.get(window)
        if counter is None:
            return 0.0
        return counter.rate_per_second()

    def get_event_count(self, window: str = "total") -> float:
        """Get total event count in the rolling window."""
        counter = self._event_counters.get(window)
        if counter is None:
            return 0.0
        return counter.count()

    def get_event_type_count(self, event_type: str) -> float:
        """Get count for a specific event type."""
        return self._event_type_counters[event_type].count()

    def get_event_latency_stats(self) -> Dict[str, float]:
        """Get latency statistics (avg, p95, p99)."""
        return {
            "avg_ms": round(self._event_latency.avg(), 2),
            "p95_ms": round(self._event_latency.p95(), 2),
            "p99_ms": round(self._event_latency.p99(), 2),
            "count": self._event_latency.count(),
        }

    # ─── Observer Metrics ─────────────────────────────────────────────────

    def record_observer_health(self, observer_id: str, health_score: float, entropy: float):
        """Record observer health snapshot."""
        self._observer_health[observer_id] = health_score
        self._observer_entropy[observer_id] = entropy

    def record_observer_error(self, observer_id: str):
        """Record an observer error."""
        self._observer_error_counters[observer_id].add(1)

    def record_observer_event(self, observer_id: str):
        """Record an event processed by an observer."""
        self._observer_event_counters[observer_id].add(1)

    def get_observer_health(self, observer_id: str) -> float:
        return self._observer_health.get(observer_id, 0.0)

    def get_observer_error_rate(self, observer_id: str) -> float:
        """Get error rate (errors/sec) for an observer."""
        return self._observer_error_counters[observer_id].rate_per_second()

    def get_avg_health(self) -> float:
        """Get average health across all observers."""
        if not self._observer_health:
            return 1.0
        return sum(self._observer_health.values()) / len(self._observer_health)

    # ─── Memory Metrics ───────────────────────────────────────────────────

    def record_memory_usage(self, layer: str, size_bytes: int, entry_count: int):
        """Record memory usage for a layer."""
        self._memory_layer_size[layer] = size_bytes
        self._memory_layer_entries[layer] = entry_count

    def record_compression_ratio(self, layer: str, ratio: float):
        """Record compression ratio for a layer."""
        self._memory_compression_ratio[layer] = ratio

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        total_size = sum(self._memory_layer_size.values())
        total_entries = sum(self._memory_layer_entries.values())
        return {
            "total_size_bytes": total_size,
            "total_entries": total_entries,
            "layers": {
                layer: {
                    "size_bytes": self._memory_layer_size.get(layer, 0),
                    "entries": self._memory_layer_entries.get(layer, 0),
                    "compression_ratio": self._memory_compression_ratio.get(layer, 1.0),
                }
                for layer in set(
                    list(self._memory_layer_size.keys())
                    + list(self._memory_layer_entries.keys())
                )
            },
        }

    # ─── Entropy Metrics ──────────────────────────────────────────────────

    def record_entropy_budget(self, consumed: float, remaining: float, total: float):
        """Record entropy budget state."""
        self._entropy_consumed.add(consumed)
        self._entropy_remaining = remaining
        self._entropy_total = total

    def get_entropy_stats(self) -> Dict[str, float]:
        """Get entropy budget statistics."""
        total = self._entropy_total if self._entropy_total > 0 else 1.0
        return {
            "consumed": self._entropy_consumed.count(),
            "remaining": self._entropy_remaining,
            "total": self._entropy_total,
            "usage_pct": round(
                (self._entropy_consumed.count() / total) * 100, 2
            ),
        }

    # ─── Summary & History ────────────────────────────────────────────────

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a full metrics snapshot."""
        now = datetime.now(timezone.utc).isoformat()
        summary = {
            "timestamp": now,
            "events": {
                "total_count": self.get_event_count("total"),
                "rate_per_sec": round(self.get_event_rate("total"), 2),
                "latency": self.get_event_latency_stats(),
                "by_type": {
                    et: cnt.count()
                    for et, cnt in self._event_type_counters.items()
                },
                "by_source": {
                    src: cnt.count()
                    for src, cnt in self._event_source_counters.items()
                },
            },
            "observers": {
                "count": len(self._observer_health),
                "avg_health": round(self.get_avg_health(), 3),
                "by_id": {
                    oid: {
                        "health": self._observer_health.get(oid, 0.0),
                        "entropy": self._observer_entropy.get(oid, 0.0),
                        "error_rate": round(self.get_observer_error_rate(oid), 4),
                    }
                    for oid in self._observer_health
                },
            },
            "memory": self.get_memory_stats(),
            "entropy": self.get_entropy_stats(),
        }
        return summary

    def get_metrics_history(
        self, metric_name: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical snapshots filtered by metric name."""
        results = []
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT snapshot_json, created_at FROM metric_snapshots ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            for row in rows:
                snapshot = json.loads(row["snapshot_json"])
                # Extract the requested metric path
                parts = metric_name.split(".")
                val = snapshot
                for part in parts:
                    if isinstance(val, dict):
                        val = val.get(part)
                    else:
                        val = None
                        break
                results.append({
                    "timestamp": row["created_at"],
                    "value": val,
                })
        return results

    def save_snapshot(self):
        """Persist current metrics snapshot to SQLite."""
        summary = self.get_metrics_summary()
        snapshot_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                "INSERT INTO metric_snapshots (id, snapshot_json, created_at) VALUES (?, ?, ?)",
                (snapshot_id, json.dumps(summary), now),
            )
            conn.commit()
        # Also keep in-memory
        self._snapshots.append(summary)
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots = self._snapshots[-self._max_snapshots:]

    def reset_counters(self):
        """Reset all rolling counters."""
        self._event_counters.clear()
        self._event_type_counters.clear()
        self._event_source_counters.clear()
        self._observer_error_counters.clear()
        self._observer_event_counters.clear()
        self._entropy_consumed = RollingCounter(WINDOW_1HR)
        logger.info("Metrics counters reset")


# ─── Singleton Access ───────────────────────────────────────────────────────

def get_metrics_collector() -> MetricsCollector:
    """Get the singleton MetricsCollector instance."""
    return MetricsCollector()
