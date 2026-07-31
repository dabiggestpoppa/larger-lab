"""Run observability stress test and export all results. Detailed logging version."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    sys.stdout.flush()

log("=" * 60)
log("Observability Layer - Full Validation Run")
log("=" * 60)

# 1. Stress test
log("\n[1/4] Running stress tests...")
from core.observability.observability_stress import ObservabilityStressTest

log("  Creating ObservabilityStressTest...")
stress = ObservabilityStressTest()
log("  Running stress.run_all()...")
results = stress.run_all()
log(f"  Stress results: {len(results)} tests completed")

for r in results:
    status = "PASS" if not r.errors else "FAIL"
    log(f"    {status}: {r.test_name} | events={r.events_generated} | obs={r.observers_spawned} | dur={r.duration_seconds}s")
    if r.errors:
        log(f"      ERRORS: {r.errors}")

log("  Exporting stress results...")
stress_path = stress.export_results()
log(f"  Results file: {stress_path}")

log("  Running validation...")
validation = stress.validate()
for check, passed in validation.items():
    log(f"    {'PASS' if passed else 'FAIL'}: {check}")

# 2. Registry
log("\n[2/4] Observer registry...")
from core.observability.observer_registry import get_registry
reg = get_registry()
graph = reg.get_observer_graph()
log(f"  Observers: {graph['total_observers']}")
log(f"  Interactions: {graph['total_interactions']}")
sync = reg.get_sync_health()
log(f"  Sync health: {sync}")
log("  Exporting registry...")
reg.export()
log("  Registry exported")

# 3. Event store
log("\n[3/4] Event store...")
from core.observability.event_schema import get_event_store
es = get_event_store()
summary = es.summary()
log(f"  Summary: {summary}")
log("  Exporting event store...")
es.export()
log("  Event store exported")

# 4. Temporal graph + attractors
log("\n[4/4] Temporal graph + attractor analysis...")
from core.observability.temporal_graph import get_temporal_graph
from core.observability.attractor_analysis import AttractorAnalyzer

tg = get_temporal_graph()
temp_summary = tg.summary()
log(f"  Temporal: {temp_summary}")

analyzer = AttractorAnalyzer()
log("  Running attractor analysis...")
attractors = analyzer.analyze_temporal_graph(tg.summary(), tg.get_node_activity())
log(f"  Attractors found: {len(attractors)}")
if attractors:
    for a in attractors[:5]:
        log(f"    {a.label}: stability={a.stability_score}, resonance={a.field_resonance}")
log("  Exporting attractors...")
analyzer.export()
log("  Exporting temporal graph...")
tg.export()
log("  Temporal graph exported")

log("\nAll exports saved to experiments/exports/")
log("=" * 60)
log("VALIDATION COMPLETE")
