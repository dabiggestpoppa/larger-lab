"""
AS Autopilot Monitor
====================
Background monitoring script for Assistant Manager (AS).
Monitors:
- Phase 11.2 chaos test progress (chaos_20x_trace.log)
- Phase 11.1-B continuity checkpoints (11-1-b-checkpoints.json)
- Team chat for @AS mentions
- Progress file sync

Run in background: python tools/as_autopilot.py
"""

import time
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path("C:/Users/wifik/Desktop/projects/larger-lab")
TRACE_LOG = WORKSPACE / "stability/chaos_20x_trace.log"
CHECKPOINTS = WORKSPACE / "progress/11-1-b-checkpoints.json"
TEAM_CHAT = WORKSPACE / "shared-conversations/team-chat.md"
PROGRESS = WORKSPACE / "progress/assistant-progress.md"

def check_chaos_progress():
    """Check latest chaos test progress from trace log."""
    if not TRACE_LOG.exists():
        return "No trace log found"
    lines = TRACE_LOG.read_text().splitlines()
    if not lines:
        return "Trace log empty"
    # Get last meaningful line
    for line in reversed(lines):
        if "CYCLE" in line or "PASS" in line or "FAIL" in line or "RESUMED" in line:
            return line.strip()
    return lines[-1].strip() if lines else "No data"

def check_continuity_checkpoints():
    """Check 72h continuity test checkpoints."""
    if not CHECKPOINTS.exists():
        return "No checkpoints file"
    try:
        data = json.loads(CHECKPOINTS.read_text())
        total = data.get("total_checkpoints", 0)
        passed = data.get("passed_checkpoints", 0)
        failed = data.get("failed_checkpoints", 0)
        max_drift = data.get("max_drift_score", 0)
        return f"Checkpoints: {total} total, {passed} pass, {failed} fail, max_drift={max_drift}"
    except:
        return "Error reading checkpoints"

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()

def run_sync():
    """Run progress sync."""
    try:
        result = subprocess.run(
            ["python", "tools/progress-sync.py", "--agent", "AS", "--force"],
            cwd=str(WORKSPACE),
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip() or "Sync OK"
    except Exception as e:
        return f"Sync error: {e}"

def main():
    print(f"[{get_timestamp()}] AS Autopilot started")
    print(f"  Monitoring: chaos trace, continuity checkpoints, team chat")
    print(f"  Sync: every 7 updates")
    print()

    cycle_count = 0
    while True:
        cycle_count += 1
        ts = get_timestamp()

        chaos = check_chaos_progress()
        continuity = check_continuity_checkpoints()

        print(f"[{ts}] Cycle {cycle_count}")
        print(f"  Chaos: {chaos}")
        print(f"  Continuity: {continuity}")

        # Sync every 7 cycles
        if cycle_count % 7 == 0:
            sync_result = run_sync()
            print(f"  Sync: {sync_result}")

        print()
        time.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    main()
