"""
Phase 11.2 — Chaos Engine Runner
Autopilot script for running chaos scenarios and monitoring recovery.
"""

import time
import json
from datetime import datetime
from pathlib import Path
from chaos_engine import ChaosEngine

# Results storage
RESULTS_FILE = Path("stability/chaos_results.json")
RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

def run_chaos_autopilot():
    """Run chaos scenarios autonomously with monitoring."""
    engine = ChaosEngine()
    
    scenarios = ["observer_death", "event_flood", "memory_poison", "full_chaos"]
    results = []
    
    print(f"[CHAOS-AUTOPILOT] Starting Phase 11.2 Chaos Engine tests")
    print(f"[CHAOS-AUTOPILOT] Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    for scenario in scenarios:
        print(f"\n[CHAOS-AUTOPILOT] Running scenario: {scenario}")
        
        # Run the scenario
        result = engine.run_chaos_scenario(scenario)
        print(f"[CHAOS-AUTOPILOT] Events injected: {result['events_injected']}")
        
        # Monitor recovery
        recovery_start = time.time()
        recovered_count = 0
        
        for _ in range(180):  # Wait up to 3 minutes for recovery
            active = engine.get_active_chaos()
            if not active:
                recovered_count = len(result['event_ids'])
                break
            time.sleep(1)
        
        recovery_time = time.time() - recovery_start
        
        scenario_result = {
            "scenario": scenario,
            "timestamp": datetime.now().isoformat(),
            "events_injected": result['events_injected'],
            "recovered": recovered_count,
            "recovery_time_seconds": round(recovery_time, 2),
            "status": "PASS" if recovered_count == result['events_injected'] else "FAIL"
        }
        
        results.append(scenario_result)
        print(f"[CHAOS-AUTOPILOT] Result: {scenario_result['status']} (recovery: {recovery_time:.1f}s)")
        
        # Wait between scenarios
        time.sleep(10)
    
    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"[CHAOS-AUTOPILOT] Completed all scenarios")
    print(f"[CHAOS-AUTOPILOT] Results saved to {RESULTS_FILE}")
    
    # Summary
    passed = sum(1 for r in results if r['status'] == 'PASS')
    print(f"[CHAOS-AUTOPILOT] Summary: {passed}/{len(results)} scenarios passed")
    
    return results

if __name__ == "__main__":
    run_chaos_autopilot()