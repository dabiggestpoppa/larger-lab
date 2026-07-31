"""
SRRA-OPH API Wrapper
====================
FastAPI wrapper exposing SRRA-OPH module status, topology, tests, and events.
Does NOT modify original SRRA-OPH Python modules.
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent dir to path for srrs_opc imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

app = FastAPI(
    title="SRRA-OPH API",
    description="API wrapper for SRRA-OPH Self-Repairing Recursive Architecture",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── SRRA-OPH Module Imports ─────────────────────────────────────────────────

from srrs_opc import (
    # Phase 1
    PlannerPatch, ExecutionPatch, MemoryPatch, RepairPatch,
    CollarLayer, AgentBridge, BasePatch, CollarState,
    # Phase 2
    DriftDetector, ConsistencyValidator,
    ReconstructionSynthesizer, ContradictionResolver, ConstraintPropagator,
    # Phase 3
    DynamicCouplingEngine, TopologicalRouter, DistributedConsensus,
    # Phase 5
    LongTermDriftTracker, ReinforcementEngine,
    # Phase 6
    TopologyObserver, CollarTopologyEngine, PredictionContractManager,
    # Phase 7
    AttractorReasoningEngine,
    # Phase 9
    CoherenceYieldAnalyzer, EntropyBudgetManager, RecoverabilityEconomics,
    AdaptiveCompressionEngine, SyncCostOptimizer, ResourceConstrainedCognition,
    SustainabilityGovernance,
)

# ─── Singleton Instances ─────────────────────────────────────────────────────

_patches: Dict[str, Any] = {}
_collar_layer: Optional[CollarLayer] = None
_topology_observer: Optional[TopologyObserver] = None
_topology_engine: Optional[CollarTopologyEngine] = None
_drift_tracker: Optional[LongTermDriftTracker] = None
_reinforcement_engine: Optional[ReinforcementEngine] = None
_coherence_analyzer: Optional[CoherenceYieldAnalyzer] = None
_entropy_budget: Optional[EntropyBudgetManager] = None
_contract_manager: Optional[PredictionContractManager] = None
_initialized = False


def _ensure_initialized():
    """Lazy-initialize SRRA-OPH components."""
    global _initialized, _patches, _collar_layer
    global _topology_observer, _topology_engine, _drift_tracker
    global _reinforcement_engine, _coherence_analyzer, _entropy_budget, _contract_manager

    if _initialized:
        return

    _patches = {
        "planner": PlannerPatch(),
        "execution": ExecutionPatch(),
        "memory": MemoryPatch(),
        "repair": RepairPatch(),
    }
    _collar_layer = CollarLayer()
    for p in _patches.values():
        _collar_layer.register_patch(p)

    _topology_observer = TopologyObserver()
    _topology_engine = CollarTopologyEngine()
    _drift_tracker = LongTermDriftTracker()
    _reinforcement_engine = ReinforcementEngine()
    _coherence_analyzer = CoherenceYieldAnalyzer()
    _entropy_budget = EntropyBudgetManager(global_budget=500.0)
    _contract_manager = PredictionContractManager()

    _initialized = True


# ─── Pydantic Models ─────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    patches: Dict[str, Dict[str, Any]]
    total_patches: int
    stable_count: int
    entropy_remaining: float
    coherence_yield: float


class ModuleInfo(BaseModel):
    name: str
    phase: int
    module_type: str
    status: str
    is_stable: bool
    repair_count: int
    local_state_keys: List[str]


class TopologyNode(BaseModel):
    id: str
    label: str
    type: str
    status: str


class TopologyEdge(BaseModel):
    source: str
    target: str
    weight: float
    label: str


class TopologyResponse(BaseModel):
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]
    stats: Dict[str, Any]


class TestResult(BaseModel):
    phase: int
    test_file: str
    status: str
    passed: Optional[int] = None
    failed: Optional[int] = None
    total: Optional[int] = None
    duration_ms: Optional[float] = None
    output: Optional[str] = None


class TestSummary(BaseModel):
    total_tests: int
    passed: int
    failed: int
    phases: List[TestResult]
    last_run: Optional[str] = None


class EventItem(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    source: str
    priority: int
    payload: Dict[str, Any]


class PhaseInfo(BaseModel):
    phase: int
    name: str
    description: str
    modules: List[str]
    status: str


# ─── Module Registry ─────────────────────────────────────────────────────────

MODULE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Phase 1: Foundational Observer Mesh
    "base_patch": {"phase": 1, "type": "core", "desc": "Base patch abstract class"},
    "planner_patch": {"phase": 1, "type": "patch", "desc": "Planning observer"},
    "execution_patch": {"phase": 1, "type": "patch", "desc": "Execution observer"},
    "memory_patch": {"phase": 1, "type": "patch", "desc": "Memory observer"},
    "repair_patch": {"phase": 1, "type": "patch", "desc": "Repair observer"},
    "collar_layer": {"phase": 1, "type": "coordinator", "desc": "Overlap synchronization"},
    "agent_bridge": {"phase": 1, "type": "bridge", "desc": "Agent communication bridge"},
    # Phase 2: Reconstruction + Recoverability
    "recovery_anchors": {"phase": 2, "type": "recovery", "desc": "Anchor-based recovery"},
    "drift_detector": {"phase": 2, "type": "monitor", "desc": "Drift detection"},
    "consistency_validator": {"phase": 2, "type": "validator", "desc": "State consistency checks"},
    "reconstruction_synthesizer": {"phase": 2, "type": "recovery", "desc": "Continuity reconstruction"},
    "contradiction_resolver": {"phase": 2, "type": "resolver", "desc": "Conflict resolution"},
    "constraint_propagator": {"phase": 2, "type": "propagator", "desc": "Constraint propagation"},
    # Phase 3: Emergent Topology
    "dynamic_coupling": {"phase": 3, "type": "topology", "desc": "Dynamic coupling engine"},
    "topological_router": {"phase": 3, "type": "router", "desc": "Topological message routing"},
    "distributed_consensus": {"phase": 3, "type": "consensus", "desc": "Distributed consensus"},
    "active_collar_fields": {"phase": 3, "type": "field", "desc": "Active collar fields"},
    "local_consensus": {"phase": 3, "type": "consensus", "desc": "Local consensus engine"},
    # Phase 4: Workspace Integration
    "capability_fields": {"phase": 4, "type": "field", "desc": "Capability field registry"},
    "workspace_integration": {"phase": 4, "type": "integration", "desc": "Workspace tool adapter"},
    "overlap_aware_tooling": {"phase": 4, "type": "tooling", "desc": "Overlap-aware execution"},
    "reconstruction_safe_exec": {"phase": 4, "type": "executor", "desc": "Safe execution wrapper"},
    # Phase 5: Long-Horizon Continuity
    "trajectory_fields": {"phase": 5, "type": "field", "desc": "Trajectory reconstruction"},
    "continuity_collars": {"phase": 5, "type": "collar", "desc": "Temporal continuity"},
    "temporal_attractors": {"phase": 5, "type": "attractor", "desc": "Temporal attractor fields"},
    "drift_tracker": {"phase": 5, "type": "monitor", "desc": "Long-term drift tracking"},
    "reinforcement_engine": {"phase": 5, "type": "engine", "desc": "Reinforcement learning"},
    # Phase 6: Recursive Topology Introspection
    "topology_observer": {"phase": 6, "type": "observer", "desc": "Topology self-observation"},
    "collar_topology_engine": {"phase": 6, "type": "engine", "desc": "Collar topology analysis"},
    "prediction_contracts": {"phase": 6, "type": "contract", "desc": "Mutation prediction"},
    # Phase 7: Multi-Scale Overlap Ecologies
    "attractor_reasoning": {"phase": 7, "type": "reasoning", "desc": "Attractor-based reasoning"},
    "structural_memory": {"phase": 7, "type": "memory", "desc": "Structural memory fields"},
    "bidirectional_coherence": {"phase": 7, "type": "coherence", "desc": "Bidirectional coherence"},
    # Phase 8: Sovereign Coevolution
    "operator_patterns": {"phase": 8, "type": "model", "desc": "Operator pattern modeling"},
    "strategic_preferences": {"phase": 8, "type": "model", "desc": "Strategic preference tracking"},
    "constraint_alignment": {"phase": 8, "type": "adapter", "desc": "Constraint alignment"},
    "operator_continuity": {"phase": 8, "type": "tracker", "desc": "Operator continuity"},
    "anti_manipulation": {"phase": 8, "type": "safeguard", "desc": "Anti-manipulation guards"},
    # Phase 9: Entropy Economics
    "coherence_yield_analyzer": {"phase": 9, "type": "analyzer", "desc": "Coherence yield analysis"},
    "entropy_budget_manager": {"phase": 9, "type": "manager", "desc": "Entropy budget tracking"},
    "recoverability_economics": {"phase": 9, "type": "economics", "desc": "Recovery cost analysis"},
    "adaptive_compression_engine": {"phase": 9, "type": "compression", "desc": "Adaptive compression"},
    "sync_cost_optimizer": {"phase": 9, "type": "optimizer", "desc": "Sync cost optimization"},
    "resource_constrained_cognition": {"phase": 9, "type": "cognition", "desc": "Resource-aware cognition"},
    "sustainability_governance": {"phase": 9, "type": "governance", "desc": "Sustainability governance"},
}

PHASE_INFO: Dict[int, Dict[str, str]] = {
    1: {"name": "Foundational Observer Mesh", "desc": "Bounded local cognition with repairable overlap"},
    2: {"name": "Reconstruction + Recoverability", "desc": "Anchor-based recovery and drift detection"},
    3: {"name": "Emergent Topology", "desc": "Dynamic coupling and distributed consensus"},
    4: {"name": "Workspace Integration", "desc": "Tool adaptation and safe execution"},
    5: {"name": "Long-Horizon Continuity", "desc": "Trajectory fields and temporal attractors"},
    6: {"name": "Recursive Topology Introspection", "desc": "Self-observing topology and prediction contracts"},
    7: {"name": "Multi-Scale Overlap Ecologies", "desc": "Attractor reasoning and structural memory"},
    8: {"name": "Sovereign Coevolution", "desc": "Operator modeling and anti-manipulation"},
    9: {"name": "Entropy Economics", "desc": "Budget management and sustainability governance"},
}


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "SRRA-OPH API",
        "version": "1.0.0",
        "phases": 9,
        "modules": len(MODULE_REGISTRY),
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Overall SRRA-OPH health check."""
    _ensure_initialized()

    stable_count = 0
    patch_status = {}
    for name, patch in _patches.items():
        status = patch.get_status()
        is_stable = status.get("is_stable", False)
        if is_stable:
            stable_count += 1
        patch_status[name] = {
            "state": "active" if is_stable else "repairing",
            "healthy": is_stable,
            "repair_count": status.get("repair_count", 0),
        }

    entropy_remaining = _entropy_budget.get_stats().get("remaining", 500.0)
    coherence_yield = _coherence_analyzer.system_yield_score()

    return HealthResponse(
        status="healthy" if stable_count == len(_patches) else "degraded",
        timestamp=datetime.now(timezone.utc).isoformat(),
        patches=patch_status,
        total_patches=len(_patches),
        stable_count=stable_count,
        entropy_remaining=entropy_remaining,
        coherence_yield=coherence_yield,
    )


