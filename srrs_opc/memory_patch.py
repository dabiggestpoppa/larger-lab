"""
Memory Patch
============
Memory observer with bounded retention.
"""

from .base_patch import BasePatch, CollarState
from typing import Dict, Any, List
from datetime import datetime


class MemoryPatch(BasePatch):
    """Maintains bounded memory of collar states."""
    
    def __init__(self):
        super().__init__()
        self.local_state = {
            "history": [],
            "max_history": 50,
            "patterns": {},
            "last_access": None
        }
    
    def process(self, collar_state: CollarState) -> CollarState:
        """Store collar state and return with memory context."""
        # Store in history
        self.local_state["history"].append(collar_state.to_json())
        self.local_state["last_access"] = datetime.now().isoformat()
        
        # Trim history
        if len(self.local_state["history"]) > self.local_state["max_history"]:
            self.local_state["history"] = self.local_state["history"][-25:]
        
        # Detect patterns
        self._detect_patterns(collar_state)
        
        return CollarState(
            patch_id=self.patch_id,
            timestamp=datetime.now().isoformat(),
            objective=collar_state.objective,
            constraints=collar_state.constraints,
            confidence=collar_state.confidence,
            state_hash=self._hash_state()
        )
    
    def _detect_patterns(self, collar_state: CollarState):
        """Detect patterns in collar states."""
        obj = collar_state.objective
        if obj in self.local_state["patterns"]:
            self.local_state["patterns"][obj] += 1
        else:
            self.local_state["patterns"][obj] = 1
    
    def self_check(self) -> bool:
        """Verify memory state consistency."""
        return (
            isinstance(self.local_state.get("history"), list) and
            len(self.local_state.get("history", [])) <= self.local_state.get("max_history", 50)
        )
    
    def repair(self) -> bool:
        """Reset memory to stable state."""
        self.local_state = {
            "history": self.local_state.get("history", [])[-10:],
            "max_history": 50,
            "patterns": {},
            "last_access": None
        }
        return True
    
    def _hash_state(self) -> str:
        """Simple state hash for collar."""
        return str(hash(str(self.local_state)))