"""
SRRA-OPH Base Patch
===================
Foundation for all observer patches.

Each patch is a bounded observer with:
- Local state only
- Collar-based communication
- Self-repair capability
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import json


@dataclass
class CollarState:
    """Structured overlap state between patches."""
    patch_id: str
    timestamp: str
    objective: str
    constraints: List[str] = field(default_factory=list)
    confidence: float = 0.0
    state_hash: str = ""
    repair_flags: List[str] = field(default_factory=list)
    
    def to_json(self) -> str:
        return json.dumps({
            "patch_id": self.patch_id,
            "timestamp": self.timestamp,
            "objective": self.objective,
            "constraints": self.constraints,
            "confidence": self.confidence,
            "state_hash": self.state_hash,
            "repair_flags": self.repair_flags
        })
    
    @classmethod
    def from_json(cls, data: str) -> 'CollarState':
        d = json.loads(data)
        return cls(**d)


class BasePatch(ABC):
    """Abstract base for all observer patches."""
    
    def __init__(self, patch_id: Optional[str] = None):
        self.patch_id = patch_id or f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
        self.local_state: Dict[str, Any] = {}
        self.last_collar: Optional[CollarState] = None
        self.is_stable = True
        self.repair_count = 0
        
    @abstractmethod
    def process(self, collar_state: CollarState) -> CollarState:
        """Process incoming collar state and produce output."""
        pass
    
    @abstractmethod
    def self_check(self) -> bool:
        """Verify local state consistency."""
        pass
    
    @abstractmethod
    def repair(self) -> bool:
        """Attempt local repair if inconsistency detected."""
        pass
    
    def run_repair_loop(self) -> bool:
        """Execute the local repair loop."""
        if not self.self_check():
            self.is_stable = False
            repaired = self.repair()
            if repaired:
                self.repair_count += 1
                self.is_stable = True
            return repaired
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Return current patch status."""
        return {
            "patch_id": self.patch_id,
            "is_stable": self.is_stable,
            "repair_count": self.repair_count,
            "local_state_keys": list(self.local_state.keys())
        }