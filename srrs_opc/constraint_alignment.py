"""
Constraint Alignment Adaptation
================================
Phase 8: Align SRRA-OPH constraints with operator's evolving goals.

Constraints adapt when operator changes strategy — not hardcoded.
Bidirectional: system suggests constraint adjustments, operator confirms/rejects.

No global state — self-stabilizing constraint adapter.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class Constraint:
    """A single SRRA-OPH constraint with adaptive weight."""

    def __init__(self, name: str, description: str, weight: float = 0.5,
                 category: str = "general"):
        self.name = name
        self.description = description
        self.weight = max(0.0, min(1.0, weight))
        self.category = category
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_adjusted = self.created_at
        self._adjustment_count = 0

    def adjust(self, delta: float):
        """Adjust constraint weight by delta (clamped to [0, 1])."""
        old_weight = self.weight
        self.weight = max(0.0, min(1.0, self.weight + delta))
        self._adjustment_count += 1
        self.last_adjusted = datetime.now(timezone.utc).isoformat()
        return self.weight - old_weight

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "weight": round(self.weight, 3),
            "category": self.category,
            "adjustment_count": self._adjustment_count,
            "last_adjusted": self.last_adjusted,
        }


class AlignmentSuggestion:
    """A system-generated suggestion for constraint adjustment."""

    def __init__(self, constraint_name: str, current_weight: float,
                     suggested_weight: float, reason: str):
        self.constraint_name = constraint_name
        self.current_weight = current_weight
        self.suggested_weight = suggested_weight
        self.reason = reason
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.status = "pending"  # pending, confirmed, rejected

    def confirm(self):
        self.status = "confirmed"

    def reject(self):
        self.status = "rejected"

    def to_dict(self) -> dict:
        return {
            "constraint_name": self.constraint_name,
            "current_weight": round(self.current_weight, 3),
            "suggested_weight": round(self.suggested_weight, 3),
            "reason": self.reason,
            "status": self.status,
            "created_at": self.created_at,
        }


class ConstraintAlignmentAdapter:
    """
    Adapts SRRA-OPH constraints to operator's evolving goals.

    Bidirectional alignment:
    - System observes operator behavior → suggests constraint adjustments
    - Operator confirms or rejects suggestions
    - Confirmed adjustments are applied; rejected ones are logged

    Self-stabilizing: constraints don't oscillate — adjustments require
    sustained evidence across multiple observations.
    """

    # How many consistent observations before suggesting adjustment
    EVIDENCE_THRESHOLD = 3
    # Max adjustment per step to prevent oscillation
    MAX_ADJUSTMENT = 0.15

    def __init__(self, operator_id: str):
        self.operator_id = operator_id
        self._constraints: Dict[str, Constraint] = {}
        self._suggestions: List[AlignmentSuggestion] = []
        self._evidence: Dict[str, List[float]] = defaultdict(list)
        self._alignment_score: float = 0.5  # 0 = misaligned, 1 = fully aligned

    def register_constraint(self, name: str, description: str,
                            weight: float = 0.5, category: str = "general"):
        """Register a constraint for alignment tracking."""
        self._constraints[name] = Constraint(
            name=name, description=description,
            weight=weight, category=category
        )

    def record_operator_action(self, constraint_name: str, alignment_delta: float):
        """
        Record whether an operator action aligns with or contradicts a constraint.

        alignment_delta: positive = aligned, negative = contradicted
        """
        if constraint_name not in self._constraints:
            return

        self._evidence[constraint_name].append(alignment_delta)

        # Check if we have enough evidence to suggest adjustment
        if len(self._evidence[constraint_name]) >= self.EVIDENCE_THRESHOLD:
            self._evaluate_constraint(constraint_name)

    def _evaluate_constraint(self, constraint_name: str):
        """Evaluate evidence and generate adjustment suggestion if warranted."""
        evidence = self._evidence[constraint_name][-self.EVIDENCE_THRESHOLD:]
        avg_alignment = sum(evidence) / len(evidence)

        constraint = self._constraints[constraint_name]

        # If consistently contradicted, suggest weakening
        if avg_alignment < -0.2:
            suggested = max(0.0, constraint.weight - self.MAX_ADJUSTMENT)
            suggestion = AlignmentSuggestion(
                constraint_name=constraint_name,
                current_weight=constraint.weight,
                suggested_weight=suggested,
                reason=f"Operator consistently contradicts this constraint "
                       f"(avg alignment: {avg_alignment:.2f} over {len(evidence)} observations)",
            )
            self._suggestions.append(suggestion)

        # If consistently aligned, suggest strengthening
        elif avg_alignment > 0.3:
            suggested = min(1.0, constraint.weight + self.MAX_ADJUSTMENT)
            if abs(suggested - constraint.weight) > 0.01:
                suggestion = AlignmentSuggestion(
                    constraint_name=constraint_name,
                    current_weight=constraint.weight,
                    suggested_weight=suggested,
                    reason=f"Operator consistently aligns with this constraint "
                           f"(avg alignment: {avg_alignment:.2f} over {len(evidence)} observations)",
                )
                self._suggestions.append(suggestion)

    def get_pending_suggestions(self) -> List[AlignmentSuggestion]:
        """Get all pending alignment suggestions."""
        return [s for s in self._suggestions if s.status == "pending"]

    def confirm_suggestion(self, constraint_name: str) -> bool:
        """Operator confirms a suggestion — apply the adjustment."""
        for s in self._suggestions:
            if s.constraint_name == constraint_name and s.status == "pending":
                s.confirm()
                delta = s.suggested_weight - s.current_weight
                actual_delta = self._constraints[constraint_name].adjust(delta)
                self._update_alignment_score()
                return True
        return False

    def reject_suggestion(self, constraint_name: str) -> bool:
        """Operator rejects a suggestion — log and clear evidence."""
        for s in self._suggestions:
            if s.constraint_name == constraint_name and s.status == "pending":
                s.reject()
                # Clear evidence so we don't immediately re-suggest
                self._evidence[constraint_name] = []
                return True
        return False

    def _update_alignment_score(self):
        """Recalculate overall alignment score."""
        if not self._constraints:
            self._alignment_score = 0.5
            return
        total_weight = sum(c.weight for c in self._constraints.values())
        self._alignment_score = total_weight / len(self._constraints)

    def get_alignment_report(self) -> Dict[str, Any]:
        """Get full alignment report."""
        self._update_alignment_score()
        return {
            "operator_id": self.operator_id,
            "alignment_score": round(self._alignment_score, 3),
            "constraints": {name: c.to_dict() for name, c in self._constraints.items()},
            "pending_suggestions": [s.to_dict() for s in self.get_pending_suggestions()],
            "total_suggestions": len(self._suggestions),
            "confirmed": len([s for s in self._suggestions if s.status == "confirmed"]),
            "rejected": len([s for s in self._suggestions if s.status == "rejected"]),
        }

    def to_dict(self) -> dict:
        return self.get_alignment_report()
