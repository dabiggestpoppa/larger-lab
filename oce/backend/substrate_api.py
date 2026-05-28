"""
O-6: Substrate API Endpoints
=============================

FastAPI endpoints for Local Execution Substrate.

API Contract — shapes aligned with substrateStore.ts expectations:
- /state → { cpu_percent, memory_percent, disk_percent, active_processes, active_sandboxes, uptime_seconds, timestamp }
- /processes → { processes: [{ id, name, pid, status, cpu, memory, command }] }
- /filesystem → { nodes: [...], edges: [...] } (flat graph; frontend can render as tree)
- /sandbox → { sandboxes: [{ id, name, type, status, activeTasks, maxTasks, resourceUsage: {cpu, memory} }] }
- /recovery → { id, action, target, status, timestamp, duration_seconds, details }
- /environment → { workspace, projects, active_projects, active_workflows, running_environments, system, timestamp }
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from .substrate import (
    get_local_runtime,
    get_permission_layer,
    get_execution_sandbox,
    get_filesystem_awareness,
    get_terminal_orchestrator,
    get_process_observer,
    get_recovery_controller,
    get_environment_model,
    get_runtime_inspector,
    get_machine_state_graph,
)


# ─── Request Models ───────────────────────────────────────────────────────────

class ExecuteRequest(BaseModel):
    task_type: str
    payload: Dict[str, Any] = {}
    sandbox_id: Optional[str] = None


class TerminalRequest(BaseModel):
    command: str
    sandbox_id: Optional[str] = None


class RecoveryRequest(BaseModel):
    action: str
    target: str


# ─── Registration Function ───────────────────────────────────────────────────

def register_substrate_endpoints(app: FastAPI):
    """Register all substrate endpoints on the given FastAPI app."""

    @app.get("/api/substrate/state")
    async def get_substrate_state():
        """Get current machine state."""
        try:
            runtime = get_local_runtime()
            state = await runtime.inspect_runtime()
            raw = state.__dict__
            # Ensure frontend-expected keys are present
            return {
                "cpu_percent": raw.get("cpu_percent", 0.0),
                "memory_percent": raw.get("memory_percent", 0.0),
                "disk_percent": raw.get("disk_percent", 0.0),
                "active_processes": raw.get("active_processes", 0),
                "active_sandboxes": raw.get("active_sandboxes", 0),
                "uptime_seconds": raw.get("uptime_seconds", 0),
                "timestamp": raw.get("timestamp", ""),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/substrate/processes")
    async def get_processes():
        """Get active processes. Shapes aligned with store Process interface."""
        try:
            po = get_process_observer()
            raw = po.get_active_processes()
            # Map pid → id (string), ensure all expected keys exist
            processes = []
            for p in raw:
                processes.append({
                    "id": str(p.get("pid", p.get("id", ""))),
                    "name": p.get("name", "unknown"),
                    "pid": p.get("pid", 0),
                    "status": p.get("status", "running"),
                    "cpu": p.get("cpu", 0.0),
                    "memory": p.get("memory", 0.0),
                    "command": p.get("command", ""),
                    "runtime": "",
                })
            return {"processes": processes}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/substrate/filesystem")
    async def get_filesystem(path: Optional[str] = None):
        """Get filesystem topology as flat graph."""
        try:
            fs = get_filesystem_awareness()
            return fs.get_workspace_topology()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/substrate/execute")
    async def execute_task(request: ExecuteRequest):
        """Execute a task in substrate."""
        try:
            runtime = get_local_runtime()
            result = await runtime.execute_task(
                task_type=request.task_type,
                payload=request.payload,
                sandbox_id=request.sandbox_id,
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/substrate/terminal")
    async def execute_terminal(request: TerminalRequest):
        """Execute terminal command."""
        try:
            to = get_terminal_orchestrator()
            result = await to.execute(request.command, request.sandbox_id)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/substrate/sandbox")
    async def get_sandbox_status():
        """Get sandbox status. Shapes aligned with store Sandbox interface."""
        try:
            sb = get_execution_sandbox()
            raw = sb.get_status()
            sandboxes = []
            for s in raw.get("sandboxes", []):
                # Derive status from active_tasks vs max_tasks
                active = s.get("active_tasks", 0)
                max_t = s.get("max_tasks", 1)
                if active == 0:
                    status = "inactive"
                elif active >= max_t:
                    status = "restricted"
                else:
                    status = "active"
                sandboxes.append({
                    "id": s.get("id", ""),
                    "name": s.get("name", ""),
                    "type": s.get("type", "dev"),
                    "status": status,
                    "activeTasks": active,
                    "maxTasks": max_t,
                    "resourceUsage": s.get("resource_usage", {"cpu": 0.0, "memory": 0.0}),
                })
            return {"sandboxes": sandboxes, "total_active_tasks": raw.get("total_active_tasks", 0)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/substrate/recovery")
    async def trigger_recovery(request: RecoveryRequest):
        """Trigger recovery action."""
        try:
            rc = get_recovery_controller()
            from .substrate.recovery_controller import RecoveryAction
            action = RecoveryAction(request.action)
            event = await rc.recover(action, request.target)
            raw = event.__dict__
            # Align with store RecoveryEvent interface
            return {
                "id": raw.get("id", ""),
                "action": raw.get("action", request.action),
                "target": raw.get("target", request.target),
                "status": raw.get("status", "stable"),
                "timestamp": raw.get("timestamp", ""),
                "duration_seconds": raw.get("duration_seconds", 0.0),
                "details": raw.get("details", {}),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/substrate/machine-graph")
    async def get_machine_graph():
        """Get machine state graph."""
        try:
            msg = get_machine_state_graph()
            return msg.get_graph()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/substrate/environment")
    async def get_environment():
        """Get environment model — live workspace awareness."""
        try:
            em = get_environment_model()
            return em.get_current_environment()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/substrate/inspector")
    async def get_inspector():
        """Get runtime inspector telemetry."""
        try:
            ri = get_runtime_inspector()
            return ri.inspect()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
