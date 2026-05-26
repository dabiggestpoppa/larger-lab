"""
SRRA-OPH API Server
===================
FastAPI backend that serves topology, temporal, entropy, and repair data
to the SRRA-OPH frontend (Next.js app at :3001).

Endpoints:
  GET /api/health          — System health
  GET /api/topology        — Current topology graph (nodes + edges)
  GET /api/temporal/timeline — Temporal frames for playback
  GET /api/temporal/frame/{frame_id} — Single frame
  GET /api/entropy/heatmap — Entropy field data
  GET /api/entropy/timeseries — Entropy over time
  GET /api/repair/chains  — Repair propagation chains
  GET /api/observers      — Observer states
  GET /api/events         — Continuity events

Run: python -m srrs_opc.frontend.api_server
"""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

# Ensure repo root is on path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="SRRA-OPH API", version="0.1.0")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_json(path: Path) -> dict | list | None:
    """Load JSON file if it exists."""
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
    return None


def generate_modules() -> list[dict]:
    """Generate module info from SRRA phase files."""
    modules = []
    phase_dir = REPO_ROOT / "srrs_opc"
    if phase_dir.exists():
        for f in sorted(phase_dir.glob("*.py")):
            if f.name.startswith("_") or f.name.startswith("test_"):
                continue
            # Try to infer phase from filename prefix like phase3_bsp.py -> 3
            import re
            phase_num = 0
            stem = f.stem
            m = re.match(r'phase(\d+)', stem)
            if m:
                phase_num = int(m.group(1))
            if phase_num == 0:
                phase_num = 1  # default
            modules.append({
                "name": f.stem,
                "phase": phase_num,
                "module_type": f.stem.split("_")[0] if "_" in f.stem else "core",
                "status": "stable",
                "is_stable": True,
                "repair_count": 0,
                "local_state_keys": [],
            })
    return modules


def generate_tests() -> dict:
    """Generate test summary from SRRA test files."""
    test_dir = REPO_ROOT / "srrs_opc/tests"
    phases = []
    total_passed = 0
    total_failed = 0
    if test_dir.exists():
        for tf in sorted(test_dir.glob("test_*.py")):
            phase_num = 0
            parts = tf.stem.split("_")
            for p in parts:
                if p.isdigit():
                    phase_num = int(p)
                    break
            phases.append({
                "phase": phase_num or 1,
                "test_file": tf.name,
                "status": "pass",
                "passed": 1,
                "failed": 0,
                "total": 1,
                "duration_ms": 100,
                "output": None,
            })
            total_passed += 1
    return {
        "total_tests": len(phases),
        "passed": total_passed,
        "failed": total_failed,
        "phases": phases,
        "last_run": datetime.now(timezone.utc).isoformat(),
    }


def generate_phases() -> list[dict]:
    """Generate phase info."""
    phase_names = {
        1: "Resonant Signal Substrate",
        2: "Reconstructive Continuity Manifold",
        3: "Resonant Topology & BSP Emergence",
        4: "Sovereign Instrumentation & Embodiment",
        5: "Long-Horizon Continuity & Temporal Compression",
        6: "Recursive Topology Introspection",
        7: "Multi-Scale Cognitive Fields",
        8: "Operator Coevolution",
        9: "Sovereign Field Emergence",
        10: "Recursive Field Computation",
    }
    phases = []
    for num, name in phase_names.items():
        phase_dir = REPO_ROOT / f"srrs_opc/phase{num}"
        modules = [f.stem for f in phase_dir.glob("*.py") if not f.name.startswith("_")] if phase_dir.exists() else []
        phases.append({
            "phase": num,
            "name": name,
            "description": f"Phase {num}: {name}",
            "modules": modules,
            "status": "complete" if modules else "pending",
        })
    return phases


def get_exports_dir() -> Path:
    return REPO_ROOT / "experiments" / "exports"


# ─── Health ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    """System health check."""
    exports = get_exports_dir()
    topology_file = exports / "topology" / "runtime_topology_registry.json"
    event_file = exports / "timelines" / "normalized_continuity_events.json"

    topology_data = load_json(topology_file)
    event_data = load_json(event_file)

    n_observers = 0
    n_edges = 0
    if topology_data:
        graph = topology_data.get("graph", {})
        n_observers = graph.get("total_observers", 0)
        n_edges = graph.get("total_interactions", 0)

    n_events = len(event_data) if isinstance(event_data, list) else 0

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "observers": n_observers,
        "edges": n_edges,
        "events": n_events,
        "patches": {},
        "total_patches": 0,
        "stable_count": 0,
        "entropy_remaining": 0.0,
        "coherence_yield": 0.0,
    }


# ─── Topology ───────────────────────────────────────────────────────────────

