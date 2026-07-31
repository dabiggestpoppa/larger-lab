"""
Resource-Constrained Cognition
================================
Phase 9 Component 6: Maintain coherent operation under severe resource constraints.

Under resource pressure, prioritizes:
1. Continuity (always preserve)
2. Repair (local repair first)
3. Sync integrity (minimal sync to maintain coherence)
4. Strategic coherence (last priority)

Deprioritizes:
- Low-value operations
- Redundant cognition

Integration: BasePatch, RepairPatch, RecoveryAnchors
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class OperationPriority:
    """Priority classification for operations."""

    CRITICAL = 1    # Continuity — always preserve
    HIGH = 2        # Repair — local repair first
    MEDIUM = 3      # Sync integrity — minimal sync
    LOW = 4         # Strategic coherence
    DEFER = 5       # Low-value / redundant — first to cut

    NAMES = {
        1: "critical",
        2: "high",
        3: "medium",
        4: "low",
        5: "defer",
    }


class PrioritizedOperation:
    """An operation with priority and resource requirements."""

    def __init__(self, operation_id: str, priority: int,
                 resource_cost: float, coherence_value: float,
                 is_redundant: bool = False):
        self.operation_id = operation_id
        self.priority = priority
        self.resource_cost = max(0.0, resource_cost)
        self.coherence_value = max(0.0, coherence_value)
        self.is_redundant = is_redundant
        self.efficiency = coherence_value / max(resource_cost, 1e-10)

    def to_dict(self) -> dict:
        return {
            "operation_id": self.operation_id,
            "priority": self.priority,
            "priority_name": OperationPriority.NAMES.get(self.priority, "unknown"),
            "resource_cost": round(self.resource_cost, 3),
            "coherence_value": round(self.coherence_value, 3),
            "efficiency": round(self.efficiency, 3),
            "is_redundant": self.is_redundant,
        }


class ResourceConstrainedCognition:
    """
    Maintains coherent operation under resource constraints.

    When resources are limited, operations are prioritized and
    low-value operations are deferred or dropped.
    """

    DEFAULT_PRIORITY_MAP = {
        "continuity": OperationPriority.CRITICAL,
        "repair": OperationPriority.HIGH,
        "sync": OperationPriority.MEDIUM,
        "strategic": OperationPriority.LOW,
        "redundant": OperationPriority.DEFER,
    }

    def __init__(self, total_resources: float = 100.0):
        self.total_resources = total_resources
        self._operations: List[PrioritizedOperation] = []
        self._constraint_history: List[dict] = []

    def register_operation(self, operation_id: str, operation_type: str,
                           resource_cost: float, coherence_value: float,
                           is_redundant: bool = False) -> PrioritizedOperation:
        """Register an operation for prioritization."""
        priority = self.DEFAULT_PRIORITY_MAP.get(operation_type, OperationPriority.LOW)
        if is_redundant:
            priority = OperationPriority.DEFER
        op = PrioritizedOperation(operation_id, priority, resource_cost,
                                  coherence_value, is_redundant)
        self._operations.append(op)
        return op

    def prioritize(self, available_resources: float,
                   operations: Optional[List[PrioritizedOperation]] = None
                   ) -> List[PrioritizedOperation]:
        """
        Return operations that fit within resource budget, prioritized.
        Critical operations are always included.
        """
        ops = operations or self._operations
        # Sort by priority (lower number = higher priority), then by efficiency
        sorted_ops = sorted(ops, key=lambda o: (o.priority, -o.efficiency))

        selected = []
        remaining = available_resources

        for op in sorted_ops:
            if op.resource_cost <= remaining:
                selected.append(op)
                remaining -= op.resource_cost
            elif op.priority == OperationPriority.CRITICAL:
                # Critical operations always get resources
                selected.append(op)
                remaining = 0

        self._constraint_history.append({
            "available_resources": available_resources,
            "selected_count": len(selected),
            "total_candidates": len(ops),
            "remaining_resources": round(remaining, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return selected

    def minimal_coherent_operation(self) -> List[dict]:
        """
        Return the minimal set of operations needed for coherent operation.
        Only CRITICAL and HIGH priority operations.
        """
        minimal = [
            op for op in self._operations
            if op.priority <= OperationPriority.HIGH
        ]
        return [op.to_dict() for op in sorted(minimal, key=lambda o: o.priority)]

    def resource_utilization(self) -> float:
        """Current resource utilization."""
        if not self._operations:
            return 0.0
        total_cost = sum(op.resource_cost for op in self._operations)
        if self.total_resources <= 0:
            return 1.0
        return min(1.0, total_cost / self.total_resources)

    def is_overloaded(self) -> bool:
        """Check if system is resource-overloaded."""
        return self.resource_utilization() > 0.9

    def get_stats(self) -> dict:
        priority_counts = defaultdict(int)
        for op in self._operations:
            priority_counts[OperationPriority.NAMES.get(op.priority, "unknown")] += 1

        return {
            "total_operations": len(self._operations),
            "total_resources": self.total_resources,
            "resource_utilization": round(self.resource_utilization(), 3),
            "is_overloaded": self.is_overloaded(),
            "priority_distribution": dict(priority_counts),
            "minimal_set_size": len(self.minimal_coherent_operation()),
        }
