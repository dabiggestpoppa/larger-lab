"""
Phase 11.2 — Chaos Engine Long Duration Test
12-hour chaos test with periodic injections every hour.
"""

import time
import json
from datetime import datetime
from pathlib import Path
from chaos_engine import ChaosEngine

# Results storage
RESULTS_FILE = Path("stability/chaos_long_results.json")
RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

def run_12hr_chaos_test():
    """Run 12-hour chaos test with hourly injections."""
    engine = ChaosEngine()
    
    scenarios = ["observer_death", "event_flood", "memory_poison", "full_chaos"]
    results = []
    
    print(f"[CHAOS-12HR] Starting 12-hour chaos persistence test")
    print(f"[CHAOS-12HR] Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Run 12 cycles (hourly for 12 hours)
    for hour in range(1, 13):
        print(f"\n[CHAOS-12HR] Hour {hour}/12 - Running scenario cycle")
        
        # Run all 4 scenarios each hour
        for scenario in scenarios:
            print(f"[CHAOS-12HR]   Running: {scenario}")
            result = engine.run_chaos_scenario(scenario)
            
            # Wait for recovery
            recovery_start = time.time()
            for _ in range(180):  # Wait up to 3 minutes
                if not engine.get_active_chaos():
                    break
                time.sleep(1)
            
            recovery_time = time.time() - recovery_start
            
            scenario_result = {
                "hour": hour,
                "scenario": scenario,
                "timestamp": datetime.now().isoformat(),
                "events_injected": result['events_injected'],
                "recovery_time_seconds": round(recovery_time, 2),
                "status": "PASS" if recovery_time < 180 else "FAIL"
            }
            results.append(scenario_result)
            print(f"[CHAOS-12HR]   Result: {scenario_result['status']} ({recovery_time:.1f}s)")
        
        # Wait until next hour (minus the time spent on scenarios)
        elapsed = time.time() - recovery_start
        wait_time = max(0, 3600 - elapsed)  # 1 hour - elapsed time
        if wait_time > 0:
            print(f"[CHAOS-12HR] Waiting {wait_time/60:.1f} minutes until next hour...")
            time.sleep(wait_time)
    
    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"[CHAOS-12HR] Completed 12-hour test")
    print(f"[CHAOS-12HR] Results saved to {RESULTS_FILE}")
    
    # Summary
    passed = sum(1 for r in results if r['status'] == 'PASS')
    print(f"[CHAOS-12HR] Summary: {passed}/{len(results)} scenarios passed")
    
    return results

if __name__ == "__main__":
    run_12hr_chaos_test()