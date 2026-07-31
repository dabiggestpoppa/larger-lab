"""
9_emergence.priority_arbiter
============================
Priority arbitration engine for the field.

Manages competing priorities from different field modules and operators,
resolving conflicts through a multi-strategy arbitration system.

Arbitration strategies:
- urgency: highest urgency wins
- impact: highest potential impact wins
- fairness: round-robin to prevent starvation
- weighted: combined score from urgency, impact, and waiting time

Maintains a priority queue with starvation prevention, ensuring that
low-priority but important tasks eventually get processed.
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.emergence.priority_arbiter")


class PriorityItem(BaseModel):
    """An item in the priority queue."""
    item_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: str  # module or operator that submitted
    description: str
    urgency: float = 0.5      # 0-1, time-sensitivity
    impact: float = 0.5        # 0-1, potential effect
    weight: float = 1.0        # base importance multiplier
    strategy: str = "weighted" # urgency, impact, fairness, weighted
    submitted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved: bool = False
    resolved_at: Optional[str] = None
    resolution: Optional[str] = None
    wait_rounds: int = 0      # how many arbitration rounds this item has waited


class ArbitrationResult(BaseModel):
    """Result of an arbitration round."""
    round_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    winner_id: str
    winner_source: str
    winner_score: float
    strategy_used: str
    queue_size: int
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PriorityArbiterConfig(BaseModel):
    """Configuration for priority_arbiter."""
    enabled: bool = True
    max_queue_size: int = 500
    starvation_threshold: int = 10  # rounds before boosting
    starvation_boost: float = 0.2   # urgency boost per starvation round
    default_strategy: str = "weighted"
    urgency_weight: float = 0.4     # weight for urgency in weighted strategy
    impact_weight: float = 0.4      # weight for impact in weighted strategy
    wait_weight: float = 0.2        # weight for waiting time in weighted strategy
    history_limit: int = 1000


class PriorityArbiterModule:
    """Priority arbitration engine for the field."""

    def __init__(self):
        self.config = PriorityArbiterConfig()
        self.running = False
        self._lock = Lock()
        self._queue: Dict[str, PriorityItem] = {}
        self._history: List[ArbitrationResult] = []
        self._source_counts: Dict[str, int] = defaultdict(int)  # source -> items resolved
        self._round_count: int = 0
        self._total_resolved: int = 0

    def start(self) -> None:
        """Start the priority arbiter."""
        self.running = True
        logger.info("PriorityArbiter started (strategy=%s)", self.config.default_strategy)

    def stop(self) -> None:
        """Stop the priority arbiter."""
        self.running = False
        logger.info("PriorityArbiter stopped — %d items resolved in %d rounds",
                     self._total_resolved, self._round_count)

    def submit(self, source: str, description: str,
               urgency: float = 0.5, impact: float = 0.5,
               weight: float = 1.0, strategy: Optional[str] = None) -> str:
        """
        Submit a priority item for arbitration.

        Args:
            source: Module or operator submitting the item.
            description: What needs to be prioritized.
            urgency: Time-sensitivity 0-1.
            impact: Potential effect 0-1.
            weight: Base importance multiplier.
            strategy: Override arbitration strategy for this item.

        Returns:
            The item_id.
        """
        item = PriorityItem(
            source=source,
            description=description,
            urgency=max(0.0, min(1.0, urgency)),
            impact=max(0.0, min(1.0, impact)),
            weight=max(0.1, weight),
            strategy=strategy or self.config.default_strategy,
        )

        with self._lock:
            if len(self._queue) >= self.config.max_queue_size:
                # Remove oldest resolved item, or oldest pending
                resolved_items = [k for k, v in self._queue.items() if v.resolved]
                if resolved_items:
                    oldest = resolved_items[0]
                    del self._queue[oldest]
                else:
                    # Remove lowest scoring item
                    lowest = min(self._queue, key=lambda k: self._queue[k].urgency + self._queue[k].impact)
                    del self._queue[lowest]
                    logger.debug("Evicted lowest priority item: %s", lowest)

            self._queue[item.item_id] = item

        logger.debug("Priority item submitted by %s: %s (urgency=%.2f, impact=%.2f)",
                      source, item.item_id, item.urgency, item.impact)
        return item.item_id

    def arbitrate(self) -> Optional[ArbitrationResult]:
        """
        Run an arbitration round to select the highest-priority item.

        Applies starvation prevention by boosting urgency of items
        that have waited too long. Uses the configured strategy to
        compute scores and select the winner.

        Returns:
            ArbitrationResult with the winner, or None if queue is empty.
        """
        with self._lock:
            pending = {k: v for k, v in self._queue.items() if not v.resolved}
            if not pending:
                return None

            self._round_count += 1

            # Apply starvation boost
            for item_id, item in pending.items():
                item.wait_rounds += 1
                if item.wait_rounds >= self.config.starvation_threshold:
                    boost = (item.wait_rounds - self.config.starvation_threshold + 1) * self.config.starvation_boost
                    item.urgency = min(1.0, item.urgency + boost)

            # Score each item
            scored = []
            for item_id, item in pending.items():
                score = self._compute_score(item)
                scored.append((item_id, score))

            # Select winner
            winner_id, winner_score = max(scored, key=lambda x: x[1])
            winner = pending[winner_id]

            # Mark as resolved
            winner.resolved = True
            winner.resolved_at = datetime.now(timezone.utc).isoformat()
            winner.resolution = f"Selected via {winner.strategy} strategy (score={winner_score:.4f})"

            self._source_counts[winner.source] += 1
            self._total_resolved += 1

            result = ArbitrationResult(
                winner_id=winner_id,
                winner_source=winner.source,
                winner_score=round(winner_score, 4),
                strategy_used=winner.strategy,
                queue_size=len(pending),
            )

            self._history.append(result)
            if len(self._history) > self.config.history_limit:
                self._history = self._history[-self.config.history_limit:]

        logger.info("Arbitration round %d: winner=%s from %s (score=%.3f, strategy=%s)",
                     self._round_count, winner_id, winner.source, winner_score, winner.strategy)
        return result

    def _compute_score(self, item: PriorityItem) -> float:
        """Compute priority score based on item's strategy."""
        cfg = self.config
        if item.strategy == "urgency":
            return item.urgency * item.weight
        elif item.strategy == "impact":
            return item.impact * item.weight
        elif item.strategy == "fairness":
            # Inverse of how many times this source has won
            source_wins = self._source_counts.get(item.source, 0)
            fairness_bonus = 1.0 / (1.0 + source_wins * 0.1)
            return fairness_bonus * item.weight
        else:  # weighted
            wait_score = min(1.0, item.wait_rounds / max(1, cfg.starvation_threshold))
            return item.weight * (
                cfg.urgency_weight * item.urgency
                + cfg.impact_weight * item.impact
                + cfg.wait_weight * wait_score
            )

    def get_queue(self, include_resolved: bool = False, limit: int = 50) -> List[Dict]:
        """
        Get current priority queue items.

        Args:
            include_resolved: Include already-resolved items.
            limit: Max items to return.

        Returns:
            List of priority item dicts, highest score first.
        """
        with self._lock:
            items = list(self._queue.values())
            if not include_resolved:
                items = [i for i in items if not i.resolved]
            # Sort by computed score descending
            items.sort(key=lambda i: self._compute_score(i), reverse=True)
            return [i.model_dump() for i in items[:limit]]

    def get_history(self, limit: int = 100) -> List[Dict]:
        """Get arbitration history, most recent first."""
        with self._lock:
            return [h.model_dump() for h in reversed(self._history[-limit:])]

    def get_stats(self) -> Dict[str, Any]:
        """Get arbiter statistics."""
        with self._lock:
            pending = sum(1 for i in self._queue.values() if not i.resolved)
            return {
                "total_submitted": len(self._queue),
                "total_resolved": self._total_resolved,
                "pending": pending,
                "rounds": self._round_count,
                "source_distribution": dict(self._source_counts),
                "avg_wait_rounds": (
                    sum(i.wait_rounds for i in self._queue.values() if not i.resolved) / max(1, pending)
                ),
            }

    def cancel(self, item_id: str) -> bool:
        """Cancel a pending priority item."""
        with self._lock:
            if item_id in self._queue and not self._queue[item_id].resolved:
                del self._queue[item_id]
                logger.debug("Cancelled priority item: %s", item_id)
                return True
        return False
