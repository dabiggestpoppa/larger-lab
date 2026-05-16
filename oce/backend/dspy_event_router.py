"""
DSPy Event Routing Optimization — OCE Phase 2
===============================================
Learns optimal routing patterns from event flow history.

Uses DSPy to reduce unnecessary event propagation and
optimize subscriber notification patterns.

Falls back to rule-based routing when DSPy is not installed.

Task: OCE-2.25
"""

import logging
from typing import Any, Dict, List, Optional, Set

from srrs_opc import SyncCostOptimizer, CollarTopologyEngine

logger = logging.getLogger("oce.dspy.event_router")

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    dspy = None


# ─── Heuristic Router ─────────────────────────────────────────────────────────

class EventRouterHeuristic:
    """Rule-based event routing optimization (no DSPy required)."""

    def __init__(self):
        self._sync_optimizer = SyncCostOptimizer()
        self._topology_engine = CollarTopologyEngine()
        self._routing_history: List[Dict] = []

    def optimize_routing(
        self,
        event_type: str,
        source: str,
        current_subscribers: List[str],
        event_history: List[Dict],
    ) -> Dict[str, Any]:
        """Determine optimal routing for an event."""
        # Analyze which subscribers actually process events of this type
        useful_subscribers = set()
        for event in event_history[-100:]:
            if event.get("event_type") == event_type:
                processed_by = event.get("processed_by", [])
                useful_subscribers.update(processed_by)

        # Remove subscribers that never process this event type
        if useful_subscribers:
            recommended = [s for s in current_subscribers if s in useful_subscribers]
            removed = [s for s in current_subscribers if s not in useful_subscribers]
        else:
            recommended = current_subscribers
            removed = []

        # Check sync cost
        should_sync = len(current_subscribers) > 0

        return {
            "recommended_subscribers": recommended,
            "removed_subscribers": removed,
            "should_sync": should_sync,
            "estimated_cost_reduction": len(removed) * 0.01,
            "method": "heuristic",
        }

    def record_routing(self, event_type: str, subscriber: str, processed: bool):
        """Record routing outcome for future optimization."""
        self._routing_history.append({
            "event_type": event_type,
            "subscriber": subscriber,
            "processed": processed,
        })


# ─── DSPy Router ──────────────────────────────────────────────────────────────

if DSPY_AVAILABLE:
    class EventRoutingSignature(dspy.Signature):
        """Optimize event routing based on event patterns and subscriber behavior."""
        event_type = dspy.InputField(desc="Event type to route")
        source = dspy.InputField(desc="Event source subsystem")
        current_subscribers = dspy.InputField(desc="Current subscriber list (comma-separated)")
        recent_routing_history = dspy.InputField(desc="Last 50 routing outcomes (JSON)")

        recommended_subscribers = dspy.OutputField(desc="Optimal subscriber list (comma-separated)")
        should_broadcast = dspy.OutputField(desc="true/false — whether to broadcast to all")
        estimated_cost_reduction = dspy.OutputField(desc="Estimated cost reduction (0.0-1.0)")


    class DSPyEventRouter(dspy.Module):
        """DSPy module for event routing optimization."""

        def __init__(self):
            self.optimize = dspy.ChainOfThought(EventRoutingSignature)

        def forward(
            self,
            event_type: str,
            source: str,
            current_subscribers: List[str],
            routing_history: List[Dict],
        ) -> Dict[str, Any]:
            result = self.optimize(
                event_type=event_type,
                source=source,
                current_subscribers=", ".join(current_subscribers),
                recent_routing_history=str(routing_history[-50:]),
            )
            return {
                "recommended_subscribers": [
                    s.strip() for s in result.recommended_subscribers.split(",") if s.strip()
                ],
                "should_broadcast": result.should_broadcast.lower() == "true",
                "estimated_cost_reduction": float(result.estimated_cost_reduction),
                "method": "dspy",
            }


# ─── Pipeline ─────────────────────────────────────────────────────────────────

class EventRoutingPipeline:
    """
    Event routing optimization pipeline.
    Uses DSPy when available, falls back to heuristics.
    """

    def __init__(self, lm: Optional[Any] = None):
        self._dspy_available = DSPY_AVAILABLE
        self._heuristic = EventRouterHeuristic()
        self._router = None
        if self._dspy_available:
            try:
                self._router = DSPyEventRouter()
                if lm:
                    dspy.configure(lm=lm)
            except Exception as e:
                logger.warning(f"DSPy router init failed: {e}")
                self._dspy_available = False

    def optimize(
        self,
        event_type: str,
        source: str,
        current_subscribers: List[str],
        event_history: List[Dict],
    ) -> Dict[str, Any]:
        """Optimize event routing."""
        if self._dspy_available and self._router:
            try:
                return self._router(event_type, source, current_subscribers, self._heuristic._routing_history)
            except Exception as e:
                logger.warning(f"DSPy routing failed: {e}")
        return self._heuristic.optimize_routing(event_type, source, current_subscribers, event_history)

    def record_routing(self, event_type: str, subscriber: str, processed: bool):
        """Record routing outcome."""
        self._heuristic.record_routing(event_type, subscriber, processed)

    def get_status(self) -> Dict[str, Any]:
        return {
            "dspy_available": self._dspy_available,
            "method": "dspy" if self._dspy_available else "heuristic",
            "routing_history_size": len(self._heuristic._routing_history),
        }
