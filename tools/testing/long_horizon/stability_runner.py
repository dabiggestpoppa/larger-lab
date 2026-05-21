"""
Phase 11.1 — Stability Runner Daemon
Orchestrates long-horizon tests and collects metrics.
"""

import time
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import threading

from .runtime_monitor import RuntimeMonitor
from .observer_stress import ObserverStressTest
from .continuity_checksum import ContinuityChecksumEngine


class StabilityRunner:
    """
    Main daemon for Phase 11.1 stability testing.
    Runs tests, collects metrics, and generates reports.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            "runtime_hours": 24,
            "metrics_interval": 60,
            "test_observer_count": 5
        }
        self.monitor = RuntimeMonitor()
        self.checksum_engine = ContinuityChecksumEngine()
        self.observer_test: Optional[ObserverStressTest] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
    def setup_observers(self):
        """Register observers for stress testing."""
        self.observer_test = ObserverStressTest(
            duration_hours=self.config["runtime_hours"]
        )
        for i in range(self.config["test_observer_count"]):
            self.observer_test.register_observer(f"observer_{i}")
            
    def run_runtime_test(self):
        """Run the runtime stability test."""
        print(f"Starting {self.config['runtime_hours']}h runtime test...")
        
        # Start monitoring
        self.monitor.start_monitoring(
            interval=self.config["metrics_interval"]
        )
        
        # Start observer stress test
        if self.observer_test:
            self.observer_test.run_test()
            
    def run_continuity_test(self):
        """Run continuity validation test."""
        print("Running continuity checksum test...")
        
        # Generate and save states periodically
        while self._running:
            # TODO: Integrate with actual observer states
            state = self.checksum_engine.generate_continuity_state(
                observer_id="test_observer",
                config={"role": "test"},
                tasks=["task1"],
                events=["event1"],
                goals=["goal1"],
                memories=[{"id": "mem1"}]
            )
            self.checksum_engine.save_state(state)
            time.sleep(300)  # Every 5 minutes
            
    def generate_report(self) -> Dict:
        """Generate final stability report."""
        return {
            "test": "Phase 11.1 Stability",
            "timestamp": datetime.now().isoformat(),
            "config": self.config,
            "status": "completed" if not self._running else "running"
        }
    
    def start(self):
        """Start the stability runner daemon."""
        self._running = True
        self.setup_observers()
        
        def run():
            self.run_runtime_test()
            
        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        print("Stability runner started.")
        
    def stop(self):
        """Stop the stability runner."""
        self._running = False
        self.monitor.stop_monitoring()
        if self._thread:
            self._thread.join(timeout=10)
        print("Stability runner stopped.")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 11 Stability Runner")
    parser.add_argument("--hours", type=int, default=24, help="Test duration in hours")
    parser.add_argument("--interval", type=int, default=60, help="Metrics interval in seconds")
    args = parser.parse_args()
    
    runner = StabilityRunner({
        "runtime_hours": args.hours,
        "metrics_interval": args.interval
    })
    
    try:
        runner.start()
        print(f"Running stability test for {args.hours} hours...")
        print("Press Ctrl+C to stop early.")
        while runner._running:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nStopping early...")
        runner.stop()
        
    report = runner.generate_report()
    print(f"\nFinal Report: {json.dumps(report, indent=2)}")


if __name__ == "__main__":
    main()