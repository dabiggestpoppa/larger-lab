"""
OCE Alerting Engine — Phase 5.3
================================
Threshold-based alerting with cooldown, acknowledgment, and auto-repair triggers.

Features:
- Configurable alert rules (metric, threshold, comparison, severity)
- Built-in rules for critical OCE conditions
- Cooldown to prevent alert storms
- Alert lifecycle: firing → acknowledged → resolved
- Auto-repair trigger integration
"""

import sqlite3
import json
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("oce.alerting")

# ─── Constants ───────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "alerts.db"


# ─── Data Models ─────────────────────────────────────────────────────────────

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertState(str, Enum):
    FIRING = "firing"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertRule(BaseModel):
    """An alert rule definition."""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    metric: str  # dot-path into metrics summary, e.g., "observers.avg_health"
    threshold: float
    comparison: str  # "lt", "gt", "lte", "gte", "eq"
    severity: AlertSeverity
    cooldown_sec: int = 300  # 5 min default
    enabled: bool = True
    description: str = ""
    auto_repair: bool = False  # trigger auto-repair action
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Alert(BaseModel):
    """An active or historical alert instance."""
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    rule_name: str
    severity: AlertSeverity
    state: AlertState = AlertState.FIRING
    metric: str
    threshold: float
    actual_value: float
    message: str
    fired_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ─── Built-in Rules ──────────────────────────────────────────────────────────

BUILTIN_RULES = [
    {
        "name": "observer_health_critical",
        "metric": "observers.avg_health",
        "threshold": 0.3,
        "comparison": "lt",
        "severity": "critical",
        "cooldown_sec": 120,
        "description": "Average observer health below 0.3",
        "auto_repair": True,
    },
    {
        "name": "event_queue_overflow",
        "metric": "events.total_count",
        "threshold": 1000,
        "comparison": "gt",
        "severity": "warning",
        "cooldown_sec": 300,
        "description": "Event queue depth exceeds 1000",
        "auto_repair": False,
    },
    {
        "name": "memory_usage_critical",
        "metric": "memory.total_size_bytes",
        "threshold": 1073741824,  # 1GB
        "comparison": "gt",
        "severity": "critical",
        "cooldown_sec": 300,
        "description": "Memory usage exceeds 1GB",
        "auto_repair": True,
    },
    {
        "name": "entropy_budget_low",
        "metric": "entropy.usage_pct",
        "threshold": 90.0,
        "comparison": "gt",
        "severity": "warning",
        "cooldown_sec": 600,
        "description": "Entropy budget usage above 90%",
        "auto_repair": False,
    },
    {
        "name": "observer_error_rate_high",
        "metric": "observers.avg_health",
        "threshold": 0.5,
        "comparison": "lt",
        "severity": "critical",
        "cooldown_sec": 180,
        "description": "Observer health degraded below 0.5",
        "auto_repair": True,
    },
]


# ─── Comparison Helper ───────────────────────────────────────────────────────

def _compare(actual: float, threshold: float, comparison: str) -> bool:
    """Evaluate a comparison."""
    if comparison == "lt":
        return actual < threshold
    elif comparison == "gt":
        return actual > threshold
    elif comparison == "lte":
        return actual <= threshold
    elif comparison == "gte":
        return actual >= threshold
    elif comparison == "eq":
        return actual == threshold
    return False


def _get_nested(data: dict, path: str) -> Any:
    """Get a nested value from a dict using dot notation."""
    parts = path.split(".")
    val = data
    for part in parts:
        if isinstance(val, dict):
            val = val.get(part)
        else:
            return None
    return val


# ─── Alerting Engine ─────────────────────────────────────────────────────────

