"""
Run all Tufte renderers with live/generated data.
"""
import sys, json, random
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tools.visualization.tufte.render_observer_density import render_observer_density
from tools.visualization.tufte.render_entropy_heatmap import render_entropy_heatmap
from tools.visualization.tufte.render_repair_timeline import render_repair_timeline
from tools.visualization.tufte.render_continuity_ribbon import render_continuity_ribbon

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("Tufte Renderers - Live Data Integration")
print("=" * 60)

# Generate live data from observability layer
from core.observability.observer_registry import get_registry, ObserverState, InteractionType
from core.observability.event_schema import get_event_store, EventType
from core.observability.temporal_graph import get_temporal_graph

reg = get_registry()
es = get_event_store()
tg = get_temporal_graph()

# Spawn observers for visualization
observer_types = ["structural", "continuity", "entropy", "repair", "routing", "memory"]
for i, otype in enumerate(observer_types):
    for j in range(3):
        oid = f"{otype}_{j}"
        if oid not in reg._observers:
            reg.register_observer(otype, oid, {"zone": f"zone_{i}"})
        state = random.choice([ObserverState.ACTIVE, ObserverState.ACTIVE, ObserverState.DEGRADED])
        reg.set_observer_state(oid, state, random.uniform(0, 0.3))

# Generate interactions
for _ in range(50):
    src = random.choice(list(reg._observers.keys()))
    tgt = random.choice(list(reg._observers.keys()))
    if src != tgt:
        reg.record_interaction(src, tgt, random.choice(list(InteractionType)),
                               random.uniform(1, 200),
                               random.choice(["synced", "synced", "desynced"]))

# Emit events
for _ in range(30):
    etype = random.choice([EventType.OBSERVER_SYNC, EventType.MEMORY_PULL,
                           EventType.ROUTE_SHIFT, EventType.REPAIR_TRIGGER,
                           EventType.FIELD_PERTURBATION])
    src = random.choice(list(reg._observers.keys()))
    es.emit(etype, source=src,
            continuity_score=random.uniform(0.7, 1.0),
            entropy_delta=random.uniform(-0.2, 0.3),
            observer_pressure=random.randint(1, 6),
            field_zone=f"zone_{random.randint(0,5)}")

# Render 1: Observer Density
print("\n[1/4] Observer Density Map...")
graph = reg.get_observer_graph()
density_output = render_observer_density(graph)
(OUTPUT_DIR / "observer_density.txt").write_text(density_output, encoding="utf-8")
print(f"  Nodes: {graph['total_observers']}, Edges: {graph['total_interactions']}")

# Render 2: Entropy Heatmap
print("[2/4] Entropy Heatmap...")
entropy_regions = {f"zone_{i}": random.uniform(0, 0.8) for i in range(6)}
entropy_output = render_entropy_heatmap({"regions": entropy_regions})
(OUTPUT_DIR / "entropy_heatmap.txt").write_text(entropy_output, encoding="utf-8")

# Render 3: Repair Timeline
print("[3/4] Repair Timeline...")
repair_events = []
for chain_id, event_ids in es._chains.items():
    for eid in event_ids:
        for ev in es._events:
            if ev.event_id == eid:
                repair_events.append({
                    "timestamp": ev.timestamp, "event_type": ev.event_type,
                    "source": ev.source, "target": ev.target,
                    "entropy_delta": ev.entropy_delta,
                    "repair_triggered": ev.event_type == EventType.REPAIR_TRIGGER.value,
                })
if not repair_events:
    repair_events = [{"timestamp": datetime.now(timezone.utc).isoformat(),
                      "event_type": "none", "source": "system", "target": "none",
                      "entropy_delta": 0, "repair_triggered": False}]
repair_output = render_repair_timeline(repair_events)
(OUTPUT_DIR / "repair_timeline.txt").write_text(repair_output, encoding="utf-8")
print(f"  Repair events: {len(repair_events)}")

# Render 4: Continuity Ribbon
print("[4/4] Continuity Ribbon...")
continuity_timeline = es.get_continuity_timeline()
if not continuity_timeline:
    continuity_timeline = [
        {"timestamp": datetime.now(timezone.utc).isoformat(),
         "continuity_score": random.uniform(0.7, 1.0),
         "entropy_delta": random.uniform(-0.1, 0.2)}
        for _ in range(50)
    ]
continuity_output = render_continuity_ribbon(continuity_timeline)
(OUTPUT_DIR / "continuity_ribbon.txt").write_text(continuity_output, encoding="utf-8")
print(f"  Timeline points: {len(continuity_timeline)}")

# Summary
summary = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "renderers_run": 4,
    "data": {
        "observers": graph["total_observers"],
        "interactions": graph["total_interactions"],
        "events": len(es._events), "chains": len(es._chains),
    }
}
(OUTPUT_DIR / "render_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(f"\nAll 4 renderers complete.")
print("=" * 60)
