"""Phase 11.2-3B — Integrated Observability Demo"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from core.observability.observer_registry import get_registry, ObserverState, InteractionType
from core.observability.event_schema import get_event_store, EventType
from core.observability.temporal_graph import get_temporal_graph
from core.observability.attractor_analysis import AttractorAnalyzer
import random

print("=" * 60)
print("Phase 11.2-3B — Integrated Observability Demo")
print("=" * 60)

reg = get_registry()
es = get_event_store()
tg = get_temporal_graph()

# Phase 1: Spawn observers
print("\n[1/6] Spawning observer field...")
observer_types = ["structural", "continuity", "entropy", "repair", "routing", "memory"]
observers = []
for i, otype in enumerate(observer_types):
    for j in range(3):
        oid = reg.register_observer(otype, f"{otype}_{j}", {"zone": f"zone_{i}"})
        observers.append(oid)
        reg.set_observer_state(oid, ObserverState.ACTIVE, entropy_score=random.uniform(0, 0.2))
print(f"  Spawned {len(observers)} observers")

# Phase 2: Simulate runtime interactions
print("\n[2/6] Simulating runtime interactions...")
for _ in range(100):
    src = random.choice(observers)
    tgt = random.choice(observers)
    if src != tgt:
        itype = random.choice(list(InteractionType))
        latency = random.uniform(1, 500)
        sync = random.choice(["synced", "synced", "synced", "desynced", "unknown"])
        reg.record_interaction(src, tgt, itype, latency, sync)
        tg.record_interaction(src, tgt, itype.value, latency,
                              entropy_before=random.uniform(0, 0.3),
                              entropy_after=random.uniform(0, 0.5),
                              repair_triggered=random.random() < 0.1,
                              continuity_shift=random.uniform(-0.2, 0.1))
print(f"  Recorded 100 interactions")

# Phase 3: Emit continuity events
print("\n[3/6] Emitting continuity events...")
event_types = [EventType.OBSERVER_SYNC, EventType.MEMORY_PULL, EventType.ROUTE_SHIFT,
               EventType.REPAIR_TRIGGER, EventType.FIELD_PERTURBATION]
for _ in range(50):
    etype = random.choice(event_types)
    src = random.choice(observers)
    es.emit(etype, source=src,
            continuity_score=random.uniform(0.7, 1.0),
            entropy_delta=random.uniform(-0.2, 0.3),
            observer_pressure=random.randint(1, 6),
            field_zone=f"zone_{random.randint(0,5)}",
            attractor_region=f"attractor_{random.randint(0,3)}")
print(f"  Emitted 50 continuity events")

# Phase 4: Export all
print("\n[4/6] Exporting all data...")
reg_path = reg.export()
es_path = es.export()
tg_path = tg.export()
print(f"  Registry: {reg_path}")
print(f"  Events: {es_path}")
print(f"  Temporal: {tg_path}")

# Phase 5: Attractor analysis
print("\n[5/6] Running attractor analysis...")
analyzer = AttractorAnalyzer()
attractors = analyzer.analyze_temporal_graph(tg.summary(), tg.get_node_activity())
resonance = analyzer.compute_field_resonance(
    {oid: {"entropy_score": random.uniform(0, 0.4), "tasks_completed": random.randint(0, 100),
           "errors": random.randint(0, 5), "field_zone": f"zone_{i%6}"}
     for i, oid in enumerate(observers)},
    es.get_entropy_profile()
)
basins = analyzer.detect_continuity_basins(es.get_continuity_timeline())
analyzer.export()
print(f"  Attractors found: {len(attractors)}")
print(f"  Global resonance: {resonance.global_resonance:.4f}")
print(f"  Continuity basins: {len(basins)}")

# Phase 6: Summary
print("\n[6/6] Summary...")
graph = reg.get_observer_graph()
sync = reg.get_sync_health()
entropy = es.get_entropy_profile()
temp = tg.summary()

print(f"  Runtime Topology:")
print(f"    Observers: {graph['total_observers']}")
print(f"    Interactions: {graph['total_interactions']}")
print(f"    Sync rate: {sync.get('sync_rate', 0):.0%}")
print(f"    Hotspots: {len(reg.get_hotspots(0.3))}")

print(f"  Event Store:")
print(f"    Total events: {entropy.get('total_events', 0)}")
print(f"    Net entropy: {entropy.get('net_entropy', 0):.4f}")

print(f"  Temporal Graph:")
print(f"    Total edges: {temp.get('total_edges', 0)}")
print(f"    Avg continuity shift: {temp.get('avg_continuity_shift', 0):.4f}")

print(f"\nIntegrated demo complete -- all data exported to experiments/exports/")