@app.get("/modules", response_model=List[ModuleInfo])
async def get_modules():
    """List all SRRA-OPH modules with status."""
    _ensure_initialized()

    modules = []
    for name, info in MODULE_REGISTRY.items():
        # Check if it's a live patch
        patch_key = name.replace("_patch", "")
        is_stable = True
        repair_count = 0
        local_state_keys = []

        for pk, pv in _patches.items():
            if pk in name or name in pk:
                status = pv.get_status()
                is_stable = status.get("is_stable", True)
                repair_count = status.get("repair_count", 0)
                local_state_keys = status.get("local_state_keys", [])
                break

        modules.append(ModuleInfo(
            name=name,
            phase=info["phase"],
            module_type=info["type"],
            status="active" if is_stable else "repairing",
            is_stable=is_stable,
            repair_count=repair_count,
            local_state_keys=local_state_keys,
        ))

    return modules


@app.get("/modules/{module_name}")
async def get_module_detail(module_name: str):
    """Get detailed info for a specific module."""
    _ensure_initialized()

    if module_name not in MODULE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' not found")

    info = MODULE_REGISTRY[module_name]
    detail = {
        "name": module_name,
        "phase": info["phase"],
        "type": info["type"],
        "description": info["desc"],
        "phase_name": PHASE_INFO.get(info["phase"], {}).get("name", "Unknown"),
    }

    # Add live status for patches
    for pk, pv in _patches.items():
        if pk in module_name or module_name in pk:
            detail["live_status"] = pv.get_status()
            break

    return detail


