"""Debug the stress test failures."""
import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from core.observability.observer_registry import get_registry, ObserverState, InteractionType
from core.observability.event_schema import get_event_store, EventType
from core.observability.temporal_graph import get_temporal_graph
import random

reg = get_registry()
es = get_event_store()
tg = get_temporal_graph()

# Test repair storm
print("Testing repair storm...")
try:
    for i in range(5):
        source = f"observer_{i % 10}"
        es.emit(EventType.REPAIR_TRIGGER, source=source,
                chain_id="test_chain",
                entropy_delta=0.2, observer_pressure=2,
                field_zone="stress_repair")
        print(f"  Emitted REPAIR_TRIGGER for {source}")
    print(f"  Event store now has {len(es._events)} events")
    chains = es.get_repair_chains()
    print(f"  Repair chains: {len(chains)}")
except Exception as e:
    traceback.print_exc()

# Test routing instability
print("\nTesting routing instability...")
try:
    for i in range(5):
        source = f"router_{i % 3}"
        es.emit(EventType.ROUTE_SHIFT, source=source,
                entropy_delta=0.1, field_zone="zone_0",
                continuity_shift=-0.2)
        tg.record_interaction(source, f"obs_{i}", "route_shift",
                              latency_ms=100, entropy_after=0.3,
                              continuity_shift=-0.2)
        print(f"  Emitted ROUTE_SHIFT for {source}")
    print(f"  Event store now has {len(es._events)} events")
except Exception as e:
    traceback.print_exc()

# Test sync drift
print("\nTesting sync drift...")
try:
    for i in range(5):
        source = f"obs_{i % 8}"
        es.emit(EventType.SYNC_DRIFT if i % 2 == 0 else EventType.SYNC_RESTORE,
                source=source, entropy_delta=0.1,
                observer_pressure=2, field_zone="zone_0",
                continuity_shift=0.1 if i % 2 == 0 else -0.1)
        reg.record_interaction(source, f"obs_{(i+1)%8}",
                               InteractionType.SYNC,
                               sync_state="desynced" if i % 2 == 0 else "synced")
        print(f"  Emitted SYNC event for {source}")
    print(f"  Event store now has {len(es._events)} events")
except Exception as e:
    traceback.print_exc()

print(f"\nTotal events: {len(es._events)}")
print(f"Total edges: {len(tg._edges)}")
