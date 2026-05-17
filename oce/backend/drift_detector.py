"""
OCE Drift Detector — Phase 7.1
===============================
Detects performance degradation in execution metrics over time.

Monitors:
- Latency trends (increasing = degradation)
- Error rate trends (increasing = degradation)
- Throughput trends (decreasing = degradation)
- Queue depth trends (increasing = bottleneck)

Rolling windows: 1hr, 6hr, 24hr, 7day
Singleton pattern consistent with existing OCE engines.
"""

import sqlite3
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("oce.drift")

# ─── Constants ───────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "drift.db"

WINDOW_1HR = 3600
WINDOW_6HR = 21600
WINDOW_24HR = 86400
WINDOW_7DAY = 604800

DEFAULT_DRIFT_THRESHOLDS = {
    "latency_increase_pct": 20.0,    # 20% latency increase = drift
    "error_rate_increase_pct": 10.0, # 10% error rate increase = drift
    "throughput_decrease_pct": 25.0, # 25% throughput drop = drift
    "queue_depth_threshold": 50,     # Queue > 50 = bottleneck
}


class DriftLevel(str):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DriftReport:
    """A drift analysis report."""

    def __init__(self):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.drifts: List[Dict[str, Any]] = []
        self.overall_level = DriftLevel.NONE
        self.healthy = True

    def add_drift(self, metric: str, task_type: str, level: str,
                  current_value: float, baseline_value: float,
                  change_pct: float, recommendation: str):
        self.drifts.append({
            "metric": metric,
            "task_type": task_type,
            "level": level,
            "current_value": current_value,
            "baseline_value": baseline_value,
            "change_pct": round(change_pct, 2),
            "recommendation": recommendation,
        })
        # Update overall level
        levels = [DriftLevel.NONE, DriftLevel.LOW, DriftLevel.MEDIUM,
                  DriftLevel.HIGH, DriftLevel.CRITICAL]
        if levels.index(level) > levels.index(self.overall_level):
            self.overall_level = level
        self.healthy = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "overall_level": self.overall_level,
            "healthy": self.healthy,
            "drift_count": len(self.drifts),
            "drifts": self.drifts,
        }


