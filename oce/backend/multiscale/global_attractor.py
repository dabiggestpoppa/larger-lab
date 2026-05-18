"""V3 Phase 7 — Global Attractor Layer

Low-frequency strategic stabilization.
The global layer sets direction but does NOT control local execution.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class AttractorState(Enum):
    """States of the global attractor."""
    STABLE = "stable"
    ADAPTING = "adapting"
    TRANSITIONING = "transitioning"
    RESOLVING = "resolving"


@dataclass
class GlobalAttractor:
    """Global attractor for low-frequency strategic stabilization."""
    
    attractor_id: str = "global_attractor"
    state: AttractorState = AttractorState.STABLE
    strategic_direction: Dict[str, Any] = field(default_factory=dict)
    influence_strength: float = 0.3  # Low influence on local execution
    last_update: datetime = field(default_factory=datetime.utcnow)
    update_frequency: int = 100  # Updates every N local operations
    local_operation_count: int = 0
    
    def set_direction(self, direction: Dict[str, Any]) -> None:
        """Set strategic direction (does not control local execution)."""
        self.strategic_direction = direction
        self.last_update = datetime.utcnow()
    
    def get_direction(self) -> Dict[str, Any]:
        """Get current strategic direction."""
        return self.strategic_direction.copy()
    
    def record_local_operation(self) -> None:
        """Record a local operation for frequency tracking."""
        self.local_operation_count += 1
    
    def should_update(self) -> bool:
        """Check if global attractor should update based on operation count."""
        return self.local_operation_count >= self.update_frequency
    
    def reset_operation_count(self) -> None:
        """Reset local operation counter."""
        self.local_operation_count = 0
    
    def transition_state(self, new_state: AttractorState) -> None:
        """Transition to a new attractor state."""
        self.state = new_state
        self.last_update = datetime.utcnow()
    
    def calculate_influence(self, scale: str = "local") -> float:
        """Calculate influence strength based on scale."""
        # Global influence is always low, especially on local execution
        influence_map = {
            "global": 1.0,
            "regional": 0.5,
            "local": 0.1,
        }
        return influence_map.get(scale, self.influence_strength)


class GlobalAttractorLayer:
    """Layer managing the global attractor system."""
    
    def __init__(self):
        self.attractor = GlobalAttractor()
        self._direction_history: List[Dict[str, Any]] = []
    
    def update_direction(self, direction: Dict[str, Any]) -> None:
        """Update strategic direction and record history."""
        self._direction_history.append({
            "direction": direction,
            "timestamp": datetime.utcnow(),
        })
        self.attractor.set_direction(direction)
    
    def get_current_direction(self) -> Dict[str, Any]:
        """Get current strategic direction."""
        return self.attractor.get_direction()
    
    def get_direction_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent direction history."""
        return self._direction_history[-limit:]
    
    def process_local_operation(self) -> Optional[Dict[str, Any]]:
        """Process a local operation and return direction if update needed."""
        self.attractor.record_local_operation()
        
        if self.attractor.should_update():
            self.attractor.reset_operation_count()
            return self.attractor.get_direction()
        return None