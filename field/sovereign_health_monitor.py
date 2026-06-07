"""
4.2 Sovereign Health Monitor — Sovereign Instrumentation
==========================================================
Health dashboard — latency, throughput, error rates, drift metrics.

Aggregates health signals from all field modules into a unified
health report with configurable alerting thresholds.

Singleton pattern consistent with OCE backend modules.
"""

import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.health")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "health.db"


class HealthMetrics(BaseModel):
    module_name: str
    latency_ms: float = 0.0
    throughput_events_per_sec: float = 0.0
    error_rate_pct: float = 0.0
    queue_depth: int = 0
    memory_mb: float = 0.0
    cpu_pct: float = 0.0
    uptime_seconds: int = 0
    status: str = "unknown"  # healthy, degraded, critical, unknown
    last_update: str = ""


class HealthAlert(BaseModel):
    alert_id: str
    module_name: str
    severity: str  # "warning", "critical"
    metric: str
    value: float
    threshold: float
    message: str
    timestamp: str
    resolved: bool = False


class HealthReport(BaseModel):
    timestamp: str
    overall_status: str  # "green", "yellow", "red"
    total_modules: int
    healthy_count: int
    degraded_count: int
    critical_count: int
    avg_latency_ms: float
    total_throughput: float
    overall_error_rate: float
    alerts: List[HealthAlert] = Field(default_factory=list)
    module_metrics: List[HealthMetrics] = Field(default_factory=list)


class SovereignHealthMonitor:
    """Singleton health monitoring engine."""

    _instance: Optional["SovereignHealthMonitor"] = None
    _lock = Lock()

    def __new__(cls) -> "SovereignHealthMonitor":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._thresholds = {
            "latency_warning_ms": 100.0,
            "latency_critical_ms": 500.0,
            "error_rate_warning_pct": 5.0,
            "error_rate_critical_pct": 15.0,
            "queue_depth_warning": 100,
            "queue_depth_critical": 500,
            "throughput_drop_pct": 30.0,
        }
        self._module_metrics: Dict[str, HealthMetrics] = {}
        self._active_alerts: Dict[str, HealthAlert] = {}
        logger.info("SovereignHealthMonitor initialized")

    def _init_db(self):
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS health_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    data TEXT NOT NULL,
                    overall_status TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT NOT NULL,
                    module_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    value REAL,
                    threshold REAL,
                    message TEXT,
                    timestamp TEXT NOT NULL,
                    resolved INTEGER DEFAULT 0
                )
            """)

    def update_module_metrics(self, module_name: str, metrics: Dict[str, Any]):
        now = datetime.now(timezone.utc).isoformat()
        hm = HealthMetrics(
            module_name=module_name,
            latency_ms=metrics.get("latency_ms", 0),
            throughput_events_per_sec=metrics.get("throughput", 0),
            error_rate_pct=metrics.get("error_rate", 0),
            queue_depth=metrics.get("queue_depth", 0),
            memory_mb=metrics.get("memory_mb", 0),
            cpu_pct=metrics.get("cpu_pct", 0),
            uptime_seconds=metrics.get("uptime_seconds", 0),
            last_update=now,
        )
        self._module_metrics[module_name] = hm
        self._evaluate_alerts(module_name, hm)

    def _evaluate_alerts(self, module_name: str, hm: HealthMetrics):
        now = datetime.now(timezone.utc).isoformat()

        checks = [
            ("latency_ms", hm.latency_ms, self._thresholds["latency_warning_ms"],
             self._thresholds["latency_critical_ms"]),
            ("error_rate_pct", hm.error_rate_pct, self._thresholds["error_rate_warning_pct"],
             self._thresholds["error_rate_critical_pct"]),
            ("queue_depth", float(hm.queue_depth), float(self._thresholds["queue_depth_warning"]),
             float(self._thresholds["queue_depth_critical"])),
        ]

        for metric_name, value, warn_thresh, crit_thresh in checks:
            alert_id = f"{module_name}:{metric_name}"
            if value >= crit_thresh:
                severity = "critical"
                hm.status = "critical"
            elif value >= warn_thresh:
                severity = "warning"
                if hm.status != "critical":
                    hm.status = "degraded"
            else:
                if alert_id in self._active_alerts:
                    self._active_alerts[alert_id].resolved = True
                if hm.status not in ("critical", "degraded"):
                    hm.status = "healthy"
                continue

            if alert_id not in self._active_alerts or not self._active_alerts[alert_id].resolved:
                alert = HealthAlert(
                    alert_id=alert_id,
                    module_name=module_name,
                    severity=severity,
                    metric=metric_name,
                    value=round(value, 2),
                    threshold=crit_thresh if severity == "critical" else warn_thresh,
                    message=f"{module_name} {metric_name} = {value:.2f} (threshold: {crit_thresh if severity == 'critical' else warn_thresh})",
                    timestamp=now,
                )
                self._active_alerts[alert_id] = alert
                self._persist_alert(alert)

    def _persist_alert(self, alert: HealthAlert):
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                """INSERT INTO alerts (alert_id, module_name, severity, metric, value, threshold, message, timestamp)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (alert.alert_id, alert.module_name, alert.severity, alert.metric,
                 alert.value, alert.threshold, alert.message, alert.timestamp),
            )

    def generate_report(self) -> HealthReport:
        now =