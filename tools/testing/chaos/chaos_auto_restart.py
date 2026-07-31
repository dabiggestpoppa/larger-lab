"""
Phase 11.2 — Chaos Test Auto-Restart Wrapper
Runs the chaos test and automatically restarts from the last completed cycle if it crashes.
"""
import subprocess
import sys
import time
import json
from pathlib import Path

SCRIPT = Path(__file__).parent / "chaos_20x_test.py"
RESULTS_FILE = Path(__file__).parent / "stability" / "chaos_20x_results.json"
MAX_RESTARTS = 50  # Safety limit

def get_last_completed_cycle():
    """Read the results file to find the last completed cycle."""
    if not RESULTS_FILE.exists():
        return 0
    try:
        with open(RESULTS_FILE) as f:
            data = json.load(f)
        cycles = data.get("cycles", [])
        if not cycles:
            return 0
        # Find the last cycle that passed
        last = 0
        for c in cycles:
            if c.get("passed"):
                last = c.get("cycle", 0)
        return last
    except Exception:
        return 0

def main():
    restart_count = 0
    while restart_count < MAX_RESTARTS:
        last_cycle = get_last_completed_cycle()
        cmd = [sys.executable, str(SCRIPT)]
        if last_cycle > 0:
            cmd.extend(["--resume", str(last_cycle)])
            print(f"[AUTO-RESTART] Starting from cycle {last_cycle + 1} (last completed: {last_cycle})")
        else:
            print(f"[AUTO-RESTART] Starting fresh")
        
        print(f"[AUTO-RESTART] Command: {' '.join(cmd)}")
        print(f"[AUTO-RESTART] Restart count: {restart_count}")
        print("=" * 60)
        
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print("[AUTO-RESTART] Test completed successfully!")
            break
        else:
            restart_count += 1
            print(f"[AUTO-RESTART] Test crashed with exit code {result.returncode}")
            print(f"[AUTO-RESTART] Restarting in 10 seconds... (attempt {restart_count}/{MAX_RESTARTS})")
            time.sleep(10)
    
    if restart_count >= MAX_RESTARTS:
        print(f"[AUTO-RESTART] Max restarts ({MAX_RESTARTS}) reached. Giving up.")
        sys.exit(1)

if __name__ == "__main__":
    main()
