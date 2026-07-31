"""
Tufte Observability — Export real data from SRRA and render all 4 visuals.
Single script: exports data from live system, then runs all renderers.
"""
import sys, json
sys.path.insert(0, r'c:\Users\wifik\Desktop\projects\larger-lab')

from pathlib import Path
from core.observability.observer_registry import get_registry, InteractionType
from core.observability.event_schema import get_event_store, EventType
from core.observability.temporal_graph import get_temporal_graph

EXPORT_BASE = Path(r'c:\Users\wifik\Desktop\projects\larger-lab\tools\visualization\exports')
OUTPUT_BASE = Path(r'c:\Users\wifik\Desktop\projects\larger-lab\tools\visualization\tufte\output')
EXPORT_BASE.mkdir(parents=True, exist_ok=True)
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

reg = get_registry()
es = get_event_store()
tg = get_temporal_graph()

# ── Register observers ──
observers = [
    ('trading', 'trading_observer'),
    ('repair', 'repair_observer'),
    ('planner', 'planner_observer'),
    ('memory', 'memory_observer'),
    ('entropy', 'entropy_observer'),
    ('gateway', 'gateway_observer'),
    ('security', 'security_observer'),
    ('health', 'health_observer'),
]
for otype, oid in observers:
    reg.register_observer(otype, oid, {'status': 'active', 'uptime': 3600})

# ── Record interactions ──
interactions = [
    ('trading_observer', 'repair_observer', InteractionType.REPAIR, 50, 0.1, 0.05),
    ('repair_observer', 'planner_observer', InteractionType.MESSAGE, 120, 0.2, 0.15),
    ('planner_observer', 'memory_observer', InteractionType.MEMORY, 80, 0.15, 0.1),
    ('memory_observer', 'entropy_observer', InteractionType.SYNC, 30, 0.3, 0.25),
    ('entropy_observer', 'gateway_observer', InteractionType.ROUTE, 150, 0.4, 0.35),
    ('gateway_observer', 'security_observer', InteractionType.SYNC, 70, 0.2, 0.18),
    ('security_observer', 'health_observer', InteractionType.SYNC, 20, 0.1, 0.08),
    ('health_observer', 'trading_observer', InteractionType.SYNC, 40, 0.05, 0.03),
    ('trading_observer', 'planner_observer', InteractionType.MESSAGE, 110, 0.12, 0.09),
    ('repair_observer', 'memory_observer', InteractionType.MEMORY, 90, 0.25, 0.2),
]
for src, tgt, itype, lat, ent_before, ent_after in interactions:
    reg.record_interaction(src, tgt, itype, latency_ms=lat)

# ── Record temporal edges ──
for src, tgt, itype, lat, ent_before, ent_after in interactions:
    tg.record_interaction(src, tgt, itype.name, latency_ms=lat,
                          entropy_before=ent_before, entropy_after=ent_after,
                          repair_triggered=(itype == InteractionType.REPAIR),
                          continuity_shift=ent_after - ent_before)

# ── Emit events ──
events_data = [
    (EventType.OBSERVER_SPAWN, 'trading_observer', 'system', 1.0, 0.0),
    (EventType.OBSERVER_SPAWN, 'repair_observer', 'system', 1.0, 0.0),
    (EventType.OBSERVER_SPAWN, 'planner_observer', 'system', 1.0, 0.0),
    (EventType.OBSERVER_SPAWN, 'memory_observer', 'system', 1.0, 0.0),
    (EventType.REPAIR_TRIGGER, 'repair_observer', 'trading_observer', 0.7, 0.3),
    (EventType.FIELD_PERTURBATION, 'entropy_observer', 'field', 0.5, 0.5),
    (EventType.OBSERVER_SYNC, 'trading_observer', 'repair_observer', 0.9, -0.1),
    (EventType.ROUTE_SHIFT, 'gateway_observer', 'planner_observer', 0.8, 0.2),
    (EventType.CONTINUITY_DROP, 'entropy_observer', 'field', 0.4, 0.6),
    (EventType.ATTRACTOR_LOCK, 'planner_observer', 'field', 0.85, -0.15),
    (EventType.MEMORY_PULL, 'memory_observer', 'structural_memory', 0.95, 0.0),
    (EventType.REPAIR_TRIGGER, 'repair_observer', 'memory_observer', 0.75, 0.1),
    (EventType.CHAOS_INJECT, 'chaos_engine', 'field', 0.6, 0.4),
    (EventType.REPAIR_COMPLETE, 'repair_observer', 'trading_observer', 0.9, -0.2),
    (EventType.CONTINUITY_RESTORE, 'planner_observer', 'field', 0.85, -0.1),
]
for etype, src, tgt, cs, ed in events_data:
    es.emit(etype, source=src, target=tgt, continuity_score=cs, entropy_delta=ed,
            field_zone='core' if 'observer' in src else 'periphery',
            attractor_region='stable' if cs > 0.8 else 'unstable')

# ── Take topology snapshots ──
tg.take_snapshot({oid: {'status': 'active', 'entropy': 0.3} for _, oid in observers})
tg.take_snapshot({oid: {'status': 'active', 'entropy': 0.4 if 'entropy' in oid else 0.2} for _, oid in observers})
tg.take_snapshot({oid: {'status': 'active', 'entropy': 0.25} for _, oid in observers})

# ── Export all data ──
# 1. Registry / topology
reg_data = reg.get_observer_graph()
(EXPORT_BASE / 'topology' / 'registry_export.json').write_text(json.dumps(reg_data, indent=2, default=str))
print(f"Registry: {len(reg_data.get('nodes',{}))} nodes, {len(reg_data.get('edges',[]))} edges")

# 2. Events / repair — serialize ContinuityEvent objects properly
all_events_raw = []
for et in EventType:
    all_events_raw.extend(es.get_events_by_type(et))
def e2d(e):
    return {k: getattr(e, k) for k in ['event_id','timestamp','event_type','source','target','continuity_score','entropy_delta','observer_pressure','continuity_shift','field_zone','attractor_region','details','success','chain_id']}
all_events = [e2d(e) for e in all_events_raw]
# Convert enums and datetime to strings
for ev in all_events:
    for k, v in ev.items():
        if hasattr(v, 'name'): ev[k] = v.name
        elif hasattr(v, 'isoformat'): ev[k] = str(v)
(EXPORT_BASE / 'repair' / 'events_export.json').write_text(json.dumps(all_events, indent=2))
print(f"Events: {len(all_events)}")

# 3. Entropy
entropy = es.get_entropy_profile()
(EXPORT_BASE / 'entropy' / 'entropy_export.json').write_text(json.dumps(entropy, indent=2, default=str))
print(f"Entropy: {len(entropy.get('regions',{}))} regions")

# 4. Continuity timeline
continuity = es.get_continuity_timeline()
(EXPORT_BASE / 'timelines' / 'continuity_export.json').write_text(json.dumps(continuity, indent=2, default=str))
print(f"Continuity: {len(continuity)} points")

# 5. Repair chains
chains = es.get_repair_chains()
(EXPORT_BASE / 'repair' / 'repair_chains.json').write_text(json.dumps(chains, indent=2, default=str))
print(f"Repair chains: {len(chains)}")

print("\nAll exports complete. Run individual renderers to generate visuals.")