@app.get("/topology", response_model=TopologyResponse)
async def get_topology():
    """Get topology graph data for visualization."""
    _ensure_initialized()

    nodes = []
    edges = []

    # Add patch nodes
    for name, patch in _patches.items():
        status = patch.get_status()
        nodes.append(TopologyNode(
            id=name,
            label=name.replace("_", " ").title(),
            type="patch",
            status="active" if status.get("is_stable", True) else "repairing",
        ))

    # Add module nodes (non-patch)
    for name, info in MODULE_REGISTRY.items():
        if name not in _patches and not name.endswith("_patch"):
            nodes.append(TopologyNode(
                id=name,
                label=name.replace("_", " ").title(),
                type=info["type"],
                status="registered",
            ))

    # Add edges between patches (collar connections)
    patch_names = list(_patches.keys())
    for i in range(len(patch_names) - 1):
        edges.append(TopologyEdge(
            source=patch_names[i],
            target=patch_names[i + 1],
            weight=0.8,
            label="collar",
        ))

    # Add edges from topology engine
    if _topology_engine:
        try:
            metrics = _topology_engine.get_system_metrics()
            if isinstance(metrics, dict):
                for key, val in metrics.items():
                    if isinstance(val, (int, float)) and key != "total_patches":
                        edges.append(TopologyEdge(
                            source="system",
                            target=key,
                            weight=min(abs(val), 1.0),
                            label="metric",
                        ))
        except Exception:
            pass

    # Stats
    stats = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "patch_count": len(_patches),
        "module_count": len(MODULE_REGISTRY),
        "phases": 9,
    }

    return TopologyResponse(nodes=nodes, edges=edges, stats=stats)


