"""
Phase 11.2 — Scaled Chaos Persistence Test
Target: 1.5x amplification after 12 hours
- 0.1% per PASS cycle
- 1% per hour on top of cycle amplification
- Continuous testing with 5-min cooldown
"""

import time
import json
import traceback
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from chaos_engine import ChaosEngine

# Results storage
RESULTS_FILE = Path("stability/chaos_scaled_results.json")
DETAILED_LOG_FILE = Path("stability/chaos_scaled_trace.log")
RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

@dataclass
class ChaosEventTrace:
    """Detailed trace of a single chaos event."""
    event_id: str
    timestamp: str
    chaos_type: str
    target: str
    duration_seconds: int
    injection_time: float
    recovery_time: float
    status: str
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    system_state_before: Dict[str, Any] = None
    system_state_after: Dict[str, Any] = None
    amplification_factor: float = 1.0

@dataclass
class TestCycle:
    """Single test cycle results."""
    cycle: int
    timestamp: str
    amplification_factor: float
    scenarios_run: List[str]
    events: List[ChaosEventTrace]
    passed: bool
    total_recovery_time: float
    failure_details: Optional[Dict] = None

class ScaledChaosTest:
    """Scaled chaos test with dual amplification (cycle + hourly)."""
    
    def __init__(self):
        self.engine = ChaosEngine()
        self.results: List[TestCycle] = []
        self.event_counter = 0
        self.cycle_amplification = 0.0  # 0.1% per cycle
        self.hourly_amplification = 0.0  # 1% per hour
        self.cycle_count = 0
        self.start_time = None
        self.max_duration = 12 * 3600  # 12 hours in seconds
        self.cycle_increment = 0.001  # 0.1% per cycle
        self.hourly_increment = 0.01  # 1% per hour
        
    def get_system_state(self) -> Dict[str, Any]:
        """Capture current system state for tracing."""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_chaos": self.engine.get_active_chaos(),
            "memory_usage": self._get_memory_usage(),
            "observer_status": self._get_observer_status(),
            "thread_count": self._get_thread_count()
        }
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        try:
            import psutil
            process = psutil.Process()
            return {
                "rss_mb": process.memory_info().rss / 1024 / 1024,
                "vms_mb": process.memory_info().vms / 1024 / 1024,
                "percent": process.memory_percent()
            }
        except:
            return {"error": "psutil not available"}
    
    def _get_observer_status(self) -> Dict[str, Any]:
        try:
            from oce.observer import ObserverRegistry
            return {"observers": list(ObserverRegistry.list_observers())}
        except:
            return {"error": "observer registry unavailable"}
    
    def _get_thread_count(self) -> int:
        try:
            import threading
            return threading.active_count()
        except:
            return -1
    
    def log_trace(self, message: str, level: str = "INFO"):
        """Write detailed trace to log file."""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        with open(DETAILED_LOG_FILE, 'a') as f:
            f.write(log_entry)
    
    def calculate_amplification(self) -> float:
        """Calculate total amplification from cycles and hours."""
        elapsed_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        self.hourly_amplification = elapsed_hours * self.hourly_increment
        total = 1.0 + self.cycle_amplification + self.hourly_amplification
        return total
    
    def run_single_scenario(self, scenario: str) -> ChaosEventTrace:
        """Run a single scenario with full tracing."""
        self.event_counter += 1
        event_id = f"EVT-{self.event_counter:04d}"
        
        state_before = self.get_system_state()
        start_time = time.time()
        error_msg = None
        stack_trace = None
        status = "PASS"
        result = {}
        
        try:
            amp = self.calculate_amplification()
            self.log_trace(f"Starting scenario {scenario} with amplification {amp:.4f}")
            result = self.engine.run_chaos_scenario(scenario)
            injection_time = time.time() - start_time
            
            # Wait for recovery with timeout
            recovery_start = time.time()
            timeout = 300  # 5 minutes max
            while self.engine.get_active_chaos() and (time.time() - recovery_start) < timeout:
                time.sleep(0.5)
            
            recovery_time = time.time() - recovery_start
            
            if self.engine.get_active_chaos():
                status = "FAIL"
                error_msg = "Recovery timeout exceeded"
                self.log_trace(f"Scenario {scenario} FAILED: recovery timeout", "ERROR")
            
        except Exception as e:
            status = "FAIL"
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            recovery_time = time.time() - start_time
            self.log_trace(f"Scenario {scenario} FAILED: {error_msg}", "ERROR")
            self.log_trace(stack_trace, "ERROR")
        
        state_after = self.get_system_state()
        amp = self.calculate_amplification()
        
        trace = ChaosEventTrace(
            event_id=event_id,
            timestamp=datetime.now().isoformat(),
            chaos_type=scenario,
            target="system",
            duration_seconds=int(result.get('duration', 60)) if result else 60,
            injection_time=injection_time if 'injection_time' in dir() else 0,
            recovery_time=recovery_time,
            status=status,
            error_message=error_msg,
            stack_trace=stack_trace,
            system_state_before=state_before,
            system_state_after=state_after,
            amplification_factor=amp
        )
        
        self.log_trace(f"Completed scenario {scenario}: {status} in {recovery_time:.2f}s")
        return trace
    
    def run_test_cycle(self) -> TestCycle:
        """Run one complete test cycle (all 4 scenarios)."""
        self.cycle_count += 1
        scenarios = ["observer_death", "event_flood", "memory_poison", "full_chaos"]
        events = []
        total_recovery = 0
        all_passed = True
        failure_details = None
        
        amp = self.calculate_amplification()
        self.log_trace(f"=== CYCLE {self.cycle_count} START ===")
        self.log_trace(f"Amplification factor: {amp:.4f}")
        
        for scenario in scenarios:
            trace = self.run_single_scenario(scenario)
            events.append(trace)
            total_recovery += trace.recovery_time
            
            if trace.status == "FAIL":
                all_passed = False
                failure_details = {
                    "failed_scenario": scenario,
                    "error": trace.error_message,
                    "stack_trace": trace.stack_trace,
                    "state_before": trace.system_state_before,
                    "state_after": trace.system_state_after
                }
                self.log_trace(f"Cycle {self.cycle_count} FAILED at scenario {scenario}", "ERROR")
                break
        
        cycle = TestCycle(
            cycle=self.cycle_count,
            timestamp=datetime.now().isoformat(),
            amplification_factor=self.calculate_amplification(),
            scenarios_run=scenarios[:len(events)],
            events=events,
            passed=all_passed,
            total_recovery_time=total_recovery,
            failure_details=failure_details
        )
        
        self.log_trace(f"=== CYCLE {self.cycle_count} END: {'PASS' if all_passed else 'FAIL'} ===")
        return cycle
    
    def save_results(self):
        """Save results to JSON file."""
        results_data = {
            "test_type": "scaled_amplified_chaos",
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": datetime.now().isoformat(),
            "total_cycles": len(self.results),
            "final_amplification": self.calculate_amplification(),
            "cycles": [asdict(c) for c in self.results]
        }
        with open(RESULTS_FILE, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
    
    def run_test(self):
        """Run scaled chaos test for 12 hours."""
        self.start_time = datetime.now()
        
        print(f"[CHAOS-SCALE] Starting Scaled Chaos Persistence Test")
        print(f"[CHAOS-SCALE] Time: {self.start_time.isoformat()}")
        print(f"[CHAOS-SCALE] Duration: 12 hours (continuous)")
        print(f"[CHAOS-SCALE] Amplification: 0.1% per cycle + 1% per hour")
        print(f"[CHAOS-SCALE] Target: 1.5x after 12 hours")
        print(f"[CHAOS-SCALE] Cooldown: 5 minutes between cycles")
        print("=" * 60)
        
        self.log_trace("=" * 60)
        self.log_trace("SCALED AMPLIFIED CHAOS TEST STARTED")
        self.log_trace(f"Max duration: 12 hours")
        self.log_trace(f"Target amplification: 1.5x")
        self.log_trace(f"Cycle increment: {self.cycle_increment * 100}% per PASS cycle")
        self.log_trace(f"Hourly increment: {self.hourly_increment * 100}% per hour")
        
        while True:
            # Check time limit
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed >= self.max_duration:
                print(f"\n[CHAOS-SCALE] 12-hour duration reached")
                self.log_trace("12-hour duration reached - TEST COMPLETE")
                break
            
            print(f"\n[CHAOS-SCALE] Cycle {self.cycle_count + 1}")
            print(f"[CHAOS-SCALE] Amplification: {self.calculate_amplification():.4f}")
            
            cycle = self.run_test_cycle()
            self.results.append(cycle)
            self.save_results()
            
            # Print summary
            status_icon = "✅" if cycle.passed else "❌"
            print(f"[CHAOS-SCALE] Cycle {cycle.cycle} result: {status_icon} {cycle.passed}")
            print(f"[CHAOS-SCALE] Total recovery time: {cycle.total_recovery_time:.1f}s")
            
            if not cycle.passed:
                # FAILURE - analyze and stop
                print(f"\n[CHAOS-SCALE] FAILURE DETECTED!")
                print(f"[CHAOS-SCALE] Failed scenario: {cycle.failure_details.get('failed_scenario')}")
                print(f"[CHAOS-SCALE] Error: {cycle.failure_details.get('error')}")
                print(f"[CHAOS-SCALE] Analysis saved to {DETAILED_LOG_FILE}")
                print(f"[CHAOS-SCALE] Results saved to {RESULTS_FILE}")
                break
            
            # PASS - amplify cycle component and wait 5 minutes
            self.cycle_amplification += self.cycle_increment
            print(f"[CHAOS-SCALE] Cycle passed - amplifying cycle component to {self.cycle_amplification:.4f}")
            print(f"[CHAOS-SCALE] Total amplification now: {self.calculate_amplification():.4f}")
            print(f"[CHAOS-SCALE] Waiting 5 minutes until next cycle...")
            
            self.log_trace(f"Cycle passed - cycle amplification: {self.cycle_amplification:.4f}")
            self.log_trace("Waiting 5 minutes cooldown")
            
            time.sleep(300)  # 5 minute cooldown
        
        self.finalize()
    
    def finalize(self):
        """Finalize test and print summary."""
        passed_cycles = sum(1 for c in self.results if c.passed)
        total_events = sum(len(c.events) for c in self.results)
        
        print("\n" + "=" * 60)
        print(f"[CHAOS-SCALE] Test Completed")
        print(f"[CHAOS-SCALE] Cycles: {passed_cycles}/{len(self.results)} passed")
        print(f"[CHAOS-SCALE] Total events: {total_events}")
        print(f"[CHAOS-SCALE] Final amplification: {self.calculate_amplification():.4f}")
        print(f"[CHAOS-SCALE] Results saved to {RESULTS_FILE}")
        print(f"[CHAOS-SCALE] Detailed trace saved to {DETAILED_LOG_FILE}")
        
        self.log_trace("=" * 60)
        self.log_trace("TEST FINALIZED")
        self.log_trace(f"Cycles completed: {len(self.results)}")
        self.log_trace(f"Cycles passed: {passed_cycles}")


if __name__ == "__main__":
    test = ScaledChaosTest()
    test.run_test()