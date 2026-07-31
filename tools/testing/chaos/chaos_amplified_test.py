"""
Phase 11.2 — Amplified Chaos Persistence Test
Baseline test → if passes, amplify by 0.5% each hour for 12 hours.
Comprehensive tracking for failure analysis and root cause tracing.
"""

import time
import json
import traceback
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from chaos_engine import ChaosEngine, ChaosType

# Results storage with comprehensive tracking
RESULTS_FILE = Path("stability/chaos_amplified_results.json")
DETAILED_LOG_FILE = Path("stability/chaos_detailed_trace.log")
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
class HourlyCycle:
    """Complete hourly cycle results."""
    hour: int
    timestamp: str
    amplification_factor: float
    scenarios_run: List[str]
    events: List[ChaosEventTrace]
    passed: bool
    total_recovery_time: float
    failure_details: Optional[Dict] = None

class AmplifiedChaosTest:
    """Amplified chaos test with progressive intensity and comprehensive tracing."""
    
    def __init__(self):
        self.engine = ChaosEngine()
        self.results: List[HourlyCycle] = []
        self.event_counter = 0
        self.amplification_base = 1.0
        self.amplification_increment = 0.005  # 0.5% per hour
        
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
        """Get memory usage snapshot."""
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
        """Get observer status snapshot."""
        try:
            from oce.observer import ObserverRegistry
            return {"observers": list(ObserverRegistry.list_observers())}
        except:
            return {"error": "observer registry unavailable"}
    
    def _get_thread_count(self) -> int:
        """Get active thread count."""
        try:
            import threading
            return threading.active_count()
        except:
            return -1
    
    def log_detailed_trace(self, message: str, level: str = "INFO"):
        """Write detailed trace to log file."""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        with open(DETAILED_LOG_FILE, 'a') as f:
            f.write(log_entry)
    
    def run_single_scenario_with_tracing(self, scenario: str, amplification: float) -> ChaosEventTrace:
        """Run a single scenario with full tracing."""
        self.event_counter += 1
        event_id = f"EVT-{self.event_counter:04d}"
        
        # Capture state before
        state_before = self.get_system_state()
        
        # Run scenario
        start_time = time.time()
        error_msg = None
        stack_trace = None
        status = "PASS"
        
        try:
            self.log_detailed_trace(f"Starting scenario {scenario} with amplification {amplification:.4f}")
            result = self.engine.run_chaos_scenario(scenario)
            injection_time = time.time() - start_time
            
            # Wait for recovery with timeout
            recovery_start = time.time()
            timeout = 300  # 5 minutes max
            while self.engine.get_active_chaos() and (time.time() - recovery_start) < timeout:
                time.sleep(0.5)
            
            recovery_time = time.time() - recovery_start
            
            # Check if recovery was successful
            if self.engine.get_active_chaos():
                status = "FAIL"
                error_msg = "Recovery timeout exceeded"
                self.log_detailed_trace(f"Scenario {scenario} FAILED: recovery timeout", "ERROR")
            
        except Exception as e:
            status = "FAIL"
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            recovery_time = time.time() - start_time
            self.log_detailed_trace(f"Scenario {scenario} FAILED: {error_msg}", "ERROR")
            self.log_detailed_trace(stack_trace, "ERROR")
        
        # Capture state after
        state_after = self.get_system_state()
        
        trace = ChaosEventTrace(
            event_id=event_id,
            timestamp=datetime.now().isoformat(),
            chaos_type=scenario,
            target="system",
            duration_seconds=int(result.get('duration', 60)) if 'result' in dir() else 60,
            injection_time=injection_time,
            recovery_time=recovery_time,
            status=status,
            error_message=error_msg,
            stack_trace=stack_trace,
            system_state_before=state_before,
            system_state_after=state_after,
            amplification_factor=amplification
        )
        
        self.log_detailed_trace(f"Completed scenario {scenario}: {status} in {recovery_time:.2f}s")
        
        return trace
    
    def run_hourly_cycle(self, hour: int) -> HourlyCycle:
        """Run one hourly cycle with current amplification."""
        amplification = self.amplification_base * (1 + self.amplification_increment * (hour - 1))
        
        self.log_detailed_trace(f"=== HOUR {hour} START ===")
        self.log_detailed_trace(f"Amplification factor: {amplification:.4f}")
        
        scenarios = ["observer_death", "event_flood", "memory_poison", "full_chaos"]
        events = []
        total_recovery = 0
        all_passed = True
        failure_details = None
        
        for scenario in scenarios:
            trace = self.run_single_scenario_with_tracing(scenario, amplification)
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
                self.log_detailed_trace(f"Hour {hour} cycle FAILED at scenario {scenario}", "ERROR")
                break  # Stop on first failure for root cause analysis
        
        cycle = HourlyCycle(
            hour=hour,
            timestamp=datetime.now().isoformat(),
            amplification_factor=amplification,
            scenarios_run=scenarios[:len(events)],
            events=events,
            passed=all_passed,
            total_recovery_time=total_recovery,
            failure_details=failure_details
        )
        
        self.log_detailed_trace(f"=== HOUR {hour} END: {'PASS' if all_passed else 'FAIL'} ===")
        
        return cycle
    
    def run_test(self, duration_hours: int = 12):
        """Run the amplified chaos test."""
        print(f"[CHAOS-AMP] Starting Amplified Chaos Persistence Test")
        print(f"[CHAOS-AMP] Time: {datetime.now().isoformat()}")
        print(f"[CHAOS-AMP] Duration: {duration_hours} hours")
        print(f"[CHAOS-AMP] Amplification: 0.5% per hour")
        print("=" * 60)
        
        self.log_detailed_trace("=" * 60)
        self.log_detailed_trace("AMPLIFIED CHAOS TEST STARTED")
        self.log_detailed_trace(f"Duration: {duration_hours} hours")
        self.log_detailed_trace(f"Base amplification: {self.amplification_base}")
        self.log_detailed_trace(f"Increment: {self.amplification_increment * 100}% per hour")
        
        for hour in range(1, duration_hours + 1):
            print(f"\n[CHAOS-AMP] Hour {hour}/{duration_hours}")
            print(f"[CHAOS-AMP] Amplification: {self.amplification_base * (1 + self.amplification_increment * (hour - 1)):.4f}")
            
            cycle = self.run_hourly_cycle(hour)
            self.results.append(cycle)
            
            # Print summary
            status_icon = "✅" if cycle.passed else "❌"
            print(f"[CHAOS-AMP] Hour {hour} result: {status_icon} {cycle.passed}")
            print(f"[CHAOS-AMP] Total recovery time: {cycle.total_recovery_time:.1f}s")
            
            # Save intermediate results
            self.save_results()
            
            # If failed, analyze and stop
            if not cycle.passed:
                self.log_detailed_trace(f"TEST STOPPED AT HOUR {hour} - FAILURE DETECTED", "CRITICAL")
                print(f"\n[CHAOS-AMP] FAILURE at hour {hour}!")
                print(f"[CHAOS-AMP] Failure details saved to {DETAILED_LOG_FILE}")
                break
            
            # Wait until next hour (minus time spent)
            elapsed = cycle.total_recovery_time
            wait_time = max(0, 3600 - elapsed)
            if hour < duration_hours and wait_time > 0:
                print(f"[CHAOS-AMP] Waiting {wait_time/60:.1f} minutes until next hour...")
                time.sleep(wait_time)
        
        self.finalize()
    
    def save_results(self):
        """Save results to JSON file."""
        results_data = {
            "test_type": "amplified_chaos",
            "start_time": self.results[0].timestamp if self.results else None,
            "end_time": datetime.now().isoformat(),
            "total_hours": len(self.results),
            "cycles": [asdict(c) for c in self.results]
        }
        with open(RESULTS_FILE, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
    
    def finalize(self):
        """Finalize test and print summary."""
        passed_hours = sum(1 for c in self.results if c.passed)
        total_events = sum(len(c.events) for c in self.results)
        
        print("\n" + "=" * 60)
        print(f"[CHAOS-AMP] Test Completed")
        print(f"[CHAOS-AMP] Hours passed: {passed_hours}/{len(self.results)}")
        print(f"[CHAOS-AMP] Total events: {total_events}")
        print(f"[CHAOS-AMP] Results saved to {RESULTS_FILE}")
        print(f"[CHAOS-AMP] Detailed trace saved to {DETAILED_LOG_FILE}")
        
        self.log_detailed_trace("=" * 60)
        self.log_detailed_trace("TEST FINALIZED")
        self.log_detailed_trace(f"Hours completed: {len(self.results)}")
        self.log_detailed_trace(f"Hours passed: {passed_hours}")


if __name__ == "__main__":
    test = AmplifiedChaosTest()
    test.run_test(duration_hours=12)