"""
O7-B7: AutonomousRepair
========================
Self-healing without operator intervention.

Detects hung tasks, entropy spikes, resource exhaustion.
Bounded repair actions — no infinite loops. Escalates to operator if repair fails.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger("persistent_field.autonomous_repair")


class RepairAction(str, Enum):
    RESTART_OBSERVER = "restart_observer"
    TERMINATE_HUNG = "terminate_hung"
    RESTORE_STATE = "restore_state"
    REDUCE_ENTROPY = "reduce_entropy"
    REBALANCE_TOPOLOGY = "rebalance_topology"
    CLEAR_CACHE = "clear_cache"


class RepairStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    STABLE = "stable"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass
class RepairEvent:
    """A repair event record."""
    event_id: str
    action: str
    target: str
    status: str = RepairStatus.PENDING
    duration_seconds: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    timestamp: str = ""
    error: str | None = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class AutonomousRepair:
    """
    Bounded self-stabilization system.

    Allowed: restart observers, terminate hung tasks, restore continuity,
    rebalance topology, clear cache.
    Forbidden: rewrite architecture, mutate orchestration core, uncontrolled spawning.
    """

    MAX_CONCURRENT_REPAIRS = 3
    REPAIR_TIMEOUT = 300.0  # 5 minutes

    def __init__(self):
        self._lock = threading.Lock()
        self._events: list[RepairEvent] = []
        self._active_repairs: dict[str, RepairEvent] = {}

    def detect_issues(self) -> list[dict[str, Any]]:
        """Detect issues requiring repair."""
        issues = []

        # Check for hung tasks (simulated)
        issues.extend(self._detect_hung_tasks())

        # Check for entropy spikes (simulated)
        issues.extend(self._detect_entropy_spikes())

        # Check for resource exhaustion (simulated)
        issues.extend(self._detect_resource_exhaustion())

        return issues

    def repair(self, action: RepairAction, target: str) -> RepairEvent:
        """Execute a bounded repair action."""
        with self._lock:
            if len(self._active_repairs) >= self.MAX_CONCURRENT_REPAIRS:
                event = RepairEvent(
                    event_id=f"repair_{int(time.time())}",
                    action=action.value,
                    target=target,
                    status=RepairStatus.FAILED,
                    error="Max concurrent repairs reached",
                )
                self._events.append(event)
                return event

            event = RepairEvent(
                event_id=f"repair_{int(time.time())}",
                action=action.value,
                target=target,
                status=RepairStatus.IN_PROGRESS,
            )
            self._active_repairs[event.event_id] = event
            self._events.append(event)

        # Execute repair (simulated — real implementation would interact with O-6 substrate)
        try:
            start = time.time()
            success = self._execute_repair(action, target)
            event.duration_seconds = time.time() - start

            if success:
                event.status = RepairStatus.STABLE
            else:
                event.retry_count += 1
                if event.retry_count >= event.max_retries:
                    event.status = RepairStatus.ESCALATED
                    event.error = "Max retries exceeded — escalated to operator"
                else:
                    event.status = RepairStatus.FAILED
                    event.error = "Repair failed, will retry"

        except Exception as e:
            event.status = RepairStatus.FAILED
            event.error = str(e)

        with self._lock:
            self._active_repairs.pop(event.event_id, None)

        logger.info(f"Repair {event.event_id}: {action.value} on {target} -> {event.status}")
        return event

    def get_active_repairs(self) -> list[dict[str, Any]]:
        """Get currently active repairs."""
        with self._lock:
            return [
                {
                    "event_id": e.event_id,
                    "action": e.action,
                    "target": e.target,
                    "status": e.status,
                    "duration_seconds": e.duration_seconds,
                }
                for e in self._active_repairs.values()
            ]

    def get_repair_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get repair event history."""
        return [
            {
                "event_id": e.event_id,
                "action": e.action,
                "target": e.target,
                "status": e.status,
                "duration_seconds": e.duration_seconds,
                "retry_count": e.retry_count,
                "error": e.error,
                "timestamp": e.timestamp,
            }
            for e in self._events[-limit:]
        ]

    def get_status(self) -> dict[str, Any]:
        """Get autonomous repair status."""
        recent = self._events[-50:]
        total = len(recent)
        stable = sum(1 for e in recent if e.status == RepairStatus.STABLE)
        failed = sum(1 for e in recent if e.status == RepairStatus.FAILED)
        escalated = sum(1 for e in recent if e.status == RepairStatus.ESCALATED)

        return {
            "total_repairs": len(self._events),
            "active_repairs": len(self._active_repairs),
            "recent_success_rate": round(stable / total, 2) if total else 1.0,
            "recent_failed": failed,
            "recent_escalated": escalated,
            "max_concurrent": self.MAX_CONCURRENT_REPAIRS,
        }

    def _execute_repair(self, action: RepairAction, target: str) -> bool:
        """Execute a repair action (simulated)."""
        # In real implementation, this would interact with O-6 substrate
        # For now, simulate success for most actions
        time.sleep(0.01)  # Simulate work
        return True

    def _detect_hung_tasks(self) -> list[dict[str, Any]]:
        """Detect hung tasks."""
        return []  # Placeholder — integrate with O-6 ProcessObserver

    def _detect_entropy_spikes(self) -> list[dict[str, Any]]:
        """Detect entropy spikes."""
        return []  # Placeholder — integrate with O-1 ObserverRuntime

    def _detect_resource_exhaustion(self) -> list[dict[str, Any]]:
        """Detect resource exhaustion."""
        return []  # Placeholder — integrate with O-6 EnvironmentalMonitor