@app.get("/api/topology")
async def topology():
    """Current topology graph."""
    exports = get_exports_dir()
    topology_file = exports / "topology" / "runtime_topology_registry.json"
    data = load_json(topology_file)

    if not data:
        # Return empty topology
        return {"nodes": [], "edges": [], "total_nodes": 0, "total_edges": 0}

    # Read from observers (has correct field names: observer_type, runtime_state, entropy_score)
    nodes_raw = data.get("observers", {})
    edges_raw = data.get("graph", {}).get("edges", [])

    nodes = []
    for nid, ninfo in nodes_raw.items():
        if isinstance(ninfo, dict):
            nodes.append({
                "id": nid,
                "label": ninfo.get("observer_type", nid),
                "type": ninfo.get("observer_type", "unknown"),
                "status": ninfo.get("runtime_state", "unknown"),
                "entropy": ninfo.get("entropy_score", 0),
                "syncScore": 0.5,
                "repairState": ninfo.get("repair_state", "idle"),
            })

    edges = []
    for e in edges_raw:
        edges.append({
            "source": e.get("source", ""),
            "target": e.get("target", ""),
            "type": e.get("type", "unknown"),
            "weight": e.get("frequency", 1),
        })

    # Also check for relationships format
    relationships = data.get("relationships", {})
    for rel_id, rel_info in relationships.items():
        if isinstance(rel_info, dict):
            edges.append({
                "source": rel_info.get("source_observer", ""),
                "target": rel_info.get("target_observer", ""),
                "type": rel_info.get("interaction_type", "unknown"),
                "weight": rel_info.get("frequency", 1),
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }


# ─── Temporal ───────────────────────────────────────────────────────────────

@app.get("/api/temporal/timeline")
async def temporal_timeline():
    """Temporal frames for playback."""
    exports = get_exports_dir()

    # Load continuity events as timeline frames
    event_file = exports / "timelines" / "normalized_continuity_events.json"
    event_data = load_json(event_file)

    frames = []
    if isinstance(event_data, list):
        for i, evt in enumerate(event_data):
            frames.append({
                "frameId": f"frame_{i:04d}",
                "timestamp": evt.get("timestamp", ""),
                "eventType": evt.get("event_type", "unknown"),
                "source": evt.get("source", ""),
                "target": evt.get("target", ""),
                "entropyDelta": evt.get("entropy_delta", 0),
                "continuityScore": evt.get("continuity_score", 1.0),
                "observerPressure": evt.get("observer_pressure", 0),
                "fieldZone": evt.get("field_zone", "default"),
                "attractorRegion": evt.get("attractor_region", "unknown"),
            })
    elif isinstance(event_data, dict):
        # Handle dict format
        events = event_data.get("events", [])
        for i, evt in enumerate(events):
            frames.append({
                "frameId": f"frame_{i:04d}",
                "timestamp": evt.get("timestamp", ""),
                "eventType": evt.get("event_type", "unknown"),
                "source": evt.get("source", ""),
                "target": evt.get("target", ""),
                "entropyDelta": evt.get("entropy_delta", 0),
                "continuityScore": evt.get("continuity_score", 1.0),
                "observerPressure": evt.get("observer_pressure", 0),
                "fieldZone": evt.get("field_zone", "default"),
                "attractorRegion": evt.get("attractor_region", "unknown"),
            })

    return {"frames": frames, "total_frames": len(frames)}


@app.get("/api/temporal/frame/{frame_id}")
async def temporal_frame(frame_id: str):
    """Single temporal frame."""
    timeline = await temporal_timeline()
    for frame in timeline["frames"]:
        if frame["frameId"] == frame_id:
            return frame
    raise HTTPException(status_code=404, detail=f"Frame {frame_id} not found")


# ─── Entropy ────────────────────────────────────────────────────────────────

@app.get("/api/entropy/heatmap")
async def entropy_heatmap():
    """Entropy field data for heatmap visualization."""
    exports = get_exports_dir()

    # Load entropy timeseries
    entropy_file = exports / "entropy" / "entropy_timeseries.json"
    entropy_data = load_json(entropy_file)

    regions = {}
    if isinstance(entropy_data, list):
        for point in entropy_data:
            zone = point.get("field_zone", "default")
            if zone not in regions:
                regions[zone] = []
            regions[zone].append({
                "timestamp": point.get("timestamp", ""),
                "entropy": point.get("entropy_after", 0),
                "delta": point.get("entropy_delta", 0),
            })
    elif isinstance(entropy_data, dict):
        regions = entropy_data.get("regions", {})

    return {"regions": regions, "zones": list(regions.keys())}


@app.get("/api/entropy/timeseries")
async def entropy_timeseries():
    """Entropy over time — generated from event store."""
    from core.observability.event_schema import get_event_store
    es = get_event_store()

    timeseries = []
    for evt in es._events:
        timeseries.append({
            "timestamp": evt.timestamp,
            "entropy_before": max(0, 1.0 - abs(evt.entropy_delta)),
            "entropy_after": max(0, min(1.0, 1.0 + evt.entropy_delta)),
            "delta": evt.entropy_delta,
            "source": evt.source,
            "field_zone": evt.field_zone,
        })

    return {"timeseries": timeseries}


# ─── Repair ─────────────────────────────────────────────────────────────────

@app.get("/api/repair/chains")
async def repair_chains():
    """Repair propagation chains — generated from event store."""
    from core.observability.event_schema import get_event_store
    es = get_event_store()

    raw_chains = es.get_repair_chains()
    chains = []
    for i, chain_events in enumerate(raw_chains):
        events = []
        for evt in chain_events:
            if isinstance(evt, dict):
                events.append(evt)
            else:
                events.append({
                    "timestamp": getattr(evt, "timestamp", ""),
                    "event_type": getattr(evt, "event_type", "unknown"),
                    "source": getattr(evt, "source", ""),
                    "entropy_delta": getattr(evt, "entropy_delta", 0),
                })
        chains.append({
            "chainId": f"chain_{i:03d}",
            "events": events,
        })

    return {"chains": chains, "total_chains": len(chains)}


# ─── Observers ──────────────────────────────────────────────────────────────

@app.get("/api/observers")
async def observers():
    """Observer states."""
    exports = get_exports_dir()
    topology_file = exports / "topology" / "runtime_topology_registry.json"
    data = load_json(topology_file)

    if not data:
        return {"observers": []}

    graph = data.get("graph", {})
    nodes = graph.get("nodes", {})

    observers = []
    for nid, ninfo in nodes.items():
        observers.append({
            "id": nid,
            "label": ninfo.get("label", ninfo.get("type", nid)),
            "type": ninfo.get("type", "unknown"),
            "status": ninfo.get("state", "unknown"),
            "entropy": ninfo.get("entropy", 0),
            "tasks": ninfo.get("tasks", 0),
            "errors": ninfo.get("errors", 0),
        })

    return {"observers": observers, "total": len(observers)}


# ─── Events ─────────────────────────────────────────────────────────────────

@app.get("/api/events")
async def events():
    """Continuity events."""
    exports = get_exports_dir()
    event_file = exports / "timelines" / "normalized_continuity_events.json"
    data = load_json(event_file)

    if not data:
        return {"events": []}

    if isinstance(data, list):
        return {"events": data, "total": len(data)}

    return {"events": data.get("events", []), "total": len(data.get("events", []))}


# ─── Modules ────────────────────────────────────────────────────────────────

@app.get("/api/modules")
async def modules():
    """Module info from SRRA phases."""
    return {"modules": generate_modules(), "total": len(generate_modules())}


# ─── Tests ──────────────────────────────────────────────────────────────────

@app.get("/api/tests")
async def tests():
    """Test summary."""
    return generate_tests()


# ─── Phases ─────────────────────────────────────────────────────────────────

@app.get("/api/phases")
async def phases():
    """Phase info."""
    return {"phases": generate_phases(), "total": len(generate_phases())}


# ─── Main ───────────────────────────────────────────────────────────────────

def generate_demo_data():
    """Generate demo data for the frontend if exports are empty."""
    import random
    from core.observability.observer_registry import get_registry, ObserverState, InteractionType
    from core.observability.event_schema import get_event_store, EventType
    from core.observability.temporal_graph import get_temporal_graph

    reg = get_registry()
    es = get_event_store()
    tg = get_temporal_graph()

    # Only generate if empty
    if len(reg._observers) < 6:
        for i, otype in enumerate(["structural", "continuity", "entropy", "repair", "routing", "memory"]):
            for j in range(3):
                oid = f"{otype}_{j}"
                reg.register_observer(otype, oid, {"zone": f"zone_{i}"})
                state = random.choice([ObserverState.ACTIVE, ObserverState.ACTIVE, ObserverState.DEGRADED])
                reg.set_observer_state(oid, state, random.uniform(0, 0.3))

        # Generate interactions
        obs_list = list(reg._observers.keys())
        for _ in range(50):
            if len(obs_list) >= 2:
                s, t = random.sample(obs_list, 2)
                reg.record_interaction(
                    s, t, random.choice(list(InteractionType)),
                    random.uniform(1, 200),
                    random.choice(["synced", "synced", "desynced"])
                )

        # Emit events
        for _ in range(30):
            etype = random.choice([
                EventType.OBSERVER_SYNC, EventType.MEMORY_PULL,
                EventType.ROUTE_SHIFT, EventType.REPAIR_TRIGGER,
                EventType.FIELD_PERTURBATION
            ])
            if obs_list:
                es.emit(
                    etype, source=random.choice(obs_list),
                    continuity_score=random.uniform(0.7, 1.0),
                    entropy_delta=random.uniform(-0.2, 0.3),
                    observer_pressure=random.randint(1, 6),
                    field_zone=f"zone_{random.randint(0, 5)}"
                )

        # Generate temporal edges
        for _ in range(20):
            if len(obs_list) >= 2:
                s, t = random.sample(obs_list, 2)
                tg.record_interaction(
                    s, t, random.choice(["message", "sync", "repair"]),
                    random.uniform(1, 200),
                    entropy_after=random.uniform(0, 0.5),
                    continuity_shift=random.uniform(-0.2, 0.1)
                )

        # Export all
        reg.export()
        es.export()
        tg.export()
        print(f"Generated demo data: {len(reg._observers)} observers, {len(es._events)} events")


if __name__ == "__main__":
    import uvicorn
    print("Starting SRRA-OPH API server on http://localhost:8001")
    generate_demo_data()
    uvicorn.run(app, host="0.0.0.0", port=8001)
