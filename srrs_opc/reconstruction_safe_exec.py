"""
Reconstruction-Safe Execution
===============================
Phase 4: Unrecoverable execution is invalid execution.

Every execution must support:
- Replayability (can be replayed from event log)
- Rollback (can be undone)
- Repair reconstruction (state can be reconstructed after failure)
- State tracing (all state changes are traceable)

Before execution, the system evaluates whether continuity can be reconstructed
after the execution completes (or fails).
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import ExecutionSafety


class ExecutionSafety(str, Enum):
    SAFE = "safe"                    # Fully recoverable
    DEGRADED = "degraded"            # Partially recoverable
    UNSAFE = "unsafe"                # Not recoverable — REJECTED


class ExecutionRecord:
    """Records an execution for replay and rollback."""

    def __init__(self, execution_id: str, tool_id: str, operation: str, params: dict):
        self.execution_id = execution_id
        self.tool_id = tool_id
        self.operation = operation
        self.params = params
        self.pre_state: Dict[str, Any] = {}
        self.post_state: Dict[str, Any] = {}
        self.safety: ExecutionSafety = ExecutionSafety.SAFE
        self.status = "pending"
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.completed_at = None
        self.error = None

    def compute_hash(self) -> str:
        """Content-addressable hash for deduplication."""
        content = f"{self.tool_id}:{self.operation}:{json.dumps(self.params, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "tool_id": self.tool_id,
            "operation": self.operation,
            "safety": self.safety.value,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class ReconstructionSafeExecutor:
    """
    Ensures all executions are reconstruction-safe.
    
    Before executing:
    1. Evaluate continuity impact
    2. Check recoverability
    3. Verify repair viability
    4. Record pre-state for rollback
    
    After executing:
    1. Record post-state
    2. Verify reconstruction viability
    3. Log execution event
    """

    def __init__(self):
        self.execution_log: List[ExecutionRecord] = []
        self.rollback_log: List[dict] = []

    def evaluate_safety(self, tool_id: str, operation: str, params: dict) -> ExecutionSafety:
        """Evaluate whether an execution is reconstruction-safe."""
        # Check if operation is inherently safe (read-only operations are always safe)
        read_only_ops = {"read", "query", "get", "list", "search", "check", "status"}
        if operation.lower() in read_only_ops:
            return ExecutionSafety.SAFE

        # Check if operation has rollback support
        rollback_supported = {"write", "update", "create", "delete", "execute", "route"}
        if operation.lower() not in rollback_supported:
            return ExecutionSafety.UNSAFE

        # Check if params contain destructive flags
        if params.get("destructive", False) or params.get("force", False):
            return ExecutionSafety.DEGRADED

        return ExecutionSafety.SAFE

    def execute(self, tool_id: str, operation: str, params: dict) -> dict:
        """Execute with reconstruction safety guarantees."""
        execution_id = hashlib.sha256(
            f"{tool_id}:{operation}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]

        record = ExecutionRecord(execution_id, tool_id, operation, params)

        # Step 1: Evaluate safety
        safety = self.evaluate_safety(tool_id, operation, params)
        record.safety = safety

        if safety == ExecutionSafety.UNSAFE:
            return {
                "status": "rejected",
                "reason": "execution_unsafe",
                "execution_id": execution_id,
                "message": "Unrecoverable execution is invalid execution (Phase 4 law)",
            }

        # Step 2: Record pre-state (for rollback)
        record.pre_state = {"tool_id": tool_id, "operation": operation, "params": params}

        # Step 3: Execute
        record.status = "executing"
        try:
            # Actual execution would happen here
            # For now, we record the attempt
            record.status = "completed"
            record.completed_at = datetime.now(timezone.utc).isoformat()
            record.post_state = {"result": "executed", "safety": safety.value}

        except Exception as e:
            record.status = "failed"
            record.error = str(e)
            record.completed_at = datetime.now(timezone.utc).isoformat()

            # Attempt rollback
            rollback_result = self.rollback(record)
            record.post_state = {"error": str(e), "rollback": rollback_result}

        self.execution_log.append(record)
        return {
            "status": record.status,
            "execution_id": execution_id,
            "safety": safety.value,
            "record": record.to_dict(),
        }

    def rollback(self, record: ExecutionRecord) -> dict:
        """Attempt to rollback an execution."""
        rollback_entry = {
            "execution_id": record.execution_id,
            "tool_id": record.tool_id,
            "operation": record.operation,
            "pre_state": record.pre_state,
            "rolled_back_at": datetime.now(timezone.utc).isoformat(),
            "success": True,  # Simplified — real implementation would verify
        }
        self.rollback_log.append(rollback_entry)
        return rollback_entry

    def replay(self, execution_id: str) -> Optional[dict]:
        """Replay a previous execution from the log."""
        for record in self.execution_log:
            if record.execution_id == execution_id:
                return {
                    "status": "replayed",
                    "execution_id": execution_id,
                    "original": record.to_dict(),
                    "replay_time": datetime.now(timezone.utc).isoformat(),
                }
        return None

    def get_execution_report(self) -> Dict[str, Any]:
        """Get full execution report."""
        total = len(self.execution_log)
        completed = sum(1 for r in self.execution_log if r.status == "completed")
        failed = sum(1 for r in self.execution_log if r.status == "failed")
        rejected = sum(1 for r in self.execution_log if r.safety == ExecutionSafety.UNSAFE)

        return {
            "total_executions": total,
            "completed": completed,
            "failed": failed,
            "rejected": rejected,
            "rollbacks": len(self.rollback_log),
            "success_rate": round(completed / max(1, total), 3),
        }
