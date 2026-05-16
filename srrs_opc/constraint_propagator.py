"""
Constraint Propagation Engine
==============================
Event-driven constraint propagation for SRRA-OPH Phase 2.

When a high-level constraint changes, all dependent state updates automatically.
Uses a simple event bus (no external dependencies for Phase 2).

Architecture:
- Constraints are stored as anchors with tag "constraint"
- When a constraint changes, an event fires
- Registered handlers receive the event and update their local state
- Propagation is bounded (max depth, no infinite loops)
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Callable, Dict, Any, List, Optional
from collections import defaultdict

# Event types
CONSTRAINT_CHANGED = "constraint_changed"
CONSTRAINT_ADDED = "constraint_added"
CONSTRAINT_REMOVED = "constraint_removed"


class ConstraintEvent:
    """A constraint change event."""

    def __init__(self, event_type: str, constraint_id: str,
                 old_value: Any, new_value: Any, source: str = "system"):
        self.event_id = f"evt_{uuid.uuid4().hex[:8]}"
        self.event_type = event_type
        self.constraint_id = constraint_id
        self.old_value = old_value
        self.new_value = new_value
        self.source = source
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.propagation_depth = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "constraint_id": self.constraint_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "source": self.source,
            "timestamp": self.timestamp,
            "propagation_depth": self.propagation_depth,
        }


class ConstraintPropagator:
    """
    Event-driven constraint propagation engine.

    Usage:
        propagator = ConstraintPropagator()

        # Register a handler
        @propagator.on(CONSTRAINT_CHANGED)
        def handle_change(event):
            print(f"Constraint {event.constraint_id} changed")

        # Fire an event
        propagator.emit(CONSTRAINT_CHANGED, "risk_preference", "low", "medium")
    """

    def __init__(self, max_depth: int = 5):
        self.max_depth = max_depth
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_log: List[Dict] = []
        self._constraint_store: Dict[str, Any] = {}

    def on(self, event_type: str):
        """Decorator to register an event handler."""
        def decorator(func: Callable):
            self._handlers[event_type].append(func)
            return func
        return decorator

    def register(self, event_type: str, handler: Callable):
        """Register an event handler."""
        self._handlers[event_type].append(handler)

    def emit(self, event_type: str, constraint_id: str,
             old_value: Any, new_value: Any, source: str = "system") -> ConstraintEvent:
        """Emit a constraint event and propagate to all handlers."""
        event = ConstraintEvent(event_type, constraint_id, old_value, new_value, source)

        # Store the constraint
        self._constraint_store[constraint_id] = new_value

        # Log the event
        self._event_log.append(event.to_dict())

        # Propagate to handlers
        self._propagate(event)

        return event

    def _propagate(self, event: ConstraintEvent):
        """Propagate event to all registered handlers."""
        handlers = self._handlers.get(event.event_type, [])

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log but don't crash — bounded propagation
                self._event_log.append({
                    "event_id": f"err_{uuid.uuid4().hex[:8]}",
                    "event_type": "handler_error",
                    "error": str(e),
                    "handler": handler.__name__,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

    def set_constraint(self, constraint_id: str, value: Any, source: str = "system"):
        """Set a constraint value, firing change event if it changed."""
        old_value = self._constraint_store.get(constraint_id)

        if old_value == value:
            return None  # No change, no event

        if old_value is None:
            return self.emit(CONSTRAINT_ADDED, constraint_id, None, value, source)
        else:
            return self.emit(CONSTRAINT_CHANGED, constraint_id, old_value, value, source)

    def get_constraint(self, constraint_id: str) -> Optional[Any]:
        """Get current value of a constraint."""
        return self._constraint_store.get(constraint_id)

    def get_all_constraints(self) -> Dict[str, Any]:
        """Get all current constraints."""
        return dict(self._constraint_store)

    def get_event_log(self, limit: int = 50) -> List[Dict]:
        """Get recent events."""
        return self._event_log[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get propagator statistics."""
        return {
            "total_constraints": len(self._constraint_store),
            "total_events": len(self._event_log),
            "handlers_registered": {et: len(h) for et, h in self._handlers.items()},
            "constraints": self._constraint_store,
        }


# Global propagator instance
_global_propagator = ConstraintPropagator()


def get_propagator() -> ConstraintPropagator:
    """Get the global constraint propagator."""
    return _global_propagator


# Convenience decorators using global propagator
def on_constraint_changed(func: Callable):
    """Decorator: register handler for constraint changes."""
    _global_propagator.register(CONSTRAINT_CHANGED, func)
    return func

def on_constraint_added(func: Callable):
    """Decorator: register handler for new constraints."""
    _global_propagator.register(CONSTRAINT_ADDED, func)
    return func


if __name__ == "__main__":
    # Demo: set up some constraints and handlers
    propagator = ConstraintPropagator()

    @propagator.on(CONSTRAINT_CHANGED)
    def log_change(event):
        print(f"  [LOG] {event.constraint_id}: {event.old_value} → {event.new_value}")

    @propagator.on(CONSTRAINT_ADDED)
    def log_new(event):
        print(f"  [NEW] {event.constraint_id} = {event.new_value}")

    # Set initial constraints
    print("Setting initial constraints:")
    propagator.set_constraint("risk_preference", "low")
    propagator.set_constraint("max_drawdown", 0.2)
    propagator.set_constraint("position_size", "micro")

    # Change a constraint
    print("\nChanging risk_preference:")
    propagator.set_constraint("risk_preference", "medium")

    # Stats
    print(f"\nStats: {json.dumps(propagator.get_stats(), indent=2)}")
