"""
V3 Phase 4 — Sovereign API Endpoints
FastAPI routes for the Sovereign Instrumentation & Operator Embodiment Layer.
"""

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging

from sovereign import (
    OCEShellRuntime, ContinuityState,
    ExecutiveRouter, RoutingDecision,
    ToolEmbodimentLayer, ToolAction,
    ContinuitySnapshotSystem, ContinuitySnapshot,
    ComputeEconomicsEngine, ComputeBudget,
    AutonomousOperationLoop, LoopPhase,
)

logger = logging.getLogger("oce.sovereign")

# Global instances
_shell: Optional[OCEShellRuntime] = None
_router: Optional[ExecutiveRouter] = None
_tools: Optional[ToolEmbodimentLayer] = None
_snapshots: Optional[ContinuitySnapshotSystem] = None
_economics: Optional[ComputeEconomicsEngine] = None
_loop: Optional[AutonomousOperationLoop] = None


def _get_shell() -> OCEShellRuntime:
    global _shell
    if _shell is None:
        _shell = OCEShellRuntime()
    return _shell


def _get_router() -> ExecutiveRouter:
    global _router
    if _router is None:
        _router = ExecutiveRouter()
    return _router


def _get_tools() -> ToolEmbodimentLayer:
    global _tools
    if _tools is None:
        _tools = ToolEmbodimentLayer()
    return _tools


def _get_snapshots() -> ContinuitySnapshotSystem:
    global _snapshots
    if _snapshots is None:
        _snapshots = ContinuitySnapshotSystem()
    return _snapshots


def _get_economics() -> ComputeEconomicsEngine:
    global _economics
    if _economics is None:
        _economics = ComputeEconomicsEngine()
    return _economics


def _get_loop() -> AutonomousOperationLoop:
    global _loop
    if _loop is None:
        _loop = AutonomousOperationLoop()
    return _loop


class RouteTaskRequest(BaseModel):
    task_type: str
    task_complexity: float = 0.5
    entropy_pressure: float = 0.5
    continuity_stability: float = 0.8
    preferred_agent: str = None


class SnapshotRequest(BaseModel):
    shell_state: dict = {}
    observer_states: dict = {}
    trajectories: list[str] = []
    topology: dict = {}
    memory_anchors: list[str] = []
    entropy_budget: float = 1.0
    field_health: float = 1.0


class LoopCycleRequest(BaseModel):
    field_health: float = 1.0
    entropy_pressure: float = 0.0
    drift_alerts: list[str] = []
    waste_report: dict = {}


def register_sovereign_endpoints(app: FastAPI) -> None:
    """Register all V3 Phase 4 sovereign endpoints."""

    # ── OCE Shell ──

    @app.get("/sovereign/shell/status")
    def get_shell_status():
        return _get_shell().get_status()

    @app.post("/sovereign/shell/update")
    def update_shell_state(request: dict):
        state = _get_shell().update_state(**request)
        return state.to_dict()

    @app.post("/sovereign/shell/snapshot")
    def snapshot_shell():
        return _get_shell().snapshot().to_dict()

    @app.post("/sovereign/shell/trajectory")
    def add_trajectory(trajectory_id: str):
        _get_shell().add_trajectory(trajectory_id)
        return {"status": "added", "trajectory_id": trajectory_id}

    # ── Executive Router ──

    @app.get("/sovereign/router/stats")
    def get_router_stats():
        return _get_router().stats

    @app.post("/sovereign/router/route")
    def route_task(req: RouteTaskRequest):
        decision = _get_router().route_task(
            task_type=req.task_type,
            task_complexity=req.task_complexity,
            entropy_pressure=req.entropy_pressure,
            continuity_stability=req.continuity_stability,
            preferred_agent=req.preferred_agent,
        )
        return decision.to_dict()

    # ── Tool Embodiment ──

    @app.get("/sovereign/tools/stats")
    def get_tools_stats():
        return _get_tools().stats

    @app.post("/sovereign/tools/terminal")
    def execute_terminal(command: str, timeout: int = 30):
        action = _get_tools().execute_terminal(command, timeout=timeout)
        return action.to_dict()

    @app.post("/sovereign/tools/read")
    def read_file(filepath: str):
        action = _get_tools().read_file(filepath)
        return action.to_dict()

    @app.post("/sovereign/tools/write")
    def write_file(filepath: str, content: str):
        action = _get_tools().write_file(filepath, content)
        return action.to_dict()

    @app.post("/sovereign/tools/kill")
    def kill_process(pid: int = None, name: str = None):
        action = _get_tools().kill_process(pid=pid, name=name)
        return action.to_dict()

    # ── Continuity Snapshots ──

    @app.get("/sovereign/snapshots/stats")
    def get_snapshot_stats():
        return _get_snapshots().stats

    @app.get("/sovereign/snapshots")
    def list_snapshots():
        return _get_snapshots().list_snapshots()

    @app.post("/sovereign/snapshots/capture")
    def capture_snapshot(req: SnapshotRequest):
        snapshot = _get_snapshots().capture(
            shell_state=req.shell_state,
            observer_states=req.observer_states,
            trajectories=req.trajectories,
            topology=req.topology,
            memory_anchors=req.memory_anchors,
            entropy_budget=req.entropy_budget,
            field_health=req.field_health,
        )
        return snapshot.to_dict()

    @app.get("/sovereign/snapshots/restore/{snapshot_id}")
    def restore_snapshot(snapshot_id: str):
        snapshot = _get_snapshots().restore(snapshot_id)
        if not snapshot:
            raise HTTPException(status_code=404, detail="Snapshot not found")
        return snapshot.to_dict()

    # ── Compute Economics ──

    @app.get("/sovereign/economics/stats")
    def get_economics_stats():
        return _get_economics().stats

    @app.post("/sovereign/economics/record")
    def record_operation(operation_type: str, tokens_used: int = 0,
                         coherence_delta: float = 0.0, entropy_delta: float = 0.0):
        _get_economics().record_operation(operation_type, tokens_used, coherence_delta, entropy_delta)
        return _get_economics().stats

    @app.get("/sovereign/economics/waste")
    def analyze_waste():
        return _get_economics().analyze_waste().__dict__

    @app.get("/sovereign/economics/recommendations")
    def get_recommendations():
        return _get_economics().get_recommendations()

    # ── Autonomous Loop ──

    @app.get("/sovereign/loop/stats")
    def get_loop_stats():
        return _get_loop().stats

    @app.post("/sovereign/loop/cycle")
    def run_loop_cycle(req: LoopCycleRequest):
        cycle = _get_loop().run_cycle(
            field_health=req.field_health,
            entropy_pressure=req.entropy_pressure,
            drift_alerts=req.drift_alerts,
            waste_report=req.waste_report,
        )
        return cycle.to_dict()

    # ── Combined Stats ──

    @app.get("/sovereign/stats")
    def get_all_sovereign_stats():
        return {
            "shell": _get_shell().get_status(),
            "router": _get_router().stats,
            "tools": _get_tools().stats,
            "snapshots": _get_snapshots().stats,
            "economics": _get_economics().stats,
            "loop": _get_loop().stats,
        }

    logger.info("V3 Phase 4 sovereign endpoints registered")
