"""
O-6: Recovery Controller — Runtime Stabilization
===============================================

Handle runtime recovery and stabilization for substrate operations.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("oce.substrate.recovery_controller")


class RecoveryAction(str, Enum):
    TERMINATE_HUNG = "terminate_hung"
    RESTART_OBSERVER = "restart_observer"
    RESTORE_STATE = "restore_state"
    REDUCE_ENTROPY = "reduce_entropy"


@dataclass
class RecoveryEvent:
    """A recovery operation event."""
    id: str
    action: RecoveryAction
    target: str
    status: str  # "stable", "recovering", "failed", "restarting"
    timestamp: str
    duration_seconds: float = 0.0
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class RecoveryController:
    """
    Handle runtime recovery and stabilization.
    
    Responsibilities:
    - Terminate hung tasks
    - Restart observers
    - Recover runtime continuity
    - Restore orchestration state
    - Reduce entropy cascades
    """
    
    _instance: Optional["RecoveryController"] = None
    
    def __init__(self):
        self.events: List[RecoveryEvent] = []
        self._recovery_history: Dict[str, List[RecoveryEvent]] = {}
    
    async def recover(
        self,
        action: RecoveryAction,
        target: str,
    ) -> RecoveryEvent:
        """
        Execute a recovery action.
        
        Args:
            action: Type of recovery action
            target: Target resource
            
        Returns:
            Recovery event record
        """
        event = RecoveryEvent(
            id=str(datetime.now(timezone.utc).timestamp()),
            action=action,
            target=target,
            status="recovering",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        start = datetime.now(timezone.utc)
        
        try:
            if action == RecoveryAction.TERMINATE_HUNG:
                result = await self._terminate_hung(target)
            elif action == RecoveryAction.RESTART_OBSERVER:
                result = await self._restart_observer(target)
            elif action == RecoveryAction.RESTORE_STATE:
                result = await self._restore_state(target)
            elif action == RecoveryAction.REDUCE_ENTROPY:
                result = await self._reduce_entropy(target)
            else:
                result = {"error": f"Unknown action: {action}"}
            
            event.status = "stable" if "error" not in result else "failed"
            event.details = result
        except Exception as e:
            event.status = "failed"
            event.details = {"error": str(e)}
            logger.error(f"Recovery failed: {e}")
        
        event.duration_seconds = (datetime.now(timezone.utc) - start).total_seconds()
        self.events.append(event)
        
        return event
    
    async def _terminate_hung(self, target: str) -> Dict[str, Any]:
        """Terminate hung processes."""
        from .process_observer import get_process_observer
        po = get_process_observer()
        
        hung = po.detect_hung_processes()
        for pid in hung:
            await po.terminate(pid)
        
        return {"terminated_pids": hung, "count": len(hung)}
    
    async def _restart_observer(self, target: str) -> Dict[str, Any]:
        """Restart an observer."""
        # Would integrate with observer_runtime
        return {"observer": target, "status": "restarted"}
    
    async def _restore_state(self, target: str) -> Dict[str, Any]:
        """Restore runtime continuity state."""
        # Would integrate with structural_memory
        return {"state": target, "status": "restored"}
    
    async def _reduce_entropy(self, target: str) -> Dict[str, Any]:
        """Reduce entropy cascade."""
        # Would integrate with entropy engine
        return {"entropy": target, "status": "reduced"}
    
    def get_recovery_history(self) -> List[Dict[str, Any]]:
        """Get recovery event history."""
        return [
            {
                "id": e.id,
                "action": e.action.value,
                "target": e.target,
                "status": e.status,
                "timestamp": e.timestamp,
                "duration": e.duration_seconds,
            }
            for e in self.events[-50:]  # Last 50 events
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Get current recovery status."""
        recent = self.events[-10:] if self.events else []
        return {
            "total_events": len(self.events),
            "recent_events": len(recent),
            "last_status": recent[-1].status if recent else "stable",
            "last_action": recent[-1].action.value if recent else None,
        }


def get_recovery_controller() -> RecoveryController:
    """Get singleton RecoveryController instance."""
    if RecoveryController._instance is None:
        RecoveryController._instance = RecoveryController()
    return RecoveryController._instance