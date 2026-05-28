"""
O7-B6: DormantStateManager
===========================
Manage idle/dormant/active transitions.

Controls active vs dormant orchestration states. The system should
spend most time in dormant/observational modes, acting only when necessary.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger("persistent_field.dormant_state")


class DormantState(str, Enum):
    DORMANT = "dormant"
    OBSERVATIONAL = "observational"
    ACTIVE = "active"
    RECOVERY = "recovery"
    CRITICAL = "critical"


STATE_TRANSITIONS: dict[DormantState, set[DormantState]] = {
    DormantState.DORMANT: {DormantState.OBSERVATIONAL, DormantState.ACTIVE},
    DormantState.OBSERVATIONAL: {DormantState.DORMANT, DormantState.ACTIVE, DormantState.CRITICAL},
    DormantState.ACTIVE: {DormantState.OBSERVATIONAL, DormantState.RECOVERY, DormantState.CRITICAL},
    DormantState.RECOVERY: {DormantState.OBSERVATIONAL, DormantState.ACTIVE, DormantState.CRITICAL},
    DormantState.CRITICAL: {DormantState.RECOVERY, DormantState.OBSERVATIONAL},
}


@dataclass
class StateTransition:
    """Record of a state transition."""
    from_state: str
    to_state: str
    reason: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class DormantStateManager:
    """
    Manage dormant/active orchestration state transitions.

    The system should spend most time in dormant/observational modes.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._current_state = DormantState.DORMANT
        self._transitions: list[StateTransition] = []
        self._state_entered_at: float = time.time()
        self._idle_threshold: float = 300.0  # 5 minutes to enter dormant

    def get_state(self) -> str:
        """Get current dormant state."""
        return self._current_state.value

    def transition(self, new_state: DormantState, reason: str = "") -> bool:
        """Transition to a new state."""
        with self._lock:
            if new_state not in STATE_TRANSITIONS.get(self._current_state, set()):
                logger.warning(
                    f"Invalid transition: {self._current_state} -> {new_state}"
                )
                return False

            old_state = self._current_state
            self._current_state = new_state
            self._state_entered_at = time.time()

            transition = StateTransition(
                from_state=old_state.value,
                to_state=new_state.value,
                reason=reason,
            )
            self._transitions.append(transition)
            logger.info(f"State transition: {old_state.value} -> {new_state.value} ({reason})")
            return True

    def check_idle_transition(self) -> DormantState | None:
        """Check if system should transition to dormant based on idle time."""
        idle_time = time.time() - self._state_entered_at
        if idle_time >= self._idle_threshold and self._current_state == DormantState.OBSERVATIONAL:
            self.transition(DormantState.DORMANT, "idle_timeout")
            return DormantState.DORMANT
        return None

    def get_time_in_state(self) -> float:
        """Get time spent in current state (seconds)."""
        return time.time() - self._state_entered_at

    def get_transition_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent state transitions."""
        return [
            {
                "from": t.from_state,
                "to": t.to_state,
                "reason": t.reason,
                "timestamp": t.timestamp,
            }
            for t in self._transitions[-limit:]
        ]

    def get_summary(self) -> dict[str, Any]:
        """Get dormant state summary."""
        return {
            "current_state": self._current_state.value,
            "time_in_state_seconds": round(self.get_time_in_state(), 1),
            "total_transitions": len(self._transitions),
            "idle_threshold_seconds": self._idle_threshold,
        }
