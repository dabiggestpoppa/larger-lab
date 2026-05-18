"""V3 Phase 7 — Local Observer Fields

Independent local cognition with bounded sync.
Each observer maintains its own coherent field region without needing global state.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


@dataclass
class LocalObserverField:
    """Independent local cognition field for a single observer."""
    
    observer_id: str
    field_state: Dict[str, Any] = field(default_factory=dict)
    coherence_level: float = 1.0
    last_sync: Optional[datetime] = None
    sync_bound: int = 100  # Max sync operations before forced sync
    local_operations: int = 0
    
    def __post_init__(self):
        if not self.field_state:
            self.field_state = {
                "local_context": {},
                "recent_observations": [],
                "pending_actions": [],
            }
    
    def update_state(self, key: str, value: Any) -> None:
        """Update local field state."""
        self.field_state[key] = value
        self.local_operations += 1
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get local field state value."""
        return self.field_state.get(key, default)
    
    def needs_sync(self) -> bool:
        """Check if sync is needed based on operation count."""
        return self.local_operations >= self.sync_bound
    
    def reset_sync_counter(self) -> None:
        """Reset local operation counter after sync."""
        self.local_operations = 0
        self.last_sync = datetime.utcnow()
    
    def calculate_coherence(self) -> float:
        """Calculate current coherence level based on state consistency."""
        # Simple coherence metric based on state completeness
        required_keys = ["local_context", "recent_observations", "pending_actions"]
        present = sum(1 for k in required_keys if k in self.field_state)
        self.coherence_level = present / len(required_keys)
        return self.coherence_level


class LocalFieldRegistry:
    """Registry for managing multiple local observer fields."""
    
    def __init__(self):
        self._fields: Dict[str, LocalObserverField] = {}
    
    def register(self, observer_id: str, **kwargs) -> LocalObserverField:
        """Register a new local field for an observer."""
        field = LocalObserverField(observer_id=observer_id, **kwargs)
        self._fields[observer_id] = field
        return field
    
    def get(self, observer_id: str) -> Optional[LocalObserverField]:
        """Get a local field by observer ID."""
        return self._fields.get(observer_id)
    
    def all_fields(self) -> List[LocalObserverField]:
        """Get all registered local fields."""
        return list(self._fields.values())
    
    def get_needing_sync(self) -> List[LocalObserverField]:
        """Get fields that need synchronization."""
        return [f for f in self._fields.values() if f.needs_sync()]
    
    def remove(self, observer_id: str) -> bool:
        """Remove a local field."""
        if observer_id in self._fields:
            del self._fields[observer_id]
            return True
        return False