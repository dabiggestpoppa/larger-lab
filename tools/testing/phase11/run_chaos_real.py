"""Run chaos engine tests with proper wait times for real recovery."""
import sys, time, json
sys.path.insert(0, '.')
from datetime import datetime, timezone
from pathlib import Path
from tools.testing.chaos.chaos_engine import ChaosEngine

RESULTS_FILE = Path("stability/chaos_real_results.json")

print("=" * 60)
print("CHAOS ENGINE TEST (REAL COMPONENT)")
print("=" * 60)

engine = ChaosEngine()
results = []

# Run each scenario with proper wait time for recovery
scenarios = [
    {"name": "observer_death", "amp": 0.5, "wait": 45},   # 30s * 0.5 = 15s + margin
    {"name": "event_flood", "amp": 0.25, "wait": 45},     # 120s * 0.25 = 30s + margin
    {"name": "memory_poison", "amp": 0.5, "wait": 45},    # 60s * 0.5 = 30s + margin
    {"name": "full_chaos", "amp": 0.25, "wait": 60},      # Multiple events, longest = 120s * 0.25 = 30s
]

for s in scenarios:
    print(f"\n  Running: {s['name']} (amp={s['amp']}, wait={s['wait']}s)...")
    result = engine.run_chaos_scenario(s["name"], amplification=s["amp"])
    events_injected = result.get("events_injected", 0)
    print(f"    Events injected: {events_injected}")

    # Wait for recovery
    recovered = False
    for i in range(s["wait"]):
        time.sleep(1)
        active = engine.get_active_chaos()
        if not active:
            recovered = True
            print(f"    Recovered after {i+1}s")
            break
        if i % 5 == 0:
            print(f"    Still recovering... ({i}s, {len(active)} active events)")

    if not recovered:
        print(f"    ⚠ Did not fully recover within {s['wait']}s")
        # Force clear for next scenario
        engine.active_events.clear()

    results.append({
        "scenario": s["name"],
        "amplification": s["amp"],
        "events_injected": events_injected,
        "recovered": recovered,
    })

all_pass = all(r["recovered"] for r in results)
print(f"\n{'=' * 60}")
print(f"RESULTS: {sum(1 for r in results if r['recovered'])}/{len(results)} passed")
for r in results:
    status = "✅" if r["recovered"] else "❌"
    print(f"  {status} {r['scenario']}: {r['events_injected']} events, recovered={r['recovered']}")
print(f"Overall: {'✅ ALL PASS' if all_pass else '❌ SOME FAIL'}")

# Write results
output = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "results": results,
    "overall_pass": all_pass,
}
RESULTS_FILE.write_text(json.dumps(output, indent=2))
print(f"\nResults: {RESULTS_FILE}")
