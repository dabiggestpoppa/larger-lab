"""
Overlap-Aware Tooling
======================
Phase 4: Tool execution requires overlap reconciliation.

Before any tool executes, the collar evaluates:
- Continuity impact (reconstruction safety)
- Entropy cost (synchronization burden)
- Repair viability (rollback recoverability)
- Capability resonance (execution fit)
- Overlap confidence (closure quality)

Execution proceeds ONLY if overlap closure is stable.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from .active_collar_fields import ActiveCollarField, CollarFieldManager
from .workspace_integration import WorkspaceIntegrationLayer, WorkspaceToolAdapter, ToolRole


class ExecutionRequest:
    """A request for tool execution through overlap reconciliation."""

    def __init__(self, tool_id: str, operation: str, params: dict, intent: str = ""):
        self.tool_id = tool_id
        self.operation = operation
        self.params = params
        self.intent = intent
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.status = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "operation": self.operation,
            "intent": self.intent,
            "timestamp": self.timestamp,
            "status": self.status,
        }


class OverlapAwareTooling:
    """
    Mediates all tool execution through overlap reconciliation.
    
    No tool executes directly. All execution passes through collar evaluation.
    This ensures reconstruction-safe execution.
    """

    def __init__(self, integration_layer: WorkspaceIntegrationLayer):
        self.integration = integration_layer
        self.pending_requests: List[ExecutionRequest] = []
        self.completed_requests: List[dict] = []
        self.rejected_requests: List[dict] = []

    def submit_request(self, request: ExecutionRequest) -> dict:
        """Submit an execution request for overlap reconciliation."""
        # Step 1: Find the tool
        tool = self.integration.get_tool(request.tool_id)
        if not tool:
            result = {"status": "rejected", "reason": "tool_not_found", "request": request.to_dict()}
            self.rejected_requests.append(result)
            return result

        # Step 2: Evaluate through capability field
        evaluation = tool.capability_field.evaluate_execution(request.operation, request.params)
        if not evaluation["viable"]:
            result = {"status": "rejected", "reason": evaluation["reason"], "request": request.to_dict()}
            self.rejected_requests.append(result)
            return result

        # Step 3: Check overlap closure stability
        collar_id = f"{request.tool_id}_execution"
        collar = self.integration.collar_manager.get_collar(collar_id)
        if collar and collar.entropy_score > 0.7:
            result = {
                "status": "deferred",
                "reason": "overlap_unstable",
                "entropy": collar.entropy_score,
                "request": request.to_dict(),
            }
            self.pending_requests.append(request)
            return result

        # Step 4: Execute through integration layer
        task = {
            "role": tool.role.value,
            "operation": request.operation,
            "params": request.params,
        }
        result = self.integration.route_task(task)
        result["overlap_evaluation"] = evaluation
        result["request"] = request.to_dict()

        if result["status"] == "accepted":
            request.status = "completed"
            self.completed_requests.append(result)
        else:
            request.status = "rejected"
            self.rejected_requests.append(result)

        return result

    def process_pending(self) -> List[dict]:
        """Process deferred requests that may now have stable overlap."""
        processed = []
        still_pending = []

        for request in self.pending_requests:
            result = self.submit_request(request)
            if result["status"] != "deferred":
                processed.append(result)
            else:
                still_pending.append(request)

        self.pending_requests = still_pending
        return processed

    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics."""
        total = len(self.completed_requests) + len(self.rejected_requests) + len(self.pending_requests)
        return {
            "total_requests": total,
            "completed": len(self.completed_requests),
            "rejected": len(self.rejected_requests),
            "pending": len(self.pending_requests),
            "success_rate": round(len(self.completed_requests) / max(1, total), 3),
        }
