"""
4_instrumentation.sovereign_dashboard
======================================
Dashboard data aggregator — pulls from all Phase 4 modules
to produce dashboard-ready data structures.
"""

import logging
import time
from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.sovereign_dashboard")


class DashboardOverview(BaseModel):
    field_health: str = "unknown"
    active_modules: int = 0
    total_events: int = 0
    active_alerts: int = 0
    uptime_seconds: float = 0.0
    last_updated: str = ""


class ModuleGridItem(BaseModel):
    name: str
    status: str = "unknown"
    health: str = "unknown"
    cpu_pct: float = 0.0
    memory_mb: float = 0.0
    event_count: int = 0
    last_heartbeat: str = ""


class ChartDataPoint(BaseModel):
    timestamp: str
    label: str
    value: float


class SovereignDashboardConfig(BaseModel):
    """Configuration for sovereign_dashboard."""
    enabled: bool = True
    refresh_interval_sec: float = 5.0
    max_alerts_shown: int = 50
    max_chart_points: int = 200


class SovereignDashboardModule:
    """Aggregates data from all Phase 4 modules into dashboard-ready format."""

    def __init__(self):
        self.config = SovereignDashboardConfig()
        self.running = False
        self._lock = Lock()
        self._module_statuses: Dict[str, ModuleGridItem] = {}
        self._alert_feed: deque = deque(maxlen=5000)
        self._chart_history: deque = deque(maxlen=200)
        self._start_time = time.monotonic()
        self._event_count = 0

    def start(self) -> None:
        self.running = True
        self._start_time = time.monotonic()
        logger.info("SovereignDashboard started")

    def stop(self) -> None:
        self.running = False
        logger.info("SovereignDashboard stopped")

    def update_module_status(self, name: str, status: str = "unknown",
                              health: str = "unknown", cpu_pct: float = 0.0,
                              memory_mb: float = 0.0, event_count: int = 0) -> None:
        with self._lock:
            self._module_statuses[name] = ModuleGridItem(
                name=name, status=status, health=health,
                cpu_pct=cpu_pct, memory_mb=memory_mb,
                event_count=event_count,
                last_heartbeat=datetime.now(timezone.utc).isoformat()
            )

    def add_alert(self, severity: str, source: str, message: str) -> None:
        with self._lock:
            self._alert_feed.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "severity": severity,
                "source": source,
                "message": message,
            })

    def record_event(self) -> None:
        with self._lock:
            self._event_count += 1

    def add_chart_point(self, label: str, value: float) -> None:
        with self._lock:
            self._chart_history.append(ChartDataPoint(
                timestamp=datetime.now(timezone.utc).isoformat(),
                label=label,
                value=value,
            ))

    def get_overview(self) -> DashboardOverview:
        with self._lock:
            active = sum(1 for m in self._module_statuses.values() if m.status == "active")
            alerts = sum(1 for a in self._alert_feed if a["severity"] in ("critical", "warning"))
            health = "green" if alerts == 0 else ("yellow" if alerts < 5 else "red")
            return DashboardOverview(
                field_health=health,
                active_modules=active,
                total_events=self._event_count,
                active_alerts=alerts,
                uptime_seconds=round(time.monotonic() - self._start_time, 1),
                last_updated=datetime.now(timezone.utc).isoformat(),
            )

    def get_module_grid(self) -> List[ModuleGridItem]:
        with self._lock:
            return list(self._module_statuses.values())

    def get_alert_feed(self, n: Optional[int] = None) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._alert_feed)
            if n:
                items = items[-n:]
            return items

    def get_performance_chart_data(self, label: str = "events") -> List[ChartDataPoint]:
        with self._lock:
            return [p for p in self._chart_history if p.label == label]

    def get_system_health(self) -> Dict[str, Any]:
        with self._lock:
            overview = self.get_overview()
            grid = self.get_module_grid()
            healthy = sum(1 for m in grid if m.health == "healthy")
            degraded = sum(1 for m in grid if m.health == "degraded")
            critical = sum(1 for m in grid if m.health == "critical")
            total = len(grid) or 1
            return {
                "overall": overview.field_health,
                "healthy_pct": round(healthy / total * 100, 1),
                "degraded_pct": round(degraded / total * 100, 1),
                "critical_pct": round(critical / total * 100, 1),
                "active_alerts": overview.active_alerts,
                "uptime_seconds": overview.uptime_seconds,
                "modules_total": len(grid),
                "modules_active": overview.active_modules,
            }
