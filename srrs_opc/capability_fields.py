"""
Capability Fields
==================
Phase 4 (Updated): Tools become distributed execution potentials within topology space.

NOT isolated callable endpoints. Each capability field exposes:
- execution affordances, entropy profile, reconstruction risk,
- synchronization burden, repair compatibility, local context resonance.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List


class CapabilityField:
    """
    Abstract execution region representing a tool's capabilities within the topology.

    Examples: Claude (reasoning), VSCode (editing), OpenClaw (messaging), Memory DB (persistence)
    """

    def __init__(self, field_id: str, field_type: str, description: str = ""):
        self.field_id = field_id
        self.field_type = field_type
        self.description = description
        self.execution_affordances: List[str] = []
        self.entropy_profile: Dict[str, float] = {}
        self.reconstruction_risk: float = 0.0
        self.synchronization_burden: float = 0.0
        self.repair_compatibility: float = 1.0
        self.local_context_resonance: Dict[str, float] = {}
        self.active: bool = True
        self.created_at = datetime.now(timezone.utc).isoformat()

    def add_affordance(self, operation: str, entropy_cost: float = 0.1):
        """Register an operation this capability can perform."""
        self.execution_affordances.append(operation)
        self.entropy_profile[operation] = entropy_cost

    def evaluate_execution(self, operation: str, context: dict) -> dict:
        """Evaluate whether an operation can execute safely."""
        if operation not in self.execution_affordances:
            return {"viable": False, "reason": "operation_not_supported"}

        entropy_cost = self.entropy_profile.get(operation, 0.5)
        risk = self.reconstruction_risk

        viable = (
            entropy_cost < 0.8 and
            risk < 0.7 and
            self.active
        )

        return {
            "viable": viable,
            "operation": operation,
            "entropy_cost": entropy_cost,
            "reconstruction_risk": risk,
            "synchronization_burden": self.synchronization_burden,
            "repair_compatibility": self.repair_compatibility,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_id": self.field_id,
            "field_type": self.field_type,
            "affordances": self.execution_affordances,
            "entropy_profile": self.entropy_profile,
            "reconstruction_risk": self.reconstruction_risk,
            "synchronization_burden": self.synchronization_burden,
            "repair_compatibility": self.repair_compatibility,
            "active": self.active,
        }


class CapabilityFieldRegistry:
    """Registry of all capability fields in the system."""

    def __init__(self):
        self.fields: Dict[str, CapabilityField] = {}

    def register(self, field: CapabilityField):
        self.fields[field.field_id] = field

    def get(self, field_id: str) -> Optional[CapabilityField]:
        return self.fields.get(field_id)

    def find_capable(self, operation: str) -> List[CapabilityField]:
        """Find all fields that support a given operation."""
        return [f for f in self.fields.values() if operation in f.execution_affordances]

    def get_entropy_report(self) -> Dict[str, float]:
        return {fid: f.synchronization_burden for fid, f in self.fields.items()}