class DriftDetector:
    """
    Singleton drift detector for OCE execution metrics.

    Analyzes execution history to detect performance degradation:
    - Latency trends per task type
    - Error rate trends per task type
    - Throughput trends overall
    - Queue depth trends
    """

    _instance: Optional["DriftDetector"] = None
    _lock = Lock()

    def __new__(cls) -> "DriftDetector":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self._thresholds = dict(DEFAULT_DRIFT_THRESHOLDS)
        self._alert_callbacks: List[Callable] = []

        # Initialize SQLite
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info("DriftDetector initialized")

    def _init_db(self):
        """Initialize SQLite database for drift history."""
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS drift_reports (
                    id TEXT PRIMARY KEY,
                    report_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_drift_created
                ON drift_reports(created_at)
            """)
            conn.commit()

    def configure_thresholds(self, **kwargs):
        """Update drift thresholds."""
        for key, value in kwargs.items():
            if key in self._thresholds:
                self._thresholds[key] = value
                logger.info(f"Drift threshold '{key}' set to {value}")

    def register_alert_callback(self, callback: Callable):
        """Register a callback to be triggered on significant drift."""
        self._alert_callbacks.append(callback)

    def _trigger_alerts(self, report: DriftReport):
        """Trigger alert callbacks for significant drift."""
        if report.overall_level in (DriftLevel.HIGH, DriftLevel.CRITICAL):
            for callback in self._alert_callbacks:
                try:
                    callback(report)
                except Exception as e:
                    logger.error(f"Drift alert callback error: {e}")

    def _get_execution_history(self, window_sec: int) -> List[Dict]:
        """Read execution history from the execution engine's SQLite DB."""
        exec_db = DATA_DIR / "execution.db"
        if not exec_db.exists():
            return []
        cutoff = datetime.now(timezone.utc).timestamp() - window_sec
        try:
            with sqlite3.connect(str(exec_db)) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """SELECT task_type, status, created_at, completed_at,
                       json_extract(result_json, '$.execution_time_ms') as exec_ms
                       FROM execution_history
                       WHERE created_at > datetime(?, 'unixepoch')
                       ORDER BY created_at DESC""",
                    (cutoff,),
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Failed to read execution history: {e}")
            return []

    def analyze_latency_trend(self, task_type: Optional[str] = None,
                               window_hours: int = 24) -> Dict[str, Any]:
        """
        Analyze latency trend for a task type (or all types).
        Compares recent window to previous window.
        """
        window_sec = window_hours * 3600
        history = self._get_execution_history(window_sec * 2)

        if task_type:
            history = [h for h in history if h["task_type"] == task_type]

        if not history:
            return {"task_type": task_type, "drift": False, "reason": "no data"}

        # Split into recent and previous windows
        now = datetime.now(timezone.utc).timestamp()
        mid = now - window_sec
        recent = [h for h in history
                  if h.get("created_at") and
                  datetime.fromisoformat(h["created_at"]).timestamp() > mid]
        previous = [h for h in history
                    if h.get("created_at") and
                    datetime.fromisoformat(h["created_at"]).timestamp() <= mid]

        recent_latencies = [h["exec_ms"] for h in recent
                           if h.get("exec_ms") is not None]
        previous_latencies = [h["exec_ms"] for h in previous
                             if h.get("exec_ms") is not None]

        if not recent_latencies or not previous_latencies:
            return {"task_type": task_type, "drift": False,
                    "reason": "insufficient data"}

        recent_avg = sum(recent_latencies) / len(recent_latencies)
        previous_avg = sum(previous_latencies) / len(previous_latencies)

        if previous_avg == 0:
            change_pct = 0.0
        else:
            change_pct = ((recent_avg - previous_avg) / previous_avg) * 100

        threshold = self._thresholds["latency_increase_pct"]
        drifted = change_pct > threshold

        return {
            "task_type": task_type,
            "drift": drifted,
            "recent_avg_ms": round(recent_avg, 2),
            "previous_avg_ms": round(previous_avg, 2),
            "change_pct": round(change_pct, 2),
            "threshold_pct": threshold,
            "recent_count": len(recent_latencies),
            "previous_count": len(previous_latencies),
        }

    def analyze_error_rate_trend(self, task_type: Optional[str] = None,
                                  window_hours: int = 24) -> Dict[str, Any]:
        """
        Analyze error rate trend for a task type (or all types).
        Compares recent window to previous window.
        """
        window_sec = window_hours * 3600
        history = self._get_execution_history(window_sec * 2)

        if task_type:
            history = [h for h in history if h["task_type"] == task_type]

        if not history:
            return {"task_type": task_type, "drift": False, "reason": "no data"}

        now = datetime.now(timezone.utc).timestamp()
        mid = now - window_sec
        recent = [h for h in history
                  if h.get("created_at") and
                  datetime.fromisoformat(h["created_at"]).timestamp() > mid]
        previous = [h for h in history
                    if h.get("created_at") and
                    datetime.fromisoformat(h["created_at"]).timestamp() <= mid]

        def error_rate(tasks):
            if not tasks:
                return 0.0
            errors = sum(1 for t in tasks if t.get("status") == "failed")
            return (errors / len(tasks)) * 100

        recent_rate = error_rate(recent)
        previous_rate = error_rate(previous)

        if previous_rate == 0:
            change_pct = recent_rate * 100  # Any errors when previously 0 = 100% increase
        else:
            change_pct = ((recent_rate - previous_rate) / previous_rate) * 100

        threshold = self._thresholds["error_rate_increase_pct"]
        drifted = change_pct > threshold and recent_rate > 5.0  # At least 5% error rate

        return {
            "task_type": task_type,
            "drift": drifted,
            "recent_error_rate": round(recent_rate, 2),
            "previous_error_rate": round(previous_rate, 2),
            "change_pct": round(change_pct, 2),
            "threshold_pct": threshold,
            "recent_count": len(recent),
            "previous_count": len(previous),
        }

    def analyze_throughput_trend(self, window_hours: int = 24) -> Dict[str, Any]:
        """
        Analyze overall throughput trend.
        Compares task completion rate between recent and previous windows.
        """
        window_sec = window_hours * 3600
        history = self._get_execution_history(window_sec * 2)

        if not history:
            return {"drift": False, "reason": "no data"}

        now = datetime.now(timezone.utc).timestamp()
        mid = now - window_sec
        recent = [h for h in history
                  if h.get("created_at") and
                  datetime.fromisoformat(h["created_at"]).timestamp() > mid
                  and h.get("status") == "completed"]
        previous = [h for h in history
                    if h.get("created_at") and
                    datetime.fromisoformat(h["created_at"]).timestamp() <= mid
                    and h.get("status") == "completed"]

        recent_rate = len(recent) / window_hours if window_hours > 0 else 0
        previous_rate = len(previous) / window_hours if window_hours > 0 else 0

        if previous_rate == 0:
            change_pct = 0.0 if recent_rate == 0 else -100.0
        else:
            change_pct = ((recent_rate - previous_rate) / previous_rate) * 100

        threshold = self._thresholds["throughput_decrease_pct"]
        drifted = change_pct < -threshold  # Negative = decrease

        return {
            "drift": drifted,
            "recent_throughput_per_hour": round(recent_rate, 2),
            "previous_throughput_per_hour": round(previous_rate, 2),
            "change_pct": round(change_pct, 2),
            "threshold_pct": threshold,
        }

    def analyze_queue_depth(self) -> Dict[str, Any]:
        """
        Analyze current queue depth for bottleneck detection.
        Reads from the execution engine's active queue.
        """
        # Read pending/running tasks from execution history
        history = self._get_execution_history(300)  # Last 5 minutes
        pending = [h for h in history if h.get("status") in ("pending", "queued", "running")]

        depth = len(pending)
        threshold = self._thresholds["queue_depth_threshold"]
        bottleneck = depth > threshold

        return {
            "bottleneck": bottleneck,
            "current_depth": depth,
            "threshold": threshold,
            "pending_count": sum(1 for h in pending if h.get("status") in ("pending", "queued")),
            "running_count": sum(1 for h in pending if h.get("status") == "running"),
        }

    def get_drift_report(self, window_hours: int = 24) -> Dict[str, Any]:
        """
        Generate a full drift analysis report.
        Analyzes all metrics and task types.
        """
        report = DriftReport()

        # Get all task types from recent history
        history = self._get_execution_history(window_hours * 3600 * 2)
        task_types = list(set(h["task_type"] for h in history if h.get("task_type")))

        # Analyze per-task-type metrics
        for tt in task_types:
            # Latency
            latency = self.analyze_latency_trend(tt, window_hours)
            if latency.get("drift"):
                level = DriftLevel.LOW
                if latency["change_pct"] > 50:
                    level = DriftLevel.HIGH
                elif latency["change_pct"] > 30:
                    level = DriftLevel.MEDIUM
                report.add_drift(
                    metric="latency",
                    task_type=tt,
                    level=level,
                    current_value=latency["recent_avg_ms"],
                    baseline_value=latency["previous_avg_ms"],
                    change_pct=latency["change_pct"],
                    recommendation=f"Increase timeout for '{tt}' tasks or investigate slow handlers",
                )

            # Error rate
            error = self.analyze_error_rate_trend(tt, window_hours)
            if error.get("drift"):
                level = DriftLevel.MEDIUM
                if error["recent_error_rate"] > 20:
                    level = DriftLevel.CRITICAL
                elif error["recent_error_rate"] > 10:
                    level = DriftLevel.HIGH
                report.add_drift(
                    metric="error_rate",
                    task_type=tt,
                    level=level,
                    current_value=error["recent_error_rate"],
                    baseline_value=error["previous_error_rate"],
                    change_pct=error["change_pct"],
                    recommendation=f"Review error logs for '{tt}' tasks, consider retry policy adjustment",
                )

        # Overall throughput
        throughput = self.analyze_throughput_trend(window_hours)
        if throughput.get("drift"):
            report.add_drift(
                metric="throughput",
                task_type="all",
                level=DriftLevel.MEDIUM,
                current_value=throughput["recent_throughput_per_hour"],
                baseline_value=throughput["previous_throughput_per_hour"],
                change_pct=throughput["change_pct"],
                recommendation="Consider increasing worker pool size or investigating task bottlenecks",
            )

        # Queue depth
        queue = self.analyze_queue_depth()
        if queue.get("bottleneck"):
            report.add_drift(
                metric="queue_depth",
                task_type="all",
                level=DriftLevel.HIGH if queue["current_depth"] > 100 else DriftLevel.MEDIUM,
                current_value=queue["current_depth"],
                baseline_value=queue["threshold"],
                change_pct=((queue["current_depth"] - queue["threshold"]) / max(queue["threshold"], 1)) * 100,
                recommendation="Scale up workers or reduce task submission rate",
            )

        # Persist report
        self._persist_report(report)

        # Trigger alerts if significant
        self._trigger_alerts(report)

        return report.to_dict()

    def _persist_report(self, report: DriftReport):
        """Persist drift report to SQLite."""
        import uuid
        report_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute(
                    "INSERT INTO drift_reports (id, report_json, created_at) VALUES (?, ?, ?)",
                    (report_id, json.dumps(report.to_dict()), now),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to persist drift report: {e}")

    def get_drift_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get historical drift reports."""
        results = []
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT report_json, created_at FROM drift_reports ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                for row in rows:
                    data = json.loads(row["report_json"])
                    data["stored_at"] = row["created_at"]
                    results.append(data)
        except Exception as e:
            logger.error(f"Failed to read drift history: {e}")
        return results


# ─── Singleton Access ───────────────────────────────────────────────────────

def get_drift_detector() -> DriftDetector:
    """Get the singleton DriftDetector instance."""
    return DriftDetector()
