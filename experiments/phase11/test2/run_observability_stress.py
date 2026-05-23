"""Run observability stress test and export all results."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from core.observability.observability_stress import ObservabilityStressTest
from core.observability.observer_registry import get_registry
from core.observability.event_schema import get_event_store
from core.observability.temporal_graph import get_temporal_graph
from core.observability.attractor_analysis import AttractorAnalyzer

print("=" * 60)
print("🔬 Observability Layer — Full Validation Run")
print("=" * 60)

# 1. Stress test
print("\n[1/4] Running stress tests...")
stress = ObservabilityStressTest()
results = stress.run_all()
stress_path = stress.export_results()
print(f"  Results: {stress_path}")

validation = stress.validate()
print("\n  Validation:")
for check, passed in validation.items():
    icon = "PASS" if passed else "FAIL"
    print(f"    [{icon}] {check}")

# 2. Registry
print("\n[2/4] Observer registry...")
reg = get_registry()
graph = reg.get_observer_graph()
print(f"  Observers: {graph['total_observers']}")
print(f"  Interactions: {graph['total_interactions']}")
print(f"  Sync health: {reg.get_sync_health()}")
reg.export()

# 3. Event store
print("\n[3/4] Event store...")
es = get_event_store()
print(f"  Summary: {es.summary()}")
es.export()

# 4. Temporal graph + attractors
print("\n[4/4] Temporal graph + attractor analysis...")
tg = get_temporal_graph()
print(f"  Temporal: {tg.summary()}")

analyzer = AttractorAnalyzer()
attractors = analyzer.analyze_temporal_graph(tg.summary(), tg.get_node_activity())
print(f"  Attractors found: {len(attractors)}")
if attractors:
    for a in attractors[:5]:
        print(f"    {a.label}: stability={a.stability_score}, resonance={a.field_resonance}")
analyzer.export()

tg.export()

print("\n✅ All exports saved to experiments/exports/")
print("=" * 60)
