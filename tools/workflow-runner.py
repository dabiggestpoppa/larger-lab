#!/usr/bin/env python3
"""
Continuous Workflow Runner
===========================
Main loop that coordinates the agent team workflow.
Designed to run continuously — checks for pending tasks,
triggers sync, updates CODEMAP, and reports status.

This is the "heartbeat" of the build pipeline.

Usage:
  python tools/workflow-runner.py --once     # Run one cycle
  python tools/workflow-runner.py --loop     # Run continuously (every 60s)
  python tools/workflow-runner.py --status   # Show workflow state
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LAB_ROOT = Path(__file__).resolve().parent.parent
PHASE_FILE = LAB_ROOT / ".phase-state.json"
WORKFLOW_LOG = LAB_ROOT / "progress" / "workflow-runner.log"

CYCLE_INTERVAL = 60  # seconds between cycles


def log(msg: str):
    """Log a message to workflow log and stdout."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{now}] {msg}"
    # Use ASCII-safe output for Windows console
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode())
    with open(WORKFLOW_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_cmd(cmd: str, cwd: str = None) -> tuple:
    """Run a shell command. Returns (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=cwd or str(LAB_ROOT), timeout=30,
            encoding="utf-8", errors="replace"
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def get_phase_state() -> dict:
    """Get current phase state."""
    if PHASE_FILE.exists():
        with open(PHASE_FILE) as f:
            return json.load(f)
    return {}


def count_pending_tasks() -> dict:
    """Count pending tasks per agent."""
    tasks_dir = LAB_ROOT / "tasks"
    counts = {"CC": 0, "OC": 0, "HR": 0, "total": 0}

    if tasks_dir.exists():
        for f in tasks_dir.glob("*.json"):
            try:
                with open(f) as fh:
                    task = json.load(fh)
                if task.get("status") == "pending":
                    agent = task.get("agent", "?")
                    if agent in counts:
                        counts[agent] += 1
                    counts["total"] += 1
            except (json.JSONDecodeError, IOError):
                continue

    return counts


def run_sync() -> bool:
    """Run progress sync. Returns True if successful."""
    rc, out, err = run_cmd("python tools/progress-sync.py")
    if rc == 0:
        log("  ✅ Progress sync OK")
        return True
    else:
        log(f"  ❌ Progress sync failed: {err[:200]}")
        return False


def run_codemap_update() -> bool:
    """Update CODEMAP diagrams. Returns True if successful."""
    rc, out, err = run_cmd("python tools/codemap-updater.py")
    if rc == 0:
        log("  ✅ CODEMAP updated")
        return True
    else:
        log(f"  ❌ CODEMAP update failed: {err[:200]}")
        return False


def run_cycle():
    """Run one workflow cycle."""
    log("=" * 50)
    log("Workflow Cycle Starting")

    # 1. Check phase state
    phase_state = get_phase_state()
    current_phase = phase_state.get("current_phase", "PHASE_1")
    log(f"  📍 Current phase: {current_phase}")

    # 2. Count pending tasks
    task_counts = count_pending_tasks()
    log(f"  📋 Pending tasks: {task_counts['total']} (CC:{task_counts['CC']} OC:{task_counts['OC']} HR:{task_counts['HR']})")

    # 3. Run progress sync
    run_sync()

    # 4. Update CODEMAP (every other cycle to save resources)
    now = datetime.now(timezone.utc)
    if now.minute % 2 == 0:
        run_codemap_update()

    # 5. Check phase gate
    rc, out, err = run_cmd("python tools/phase-gate.py --check")
    if rc == 0 and "All criteria met" in out:
        log(f"  Phase {current_phase} criteria all met! Ready to advance.")
        log(f"     CC should run: python tools/phase-gate.py --advance")

    log("Workflow Cycle Complete")
    log("")


def show_status():
    """Show full workflow state."""
    print("\n" + "=" * 60)
    print("Continuous Workflow — Status")
    print("=" * 60)

    # Phase state
    phase_state = get_phase_state()
    current = phase_state.get("current_phase", "Unknown")
    print(f"\n📍 Current Phase: {current}")
    phases = phase_state.get("phases", {})
    for pid, ps in phases.items():
        status = ps.get("status", "?")
        emoji = {"complete": "✅", "in_progress": "🔄", "pending": "⏳"}.get(status, "❓")
        marker = " ←" if pid == current else ""
        print(f"   {emoji} {pid}: {ps.get('name', '?')}{marker}")

    # Tasks
    task_counts = count_pending_tasks()
    print(f"\n📋 Tasks: {task_counts['total']} pending")
    for agent in ["CC", "OC", "HR"]:
        print(f"   {agent}: {task_counts[agent]} pending")

    # Progress files
    progress_dir = LAB_ROOT / "progress"
    if progress_dir.exists():
        print(f"\n📁 Progress Files:")
        for f in sorted(progress_dir.glob("*.md")):
            stat = f.stat()
            size = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%H:%M:%S")
            print(f"   {f.name}: {size}B (modified {mtime})")

    # Tools
    tools_dir = LAB_ROOT / "tools"
    if tools_dir.exists():
        print(f"\n🔧 Tools:")
        for f in sorted(tools_dir.glob("*.py")):
            print(f"   {f.name}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Continuous Workflow Runner")
    parser.add_argument("--once", action="store_true", help="Run one cycle")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--status", action="store_true", help="Show workflow state")
    parser.add_argument("--interval", type=int, default=CYCLE_INTERVAL,
                        help=f"Loop interval in seconds (default: {CYCLE_INTERVAL})")
    args = parser.parse_args()

    # Ensure progress directory exists
    WORKFLOW_LOG.parent.mkdir(parents=True, exist_ok=True)

    if args.status:
        show_status()
    elif args.once:
        run_cycle()
    elif args.loop:
        log("🚀 Continuous workflow started")
        log(f"   Interval: {args.interval}s")
        log(f"   Working dir: {LAB_ROOT}")
        log("")

        try:
            while True:
                run_cycle()
                log(f"  😴 Sleeping {args.interval}s...")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            log("\n🛑 Workflow stopped by user.")
    else:
        # Default: show status
        show_status()


if __name__ == "__main__":
    main()
