"""
V3 Phase 9 — Alert System
Threshold-based alerting with lifecycle management.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


class AlertSeverity(str):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertState(str):
    FIRING = "firing"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class AlertRule:
    """An alert rule definition."""
    rule_id: str
    name: str
    metric_name: str
    threshold: float
    severity: str = "warning"
    cooldown_seconds: float = 300.0
    enabled: bool = True


@dataclass
class Alert:
    """An alert instance."""
    alert_id: str
    rule_id: str
    name: str
    severity: str
    state: str = "firing"
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    acknowledged_at: Optional[float] = None
    resolved_at: Optional[float] = None

    @property
    def is_active(self) -> bool:
        return self.state in ("firing", "acknowledged")

    @property
    def duration(self) -> float:
        end = self.resolved_at or time.time()
        return end - self.timestamp


class AlertSystem:
    """
    Threshold-based alerting with lifecycle management.
    
    Lifecycle: firing → acknowledged → resolved
    Cooldown prevents alert storms.
    """

    def __init__(self):
        self._rules: dict[str, AlertRule] = {}
        self._alerts: list[Alert] = []
        self._last_fired: dict[str, float] = {}  # rule_id → last fire time

    def add_rule(self, name: str, metric_name: str, threshold: float,
                 severity: str = "warning", cooldown_seconds: float = 300.0) -> AlertRule:
        """Add an alert rule."""
        rule = AlertRule(
            rule_id=f"rule_{uuid.uuid4().hex[:8]}",
            name=name, metric_name=metric_name,
            threshold=threshold, severity=severity,
            cooldown_seconds=cooldown_seconds,
        )
        self._rules[rule.rule_id] = rule
        return rule

    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def evaluate(self, metric_name: str, value: float) -> list[Alert]:
        """Evaluate all rules against a metric value. Returns new alerts."""
        new_alerts = []
        for rule in self._rules.values():
            if not rule.enabled or rule.metric_name != metric_name:
                continue
            if value < rule.threshold:
                continue

            # Check cooldown
            last_fired = self._last_fired.get(rule.rule_id, 0)
            if time.time() - last_fired < rule.cooldown_seconds:
                continue

            alert = Alert(
                alert_id=f"alert_{uuid.uuid4().hex[:8]}",
                rule_id=rule.rule_id,
                name=rule.name,
                severity=rule.severity,
                message=f"{metric_name}={value:.3f} exceeds threshold {rule.threshold}",
            )
            self._alerts.append(alert)
            self._last_fired[rule.rule_id] = time.time()
            new_alerts.append(alert)

        return new_alerts

    def acknowledge(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self._alerts:
            if alert.alert_id == alert_id and alert.state == "firing":
                alert.state = "acknowledged"
                alert.acknowledged_at = time.time()
                return True
        return False

    def resolve(self, alert_id: str) -> bool:
        """Resolve an alert."""
        for alert in self._alerts:
            if alert.alert_id == alert_id and alert.is_active:
                alert.state = "resolved"
                alert.resolved_at = time.time()
                return True
        return False

    def get_active_alerts(self) -> list[Alert]:
        """Get all active (firing or acknowledged) alerts."""
        return [a for a in self._alerts if a.is_active]

    def get_alerts_by_severity(self, severity: str) -> list[Alert]:
        """Get all alerts of a given severity."""
        return [a for a in self._alerts if a.severity == severity]

    @property
    def stats(self) -> dict:
        active = sum(1 for a in self._alerts if a.is_active)
        critical = sum(1 for a in self._alerts if a.severity == "critical" and a.is_active)
        return {
            "total_rules": len(self._rules),
            "total_alerts": len(self._alerts),
            "active_alerts": active,
            "critical_alerts": critical,
            "resolved": sum(1 for a in self._alerts if a.state == "resolved"),
        }
