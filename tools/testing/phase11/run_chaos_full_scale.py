"""
Phase 11.2 — Full Scale Chaos Test
Target: 3.0x normal chaos, 14.3% increment per cycle
"""
import time, json, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.testing.chaos.chaos_engine import ChaosEngine

RESULTS_FILE = Path("stability/chaos_full_scale_results.json")
TRACE_FILE = Path("stability/chaos_full_scale_trace.log")

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(TRACE_FILE, 'a', encoding='utf-8') as f:
        f.write(line + "\n")

def get_timeout(amp):
    base = {"observer_kill": 30, "event_flood": 120, "memory_corrupt": 60, "websocket_loss": 30}
    return min(max(base.values()) * amp * 1.5 + 15, 900)

def run():
    engine = ChaosEngine()
    results = []
    amplification = 1.0
    cycle_increment = 0.143
    max_amp = 3.0
    scenarios = ["observer_death", "event_flood", "memory_poison", "full_chaos"]

    log("=" * 60)
    log("PHASE 11.2 — FULL SCALE CHAOS TEST")
    log(f"Target: {max_amp}x | Increment: {cycle_increment*100:.1f}%")
    log("=" * 60)

    for cycle in range(1, 21):
        amplification = min(1.0 + (cycle * cycle_increment), max_amp)
        log(f"\nCYCLE {cycle} | Amp: {amplification:.4f}x")

        cycle_events = 0
        cycle_recovery = 0
        all_passed = True
        details = []

        for scenario in scenarios:
            log(f"  {scenario}...")
            try:
                result = engine.run_chaos_scenario(scenario, amplification=amplification)
                events = result.get("events_injected", 0)
                cycle_events += events

                timeout = get_timeout(amplification)
                start = time.time()
                recovered = False
                for _ in range(int(timeout)):
                    time.sleep(1)
                    if not engine.get_active_chaos():
                        recovered = True
                        break

                recovery = time.time() - start
                cycle_recovery += recovery

                if not recovered:
                    log(f"    [WARN] Timeout ({timeout:.0f}s)")
                    engine.active_events.clear()
                    all_passed = False

                status = "PASS" if recovered else "FAIL"
                log(f"    [{status}] {events} events, {recovery:.1f}s")
                details.append({"scenario": scenario, "events": events, "recovered": recovered, "time": round(recovery, 2)})

            except Exception as e:
                log(f"    [ERROR] {e}")
                all_passed = False
                details.append({"scenario": scenario, "error": str(e)})

        results.append({"cycle": cycle, "amp": round(amplification, 4), "events": cycle_events, "passed": all_passed, "recovery": round(cycle_recovery, 2), "details": details})

        if all_passed:
            log(f"  [PASS] {cycle_events} events, {cycle_recovery:.1f}s")
        else:
            log(f"  [FAIL] consecutive failures — stopping")
            break

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    max_amp_reached = max(r["amp"] for r in results)

    summary = {"test_id": "11.2-full-scale", "timestamp": datetime.now(timezone.utc).isoformat(), "total_cycles": total, "passed_cycles": passed, "failed_cycles": total - passed, "pass_rate": round(passed/total*100, 1) if total else 0, "max_amplification": max_amp_reached, "overall_pass": passed == total, "cycles": results}
    RESULTS_FILE.write_text(json.dumps(summary, indent=2, default=str))

    log(f"\n{'='*60}")
    log(f"RESULTS: {passed}/{total} cycles | Max amp: {max_amp_reached:.4f}x")
    log(f"Overall: {'ALL PASS' if summary['overall_pass'] else 'SOME FAIL'}")
    return summary

if __name__ == "__main__":
    run()
