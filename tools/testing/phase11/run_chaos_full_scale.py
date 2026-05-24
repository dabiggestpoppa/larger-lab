"""
Phase 11.2 — Full Scale Chaos Test
===================================
Runs the real chaos engine with amplification scaling.
Target: 5x normal chaos (like the original v2 test)
Increment: 14.3% per cycle
Max: 5x cap
Scenarios: observer_death, event_flood, memory_poison, full_chaos
"""
import time, json, traceback
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import sys; sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.testing.chaos.chaos_engine import ChaosEngine

RESULTS_FILE = Path("stability/chaos_full_scale_results.json")
TRACE_FILE = Path("stability/chaos_full_scale_trace.log")
RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

@dataclass
class CycleResult:
    cycle: int
    timestamp: str
    amplification: float
    scenarios_run: List[str]
    events_count: int
    passed: bool
    total_recovery_time: float
    details: List[Dict]

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(TRACE_FILE, 'a', encoding='utf-8') as f:
        f.write(line + "\n")

def run_full_scale_chaos():
    engine = ChaosEngine()
    results: List[CycleResult] = []

    # Test parameters — same as original v2
    amplification = 1.0
    cycle_increment = 0.143  # 14.3% per cycle
    max_amplification = 5.0
    max_cycles = 30  # Safety cap
    scenarios = ["observer_death", "event_flood", "memory_poison", "full_chaos"]

    log("=" * 60)
    log("PHASE 11.2 — FULL SCALE CHAOS TEST")
    log(f"Target: {max_amplification}x normal chaos")
    log(f"Increment: {cycle_increment*100:.1f}% per cycle")
    log(f"Max cycles: {max_cycles}")
    log(f"Scenarios per cycle: {scenarios}")
    log("=" * 60)

    cycle = 0
    consecutive_failures = 0
    max_consecutive_failures = 3

    while amplification <= max_amplification and cycle < max_cycles:
        cycle += 1
        amplification = min(1.0 + (cycle * cycle_increment), max_amplification)

        log(f"\n{'='*60}")
        log(f"CYCLE {cycle} | Amplification: {amplification:.4f}x")
        log(f"{'='*60}")

        cycle_events = 0
        cycle_recovery_time = 0
        all_passed = True
        scenario_details = []

        for scenario in scenarios:
            log(f"  Running: {scenario} (amp={amplification:.4f}x)")
            try:
                result = engine.run_chaos_scenario(scenario, amplification=amplification)
                events_injected = result.get("events_injected", 0)
                cycle_events += events_injected

                # Wait for recovery — scale timeout with amplification
                base_timeout = 30 + (amplification - 1.0) * 60  # 30s base + 60s per amp
                timeout = min(base_timeout, 300)  # Max 5 min

                recovery_start = time.time()
                recovered = False
                for _ in range(int(timeout)):
                    time.sleep(1)
                    if not engine.get_active_chaos():
                        recovered = True
                        break

                recovery_time = time.time() - recovery_start
                cycle_recovery_time += recovery_time

                if not recovered:
                    log(f"    [WARN] Recovery timeout ({timeout:.0f}s) — forcing clear")
                    engine.active_events.clear()
                    all_passed = False

                detail = {
                    "scenario": scenario,
                    "events_injected": events_injected,
                    "recovered": recovered,
                    "recovery_time": round(recovery_time, 2),
                    "timeout": timeout,
                }
                scenario_details.append(detail)

                status = "PASS" if recovered else "FAIL"
                log(f"    [{status}] {events_injected} events, recovery={recovery_time:.1f}s")

            except Exception as e:
                log(f"    [ERROR] {e}")
                all_passed = False
                scenario_details.append({
                    "scenario": scenario,
                    "error": str(e),
                    "recovered": False,
                })

        cycle_result = CycleResult(
            cycle=cycle,
            timestamp=datetime.now(timezone.utc).isoformat(),
            amplification=round(amplification, 4),
            scenarios_run=scenarios,
            events_count=cycle_events,
            passed=all_passed,
            total_recovery_time=round(cycle_recovery_time, 2),
            details=scenario_details,
        )
        results.append(cycle_result)

        if all_passed:
            consecutive_failures = 0
            log(f"  [PASS] CYCLE {cycle} — {cycle_events} events, {cycle_recovery_time:.1f}s total recovery")
        else:
            consecutive_failures += 1
            log(f"  [FAIL] CYCLE {cycle} — consecutive failures: {consecutive_failures}")
            if consecutive_failures >= max_consecutive_failures:
                log(f"\n  ⚠ {max_consecutive_failures} consecutive failures — stopping test")
                break

    # Summary
    total_cycles = len(results)
    passed_cycles = sum(1 for r in results if r.passed)
    failed_cycles = total_cycles - passed_cycles
    max_amp_reached = max(r.amplification for r in results)
    total_events = sum(r.events_count for r in results)

    summary = {
        "test_id": "11.2-full-scale",
        "test_name": "chaos_full_scale",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_cycles": total_cycles,
        "passed_cycles": passed_cycles,
        "failed_cycles": failed_cycles,
        "pass_rate": round(passed_cycles / total_cycles * 100, 1) if total_cycles > 0 else 0,
        "max_amplification": max_amp_reached,
        "total_events_injected": total_events,
        "overall_pass": passed_cycles == total_cycles,
        "cycles": [asdict(r) for r in results],
    }

    with open(RESULTS_FILE, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    log(f"\n{'='*60}")
    log(f"FINAL RESULTS")
    log(f"{'='*60}")
    log(f"Total cycles: {total_cycles}")
    log(f"Passed: {passed_cycles}")
    log(f"Failed: {failed_cycles}")
    log(f"Pass rate: {summary['pass_rate']}%")
    log(f"Max amplification: {max_amp_reached:.4f}x")
    log(f"Total events injected: {total_events}")
    log(f"Overall: {'ALL PASS' if summary['overall_pass'] else 'SOME FAIL'}")
    log(f"Results: {RESULTS_FILE}")
    log(f"Trace: {TRACE_FILE}")

    return summary

if __name__ == "__main__":
    run_full_scale_chaos()
