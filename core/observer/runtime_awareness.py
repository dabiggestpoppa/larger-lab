"""
O-1-B3: RuntimeAwareness
========================
Maintains awareness of topology, active observers, entropy, repair state,
spawned agents, execution systems.

Inputs: event_bus, topology_state, observer_registry, runtime_metrics,
entropy_metrics.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass
class RuntimeSnapshot:
    """Point-in-time runtime awareness snapshot."""
    timestamp: str
    topology_node_count: int = 0
    topology_edge_count: int = 0
    active_observers: list[str] = field(default_factory=list)
    entropy_level: float = 0.0
    entropy_trend: str = "stable"  # "rising", "falling", "stable"
    repair_active: bool = False
    repair_targets: list[str] = field(default_factory=list)
    spawned_agents: int = 0
    execution_systems: dict[str, str] = field(default_factory=dict)
    alerts: list[dict[str, Any]] = field(default_factory=list)


class RuntimeAwareness:
    """
    Maintains live awareness of the runtime environment.
    
    Subscribes to events and topology changes to keep an accurate
    picture of the current system state.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._snapshot = RuntimeSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self._history: list[RuntimeSnapshot] = []
        self._max_history = 100
        self._listeners: list[Callable] = []

    @property
    def snapshot(self) -> RuntimeSnapshot:
        return self._snapshot

    def update_topology(self, node_count: int, edge_count: int) -> None:
        with self._lock:
            self._snapshot.topology_node_count = node_count
            self._snapshot.topology_edge_count = edge_count
            self._snapshot.timestamp = datetime.now(timezone.utc).isoformat()
            self._check_topology_alerts()

    def update_observers(self, observer_ids: list[str]) -> None:
        with self._lock:
            self._snapshot.active_observers = list(observer_ids)
            self._snapshot.timestamp = datetime.now(timezone.utc).isoformat()

    def update_entropy(self, level: float, trend: str = "stable") -> None:
        with self._lock:
            prev = self._snapshot.entropy_level
            self._snapshot.entropy_level = max(0.0, min(1.0, level))
            self._snapshot.entropy_trend = trend
            self._snapshot.timestamp = datetime.now(timezone.utc).isoformat()
            if level > 0.7 and prev <= 0.7:
                self._add_alert("entropy_spike", f"Entropy rose to {level:.2f}")
            self._notify_listeners("entropy", level)

    def update_repair(self, active: bool, targets: list[str] | None = None) -> None:
        with self._lock:
            self._snapshot.repair_active = active
            self._snapshot.repair_targets = targets or []
            self._snapshot.timestamp = datetime.now(timezone.utc).isoformat()

    def update_spawned_agents(self, count: int) -> None:
        with self._lock:
            self._snapshot.spawned_agents = count
            self._snapshot.timestamp = datetime.now(timezone.utc).isoformat()

    def update_execution_systems(self, systems: dict[str, str]) -> None:
        with self._lock:
            self._snapshot.execution_systems = dict(systems)
            self._snapshot.timestamp = datetime.now(timezone.utc).isoformat()

    def get_snapshot_dict(self) -> dict[str, Any]:
        s = self._snapshot
        return {
            "timestamp": s.timestamp,
            "topology": {
                "nodes": s.topology_node_count,
                "edges": s.topology_edge_count,
            },
            "active_observers": s.active_observers,
            "entropy": {
                "level": s.entropy_level,
                "trend": s.entropy_trend,
            },
            "repair": {
                "active": s.repair_active,
                "targets": s.repair_targets,
            },
            "spawned_agents": s.spawned_agents,
            "execution_systems": s.execution_systems,
            "alerts": s.alerts[-10:],  # last 10 alerts
        }

    def take_snapshot(self) -> None:
        """Save current snapshot to history."""
        with self._lock:
            import copy
            self._history.append(copy.deepcopy(self._snapshot))
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

    def subscribe(self, callback: Callable) -> None:
        self._listeners.append(callback)

    def _add_alert(self, alert_type: str, message: str) -> None:
        self._snapshot.alerts.append({
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def _check_topology_alerts(self) -> None:
        if self._snapshot.topology_node_count == 0:
            self._add_alert("topology_empty", "No topology nodes detected")

    def _notify_listeners(self, key: str, value: Any) -> None:
        for cb in self._listeners:
            try:
                cb(key, value)
            except Exception:
                pass
