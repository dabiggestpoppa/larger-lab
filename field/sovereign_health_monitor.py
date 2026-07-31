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
    latency_warning_ms: float = 100.0
    latency_critical_ms: float = 500.0
    error_rate_warning_pct: float = 5.0
    error_rate_critical_pct: float = 20.0
    memory_warning_mb: float = 512.0
    memory_critical_mb: float = 2048.0
    cpu_warning_pct: float = 80.0
    cpu_critical_pct: float = 95.0
    retention_hours: float = 24.0


# ── Database Setup ───────────────────────────────────────────────

def _init_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_name TEXT NOT NULL,
            latency_ms REAL,
            throughput REAL,
            error_rate REAL,
            queue_depth INTEGER,
            memory_mb REAL,
            cpu_pct REAL,
            status TEXT,
            timestamp TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_metrics_module ON metrics(module_name);
        CREATE INDEX IF NOT EXISTS idx_metrics_ts ON metrics(timestamp);

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT UNIQUE,
            module_name TEXT,
            severity TEXT,
            metric TEXT,
            value REAL,
            threshold REAL,
            message TEXT,
            timestamp TEXT,
            resolved INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON alerts(resolved, severity);
    """)
    return conn


# ── Health Monitor Singleton ─────────────────────────────────────

class SovereignHealthMonitor:
    """
    Monitors all field modules and agents for health, performance,
    and anomalies. Produces real-time health reports and alerts.
    """

    _instance: Optional["SovereignHealthMonitor"] = None
    _lock = Lock()

    def __new__(cls) -> "SovereignHealthMonitor":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.config = HealthConfig()
        self._conn = _init_db(DB_PATH)
        self._modules: Dict[str, dict] = {}
        self._agents: Dict[str, dict] = {}
        self._history: List[HealthReport] = []
        self._running = False
        self._monitor_thread: Optional[Thread] = None
        self._lock = Lock()
        self._initialized = True
        self._start_time = monotonic()
        logger.info("SovereignHealthMonitor initialized (pid=%s)", os.getpid())

    # ── Module Registration ──────────────────────────────────────

    def register_module(self, name: str, initial_metrics: Optional[dict] = None) -> None:
        with self._lock:
            self._modules[name] = {
                "status": "unknown",
                "latency_ms": 0.0,
                "throughput": 0.0,
                "error_rate": 0.0,
                "queue_depth": 0,
                "memory_mb": 0.0,
                "cpu_pct": 0.0,
                "uptime_seconds": 0,
                "last_update": "",
                "alert_count": 0,
            }
            if initial_metrics:
                self.update_module_metrics(name, **initial_metrics)
            logger.debug("Registered module: %s", name)

    def deregister_module(self, name: str) -> None:
        with self._lock:
            self._modules.pop(name, None)
            logger.debug("Deregistered module: %s", name)

    def reset_module(self, name: str) -> None:
        """Reset a module's health metrics to defaults."""
        with self._lock:
            if name in self._modules:
                self._modules[name] = {
                    "status": "unknown",
                    "latency_ms": 0.0,
                    "throughput": 0.0,
                    "error_rate": 0.0,
                    "queue_depth": 0,
                    "memory_mb": 0.0,
                    "cpu_pct": 0.0,
                    "uptime_seconds": 0,
                    "last_update": datetime.now(timezone.utc).isoformat(),
                    "alert_count": 0,
                }
                logger.info("Reset module: %s", name)

    # ── Metric Updates ───────────────────────────────────────────

    def update_module_metrics(
        self,
        name: str,
        latency_ms: float = 0.0,
        throughput: float = 0.0,
        error_rate: float = 0.0,
        queue_depth: int = 0,
        memory_mb: float = 0.0,
        cpu_pct: float = 0.0,
        status: str = "unknown",
    ) -> None:
        with self._lock:
            if name not in self._modules:
                self.register_module(name)
            now = datetime.now(timezone.utc).isoformat()
            self._modules[name].update({
                "latency_ms": latency_ms,
                "throughput": throughput,
                "error_rate": error_rate,
                "queue_depth": queue_depth,
                "memory_mb": memory_mb,
                "cpu_pct": cpu_pct,
                "status": status,
                "last_update": now,
            })
            self._persist_metric(name, latency_ms, throughput, error_rate,
                                 queue_depth, memory_mb, cpu_pct, status, now)

    def _persist_metric(self, name: str, latency_ms: float, throughput: float,
                        error_rate: float, queue_depth: int, memory_mb: float,
                        cpu_pct: float, status: str, ts: str) -> None:
        try:
            self._conn.execute(
                "INSERT INTO metrics (module_name, latency_ms, throughput, error_rate, "
                "queue_depth, memory_mb, cpu_pct, status, timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
                (name, latency_ms, throughput, error_rate, queue_depth,
                 memory_mb, cpu_pct, status, ts),
            )
            self._conn.commit()
        except sqlite3.Error as e:
            logger.error("DB write failed: %s", e)

    # ── Alerting ─────────────────────────────────────────────────

    def _evaluate_alerts(self) -> List[HealthAlert]:
        alerts: List[HealthAlert] = []
        cfg = self.config
        for name, m in self._modules.items():
            if m["latency_ms"] > cfg.latency_critical_ms:
                alerts.append(HealthAlert(
                    alert_id=f"crit_latency_{name}",
                    module_name=name, severity="critical", metric="latency_ms",
                    value=m["latency_ms"], threshold=cfg.latency_critical_ms,
                    message=f"Critical latency: {m['latency_ms']:.1f}ms",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ))
            elif m["latency_ms"] > cfg.latency_warning_ms:
                alerts.append(HealthAlert(
                    alert_id=f"warn_latency_{name}",
                    module_name=name, severity="warning", metric="latency_ms",
                    value=m["latency_ms"], threshold=cfg.latency_warning_ms,
                    message=f"High latency: {m['latency_ms']:.1f}ms",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ))
            if m["error_rate"] > cfg.error_rate_critical_pct:
                alerts.append(HealthAlert(
                    alert_id=f"crit_error_{name}",
                    module_name=name, severity="critical", metric="error_rate_pct",
                    value=m["error_rate"], threshold=cfg.error_rate_critical_pct,
                    message=f"Critical error rate: {m['error_rate']:.1f}%",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ))
            elif m["error_rate"] > cfg.error_rate_warning_pct:
                alerts.append(HealthAlert(
                    alert_id=f"warn_error_{name}",
                    module_name=name, severity="warning", metric="error_rate_pct",
                    value=m["error_rate"], threshold=cfg.error_rate_warning_pct,
                    message=f"High error rate: {m['error_rate']:.1f}%",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ))
            if m["memory_mb"] > cfg.memory_critical_mb:
                alerts.append(HealthAlert(
                    alert_id=f"crit_mem_{name}",
                    module_name=name, severity="critical", metric="memory_mb",
                    value=m["memory_mb"], threshold=cfg.memory_critical_mb,
                    message=f"Critical memory: {m['memory_mb']:.1f}MB",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ))
            if m["cpu_pct"] > cfg.cpu_critical_pct:
                alerts.append(HealthAlert(
                    alert_id=f"crit_cpu_{name}",
                    module_name=name, severity="critical", metric="cpu_pct",
                    value=m["cpu_pct"], threshold=cfg.cpu_critical_pct,
                    message=f"Critical CPU: {m['cpu_pct']:.1f}%",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ))
        return alerts

    # ── Report Generation ────────────────────────────────────────

    def generate_report(self) -> HealthReport:
        """Generate a comprehensive health report for all registered modules."""
        with self._lock:
            now = datetime.now(timezone.utc).isoformat()
            metrics: List[HealthMetrics] = []
            healthy = degraded = critical = 0
            total_latency = 0.0
            total_throughput = 0.0
            total_errors = 0.0

            for name, m in self._modules.items():
                status = m.get("status", "unknown")
                metric = HealthMetrics(
                    module_name=name,
                    latency_ms=m.get("latency_ms", 0.0),
                    throughput_events_per_sec=m.get("throughput", 0.0),
                    error_rate_pct=m.get("error_rate", 0.0),
                    queue_depth=m.get("queue_depth", 0),
                    memory_mb=m.get("memory_mb", 0.0),
                    cpu_pct=m.get("cpu_pct", 0.0),
                    uptime_seconds=m.get("uptime_seconds", 0),
                    status=status,
                    last_update=m.get("last_update", ""),
                )
                metrics.append(metric)
                if status == "healthy":
                    healthy += 1
                elif status == "degraded":
                    degraded += 1
                elif status in ("critical", "error"):
                    critical += 1
                total_latency += metric.latency_ms
                total_throughput += metric.throughput_events_per_sec
                total_errors += metric.error_rate_pct

            total = len(self._modules)
            avg_latency = total_latency / total if total else 0.0
            avg_errors = total_errors / total if total else 0.0

            # Determine overall status
            if critical > 0:
                overall = "red"
            elif degraded > 0:
                overall = "yellow"
            elif total == 0:
                overall = "red"
            else:
                overall = "green"

            alerts = self._evaluate_alerts()

            report = HealthReport(
                timestamp=now,
                overall_status=overall,
                total_modules=total,
                healthy_count=healthy,
                degraded_count=degraded,
                critical_count=critical,
                avg_latency_ms=round(avg_latency, 2),
                total_throughput=round(total_throughput, 2),
                overall_error_rate=round(avg_errors, 2),
                alerts=alerts,
                module_metrics=metrics,
            )
            self._history.append(report)
            # Keep only last hour of reports (roughly)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
            self._history = [
                r for r in self._history
                if datetime.fromisoformat(r.timestamp.replace("Z", "+00:00")) > cutoff
            ]
            return report

    # ── System Metrics ───────────────────────────────────────────

    def get_system_metrics(self) -> dict:
        """Get host-level system metrics."""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            net = psutil.net_io_counters()
            return {
                "cpu_pct": cpu,
                "memory_total_mb": round(mem.total / 1024 / 1024, 1),
                "memory_used_mb": round(mem.used / 1024 / 1024, 1),
                "memory_pct": mem.percent,
                "disk_total_gb": round(disk.total / 1024 ** 3, 2),
                "disk_used_pct": disk.percent,
                "bytes_sent": net.bytes_sent,
                "bytes_recv": net.bytes_recv,
                "uptime_seconds": round(monotonic() - self._start_time, 1),
            }
        except Exception as e:
            logger.error("System metrics failed: %s", e)
            return {}

    # ── Querying ─────────────────────────────────────────────────

    def get_module_history(self, name: str, limit: int = 100) -> List[dict]:
        """Get recent metric history for a module from the database."""
        try:
            cursor = self._conn.execute(
                "SELECT latency_ms, throughput, error_rate, queue_depth, "
                "memory_mb, cpu_pct, status, timestamp FROM metrics "
                "WHERE module_name = ? ORDER BY timestamp DESC LIMIT ?",
                (name, limit),
            )
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error("History query failed: %s", e)
            return []

    def get_latest_metrics(self, name: str) -> Optional[dict]:
        """Get the latest in-memory metrics for a module."""
        return self._modules.get(name, {}).copy() or None

    # ── Lifecycle ─────────────────────────────────