"""
4.2 Sovereign Health Monitor — Sovereign Instrumentation
==========================================================
Health dashboard — latency, throughput, error rates, drift metrics.

Aggregates health signals from all field modules into a unified
health report with configurable alerting thresholds.

Singleton pattern consistent with OCE backend modules.
"""

import sqlite3
import json
import logging
import os
import psutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Dict, List, Optional
from time import monotonic

from pydantic import BaseModel, Field

logger = logging.getLogger("field.health")

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "health.db"


# ── Pydantic Models ──────────────────────────────────────────────

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


class HealthConfig(BaseModel):
    """Configuration for the Sovereign Health Monitor."""

    enabled: bool = True
    check_interval_seconds: float = 5.0
    latency_warning_ms: float = 200.0
    latency_critical_ms: float = 1000.0
    error_rate_warning_pct: float = 5.0
    error_rate_critical_pct: float = 20.0
    memory_warning_mb: float = 512.0
    memory_critical_mb: float = 2048.0
    retention_hours: int = 168  # 7 days
    persistence_enabled: bool = True


# ── Database Layer ───────────────────────────────────────────────

def _init_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS module_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_name TEXT NOT NULL,
            latency_ms REAL,
            throughput REAL,
            error_rate REAL,
            memory_mb REAL,
            cpu_pct REAL,
            status TEXT,
            timestamp TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_metrics_module_ts
            ON module_metrics(module_name, timestamp);

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT NOT NULL,
            module_name TEXT,
            severity TEXT,
            metric TEXT,
            value REAL,
            threshold REAL,
            message TEXT,
            timestamp TEXT NOT NULL,
            resolved INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_alerts_unresolved
            ON alerts(resolved, severity);

        CREATE TABLE IF NOT EXISTS health_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            overall_status TEXT,
            total_modules INTEGER,
            healthy INTEGER,
            degraded INTEGER,
            critical INTEGER,
            avg_latency REAL,
            total_throughput REAL,
            overall_error_rate REAL,
            timestamp TEXT NOT NULL
        );
    """)
    return conn


def _cleanup_old_data(conn: sqlite3.Connection, retention_hours: int):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=retention_hours)).isoformat()
    conn.execute("DELETE FROM module_metrics WHERE timestamp < ?", (cutoff,))
    conn.execute("DELETE FROM alerts WHERE timestamp < ? AND resolved = 1", (cutoff,))
    conn.execute("DELETE FROM health_snapshots WHERE timestamp < ?", (cutoff,))
    conn.commit()


# ── Core Monitor ─────────────────────────────────────────────────

class SovereignHealthMonitor:
    """Singleton health monitoring engine.

    Aggregates metrics from all registered field modules, evaluates
    them against configurable thresholds, generates health reports,
    and persists data to SQLite for historical analysis.
    """

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
        self.config = HealthConfig()
        self._conn = _init_db(DB_PATH)
        self._modules: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._monitor_thread: Optional[Thread] = None
        self._initialized = True

    # ── Module Registration ────────────────────────────────────

    def register_module(self, name: str, **kwargs):
        """Register a field module for health tracking."""
        self._modules[name] = {
            "latency_ms": kwargs.get("latency_ms", 0.0),
            "throughput": kwargs.get("throughput", 0.0),
            "error_rate": kwargs.get("error_rate", 0.0),
            "queue_depth": kwargs.get("queue_depth", 0),
            "memory_mb": kwargs.get("memory_mb", 0.0),
            "cpu_pct": kwargs.get("cpu_pct", 0.0),
            "status": kwargs.get("status", "unknown"),
            "last_update": kwargs.get("last_update", ""),
            "uptime_seconds": kwargs.get("uptime_seconds", 0),
        }

    def unregister_module(self, name: str):
        """Remove a module from health tracking."""
        self._modules.pop(name, None)

    def update_module_metrics(self, name: str, **kwargs):
        """Update metrics for a registered module."""
        if name in self._modules:
            self._modules[name].update(kwargs)
            self._modules[name]["last_update"] = datetime.now(timezone.utc).isoformat()

    # ── Alert Evaluation ───────────────────────────────────────

    def _evaluate_alerts(self, metrics: HealthMetrics) -> List[HealthAlert]:
        """Check module metrics against thresholds and generate alerts."""
        alerts = []
        ts = datetime.now(timezone.utc).isoformat()

        if metrics.latency_ms >= self.config.latency_critical_ms:
            alerts.append(HealthAlert(
                alert_id=f"LATENCY_CRITICAL_{metrics.module_name}",
                module_name=metrics.module_name,
                severity="critical",
                metric="latency_ms",
                value=metrics.latency_ms,
                threshold=self.config.latency_critical_ms,
                message=f"Module {metrics.module_name} latency {metrics.latency_ms:.1f}ms exceeds critical threshold {self.config.latency_critical_ms}ms",
                timestamp=ts,
            ))
        elif metrics.latency_ms >= self.config.latency_warning_ms:
            alerts.append(HealthAlert(
                alert_id=f"LATENCY_WARNING_{metrics.module_name}",
                module_name=metrics.module_name,
                severity="warning",
                metric="latency_ms",
                value=metrics.latency_ms,
                threshold=self.config.latency_warning_ms,
                message=f"Module {metrics.module_name} latency {metrics.latency_ms:.1f}ms exceeds warning threshold {self.config.latency_warning_ms}ms",
                timestamp=ts,
            ))

        if metrics.error_rate_pct >= self.config.error_rate_critical_pct:
            alerts.append(HealthAlert(
                alert_id=f"ERROR_CRITICAL_{metrics.module_name}",
                module_name=metrics.module_name,
                severity="critical",
                metric="error_rate_pct",
                value=metrics.error_rate_pct,
                threshold=self.config.error_rate_critical_pct,
                message=f"Module {metrics.module_name} error rate {metrics.error_rate_pct:.1f}% exceeds critical threshold",
                timestamp=ts,
            ))
        elif metrics.error_rate_pct >= self.config.error_rate_warning_pct:
            alerts.append(HealthAlert(
                alert_id=f"ERROR_WARNING_{metrics.module_name}",
                module_name=metrics.module_name,
                severity="warning",
                metric="error_rate_pct",
                value=metrics.error_rate_pct,
                threshold=self.config.error_rate_warning_pct,
                message=f"Module {metrics.module_name} error rate {metrics.error_rate_pct:.1f}% exceeds warning threshold",
                timestamp=ts,
            ))

        if metrics.memory_mb >= self.config.memory_critical_mb:
            alerts.append(HealthAlert(
                alert_id=f"MEMORY_CRITICAL_{metrics.module_name}",
                module_name=metrics.module_name,
                severity="critical",
                metric="memory_mb",
                value=metrics.memory_mb,
                threshold=self.config.memory_critical_mb,
                message=f"Module {metrics.module_name} memory {metrics.memory_mb:.1f}MB exceeds critical threshold",
                timestamp=ts,
            ))
        elif metrics.memory_mb >= self.config.memory_warning_mb:
            alerts.append(HealthAlert(
                alert_id=f"MEMORY_WARNING_{metrics.module_name}",
                module_name=metrics.module_name,
                severity="warning",
                metric="memory_mb",
                value=metrics.memory_mb,
                threshold=self.config.memory_warning_mb,
                message=f"Module {metrics.module_name} memory {metrics.memory_mb:.1f}MB exceeds warning threshold",
                timestamp=ts,
            ))

        return alerts

    def _classify_status(self, alerts: List[HealthAlert]) -> str:
        """Classify module status from alerts."""
        for a in alerts:
            if a.severity == "critical":
                return "critical"
        for a in alerts:
            if a.severity == "warning":
                return "degraded"
        return "healthy"

    # ── Report Generation (PM2-flagged method) ─────────────────

    def generate_report(self) -> HealthReport:
        """Generate a comprehensive health report for the entire field.

        Aggregates metrics from all registered modules, evaluates alerts,
        computes field-wide statistics, persists to DB, and returns a
        structured HealthReport.
        """
        ts = datetime.now(timezone.utc).isoformat()
        all_alerts: List[HealthAlert] = []
        module_metrics: List[HealthMetrics] = []

        healthy = degraded = critical = 0
        total_latency = 0.0
        total_throughput = 0.0
        total_errors = 0.0

        # Include system-level metrics
        try:
            proc = psutil.Process(os.getpid())
            system_cpu = proc.cpu_percent(interval=0)
            system_mem = proc.memory_info().rss / (1024 * 1024)
        except Exception:
            system_cpu = 0.0
            system_mem = 0.0

        for name, data in self._modules.items():
            metrics = HealthMetrics(
                module_name=name,
                latency_ms=data.get("latency_ms", 0.0),
                throughput_events_per_sec=data.get("throughput", 0.0),
                error_rate_pct=data.get("error_rate", 0.0),
                queue_depth=data.get("queue_depth", 0),
                memory_mb=data.get("memory_mb", 0.0),
                cpu_pct=data.get("cpu_pct", 0.0),
                uptime_seconds=data.get("uptime_seconds", 0),
                status=data.get("status", "unknown"),
                last_update=data.get("last_update", ""),
            )
            module_metrics.append(metrics)

            # Evaluate alerts per module
            module_alerts = self._evaluate_alerts(metrics)
            all_alerts.extend(module_alerts)

            # Classify module status
            status = self._classify_status(module_alerts)
            if status == "healthy":
                healthy += 1
            elif status == "degraded":
                degraded += 1
            else:
                critical += 1

            total_latency += metrics.latency_ms
            total_throughput += metrics.throughput_events_per_sec
            total_errors += metrics.error_rate_pct

        total_modules = len(self._modules)
        if total_modules == 0:
            total_modules = 1  # avoid division by zero

        # Determine overall field status
        if critical > 0:
            overall_status = "red"
        elif degraded > 0:
            overall_status = "yellow"
        else:
            overall_status = "green"

        report = HealthReport(
            timestamp=ts,
            overall_status=overall_status,
            total_modules=total_modules,
            healthy_count=healthy,
            degraded_count=degraded,
            critical_count=critical,
            avg_latency_ms=total_latency / total_modules,
            total_throughput=total_throughput,
            overall_error_rate=total_errors / total_modules,
            alerts=all_alerts,
            module_metrics=module_metrics,
        )

        # Persist to DB
        if self.config.persistence_enabled:
            self._persist_report(report)

        return report

    def _persist_report(self, report: HealthReport):
        """Persist report data to SQLite."""
        try:
            # Insert health snapshot
            self._conn.execute(
                "INSERT INTO health_snapshots (overall_status, total_modules, healthy, degraded, critical, avg_latency, total_throughput, overall_error_rate, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    report.overall_status,
                    report.total_modules,
                    report.healthy_count,
                    report.degraded_count,
                    report.critical_count,
                    report.avg_latency_ms,
                    report.total_throughput,
                    report.overall_error_rate,
                    report.timestamp,
                ),
            )

            # Insert module metrics
            for m in report.module_metrics:
                self._conn.execute(
                    "INSERT INTO module_metrics (module_name, latency_ms, throughput, error_rate, memory_mb, cpu_pct, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        m.module_name,
                        m.latency_ms,
                        m.throughput_events_per_sec,
                        m.error_rate_pct,
                        m.memory_mb,
                        m.cpu_pct,
                        m.status,
                        report.timestamp,
                    ),
                )

            # Insert unresolved alerts
            for a in report.alerts:
                if not a.resolved:
                    self._conn.execute(
                        "INSERT INTO alerts (alert_id, module_name, severity, metric, value, threshold, message, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            a.alert_id,
                            a.module_name,
                            a.severity,
                            a.metric,
                            a.value,
                            a.threshold,
                            a.message,
                            report.timestamp,
                        ),
                    )

            # Cleanup old data
            _cleanup_old_data(self._conn, self.config.retention_hours)
            self._conn.commit()
        except sqlite3.Error as e:
            logger.error(f"DB persistence failed: {e}")

    # ── Query Methods ──────────────────────────────────────────

    def get_recent_reports(self, limit: int = 10) -> List[HealthReport]:
        """Retrieve recent health reports from DB."""
        cursor = self._conn.execute(
            "SELECT * FROM health_snapshots ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        reports = []
        for row in rows:
            reports.append(HealthReport(
                timestamp=row[8],
                overall_status=row[1] or "unknown",
                total_modules=row[2] or 0,
                healthy_count=row[3] or 0,
                degraded_count=row[4] or 0,
                critical_count=row[5] or 0,
                avg_latency_ms=row[6] or 0.0,
                total_throughput=row[7] or 0.0,
                overall_error_rate=0.0,
            ))
        return reports