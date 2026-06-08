"""8_coevolution.autonomy_manager

Manages autonomous field operation levels and self-governance policies.

Tracks which field operations can run autonomously vs. require human
approval, with graduated autonomy levels and safety constraints.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.coevolution.autonomy")


class AutonomyPolicy(BaseModel):
    """Autonomy policy for a specific operation type."""
    operation_type: str
    autonomy_level: int = 0  # 0=manual, 1=suggest, 2=auto-with-log, 3=full-auto
    max_daily_executions: int = 100
    requires_approval_above: Optional[float] = None  # cost/resource threshold
    safety_constraints: List[str] = Field(default_factory=list)
    last_updated: str = ""


class AutonomyEvent(BaseModel):
    """Record of an autonomous action."""
    event_id: str
    operation_type: str
    autonomy_level: int
    description: str
    approved: bool
    timestamp: str = ""
    outcome: Optional[str] = None


class AutonomyManagerConfig(BaseModel):
    """Configuration for autonomy_manager."""
    enabled: bool = True
    max_autonomy_level: int = 3
    default_level: int = 0
    max_events: int = 10000
    review_interval_hours: int = 24


class AutonomyManagerModule:
    """Manages autonomous field operation levels and policies."""

    def __init__(self):
        self.config = AutonomyManagerConfig()
        self.running = False
        self._lock = Lock()
        self._policies: Dict[str, AutonomyPolicy] = {}
        self._events: List[AutonomyEvent] = []
        self._daily_counts: Dict[str, int] = defaultdict(int)
        self._last_review: str = ""

    def start(self) -> None:
        self.running = True
        self._last_review = datetime.now(timezone.utc).isoformat()
        logger.info("AutonomyManager started (max_level=%d)", self.config.max_autonomy_level)

    def stop(self) -> None:
        self.running = False
        logger.info("AutonomyManager stopped")

    def set_policy(self, operation_type: str, autonomy_level: int,
                   max_daily: int = 100,
                   requires_approval_above: Optional[float] = None,
                   safety_constraints: Optional[List[str]] = None) -> AutonomyPolicy:
        """Set autonomy policy for an operation type.

        Args:
            operation_type: Type of operation (e.g., 'trade', 'deploy', 'modify').
            autonomy_level: 0=manual, 1=suggest, 2=auto-with-log, 3=full-auto.
            max_daily: Maximum autonomous executions per day.
            requires_approval_above: Require approval if cost exceeds this.
            safety_constraints: List of safety constraint identifiers.

        Returns:
            The created/updated policy.
        """
        level = max(0, min(self.config.max_autonomy_level, autonomy_level))
        with self._lock:
            policy = AutonomyPolicy(
                operation_type=operation_type,
                autonomy_level=level,
                max_daily_executions=max_daily,
                requires_approval_above=requires_approval_above,
                safety_constraints=safety_constraints or [],
                last_updated=datetime.now(timezone.utc).isoformat(),
            )
            self._policies[operation_type] = policy
            logger.info("Autonomy policy set: %s -> level %d", operation_type, level)
            return policy

    def check_autonomy(self, operation_type: str,
                       estimated_cost: Optional[float] = None) -> Dict[str, Any]:
        """Check if an operation can run autonomously.

        Args:
            operation_type: Type of operation to check.
            estimated_cost: Estimated cost/resource usage.

        Returns:
            Dict with 'allowed' (bool), 'level' (int), 'reason' (str).
        """
        with self._lock:
            policy = self._policies.get(operation_type)
            if not policy:
                return {
                    "allowed": False,
                    "level": 0,
                    "reason": f"No policy for '{operation_type}' — default to manual",
                }

            level = policy.autonomy_level

            # Check daily limit
            if self._daily_counts[operation_type] >= policy.max_daily_executions:
                return {
                    "allowed": False,
                    "level": level,
                    "reason": f"Daily limit reached ({policy.max_daily_executions})",
                }

            # Check cost threshold
            if (estimated_cost is not None
                    and policy.requires_approval_above is not None
                    and estimated_cost > policy.requires_approval_above):
                return {
                    "allowed": False,
                    "level": level,
                    "reason": f"Cost {estimated_cost} exceeds threshold {policy.requires_approval_above}",
                }

            if level == 0:
                return {"allowed": False, "level": 0, "reason": "Manual approval required"}
            elif level == 1:
                return {"allowed": False, "level": 1, "reason": "Suggestion mode — human decides"}
            elif level == 2:
                return {"allowed": True, "level": 2, "reason": "Auto with logging"}
            else:
                return {"allowed": True, "level": 3, "reason": "Full autonomous"}

    def record_execution(self, operation_type: str, description: str,
                         approved: bool, outcome: Optional[str] = None) -> None:
        """Record an autonomous or manual execution event.

        Args:
            operation_type: Type of operation.
            description: What was executed.
            approved: Whether it was approved (or auto-executed).
            outcome: Result description.
        """
        import uuid
        with self._lock:
            self._daily_counts[operation_type] += 1
            event = AutonomyEvent(
                event_id=str(uuid.uuid4())[:8],
                operation_type=operation_type,
                autonomy_level=self._policies.get(operation_type, AutonomyPolicy(operation_type=operation_type)).autonomy_level,
                description=description,
                approved=approved,
                timestamp=datetime.now(timezone.utc).isoformat(),
                outcome=outcome,
            )
            self._events.append(event)
            if len(self._events) > self.config.max_events:
                self._events = self._events[-self.config.max_events:]
        logger.debug("Autonomy event: %s — %s (approved=%s)", operation_type, description, approved)

    def get_policy(self, operation_type: str) -> Optional[AutonomyPolicy]:
        """Get the autonomy policy for an operation type."""
        with self._lock:
            return self._policies.get(operation_type)

    def get_events(self, operation_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get autonomy events, optionally filtered."""
        with self._lock:
            events = list(reversed(self._events))
            if operation_type:
                events = [e for e in events if e.operation_type == operation_type]
            return [e.model_dump() for e in events[:limit]]

    def get_stats(self) -> Dict[str, Any]:
        """Get autonomy manager statistics."""
        with self._lock:
            level_counts: Dict[int, int] = defaultdict(int)
            for p in self._policies.values():
                level_counts[p.autonomy_level] += 1
            return {
                "total_policies": len(self._policies),
                "total_events": len(self._events),
                "autonomy_level_distribution": dict(level_counts),
                "daily_counts": dict(self._daily_counts),
                "last_review": self._last_review,
            }
