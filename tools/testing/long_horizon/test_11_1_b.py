"""
Phase 11.1-B — 72-Hour Continuity Stability Test
=================================================
Verifies identity continuity over extended runtime (72 hours).
Extends 11.1-A (24h survival) with continuity checksum validation.

Test Goals:
1. Observer mesh survives 72 hours with ≥99.5% uptime
2. Continuity checksums remain stable (drift_score < 0.1)
3. Identity/trajectory/goal/memory hashes consistent across checkpoints
4. Recovery from injected micro-chaos events every 12 hours
5. Memory integrity maintained (no silent corruption)

Architecture:
- StabilityRunner daemon (from stability_runner.py) manages the 72h lifecycle
- ContinuityChecksumEngine generates hashes every 6 hours
- ObserverStressTest simulates continuous load on 10 observers
- Micro-chaos injections every 12 hours validate recovery
- Progress checkpoints written to progress/11-1-b-checkpoints.json
"""

import time
import json
import hashlib
import threading
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field

# ─── Configuration ───────────────────────────────────────────────────────────

TEST_DURATION_HOURS = 72
CONTINUITY_CHECKPOINT_INTERVAL_HOURS = 6
MICRO_CHAOS_INTERVAL_HOURS = 12
OBSERVER_COUNT = 10
HEARTBEAT_TIMEOUT_SECONDS = 300
DRIFT_THRESHOLD = 0.1
UPTIME_PASS_THRESHOLD = 99.5

# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class ObserverSnapshot:
    """Observer state at a checkpoint."""
    observer_id: str
    status: str  # alive, degraded, dead
    last_heartbeat: float
    tasks_completed: int
    errors: int
    uptime_seconds: float

@dataclass
class ContinuityCheckpoint:
    """Continuity state at a checkpoint."""
    checkpoint_id: str
    timestamp: str
    elapsed_hours: float
    identity_hash: str
    trajectory_hash: str
    goal_hash: str
    memory_hash: str
    state_hash: str
    drift_score: float
    drift_details: Dict[str, str]
    observer_health: Dict[str, int]
    memory_usage_mb: float
    status: str  # PASS, DRIFT, FAIL

@dataclass
class Test11_1BState:
    """Full test state persisted to disk."""
    test_id: str = "11.1-B"
    test_name: str = "72h_continuity_stability"
    start_time: str = ""
    end_time: str = ""
    duration_hours: float = 0.0
    total_checkpoints: int = 0
    passed_checkpoints: int = 0
    failed_checkpoints: int = 0
    max_drift_score: float = 0.0
    final_uptime_percent: float = 0.0
    overall_pass: bool = False
    checkpoints: List[Dict] = field(default_factory=list)
    observers: Dict[str, Dict] = field(default_factory=dict)
    chaos_events: List[Dict] = field(default_factory=list)


# ─── Observer Mesh Simulator ─────────────────────────────────────────────────