class AlertingEngine:
    """
    Singleton alerting engine for OCE.

    Evaluates metrics against rules, manages alert lifecycle,
    and supports auto-repair triggers.
    """

    _instance: Optional["AlertingEngine"] = None
    _lock = Lock()

    def __new__(cls) -> "AlertingEngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self._rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._max_history = 5000
        self._last_fired: Dict[str, float] = {}  # rule_id -> timestamp

        # Initialize SQLite
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

        # Load built-in rules
        for rule_data in BUILTIN_RULES:
            self.add_rule(**rule_data)

        logger.info(
            f"AlertingEngine initialized with {len(BUILTIN_RULES)} built-in rules"
        )

    def _init_db(self):
        """Initialize SQLite database for alert persistence."""
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_history (
                    alert_id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    rule_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    state TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    threshold REAL,
                    actual_value REAL,
                    message TEXT,
                    fired_at TEXT NOT NULL,
                    acknowledged_at TEXT,
                    resolved_at TEXT,
                    alert_json TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_state
                ON alert_history(state)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_fired
                ON alert_history(fired_at)
            """)
            conn.commit()

    # ─── Rule Management ─────────────────────────────────────────────────

    def add_rule(
        self,
        name: str,
        metric: str,
        threshold: float,
        comparison: str = "lt",
        severity: str = "warning",
        cooldown_sec: int = 300,
        description: str = "",
        auto_repair: bool = False,
    ) -> str:
        """Add an alert rule. Returns rule_id."""
        rule = AlertRule(
            name=name,
            metric=metric,
            threshold=threshold,
            comparison=comparison,
            severity=AlertSeverity(severity),
            cooldown_sec=cooldown_sec,
            description=description,
            auto_repair=auto_repair,
        )
        self._rules[rule.rule_id] = rule
        logger.info(f"Alert rule added: {name} ({rule.rule_id})")
        return rule.rule_id

    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def get_rules(self) -> List[Dict[str, Any]]:
        """Get all alert rules."""
        return [r.model_dump() for r in self._rules.values()]

    # ─── Evaluation ──────────────────────────────────────────────────────

    def evaluate(self, metrics_snapshot: Dict[str, Any]) -> List[Alert]:
        """
        Evaluate all rules against a metrics snapshot.
        Returns list of newly fired alerts.
        """
        import time as _time

        newly_fired = []
        now = _time.time()

        for rule in self._rules.values():
            if not rule.enabled:
                continue

            # Check cooldown
            last_fired = self._last_fired.get(rule.rule_id, 0)
            if now - last_fired < rule.cooldown_sec:
                continue

            # Get metric value
            actual = _get_nested(metrics_snapshot, rule.metric)
            if actual is None:
                continue

            # Evaluate
            if _compare(float(actual), rule.threshold, rule.comparison):
                alert = Alert(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    metric=rule.metric,
                    threshold=rule.threshold,
                    actual_value=float(actual),
                    message=(
                        f"{rule.name}: {rule.metric}={actual:.3f} "
                        f"{rule.comparison} {rule.threshold}"
                    ),
                    metadata={
                        "comparison": rule.comparison,
                        "auto_repair": rule.auto_repair,
                    },
                )
                self._active_alerts[alert.alert_id] = alert
                self._last_fired[rule.rule_id] = now
                newly_fired.append(alert)
                logger.warning(f"ALERT FIRING: {alert.message}")

        return newly_fired

    # ─── Alert Lifecycle ─────────────────────────────────────────────────

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all currently firing/acknowledged alerts."""
        return [a.model_dump() for a in self._active_alerts.values()]

    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alert history."""
        recent = self._alert_history[-limit:]
        return [a.model_dump() for a in reversed(recent)]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an active alert."""
        alert = self._active_alerts.get(alert_id)
        if alert is None:
            return False
        alert.state = AlertState.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(timezone.utc)
        logger.info(f"Alert acknowledged: {alert_id}")
        return True

    def clear_alert(self, alert_id: str) -> bool:
        """Clear (resolve) an active alert."""
        alert = self._active_alerts.pop(alert_id, None)
        if alert is None:
            return False
        alert.state = AlertState.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)
        self._alert_history.append(alert)
        if len(self._alert_history) > self._max_history:
            self._alert_history = self._alert_history[-self._max_history:]
        self._persist_alert(alert)
        logger.info(f"Alert resolved: {alert_id}")
        return True

    def _persist_alert(self, alert: Alert):
        """Persist an alert to SQLite."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO alert_history
                    (alert_id, rule_id, rule_name, severity, state, metric,
                     threshold, actual_value, message, fired_at,
                     acknowledged_at, resolved_at, alert_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        alert.alert_id,
                        alert.rule_id,
                        alert.rule_name,
                        alert.severity.value,
                        alert.state.value,
                        alert.metric,
                        alert.threshold,
                        alert.actual_value,
                        alert.message,
                        alert.fired_at.isoformat(),
                        alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                        alert.resolved_at.isoformat() if alert.resolved_at else None,
                        json.dumps(alert.model_dump(), default=str),
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to persist alert: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get alerting statistics."""
        firing = sum(
            1 for a in self._active_alerts.values()
            if a.state == AlertState.FIRING
        )
        acknowledged = sum(
            1 for a in self._active_alerts.values()
            if a.state == AlertState.ACKNOWLEDGED
        )
        by_severity: Dict[str, int] = {}
        for alert in self._active_alerts.values():
            sev = alert.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

        return {
            "active_firing": firing,
            "active_acknowledged": acknowledged,
            "total_active": len(self._active_alerts),
            "total_history": len(self._alert_history),
            "rules_count": len(self._rules),
            "by_severity": by_severity,
        }


# ─── Singleton Access ───────────────────────────────────────────────────────

def get_alerting_engine() -> AlertingEngine:
    """Get the singleton AlertingEngine instance."""
    return AlertingEngine()