@app.get("/tests", response_model=TestSummary)
async def get_tests():
    """Get test results summary for all phases."""
    _ensure_initialized()

    test_dir = Path(__file__).parent.parent / "tests"
    phases = []
    total_passed = 0
    total_failed = 0
    total_tests = 0
    last_run = None

    if test_dir.exists():
        for test_file in sorted(test_dir.glob("test_*.py")):
            phase_num = 0
            parts = test_file.stem.split("_")
            for p in parts:
                if p.isdigit():
                    phase_num = int(p)
                    break

            # Try to run the test
            status_str = "unknown"
            passed = None
            failed = None
            total = None
            duration_ms = None
            output = None

            try:
                start = datetime.now()
                result = subprocess.run(
                    [sys.executable, str(test_file)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(test_dir.parent),
                )
                duration_ms = (datetime.now() - start).total_seconds() * 1000
                output = result.stdout[-500:] if result.stdout else ""

                if result.returncode == 0:
                    status_str = "passed"
                    passed = 1
                    failed = 0
                    total = 1
                else:
                    status_str = "failed"
                    passed = 0
                    failed = 1
                    total = 1
                    if result.stderr:
                        output = result.stderr[-500:]

                last_run = datetime.now(timezone.utc).isoformat()

            except subprocess.TimeoutExpired:
                status_str = "timeout"
                passed = 0
                failed = 1
                total = 1
                output = "Test timed out after 30s"
            except Exception as e:
                status_str = "error"
                passed = 0
                failed = 1
                total = 1
                output = str(e)[:500]

            total_passed += passed or 0
            total_failed += failed or 0
            total_tests += total or 0

            phases.append(TestResult(
                phase=phase_num,
                test_file=test_file.name,
                status=status_str,
                passed=passed,
                failed=failed,
                total=total,
                duration_ms=duration_ms,
                output=output,
            ))

    return TestSummary(
        total_tests=total_tests,
        passed=total_passed,
        failed=total_failed,
        phases=phases,
        last_run=last_run,
    )


@app.get("/events", response_model=List[EventItem])
async def get_events(
    limit: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = None,
):
    """Get SRRA-OPH event stream."""
    _ensure_initialized()

    events = []
    now = datetime.now(timezone.utc)

    # Generate events from system state
    for i, (name, patch) in enumerate(_patches.items()):
        status = patch.get_status()
        events.append(EventItem(
            event_id=f"evt_{i}_{int(now.timestamp())}",
            event_type="patch.status",
            timestamp=now.isoformat(),
            source=name,
            priority=0,
            payload={
                "is_stable": status.get("is_stable", True),
                "repair_count": status.get("repair_count", 0),
            },
        ))

    # Add topology events
    if _topology_observer:
        try:
            snapshot = _topology_observer.take_snapshot()
            if snapshot:
                events.append(EventItem(
                    event_id=f"evt_topo_{int(now.timestamp())}",
                    event_type="topology.snapshot",
                    timestamp=now.isoformat(),
                    source="topology_observer",
                    priority=1,
                    payload=snapshot.to_dict(),
                ))
        except Exception:
            pass

    # Add entropy events
    try:
        budget_stats = _entropy_budget.get_stats()
        events.append(EventItem(
            event_id=f"evt_entropy_{int(now.timestamp())}",
            event_type="entropy.budget",
            timestamp=now.isoformat(),
            source="entropy_budget",
            priority=0,
            payload=budget_stats,
        ))
    except Exception:
        pass

    # Filter by type if specified
    if event_type:
        events = [e for e in events if e.event_type == event_type]

    return events[:limit]


@app.get("/phases", response_model=List[PhaseInfo])
async def get_phases():
    """Get status of all 9 phases."""
    _ensure_initialized()

    phases = []
    for phase_num, info in PHASE_INFO.items():
        modules_in_phase = [
            name for name, minfo in MODULE_REGISTRY.items()
            if minfo["phase"] == phase_num
        ]

        # Determine phase status
        phase_patches = [
            name for name in modules_in_phase
            if any(pk in name for pk in _patches.keys())
        ]
        all_stable = all(
            _patches.get(p, type("obj", (), {"get_status": lambda: {"is_stable": True}})()).get_status().get("is_stable", True)
            for p in phase_patches
            if p in _patches
        )

        phases.append(PhaseInfo(
            phase=phase_num,
            name=info["name"],
            description=info["desc"],
            modules=modules_in_phase,
            status="active" if all_stable else "degraded",
        ))

    return phases


@app.get("/phases/{phase_id}")
async def get_phase_detail(phase_id: int):
    """Get detailed info for a specific phase."""
    _ensure_initialized()

    if phase_id not in PHASE_INFO:
        raise HTTPException(status_code=404, detail=f"Phase {phase_id} not found")

    info = PHASE_INFO[phase_id]
    modules_in_phase = [
        {"name": name, "type": minfo["type"], "description": minfo["desc"]}
        for name, minfo in MODULE_REGISTRY.items()
        if minfo["phase"] == phase_id
    ]

    return {
        "phase": phase_id,
        "name": info["name"],
        "description": info["desc"],
        "modules": modules_in_phase,
        "module_count": len(modules_in_phase),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
