"""V3 Phase 7 — Nested Repair Geometry

Multi-scale repair escalation.
Local repairs happen first, escalate to regional only if needed, global only for systemic issues.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class RepairEscalation(Enum):
    """Levels of repair escalation."""
    LOCAL = "local"       # Handle at local field level
    REGIONAL = "regional"  # Escalate to regional cluster
    GLOBAL = "global"     # Escalate to global attractor


@dataclass
class RepairRequest:
    """A request for repair at a specific scale."""
    
    request_id: str
    issue_type: str
    severity: float  # 0.0 to 1.0
    location: str
    description: str
    escalation_level: RepairEscalation = RepairEscalation.LOCAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None


class NestedRepairSystem:
    """Multi-scale repair system with escalation logic."""
    
    def __init__(self):
        self._repair_queue: List[RepairRequest] = []
        self._repair_history: List[RepairRequest] = []
        self._severity_thresholds = {
            RepairEscalation.LOCAL: 0.3,
            RepairEscalation.REGIONAL: 0.6,
            RepairEscalation.GLOBAL: 0.9,
        }
    
    def submit_repair(self, issue_type: str, severity: float, location: str, description: str) -> RepairRequest:
        """Submit a repair request with automatic escalation level."""
        escalation = self._determine_escalation(severity)
        
        request = RepairRequest(
            request_id=f"repair_{int(datetime.utcnow().timestamp() * 1000)}",
            issue_type=issue_type,
            severity=severity,
            location=location,
            description=description,
            escalation_level=escalation,
        )
        
        self._repair_queue.append(request)
        return request
    
    def _determine_escalation(self, severity: float) -> RepairEscalation:
        """Determine escalation level based on severity."""
        if severity >= self._severity_thresholds[RepairEscalation.GLOBAL]:
            return RepairEscalation.GLOBAL
        elif severity >= self._severity_thresholds[RepairEscalation.REGIONAL]:
            return RepairEscalation.REGIONAL
        return RepairEscalation.LOCAL
    
    def get_pending_repairs(self, escalation: Optional[RepairEscalation] = None) -> List[RepairRequest]:
        """Get pending repairs, optionally filtered by escalation level."""
        if escalation:
            return [r for r in self._repair_queue if r.escalation_level == escalation]
        return list(self._repair_queue)
    
    def process_repair(self, request_id: str, resolution: str) -> Optional[RepairRequest]:
        """Process and resolve a repair request."""
        for i, request in enumerate(self._repair_queue):
            if request.request_id == request_id:
                request.resolved_at = datetime.utcnow()
                request.resolution = resolution
                self._repair_history.append(request)
                del self._repair_queue[i]
                return request
        return None
    
    def escalate_repair(self, request_id: str) -> Optional[RepairRequest]:
        """Escalate a repair to the next level."""
        escalation_order = [
            RepairEscalation.LOCAL,
            RepairEscalation.REGIONAL,
            RepairEscalation.GLOBAL,
        ]
        
        for request in self._repair_queue:
            if request.request_id == request_id:
                current_idx = escalation_order.index(request.escalation_level)
                if current_idx < len(escalation_order) - 1:
                    request.escalation_level = escalation_order[current_idx + 1]
                return request
        return None
    
    def get_repair_history(self, limit: int = 100) -> List[RepairRequest]:
        """Get repair history."""
        return self._repair_history[-limit:]
    
    def get_stats(self) -> Dict[str, int]:
        """Get repair statistics."""
        pending_by_level = {
            level: len(self.get_pending_repairs(level))
            for level in RepairEscalation
        }
        return {
            "pending_total": len(self._repair_queue),
            "resolved_total": len(self._repair_history),
            **{f"pending_{level.value}": count for level, count in pending_by_level.items()},
        }