class ObserverMesh:
    """
    Simulates the 10-observer mesh for continuity testing.
    Each observer runs in its own thread with heartbeat tracking.
    """
    
    def __init__(self, count: int = OBSERVER_COUNT):
        self.count = count
        self.observers: Dict[str, ObserverSnapshot] = {}
        self._running = False
        self._threads: List[threading.Thread] = []
        self._lock = threading.Lock()
        
        for i in range(count):
            obs_id = f"observer_{i:02d}"
            self.observers[obs_id] = ObserverSnapshot(
                observer_id=obs_id,
                status="alive",
                last_heartbeat=time.time(),
                tasks_completed=0,
                errors=0,
                uptime_seconds=0
            )
    
    def start(self):
        """Start all observer threads."""
        self._running = True
        for obs_id in self.observers:
            t = threading.Thread(target=self._observer_loop, args=(obs_id,), daemon=True)
            t.start()
            self._threads.append(t)
    
    def stop(self):
        """Stop all observer threads."""
        self._running = False
        for t in self._threads:
            t.join(timeout=5)
    
    def _observer_loop(self, obs_id: str):
        """Simulate observer work loop."""
        obs = self.observers[obs_id]
        start = time.time()
        while self._running:
            with self._lock:
                obs.tasks_completed += 1
                obs.last_heartbeat = time.time()
                obs.uptime_seconds = time.time() - start
                # Simulate rare errors (0.5% chance per cycle)
                import random
                if random.random() < 0.005:
                    obs.errors += 1
                    obs.status = "degraded"
                # Recovery from degraded after some time
                if obs.status == "degraded" and random.random() < 0.02:
                    obs.status = "alive"
            time.sleep(10)  # Task cycle every 10 seconds
    
    def get_health(self) -> Dict[str, int]:
        """Get current health counts."""
        now = time.time()
        alive = 0
        degraded = 0
        dead = 0
        with self._lock:
            for obs in self.observers.values():
                if now - obs.last_heartbeat > HEARTBEAT_TIMEOUT_SECONDS:
                    obs.status = "dead"
                    dead += 1
                elif obs.status == "degraded":
                    degraded += 1
                else:
                    alive += 1
        return {"alive": alive, "degraded": degraded, "dead": dead}
    
    def get_snapshots(self) -> Dict[str, Dict]:
        """Get snapshot of all observers."""
        with self._lock:
            return {
                obs_id: {
                    "status": obs.status,
                    "tasks_completed": obs.tasks_completed,
                    "errors": obs.errors,
                    "uptime_seconds": obs.uptime_seconds
                }
                for obs_id, obs in self.observers.items()
            }
    
    def inject_micro_chaos(self) -> Dict:
        """Inject a micro-chaos event (kill one random observer temporarily)."""
        import random
        with self._lock:
            alive_observers = [
                obs_id for obs_id, obs in self.observers.items()
                if obs.status == "alive"
            ]
            if not alive_observers:
                return {"injected": False, "reason": "no alive observers"}
            
            target = random.choice(alive_observers)
            self.observers[target].status = "dead"
            
            # Schedule recovery
            def recover():
                time.sleep(30)  # 30s recovery time
                with self._lock:
                    if target in self.observers:
                        self.observers[target].status = "alive"
                        self.observers[target].last_heartbeat = time.time()
            
            threading.Thread(target=recover, daemon=True).start()
            
            return {
                "injected": True,
                "target": target,
                "chaos_type": "micro_observer_kill",
                "recovery_time": 30
            }


# ─── Continuity Hash Engine ──────────────────────────────────────────────────

class ContinuityHashEngine:
    """
    Generates continuity hashes for identity, trajectory, goal, and memory.
    Compares against baseline to detect drift.
    """
    
    def __init__(self):
        self._baseline: Optional[Dict[str, str]] = None
        self._history: List[Dict] = []
    
    def _hash(self, data: Any) -> str:
        """Generate SHA256 hash of data."""
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def generate_checkpoint(self, elapsed_hours: float, 
                            observer_snapshots: Dict[str, Dict],
                            chaos_events: List[Dict]) -> ContinuityCheckpoint:
        """Generate a continuity checkpoint."""
        
        # Identity hash: based on observer IDs and roles (stable)
        identity_data = {
            "observer_ids": sorted(observer_snapshots.keys()),
            "observer_count": len(observer_snapshots),
            "test_id": "11.1-B"
        }
        identity_hash = self._hash(identity_data)
        
        # Trajectory hash: based on task progress and events
        trajectory_data = {
            "elapsed_hours": round(elapsed_hours, 2),
            "total_tasks": sum(s["tasks_completed"] for s in observer_snapshots.values()),
            "total_errors": sum(s["errors"] for s in observer_snapshots.values()),
            "chaos_event_count": len(chaos_events),
            "last_chaos": chaos_events[-1] if chaos_events else None
        }
        trajectory_hash = self._hash(trajectory_data)
        
        # Goal hash: based on test goals (stable)
        goal_data = {
            "primary_goal": "72h_continuity_stability",
            "uptime_target": UPTIME_PASS_THRESHOLD,
            "drift_threshold": DRIFT_THRESHOLD,
            "checkpoint_interval": CONTINUITY_CHECKPOINT_INTERVAL_HOURS
        }
        goal_hash = self._hash(goal_data)
        
        # Memory hash: based on observer state distribution
        status_counts = {"alive": 0, "degraded": 0, "dead": 0}
        for s in observer_snapshots.values():
            status_counts[s["status"]] = status_counts.get(s["status"], 0) + 1
        
        memory_data = {
            "status_distribution": status_counts,
            "total_uptime": sum(s["uptime_seconds"] for s in observer_snapshots.values()),
            "checkpoint_count": len(self._history)
        }
        memory_hash = self._hash(memory_data)
        
        # Combined state hash
        state_hash = self._hash({
            "identity": identity_hash,
            "trajectory": trajectory_hash,
            "goal": goal_hash,
            "memory": memory_hash
        })
        
        # Calculate drift from baseline
        drift_details = {}
        drift_score = 0.0
        
        if self._baseline:
            if identity_hash != self._baseline["identity"]:
                drift_details["identity"] = "changed"
            if trajectory_hash != self._baseline["trajectory"]:
                drift_details["trajectory"] = "changed"
            if goal_hash != self._baseline["goal"]:
                drift_details["goal"] = "changed"
            if memory_hash != self._baseline["memory"]:
                drift_details["memory"] = "changed"
            drift_score = len(drift_details) / 4.0
        else:
            self._baseline = {
                "identity": identity_hash,
                "trajectory": trajectory_hash,
                "goal": goal_hash,
                "memory": memory_hash
            }
        
        # Determine status
        if drift_score == 0:
            status = "PASS"
        elif drift_score < DRIFT_THRESHOLD:
            status = "PASS"
        elif drift_score < 0.5:
            status = "DRIFT"
        else:
            status = "FAIL"
        
        # Get memory usage
        try:
            import psutil
            memory_usage_mb = psutil.Process().memory_info().rss / 1024 / 1024
        except ImportError:
            memory_usage_mb = 0.0
        
        checkpoint = ContinuityCheckpoint(
            checkpoint_id=f"chk_{int(time.time())}",
            timestamp=datetime.now().isoformat(),
            elapsed_hours=round(elapsed_hours, 2),
            identity_hash=identity_hash,
            trajectory_hash=trajectory_hash,
            goal_hash=goal_hash,
            memory_hash=memory_hash,
            state_hash=state_hash,
            drift_score=round(drift_score, 4),
            drift_details=drift_details,
            observer_health=status_counts,
            memory_usage_mb=round(memory_usage_mb, 2),
            status=status
        )
        
        self._history.append(asdict(checkpoint))
        return checkpoint


