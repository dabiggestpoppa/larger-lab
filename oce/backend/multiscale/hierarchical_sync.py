"""V3 Phase 7 — Hierarchical Synchronization

Scale-appropriate sync frequency.
Local sync happens constantly, regional sync periodically, global sync rarely.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import time


class SyncFrequency(Enum):
    """Sync frequency levels for different scales."""
    LOCAL = "local"      # High frequency (every operation)
    REGIONAL = "regional"  # Medium frequency (periodic)
    GLOBAL = "global"    # Low frequency (rare)


@dataclass
class SyncRecord:
    """Record of a synchronization event."""
    
    sync_id: str
    scale: SyncFrequency
    timestamp: datetime
    participants: List[str]
    data: Dict[str, Any]
    duration_ms: float = 0.0


class SyncManager:
    """Manager for hierarchical synchronization across scales."""
    
    def __init__(self):
        self._sync_intervals = {
            SyncFrequency.LOCAL: 0.1,      # 100ms
            SyncFrequency.REGIONAL: 5.0,   # 5 seconds
            SyncFrequency.GLOBAL: 60.0,    # 60 seconds
        }
        self._last_sync: Dict[SyncFrequency, float] = {
            freq: 0.0 for freq in SyncFrequency
        }
        self._sync_history: List[SyncRecord] = []
    
    def should_sync(self, scale: SyncFrequency) -> bool:
        """Check if sync is needed for a given scale."""
        last = self._last_sync.get(scale, 0.0)
        interval = self._sync_intervals.get(scale, 1.0)
        return (time.time() - last) >= interval
    
    def perform_sync(self, scale: SyncFrequency, participants: List[str], data: Dict[str, Any]) -> SyncRecord:
        """Perform synchronization at a given scale."""
        start_time = time.time()
        
        record = SyncRecord(
            sync_id=f"sync_{int(start_time * 1000)}",
            scale=scale,
            timestamp=datetime.utcnow(),
            participants=participants,
            data=data,
            duration_ms=(time.time() - start_time) * 1000,
        )
        
        self._last_sync[scale] = time.time()
        self._sync_history.append(record)
        
        return record
    
    def get_sync_history(self, scale: Optional[SyncFrequency] = None, limit: int = 100) -> List[SyncRecord]:
        """Get sync history, optionally filtered by scale."""
        if scale:
            return [r for r in self._sync_history if r.scale == scale][-limit:]
        return self._sync_history[-limit:]
    
    def get_sync_interval(self, scale: SyncFrequency) -> float:
        """Get the sync interval for a scale."""
        return self._sync_intervals.get(scale, 1.0)
    
    def set_sync_interval(self, scale: SyncFrequency, interval: float) -> None:
        """Set the sync interval for a scale."""
        self._sync_intervals[scale] = interval
    
    def get_time_since_last_sync(self, scale: SyncFrequency) -> float:
        """Get time elapsed since last sync for a scale."""
        last = self._last_sync.get(scale, 0.0)
        return time.time() - last