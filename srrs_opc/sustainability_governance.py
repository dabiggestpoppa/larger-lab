"""
Sustainability Governance
===========================
Phase 9 Component 7: Ensure all optimization remains constrained by sustainability.

Validates all optimizations against:
1. Continuity integrity
2. Recoverability preservation
3. Entropy sustainability
4. Operator alignment

Blocks optimizations that violate constraints. Provides rollback capability.

Integration: AntiManipulationSafeguards, BidirectionalCoherenceEngine,
             PredictionContracts
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class OptimizationCandidate:
    """A proposed optimization to be validated."""

    def __init__(self, optimization_id: str, target: str,
                 expected_coherence_gain: float,
                 expected_entropy_reduction: float,
                 expected_recovery_cost: float,
                 rollback_feasibility: float,
                 description: str = ""):
        self.optimization_id = optimization_id
        self.target = target
        self.expected_coherence_gain = expected_coherence_gain
        self.expected_entropy_reduction = expected_entropy_reduction
        self.expected_recovery_cost = max(0.0, min(1.0, expected_recovery_cost))
        self.rollback_feasibility = max(0.0, min(1.0, rollback_feasibility))
        self.description = description
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "optimization_id": self.optimization_id,
            "target": self.target,
            "expected_coherence_gain": round(self.expected_coherence_gain, 4),
            "expected_entropy_reduction": round(self.expected_entropy_reduction, 4),
            "expected_recovery_cost": round(self.expected_recovery_cost, 4),
            "rollback_feasibility": round(self.rollback_feasibility, 4),
            "description": self.description,
            "timestamp": self.timestamp,
        }


class GovernanceDecision:
    """Result of a governance validation."""

    def __init__(self, candidate: OptimizationCandidate,
                 approved: bool, checks: Dict[str, bool],
                 reason: str):
        self.candidate = candidate
        self.approved = approved
        self.checks = checks
        self.reason = reason
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "optimization_id": self.candidate.optimization_id,
            "approved": self.approved,
            "checks": self.checks,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


class SustainabilityGovernance:
    """
    Governance layer that validates all optimizations.

    Hard constraints:
    - Continuity integrity must be preserved
    - Recoverability must not drop below threshold
    - Entropy must remain sustainable
    - Operator alignment must be maintained

    Block if reconstruction_viability < 0.5.
    Log overrides to PredictionContracts.
    """

    # Thresholds
    MIN_RECONSTRUCTION_VIABILITY = 0.5
    MIN_ROLLBACK_FEASIBILITY = 0.3
    MAX_RECOVERY_COST = 0.8

    def __init__(self):
        self._decisions: List[GovernanceDecision] = []
        self._applied_optimizations: Dict[str, OptimizationCandidate] = {}
        self._rollback_log: List[dict] = []

    def validate_optimization(self, candidate: OptimizationCandidate,
                              current_viability: float = 1.0,
                              operator_aligned: bool = True) -> GovernanceDecision:
        """
        Validate an optimization candidate against all sustainability constraints.

        Returns a GovernanceDecision with approval status.
        """
        checks = {
            "continuity_integrity": self._check_continuity_integrity(candidate),
            "recoverability": self._check_recoverability(candidate, current_viability),
            "entropy_sustainability": self._check_entropy_sustainability(candidate),
            "operator_alignment": operator_aligned,
            "rollback_feasible": candidate.rollback_feasibility >= self.MIN_ROLLBACK_FEASIBILITY,
        }

        failed = [k for k, v in checks.items() if not v]
        approved = len(failed) == 0

        if approved:
            reason = "All sustainability checks passed"
            self._applied_optimizations[candidate.optimization_id] = candidate
        else:
            reason = f"Failed checks: {', '.join(failed)}"

        decision = GovernanceDecision(candidate, approved, checks, reason)
        self._decisions.append(decision)
        return decision

    def _check_continuity_integrity(self, candidate: OptimizationCandidate) -> bool:
        """Check that optimization doesn't break continuity."""
        # Optimization must have positive or neutral coherence gain
        return candidate.expected_coherence_gain >= 0

    def _check_recoverability(self, candidate: OptimizationCandidate,
                              current_viability: float) -> bool:
        """Check that recoverability is preserved."""
        # Recovery cost must not exceed max
        if candidate.expected_recovery_cost > self.MAX_RECOVERY_COST:
            return False
        # Current viability must not drop below minimum
        if current_viability < self.MIN_RECONSTRUCTION_VIABILITY:
            return False
        return True

    def _check_entropy_sustainability(self, candidate: OptimizationCandidate) -> bool:
        """Check that entropy remains sustainable."""
        # Optimization should reduce or maintain entropy
        return candidate.expected_entropy_reduction >= 0

    def rollback(self, optimization_id: str) -> dict:
        """Roll back a destabilizing optimization."""
        candidate = self._applied_optimizations.pop(optimization_id, None)
        rollback_record = {
            "optimization_id": optimization_id,
            "rolled_back_at": datetime.now(timezone.utc).isoformat(),
            "candidate": candidate.to_dict() if candidate else None,
            "reason": "destabilizing",
        }
        self._rollback_log.append(rollback_record)
        return rollback_record

    def get_applied_optimizations(self) -> List[dict]:
        """Get all currently applied optimizations."""
        return [c.to_dict() for c in self._applied_optimizations.values()]

    def get_rejected_optimizations(self) -> List[dict]:
        """Get all rejected optimizations."""
        return [
            d.to_dict() for d in self._decisions
            if not d.approved
        ]

    def approval_rate(self) -> float:
        """Rate of approved optimizations."""
        if not self._decisions:
            return 1.0
        approved = sum(1 for d in self._decisions if d.approved)
        return round(approved / len(self._decisions), 3)

    def get_stats(self) -> dict:
        return {
            "total_validations": len(self._decisions),
            "approved": sum(1 for d in self._decisions if d.approved),
            "rejected": sum(1 for d in self._decisions if not d.approved),
            "approval_rate": self.approval_rate(),
            "applied_optimizations": len(self._applied_optimizations),
            "rollbacks": len(self._rollback_log),
        }
