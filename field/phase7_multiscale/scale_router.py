"""
7.4 Scale Router — Multi-Scale Intelligence
=============================================
Routes signals and decisions across time scales.

Each signal is tagged with a natural time scale (tick, bar, daily, weekly).
The router dispatches to the appropriate engine and handles
cross-scale signal amplification or dampening.

Routing rules:
  - Signals below noise floor → dropped
  - Cross-scale consensus → amplified
  - Cross-scale conflict → flagged for arbitration
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.multiscale.router")


class TimeScale(str, Enum):
    TICK = "tick"
    BAR = "bar"
    DAILY = "daily"
    WEEKLY = "weekly"


class Signal(BaseModel):
    signal_id: str = ""
    source: str
    scale: TimeScale
    direction: str  # bullish, bearish, neutral
    strength: float = 0.5  # 0.0 to 1.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RoutingResult(BaseModel):
    signal_id: str
    routed_to: str
    action: str  # dispatch, amplify, dampen, drop, flag_conflict
    reason: str


class ScaleRouterConfig(BaseModel):
    """Configuration for scale_router."""
    enabled: bool = True
    noise_floor: float = 0.15
    consensus_threshold: float = 0.7
    conflict_threshold: float = 0.5
    max_signals: int = 50000


class ScaleRouterModule:
    """Routes signals across multi-scale time frames."""

    def __init__(self):
        self.config = ScaleRouterConfig()
        self.running = False
        self._lock = Lock()
        self._signals: List[Signal] = []
        self._routing_log: List[RoutingResult] = []
        self._scale_counts: Dict[str, int] = defaultdict(int)
        self._engine_registry: Dict[TimeScale, str] = {
            TimeScale.TICK: "tick_engine",
            TimeScale.BAR: "bar_engine",
            TimeScale.DAILY: "daily_engine",
            TimeScale.WEEKLY: "weekly_engine",
        }

    def start(self) -> None:
        """Start the router."""
        self.running = True
        logger.info("ScaleRouter started")

    def stop(self) -> None:
        """Stop the router."""
        self.running = False
        logger.info("ScaleRouter stopped")

    def register_engine(self, scale: TimeScale, engine_name: str) -> None:
        """Register an engine name for a time scale."""
        with self._lock:
            self._engine_registry[scale] = engine_name
            logger.info("Registered engine '%s' for scale '%s'", engine_name, scale)

    def route_signal(self, signal: Signal) -> RoutingResult:
        """Route a signal to the appropriate engine.

        Applies noise filtering, cross-scale consensus/amplification,
        and conflict detection.
        """
        import uuid
        if not signal.signal_id:
            signal.signal_id = str(uuid.uuid4())[:8]

        with self._lock:
            # Noise filter
            if signal.strength < self.config.noise_floor:
                result = RoutingResult(
                    signal_id=signal.signal_id,
                    routed_to="none",
                    action="drop",
                    reason=f"Below noise floor ({signal.strength:.3f} < {self.config.noise_floor})",
                )
                self._routing_log.append(result)
                return result

            # Check cross-scale consensus/conflict
            action, reason = self._check_cross_scale(signal)

            engine = self._engine_registry.get(signal.scale, "unknown")
            self._signals.append(signal)
            self._scale_counts[signal.scale.value] += 1

            # Evict old signals
            if len(self._signals) > self.config.max_signals:
                self._signals = self._signals[-self.config.max_signals // 2:]

            result = RoutingResult(
                signal_id=signal.signal_id,
                routed_to=engine,
                action=action,
                reason=reason,
            )
            self._routing_log.append(result)
            logger.debug("Signal %s routed to %s: %s", signal.signal_id, engine, action)
            return result

    def _check_cross_scale(self, signal: Signal) -> tuple:
        """Check for cross-scale consensus or conflict.

        Returns (action, reason) tuple.
        """
        # Look at recent signals in other scales for same source
        recent = self._signals[-100:]
        same_source = [s for s in recent if s.source == signal.source and s.scale != signal.scale]

        if not same_source:
            return "dispatch", "No cross-scale signals — standard dispatch"

        # Check consensus
        agreeing = [s for s in same_source if s.direction == signal.direction]
        agreement_ratio = len(agreeing) / len(same_source)

        if agreement_ratio >= self.config.consensus_threshold:
            return "amplify", f"Cross-scale consensus ({agreement_ratio:.0%} agreement)"
        elif agreement_ratio <= (1 - self.config.conflict_threshold):
            return "flag_conflict", f"Cross-scale conflict ({agreement_ratio:.0%} agreement)"
        else:
            return "dispatch", f"Mixed cross-scale signals ({agreement_ratio:.0%} agreement)"

    def get_signals_by_scale(self, scale: TimeScale, limit: int = 100) -> List[Dict]:
        """Get recent signals for a specific time scale."""
        with self._lock:
            filtered = [s for s in self._signals if s.scale == scale]
            return [s.model_dump() for s in filtered[-limit:]]

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        with self._lock:
            actions = defaultdict(int)
            for r in self._routing_log:
                actions[r.action] += 1
            return {
                "total_signals": len(self._signals),
                "total_routes": len(self._routing_log),
                "signals_by_scale": dict(self._scale_counts),
                "actions": dict(actions),
                "engine_registry": {k.value: v for k, v in self._engine_registry.items()},
            }
