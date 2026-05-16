"""
Prediction Contracts
======================
Phase 6 Refinement: Falsifiable evolution contracts.

Every topology mutation MUST generate a prediction contract:
- Expected coherence gain
- Expected entropy cost
- Expected repair burden
- Expected reconstruction viability
- Rollback feasibility

Without this, self-evolution becomes incoherent mutation.
"""

import json
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum
from collections import defaultdict


class ContractStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    VIOLATED = "violated"
    EXPIRED = "expired"
    ROLLED_BACK = "rolled_back"


class PredictionContract:
    """A falsifiable contract for a topology mutation."""

    def __init__(self, mutation_type: str, target: str,
                 expected_coherence_gain: float,
                 expected_entropy_cost: float,
                 expected_repair_burden: float,
                 expected_reconstruction_viability: float,
                 rollback_feasibility: float,
                 ttl_seconds: int = 3600):
        self.contract_id = f"pc_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(self) % 10000}"
        self.mutation_type = mutation_type
        self.target = target
        self.expected_coherence_gain = expected_coherence_gain
        self.expected_entropy_cost = expected_entropy_cost
        self.expected_repair_burden = expected_repair_burden
        self.expected_reconstruction_viability = expected_reconstruction_viability
        self.rollback_feasibility = max(0.0, min(1.0, rollback_feasibility))
        self.status = ContractStatus.PENDING
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.ttl_seconds = ttl_seconds
        self.validated_at = None
        self.actual_coherence_gain = None
        self.actual_entropy_cost = None

    def validate(self, actual_coherence_gain: float, actual_entropy_cost: float):
        """Validate the contract against actual outcomes."""
        self.actual_coherence_gain = actual_coherence_gain
        self.actual_entropy_cost = actual_entropy_cost

        # Check if predictions were within tolerance
        coherence_ok = abs(actual_coherence_gain - self.expected_coherence_gain) < 0.2
        entropy_ok = actual_entropy_cost <= self.expected_entropy_cost * 1.5

        if coherence_ok and entropy_ok:
            self.status = ContractStatus.VALIDATED
        else:
            self.status = ContractStatus.VIOLATED

        self.validated_at = datetime.now(timezone.utc).isoformat()
        return self.status == ContractStatus.VALIDATED

    def should_rollback(self) -> bool:
        """Check if the mutation should be rolled back."""
        if self.status == ContractStatus.VIOLATED:
            return self.rollback_feasibility > 0.5
        return False

    def to_dict(self) -> dict:
        return {
            "contract_id": self.contract_id,
            "mutation_type": self.mutation_type,
            "target": self.target,
            "expected_coherence_gain": self.expected_coherence_gain,
            "expected_entropy_cost": self.expected_entropy_cost,
            "expected_repair_burden": self.expected_repair_burden,
            "expected_reconstruction_viability": self.expected_reconstruction_viability,
            "rollback_feasibility": self.rollback_feasibility,
            "status": self.status.value,
            "created_at": self.created_at,
            "validated_at": self.validated_at,
            "actual_coherence_gain": self.actual_coherence_gain,
            "actual_entropy_cost": self.actual_entropy_cost,
        }


class PredictionContractManager:
    """Manages prediction contracts for topology mutations."""

    def __init__(self):
        self._contracts: Dict[str, PredictionContract] = {}
        self._mutation_history: List[dict] = []

    def create_contract(self, mutation_type: str, target: str,
                        expected_coherence_gain: float = 0.1,
                        expected_entropy_cost: float = 0.05,
                        expected_repair_burden: float = 0.1,
                        expected_reconstruction_viability: float = 0.8,
                        rollback_feasibility: float = 0.7) -> PredictionContract:
        """Create a prediction contract for a topology mutation."""
        contract = PredictionContract(
            mutation_type=mutation_type,
            target=target,
            expected_coherence_gain=expected_coherence_gain,
            expected_entropy_cost=expected_entropy_cost,
            expected_repair_burden=expected_repair_burden,
            expected_reconstruction_viability=expected_reconstruction_viability,
            rollback_feasibility=rollback_feasibility,
        )
        self._contracts[contract.contract_id] = contract
        self._mutation_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mutation_type": mutation_type,
            "target": target,
            "contract_id": contract.contract_id,
        })
        return contract

    def validate_contract(self, contract_id: str,
                          actual_coherence_gain: float,
                          actual_entropy_cost: float) -> bool:
        """Validate a contract against actual outcomes."""
        contract = self._contracts.get(contract_id)
        if not contract:
            return False
        return contract.validate(actual_coherence_gain, actual_entropy_cost)

    def get_rollbacks_needed(self) -> List[dict]:
        """Get contracts that need rollback."""
        return [c.to_dict() for c in self._contracts.values()
                if c.should_rollback()]

    def get_stats(self) -> dict:
        if not self._contracts:
            return {"status": "no_contracts"}

        statuses = defaultdict(int)
        for c in self._contracts.values():
            statuses[c.status.value] += 1

        return {
            "total_contracts": len(self._contracts),
            "statuses": dict(statuses),
            "total_mutations": len(self._mutation_history),
            "rollbacks_needed": len(self.get_rollbacks_needed()),
        }


if __name__ == "__main__":
    manager = PredictionContractManager()

    # Simulate topology mutations with contracts
    c1 = manager.create_contract("weaken_edge", "memory-repair",
                                  expected_coherence_gain=0.05,
                                  expected_entropy_cost=0.02,
                                  rollback_feasibility=0.9)
    print(f"Created contract: {c1.contract_id}")

    c2 = manager.create_contract("strengthen_edge", "planner-execution",
                                  expected_coherence_gain=0.15,
                                  expected_entropy_cost=0.1,
                                  rollback_feasibility=0.6)
    print(f"Created contract: {c2.contract_id}")

    # Validate contracts
    manager.validate_contract(c1.contract_id, 0.04, 0.03)  # Close to prediction
    manager.validate_contract(c2.contract_id, -0.05, 0.3)  # Way off — violated

    print(f"\nStats: {json.dumps(manager.get_stats(), indent=2)}")

    print(f"\nRollbacks needed:")
    for r in manager.get_rollbacks_needed():
        print(f"  {r['contract_id']}: {r['mutation_type']} on {r['target']}")
