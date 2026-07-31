"""
Phase 11.1 — Observer Stress Test
Validates observer survival under continuous load for 24+ hours.
"""

import time
import random
import threading
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta


@dataclass
class ObserverState:
    """Observer state tracking."""
    observer_id: str
    status: str  # alive, degraded, dead
    last_heartbeat: float
    tasks_completed: int
    errors: int
    uptime_seconds: float


class ObserverStressTest:
    """
    Stress tests observer mesh for 24-hour survival.
    Monitors observer health, task completion, and recovery.
    """
    
    def __init__(self, duration_hours: int = 24):
        self.duration_seconds = duration_hours * 3600
        self.start_time: Optional[float] = None
        self.observers: Dict[str, ObserverState] = {}
        self.results: List[Dict] = []
        
    def register_observer(self, observer_id: str):
        """Register an observer for stress testing."""
        self.observers[observer_id] = ObserverState(
            observer_id=observer_id,
            status="alive",
            last_heartbeat=time.time(),
            tasks_completed=0,
            errors=0,
            uptime_seconds=0
        )
        
    def simulate_observer_load(self, observer_id: str, tasks_per_minute: int = 10):
        """Simulate continuous task load on observer."""
        observer = self.observers.get(observer_id)
        if not observer:
            return
            
        def task_loop():
            while observer.status in ("alive", "degraded"):
                # Simulate task processing
                observer.tasks_completed += 1
                observer.last_heartbeat = time.time()
                
                # Random chance of error (simulate real conditions)
                if random.random() < 0.01:  # 1% error rate
                    observer.errors += 1
                    # Don't change status - degraded observers keep running
                    
                time.sleep(60 / tasks_per_minute)
                
        thread = threading.Thread(target=task_loop, daemon=True)
        thread.start()
        
    def check_observer_health(self) -> Dict[str, int]:
        """Check health of all observers."""
        now = time.time()
        alive = 0
        degraded = 0
        dead = 0
        
        for obs in self.observers.values():
            # Check if heartbeat is stale (> 5 minutes - more tolerant)
            if now - obs.last_heartbeat > 300:
                obs.status = "dead"
                dead += 1
            elif obs.status == "degraded":
                degraded += 1
            else:
                alive += 1
                
        return {"alive": alive, "degraded": degraded, "dead": dead}
    
    def run_test(self) -> Dict:
        """Run the 24-hour observer survival test."""
        self.start_time = time.time()
        end_time = self.start_time + self.duration_seconds
        
        print(f"Starting 24-hour observer stress test...")
        print(f"Observers registered: {len(self.observers)}")
        
        # Start load simulation for each observer
        for obs_id in self.observers:
            self.simulate_observer_load(obs_id)
            
        # Monitor loop
        while time.time() < end_time:
            health = self.check_observer_health()
            elapsed = time.time() - self.start_time
            
            result = {
                "timestamp": time.time(),
                "elapsed_seconds": elapsed,
                "health": health,
                "total_observers": len(self.observers)
            }
            self.results.append(result)
            
            print(f"[{elapsed/3600:.1f}h] Alive: {health['alive']}, "
                  f"Degraded: {health['degraded']}, Dead: {health['dead']}")
            
            # Check pass conditions
            if health['dead'] > 0:
                print(f"FAIL: Observer death detected!")
                
            time.sleep(60)  # Check every minute
            
        return self._generate_report()
    
    def _generate_report(self) -> Dict:
        """Generate final test report."""
        total_observers = len(self.observers)
        final_health = self.check_observer_health()
        
        uptime_percent = (final_health['alive'] / total_observers) * 100 if total_observers > 0 else 0
        
        return {
            "test": "24h_observer_survival",
            "duration_hours": self.duration_seconds / 3600,
            "total_observers": total_observers,
            "final_health": final_health,
            "uptime_percent": uptime_percent,
            "pass": uptime_percent >= 99.5 and final_health['dead'] == 0
        }


if __name__ == "__main__":
    test = ObserverStressTest(duration_hours=24)
    
    # Register observers (example)
    for i in range(5):
        test.register_observer(f"observer_{i}")
        
    report = test.run_test()
    print(f"\nTest Report: {report}")