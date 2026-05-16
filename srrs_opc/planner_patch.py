"""
Planner Patch
=============
Strategic planning observer with bounded horizon.
"""

from .base_patch import BasePatch, CollarState
from typing import Dict, Any, List
from datetime import datetime


class PlannerPatch(BasePatch):
    """Plans objectives within bounded horizon."""
    
    def __init__(self):
        super().__init__()
        self.local_state = {
            "objectives": [],
            "constraints": [],
            "horizon": 10,  # Bounded planning horizon
            "last_plan": None
        }
    
    def process(self, collar_state: CollarState) -> CollarState:
        """Process collar and produce planning output."""
        # Update local state from collar
        if collar_state.objective:
            self.local_state["objectives"].append(collar_state.objective)
            self.local_state["constraints"].extend(collar_state.constraints)
        
        # Generate plan within horizon
        plan = self._generate_plan()
        self.local_state["last_plan"] = plan
        
        # Return updated collar
        return CollarState(
            patch_id=self.patch_id,
            timestamp=datetime.now().isoformat(),
            objective=plan.get("primary", ""),
            constraints=plan.get("constraints", []),
            confidence=plan.get("confidence", 0.5),
            state_hash=self._hash_state()
        )
    
    def _generate_plan(self) -> Dict[str, Any]:
        """Generate bounded plan."""
        objectives = self.local_state["objectives"][-self.local_state["horizon"]:]
        constraints = self.local_state["constraints"][-5:]  # Last 5 constraints
        
        return {
            "primary": objectives[-1] if objectives else "maintain_stability",
            "constraints": constraints,
            "confidence": 0.7,
            "steps": len(objectives)
        }
    
    def self_check(self) -> bool:
        """Verify planning state consistency."""
        return (
            isinstance(self.local_state.get("objectives"), list) and
            isinstance(self.local_state.get("horizon"), int) and
            self.local_state.get("horizon", 0) > 0
        )
    
    def repair(self) -> bool:
        """Reset to stable planning state."""
        self.local_state = {
            "objectives": self.local_state.get("objectives", [])[-5:],
            "constraints": [],
            "horizon": 10,
            "last_plan": None
        }
        return True
    
    def _hash_state(self) -> str:
        """Simple state hash for collar."""
        return str(hash(str(self.local_state)))