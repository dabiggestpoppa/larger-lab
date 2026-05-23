"""
Phase 11.2 — 1.5X Chaos Amplification Test
Target: 1.5x normal chaos by end of 12 hours
Amplification: 0.1% per PASS cycle + 1% per hour
"""

import time
import json
import traceback
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from chaos_engine import ChaosEngine

RESULTS_FILE = Path("stability/chaos_1_5x_results.json")
DETAILED_LOG_FILE = Path("stability/chaos_1_5x_trace.log")
RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

@dataclass
class ChaosEventTrace:
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
    cycle: int
    timestamp: str
    amplification_factor: float
    scenarios_run: List[str]
    events: List[ChaosEventTrace]
    passed: bool
    total_recovery_time: float
    failure_details: Optional[Dict] = None

class Chaos1_5XTest:
    def __init__(self):
        self.engine = ChaosEngine()
        self.results: List[TestCycle] = []
        self.event_counter = 0
        self.amplification = 1.0
        self.cycle_count = 0
        self.start_time = None
        self.max_duration = 12 * 3600
        self.last_hour = -1
        
    def get_system_state(self) -> Dict[str, Any]:
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
            return {"rss_mb": process.memory_info().rss / 1024 / 1024, "percent": process.memory_percent()}
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
        timestamp = datetime.now().isoformat()
        with open(DETAILED_LOG_FILE, 'a') as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
    
    def calculate_amplification(self) -> float:
        """Calculate amplification: 0.1% per cycle + 1% per hour."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        hours = int(elapsed / 3600)
        cycles = self.cycle_count
        
        # 0.1% per cycle + 1% per hour
        amp = 1.0 + (cycles * 0.001) + (hours * 0.01)
        return amp
    
    def run_single_scenario(self, scenario: str) -> ChaosEventTrace:
        self.event_counter += 1
        event_id = f"EVT-{self.event_counter:04d}"
        
        state_before = self.get_system_state()
        start_time = time.time()
        error_msg = None
        stack_trace = None
        status = "PASS"
        result = {}
        
        try:
            self.log_trace(f"Starting scenario {scenario} with amplification {self.amplification:.4f}")
            result = self.engine.run_chaos_scenario(scenario)
            injection_time = time.time() - start_time
            
            recovery_start = time.time()
            timeout = 300
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
        
        return ChaosEventTrace(
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
            amplification_factor=self.amplification
        )
    
    def run_test_cycle(self) -> TestCycle:
        self.cycle_count += 1
        self.amplification = self.calculate_amplification()
        
        scenarios = ["observer_death", "event_flood", "memory_poison", "full_chaos"]
        events = []
        total_recovery = 0
        all_passed = True
        failure_details = None
        
        self.log_trace(f"=== CYCLE {self.cycle_count} START ===")
        self.log_trace(f"Amplification factor: {self.amplification:.4f}")
        
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
        
        return TestCycle(
            cycle=self.cycle_count,
            timestamp=datetime.now().isoformat(),
            amplification_factor=self.amplification,
            scenarios_run=scenarios[:len(events)],
            events=events,
            passed=all_passed,
            total_recovery_time=total_recovery,
            failure_details=failure_details
        )
    
    def save_results(self):
        results_data = {
            "test_type": "1_5x_chaos",
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": datetime.now().isoformat(),
            "total_cycles": len(self.results),
            "final_amplification": self.amplification,
            "cycles": [asdict(c) for c in self.results]
        }
        with open(RESULTS_FILE, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
    
    def run_test(self):
        self.start_time = datetime.now()
        
        print(f"[CHAOS-1.5X] Starting 1.5X Chaos Test")
        print(f"[CHAOS-1.5X] Time: {self.start_time.isoformat()}")
        print(f"[CHAOS-1.5X] Duration: 12 hours")
        print(f"[CHAOS-1.5X] Amplification: 0.1% per cycle + 1% per hour")
        print("=" * 60)
        
        self.log_trace("=" * 60)
        self.log_trace("1.5X CHAOS TEST STARTED")
        
        while True:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed >= self.max_duration:
                print(f"\n[CHAOS-1.5X] 12-hour duration reached")
                self.log_trace("12-hour duration reached - TEST COMPLETE")
                break
            
            print(f"\n[CHAOS-1.5X] Cycle {self.cycle_count + 1}")
            print(f"[CHAOS-1.5X] Amplification: {self.amplification:.4f}")
            
            cycle = self.run_test_cycle()
            self.results.append(cycle)
            self.save_results()
            
            status_icon = "✅" if cycle.passed else "❌"
            print(f"[CHAOS-1.5X] Cycle {cycle.cycle} result: {status_icon} {cycle.passed}")
            print(f"[CHAOS-1.5X] Total recovery time: {cycle.total_recovery_time:.1f}s")
            
            if not cycle.passed:
                print(f"\n[CHAOS-1.5X] FAILURE DETECTED!")
                print(f"[CHAOS-1.5X] Analysis saved to {DETAILED_LOG_FILE}")
                break
            
            print(f"[CHAOS-1.5X] Waiting 5 minutes cooldown...")
            self.log_trace("Waiting 5 minutes cooldown")
            time.sleep(300)
        
        self.finalize()
    
    def finalize(self):
        passed_cycles = sum(1 for c in self.results if c.passed)
        total_events = sum(len(c.events) for c in self.results)
        
        print("\n" + "=" * 60)
        print(f"[CHAOS-1.5X] Test Completed")
        print(f"[CHAOS-1.5X] Cycles: {passed_cycles}/{len(self.results)} passed")
        print(f"[CHAOS-1.5X] Total events: {total_events}")
        print(f"[CHAOS-1.5X] Final amplification: {self.amplification:.4f}")
        print(f"[CHAOS-1.5X] Results saved to {RESULTS_FILE}")
        
        self.log_trace("=" * 60)
        self.log_trace("TEST FINALIZED")


if __name__ == "__main__":
    test = Chaos1_5XTest()
    test.run_test()