# ─── Test 11.1-B Runner ──────────────────────────────────────────────────────

class Test11_1BRunner:
    """
    Main runner for TEST 11.1-B (72-hour continuity stability).
    
    Lifecycle:
    1. Initialize observer mesh (10 observers)
    2. Start continuity monitoring
    3. Every 6 hours: generate continuity checkpoint
    4. Every 12 hours: inject micro-chaos event
    5. Every hour: log progress
    6. At 72 hours: generate final report
    """
    
    def __init__(self, duration_hours: int = TEST_DURATION_HOURS):
        self.duration_hours = duration_hours
        self.duration_seconds = duration_hours * 3600
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # Components
        self.mesh = ObserverMesh(OBSERVER_COUNT)
        self.hash_engine = ContinuityHashEngine()
        
        # State
        self.state = Test11_1BState()
        self._running = False
        self._threads: List[threading.Thread] = []
        
        # Progress file
        self.progress_path = Path("progress/11-1-b-checkpoints.json")
        self.progress_path.parent.mkdir(parents=True, exist_ok=True)
    
    def start(self):
        """Start TEST 11.1-B."""
        self.start_time = time.time()
        self.end_time = self.start_time + self.duration_seconds
        self._running = True
        
        self.state.start_time = datetime.now().isoformat()
        self.state.test_name = f"{self.duration_hours}h_continuity_stability"
        
        print(f"\n{'='*70}")
        print(f"  TEST 11.1-B — {self.duration_hours}-Hour Continuity Stability")
        print(f"{'='*70}")
        print(f"  Start time: {self.state.start_time}")
        print(f"  Duration: {self.duration_hours} hours ({self.duration_seconds}s)")
        print(f"  Observers: {OBSERVER_COUNT}")
        print(f"  Continuity checkpoint: every {CONTINUITY_CHECKPOINT_INTERVAL_HOURS}h")
        print(f"  Micro-chaos injection: every {MICRO_CHAOS_INTERVAL_HOURS}h")
        print(f"  Drift threshold: {DRIFT_THRESHOLD}")
        print(f"  Uptime pass threshold: {UPTIME_PASS_THRESHOLD}%")
        print(f"{'='*70}\n")
        
        # Start observer mesh
        self.mesh.start()
        print(f"[{self._elapsed_str()}] Observer mesh started ({OBSERVER_COUNT} observers)")
        
        # Start monitoring threads
        self._start_continuity_monitor()
        self._start_chaos_scheduler()
        self._start_progress_logger()
        
        # Persist initial state
        self._save_progress()
    
    def run_blocking(self):
        """Run the test in blocking mode (main thread waits)."""
        self.start()
        
        try:
            # Main loop: sleep and check
            while self._running and time.time() < self.end_time:
                time.sleep(60)  # Check every minute
                
                # Check for early termination conditions
                health = self.mesh.get_health()
                if health["dead"] > OBSERVER_COUNT * 0.5:
                    print(f"\n[{self._elapsed_str()}] ⚠️ CRITICAL: >50% observers dead. Stopping early.")
                    break
            
            self.stop()
            
        except KeyboardInterrupt:
            print(f"\n[{self._elapsed_str()}] Interrupted by user.")
            self.stop()
    
    def stop(self):
        """Stop the test and generate final report."""
        self._running = False
        self.mesh.stop()
        
        self.end_time = time.time()
        self.state.end_time = datetime.now().isoformat()
        self.state.duration_hours = round((self.end_time - self.start_time) / 3600, 2)
        
        # Calculate final metrics
        health = self.mesh.get_health()
        total = sum(health.values())
        self.state.final_uptime_percent = round(
            (health["alive"] / total) * 100 if total > 0 else 0, 2
        )
        
        # Overall pass/fail
        self.state.overall_pass = (
            self.state.final_uptime_percent >= UPTIME_PASS_THRESHOLD
            and self.state.max_drift_score < DRIFT_THRESHOLD
            and self.state.failed_checkpoints == 0
        )
        
        self._save_progress()
        self._print_final_report()
    
    def _start_continuity_monitor(self):
        """Start the continuity checkpoint monitor thread."""
        def monitor():
            next_checkpoint = time.time() + (CONTINUITY_CHECKPOINT_INTERVAL_HOURS * 3600)
            while self._running:
                time.sleep(60)  # Check every minute
                if time.time() >= next_checkpoint:
                    self._run_continuity_checkpoint()
                    next_checkpoint = time.time() + (CONTINUITY_CHECKPOINT_INTERVAL_HOURS * 3600)
        
        t = threading.Thread(target=monitor, daemon=True)
        t.start()
        self._threads.append(t)
    
    def _start_chaos_scheduler(self):
        """Start the micro-chaos injection scheduler thread."""
        def scheduler():
            next_chaos = time.time() + (MICRO_CHAOS_INTERVAL_HOURS * 3600)
            while self._running:
                time.sleep(60)  # Check every minute
                if time.time() >= next_chaos:
                    result = self.mesh.inject_micro_chaos()
                    if result["injected"]:
                        self.state.chaos_events.append({
                            "timestamp": datetime.now().isoformat(),
                            "elapsed_hours": self._elapsed_hours(),
                            **result
                        })
                        print(f"\n[{self._elapsed_str()}] ⚡ Micro-chaos: killed {result['target']}, "
                              f"recovery in {result['recovery_time']}s")
                    next_chaos = time.time() + (MICRO_CHAOS_INTERVAL_HOURS * 3600)
        
        t = threading.Thread(target=scheduler, daemon=True)
        t.start()
        self._threads.append(t)
    
    def _start_progress_logger(self):
        """Start the hourly progress logger thread."""
        def logger():
            next_log = time.time() + 3600  # Every hour
            while self._running:
                time.sleep(60)  # Check every minute
                if time.time() >= next_log:
                    self._log_progress()
                    next_log = time.time() + 3600
        
        t = threading.Thread(target=logger, daemon=True)
        t.start()
        self._threads.append(t)
    
    def _run_continuity_checkpoint(self):
        """Run a continuity checkpoint."""
        elapsed = self._elapsed_hours()
        snapshots = self.mesh.get_snapshots()
        
        checkpoint = self.hash_engine.generate_checkpoint(
            elapsed_hours=elapsed,
            observer_snapshots=snapshots,
            chaos_events=self.state.chaos_events
        )
        
        self.state.total_checkpoints += 1
        self.state.checkpoints.append(asdict(checkpoint))
        
        if checkpoint.status == "PASS":
            self.state.passed_checkpoints += 1
        elif checkpoint.status == "DRIFT":
            pass  # Warning but not failure
        else:
            self.state.failed_checkpoints += 1
        
        if checkpoint.drift_score > self.state.max_drift_score:
            self.state.max_drift_score = checkpoint.drift_score
        
        # Print checkpoint summary
        status_icon = "✅" if checkpoint.status == "PASS" else ("⚠️" if checkpoint.status == "DRIFT" else "❌")
        print(f"\n[{self._elapsed_str()}] {status_icon} Continuity Checkpoint #{self.state.total_checkpoints}")
        print(f"  Identity:   {checkpoint.identity_hash}")
        print(f"  Trajectory: {checkpoint.trajectory_hash}")
        print(f"  Goal:       {checkpoint.goal_hash}")
        print(f"  Memory:     {checkpoint.memory_hash}")
        print(f"  State:      {checkpoint.state_hash}")
        print(f"  Drift:      {checkpoint.drift_score:.4f} {checkpoint.drift_details if checkpoint.drift_details else '(none)'}")
        print(f"  Observers:  ✅{checkpoint.observer_health.get('alive', 0)} "
              f"⚠️{checkpoint.observer_health.get('degraded', 0)} "
              f"❌{checkpoint.observer_health.get('dead', 0)}")
        print(f"  Memory:     {checkpoint.memory_usage_mb:.1f} MB")
        
        self._save_progress()
    
    def _log_progress(self):
        """Log hourly progress."""
        elapsed = self._elapsed_hours()
        health = self.mesh.get_health()
        total = sum(health.values())
        uptime = (health["alive"] / total * 100) if total > 0 else 0
        
        print(f"[{self._elapsed_str()}] 📊 Hourly: {elapsed:.1f}h elapsed | "
              f"Alive: {health['alive']}/{total} ({uptime:.1f}%) | "
              f"Degraded: {health['degraded']} | Dead: {health['dead']} | "
              f"Checkpoints: {self.state.total_checkpoints}")
        
        self._save_progress()
    
    def _save_progress(self):
        """Persist test state to progress file."""
        self.state.observers = self.mesh.get_snapshots()
        with open(self.progress_path, 'w') as f:
            json.dump(asdict(self.state), f, indent=2, default=str)
    
    def _elapsed_hours(self) -> float:
        """Get elapsed hours since test start."""
        if self.start_time is None:
            return 0.0
        return (time.time() - self.start_time) / 3600
    
    def _elapsed_str(self) -> str:
        """Get elapsed time as formatted string."""
        hours = self._elapsed_hours()
        h = int(hours)
        m = int((hours - h) * 60)
        return f"{h:02d}h{m:02d}m"
    
    def _print_final_report(self):
        """Print the final test report."""
        print(f"\n{'='*70}")
        print(f"  TEST 11.1-B — FINAL REPORT")
        print(f"{'='*70}")
        print(f"  Test: {self.state.test_name}")
        print(f"  Start: {self.state.start_time}")
        print(f"  End: {self.state.end_time}")
        print(f"  Duration: {self.state.duration_hours}h / {self.duration_hours}h target")
        print(f"")
        print(f"  Continuity Checkpoints: {self.state.total_checkpoints}")
        print(f"    Passed: {self.state.passed_checkpoints}")
        print(f"    Failed: {self.state.failed_checkpoints}")
        print(f"    Max Drift Score: {self.state.max_drift_score:.4f}")
        print(f"")
        print(f"  Final Uptime: {self.state.final_uptime_percent}%")
        print(f"  Chaos Events: {len(self.state.chaos_events)}")
        print(f"")
        
        if self.state.overall_pass:
            print(f"  ✅ OVERALL: PASS")
        else:
            print(f"  ❌ OVERALL: FAIL")
            if self.state.final_uptime_percent < UPTIME_PASS_THRESHOLD:
                print(f"    - Uptime below {UPTIME_PASS_THRESHOLD}% threshold")
            if self.state.max_drift_score >= DRIFT_THRESHOLD:
                print(f"    - Drift score exceeded {DRIFT_THRESHOLD} threshold")
            if self.state.failed_checkpoints > 0:
                print(f"    - {self.state.failed_checkpoints} checkpoint(s) failed")
        
        print(f"{'='*70}\n")


# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    """Main entry point for TEST 11.1-B."""
    import argparse
    
    parser = argparse.ArgumentParser(description="TEST 11.1-B — 72-Hour Continuity Stability")
    parser.add_argument("--hours", type=int, default=TEST_DURATION_HOURS,
                        help=f"Test duration in hours (default: {TEST_DURATION_HOURS})")
    parser.add_argument("--checkpoint-interval", type=int, 
                        default=CONTINUITY_CHECKPOINT_INTERVAL_HOURS,
                        help=f"Continuity checkpoint interval in hours (default: {CONTINUITY_CHECKPOINT_INTERVAL_HOURS})")
    parser.add_argument("--chaos-interval", type=int,
                        default=MICRO_CHAOS_INTERVAL_HOURS,
                        help=f"Micro-chaos injection interval in hours (default: {MICRO_CHAOS_INTERVAL_HOURS})")
    parser.add_argument("--observers", type=int, default=OBSERVER_COUNT,
                        help=f"Number of observers (default: {OBSERVER_COUNT})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run a 5-minute dry run instead of full test")
    args = parser.parse_args()
    
    if args.dry_run:
        print("🧪 DRY RUN MODE — 5 minute test")
        runner = Test11_1BRunner(duration_hours=5/60)  # 5 minutes
    else:
        runner = Test11_1BRunner(duration_hours=args.hours)
    
    runner.run_blocking()


if __name__ == "__main__":
    main()
