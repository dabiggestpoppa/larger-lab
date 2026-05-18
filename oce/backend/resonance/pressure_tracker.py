"""
V3 Phase 1 — Pressure Tracker
Monitors entropy pressure across the cognitive field.

Pressure = amplitude × (1 - coherence) × entropy_delta
High pressure = strong signal that doesn't fit the field = instability.

The pressure tracker is the "nervous system" — it detects where the field
is under stress and triggers repair when thresholds are exceeded.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional, Callable

from .signal_packet import SignalPacket, SignalField
from .boundary_mapper import BoundaryMapper, Boundary, PressureZone


@dataclass
class PressureAlert:
    """Alert generated when pressure exceeds threshold."""
    alert_id: str
    zone_id: str
    boundary_id: str
    pressure: float
    severity: str  # "low", "medium", "high", "critical"
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    resolved_at: Optional[float] = None

    def resolve(self) -> None:
        self.resolved = True
        self.resolved_at = time.time()

    def to_dict(self) -> dict:
        return {
            "alert_id": self.alert_id,
            "zone_id": self.zone_id,
            "boundary_id": self.boundary_id,
            "pressure": round(self.pressure, 4),
            "severity": self.severity,
            "timestamp": self.timestamp,
            "resolved": self.resolved,
        }


class PressureTracker:
    """
    Tracks entropy pressure across the cognitive field.
    
    Monitors:
    - Observer overload (too many signals per observer)
    - Synchronization instability (phase drift)
    - Entropy spikes (sudden entropy increases)
    - Coherence drift (gradual coherence loss)
    - Trajectory fragmentation (conflicting action paths)
    """

    def __init__(
        self,
        warning_threshold: float = 0.5,
        critical_threshold: float = 0.8,
        cooldown: float = 5.0,  # seconds between alerts for same zone
    ):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.cooldown = cooldown
        self._alerts: list[PressureAlert] = []
        self._alert_counter = 0
        self._last_alert_time: dict[str, float] = {}
        self._pressure_history: list[dict] = []
        self._max_history = 1000
        self._callbacks: list[Callable[[PressureAlert], None]] = []

    def register_callback(self, callback: Callable[[PressureAlert], None]) -> None:
        """Register a callback for when alerts are generated."""
        self._callbacks.append(callback)

    def scan(
        self, field: SignalField, boundary_mapper: BoundaryMapper,
    ) -> list[PressureAlert]:
        """
        Scan the field for pressure anomalies.
        Returns new alerts generated.
        """
        new_alerts = []
        now = time.time()

        # Check boundary pressures
        for boundary in boundary_mapper.boundaries.values():
            if boundary.pressure >= self.warning_threshold:
                # Cooldown check
                last_time = self._last_alert_time.get(boundary.boundary_id, 0)
                if now - last_time < self.cooldown:
                    continue

                severity = (
                    "critical" if boundary.pressure >= self.critical_threshold
                    else "warning"
                )

                self._alert_counter += 1
                alert = PressureAlert(
                    alert_id=f"alert_{self._alert_counter}",
                    zone_id="",
                    boundary_id=boundary.boundary_id,
                    pressure=boundary.pressure,
                    severity=severity,
                )
                new_alerts.append(alert)
                self._alerts.append(alert)
                self._last_alert_time[boundary.boundary_id] = now

        # Check pressure zones
        for zone in boundary_mapper.pressure_zones.values():
            if zone.intensity >= self.warning_threshold:
                last_time = self._last_alert_time.get(zone.zone_id, 0)
                if now - last_time < self.cooldown:
                    continue

                severity = (
                    "critical" if zone.intensity >= self.critical_threshold
                    else "warning"
                )

                self._alert_counter += 1
                alert = PressureAlert(
                    alert_id=f"alert_{self._alert_counter}",
                    zone_id=zone.zone_id,
                    boundary_id="",
                    pressure=zone.intensity,
                    severity=severity,
                )
                new_alerts.append(alert)
                self._alerts.append(alert)
                self._last_alert_time[zone.zone_id] = now

        # Check field-level pressure
        field_pressure = self._calc_field_pressure(field)
        if field_pressure >= self.warning_threshold:
            last_time = self._last_alert_time.get("__field__", 0)
            if now - last_time >= self.cooldown:
                severity = (
                    "critical" if field_pressure >= self.critical_threshold
                    else "warning"
                )
                self._alert_counter += 1
                alert = PressureAlert(
                    alert_id=f"alert_{self._alert_counter}",
                    zone_id="__field__",
                    boundary_id="",
                    pressure=field_pressure,
                    severity=severity,
                )
                new_alerts.append(alert)
                self._alerts.append(alert)
                self._last_alert_time["__field__"] = now

        # Record history
        self._pressure_history.append({
            "timestamp": now,
            "field_pressure": field_pressure,
            "boundary_count": len(boundary_mapper.boundaries),
            "zone_count": len(boundary_mapper.pressure_zones),
            "new_alerts": len(new_alerts),
        })
        if len(self._pressure_history) > self._max_history:
            self._pressure_history = self._pressure_history[-self._max_history:]

        # Fire callbacks
        for alert in new_alerts:
            for cb in self._callbacks:
                cb(alert)

        return new_alerts

    def _calc_field_pressure(self, field: SignalField) -> float:
        """Calculate overall field pressure."""
        if not field.signals:
            return 0.0
        total_pressure = sum(s.signal_pressure for s in field.signals)
        return min(1.0, total_pressure / max(len(field.signals), 1))

    def get_active_alerts(self) -> list[PressureAlert]:
        """Get all unresolved alerts."""
        return [a for a in self._alerts if not a.resolved]

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.resolve()
                return True
        return False

    def get_pressure_trend(self, window: int = 10) -> float:
        """Get pressure trend (positive = increasing, negative = decreasing)."""
        if len(self._pressure_history) < 2:
            return 0.0
        recent = self._pressure_history[-window:]
        if len(recent) < 2:
            return 0.0
        values = [h["field_pressure"] for h in recent]
        return (values[-1] - values[0]) / len(values)

    @property
    def stats(self) -> dict:
        """Pressure tracker statistics."""
        active = self.get_active_alerts()
        return {
            "total_alerts": len(self._alerts),
            "active_alerts": len(active),
            "critical_alerts": sum(1 for a in active if a.severity == "critical"),
            "warning_alerts": sum(1 for a in active if a.severity == "warning"),
            "pressure_trend": round(self.get_pressure_trend(), 4),
            "history_size": len(self._pressure_history),
        }

    def __repr__(self) -> str:
        active = self.get_active_alerts()
        return (
            f"PressureTracker(alerts={len(active)}, "
            f"critical={sum(1 for a in active if a.severity == 'critical')})"
        )
