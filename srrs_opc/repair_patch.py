"""
Repair Patch
============
Self-repair observer for patch stabilization.
"""

from .base_patch import BasePatch, CollarState
from typing import Dict, Any, List
from datetime import datetime


class RepairPatch(BasePatch):
    """Monitors and repairs other patches."""
    
    def __init__(self):
        super().__init__()
        self.local_state = {
            "monitored_patches": {},
            "repair_log": [],
            "max_log": 100
        }
    
    def process(self, collar_state: CollarState) -> CollarState:
        """Process collar and check for repair needs."""
        # Check if repair is needed
        repair_needed = len(collar_state.repair_flags) > 0
        
        if repair_needed:
            self._log_repair(collar_state.patch_id, collar_state.repair_flags)
        
        return CollarState(
            patch_id=self.patch_id,
            timestamp=datetime.now().isoformat(),
            objective="repair_check" if repair_needed else "stable",
            constraints=collar_state.constraints,
            confidence=0.9 if not repair_needed else 0.3,
            state_hash=self._hash_state(),
            repair_flags=["repair_complete"] if repair_needed else []
        )
    
    def _log_repair(self, patch_id: str, flags: List[str]):
        """Log repair action."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "patch_id": patch_id,
            "flags": flags
        }
        self.local_state["repair_log"].append(entry)
        
        # Trim log
        if len(self.local_state["repair_log"]) > self.local_state["max_log"]:
            self.local_state["repair_log"] = self.local_state["repair_log"][-50:]
    
    def self_check(self) -> bool:
        """Verify repair state consistency."""
        return (
            isinstance(self.local_state.get("repair_log"), list) and
            len(self.local_state.get("repair_log", [])) <= self.local_state.get("max_log", 100)
        )
    
    def repair(self) -> bool:
        """Reset repair log."""
        self.local_state["repair_log"] = []
        return True
    
    def _hash_state(self) -> str:
        """Simple state hash for collar."""
        return str(hash(str(self.local_state)))