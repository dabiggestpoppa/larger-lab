"""
Phase 11.2 — Chaos 3x Target Test
==================================
Runs chaos engine from 1.0x to 3.0x amplification.
Each cycle: observer_death, event_flood, memory_poison, full_chaos
Proper wait times based on actual scaled durations.
"""
import sys, time, json
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.testing.chaos.chaos_engine import ChaosEngine

RESULTS_FILE = Path("stability/chaos_3x_results.json")
TRACE_FILE = Path("stability/chaos_3x_trace.log")

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(TRACE_FILE, 'a', encoding='utf-8') as f:
        f.write(line + "\n")

engine = ChaosEngine()
results = []

# Start at 1.0x, increment by 0.5x per cycle up to 3.0x
amplification_levels = [1.0, 1.5, 2.0, 2.5, 3.0]
scenarios = ["observer_death", "event_flood", "memory_poison", "full_chaos"]

log("=" * 60)
log("PHASE 11.2 — CHAOS 3x TARGET TEST")
log(f"Amplification levels: {amplification_levels}")
log(f"Scenarios: {scenarios}")
log("=" * 60)

for cycle_num, amp in enumerate(amplification_levels, 1):
    log(f"\n{'='*60}")
    log(f"CYCLE {cycle_num}/{len(amplification_levels)} | Amplification: {amp:.1f}x")
    log(f"{'='*60}")

    cycle_events = 0
    cycle_recovery = 0
    all_passed = True
    scenario_details = []

    for scenario in scenarios:
        log(f"  Running: {scenario} (amp={amp:.1f}x)")
        try:
            result = engine.run_chaos_scenario(scenario, amplification=amp)
            events_injected = result.get("events_injected", 0)
            cycle_events += events_injected

            # Compute proper timeout based on actual scaled durations
            base_durations = {
                "observer_kill": 30, "event_flood": 120, "memory_corrupt": 60,
                "websocket_loss": 30, "router_failure": 45, "token_starve": 180,
                "recursive_storm": 60, "twin_desync": 120,
            }
            max_base = max(base_durations.values())
            scaled_max = max_base * amp
            timeout = min(scaled_max * 1.5 + 15, 900)  # Max 15 min

            # Wait for recovery
            recovery_start = time.time()
            recovered = False
            for _ in range(int(timeout)):
                time.sleep(1)
                if not engine.get_active_chaos():
                    recovered = True
                    break

            recovery_time = time.time() - recovery_start
            cycle_recovery += recovery_time

            if not recovered:
                log(f"    [WARN] Timeout ({timeout:.0f}s) — forcing clear")
                engine.active_events.clear()
                all_passed = False

            status = "PASS" if recovered else "FAIL"
            log(f"    [{status}] {events_injected} events, recovery={recovery_time:.1f}s (timeout={timeout:.0f}s)")

            scenario_details.append({
                "scenario": scenario, "events": events_injected,
                "recovered": recovered, "recovery_time": round(recovery_time, 2),
            })

        except Exception as e:
            log(f"    [ERROR] {e}")
            all_passed = False
            scenario_details.append({"scenario": scenario, "error": str(e)})

    cycle_result = {
        "cycle": cycle_num, "amplification": amp,
        "events": cycle_events, "recovery_time": round(cycle_recovery, 2),
        "passed": all_passed, "details": scenario_details,
    }
    results.append(cycle_result)

    status = "PASS" if all_passed else "FAIL"
    log(f"  [{status}] CYCLE {cycle_num} — {cycle_events} events, {cycle_recovery:.1f}s total")

# Summary
passed = sum(1 for r in results if r["passed"])
total = len(results)
max_amp = max(r["amplification"] for r in results)
total_events = sum(r["events"] for r in results)

log(f"\n{'='*60}")
log(f"FINAL RESULTS")
log(f"{'='*60}")
log(f"Total cycles: {total}")
log(f"Passed: {passed}")
log(f"Failed: {total - passed}")
log(f"Max amplification: {max_amp:.1f}x")
log(f"Total events: {total_events}")
log(f"Overall: {'ALL PASS' if passed == total else 'SOME FAIL'}")

for r in results:
    s = "PASS" if r["passed"] else "FAIL"
    log(f"  [{s}] Cycle {r['cycle']} (amp={r['amplification']:.1f}x): {r['events']} events, {r['recovery_time']:.1f}s")

# Write results
output = {
    "test_id": "11.2-3x-target",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "total_cycles": total, "passed_cycles": passed, "failed_cycles": total - passed,
    "pass_rate": round(passed / total * 100, 1),
    "max_amplification": max_amp, "total_events": total_events,
    "overall_pass": passed == total,
    "cycles": results,
}
RESULTS_FILE.write_text(json.dumps(output, indent=2, default=str))
log(f"\nResults: {RESULTS_FILE}")
