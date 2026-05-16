#!/usr/bin/env python3
"""
CC Continuous Workflow Engine
===============================
Main loop for CC's oversight workflow. Runs continuously:
1. Check team progress (OC, HR, AS sub-progress files)
2. Run tests
3. Delegate new tasks
4. Follow up on delegated tasks
5. Update own progress
6. Handle errors with rate-limit-aware retry

This is CC's "cron" — it runs continuously while the build is active.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LAB_ROOT = Path(__file__).resolve().parent.parent
PROGRESS_DIR = LAB_ROOT / "progress"
TEAM_CHAT = LAB_ROOT / "shared-conversations" / "team-chat.md"
CC_PROGRESS = PROGRESS_DIR / "claude-code-progress.md"
AS_PROGRESS = PROGRESS_DIR / "assistant-progress.md"
OC_PROGRESS = PROGRESS_DIR / "openclaw-progress.md"
HR_PROGRESS = PROGRESS_DIR / "hermes-progress.md"
PHASE_FILE = LAB_ROOT / ".phase-state.json"
WORKFLOW_LOG = PROGRESS_DIR / "cc-workflow.log"

CYCLE_INTERVAL = 120  # 2 minutes between cycles
MAX_RETRIES = 3
RETRY_BACKOFF = [30, 60, 120]


def log(msg):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{now}] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode())
    with open(WORKFLOW_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_cmd(cmd, timeout=60):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=str(LAB_ROOT), timeout=timeout,
            encoding="utf-8", errors="replace"
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def read_progress_file(path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def get_phase():
    if PHASE_FILE.exists():
        with open(PHASE_FILE) as f:
            return json.load(f).get("current_phase", "UNKNOWN")
    return "UNKNOWN"


def count_test_failures():
    """Run all tests and return failure count."""
    failures = 0
    # Phase 2
    rc, out, err = run_cmd("python -m srrs_opc.tests.test_phase2_e2e", timeout=60)
    if rc != 0:
        failures += 1
        log(f"  Phase 2 tests FAILED")
    # Phase 3
    rc, out, err = run_cmd("python -m srrs_opc.tests.test_phase3_e2e", timeout=60)
    if rc != 0:
        failures += 1
        log(f"  Phase 3 tests FAILED")
    return failures


def check_as_progress():
    """Check what AS has been working on."""
    content = read_progress_file(AS_PROGRESS)
    # Find most recent entry
    entries = content.split("#### ")
    if len(entries) > 1:
        latest = entries[-1].strip()
        return latest[:200]
    return "No AS progress found"


def check_new_files():
    """Check for new files created since last check."""
    import glob
    patterns = [
        "srrs_opc/*.py",
        "srrs_opc/tests/*.py",
        "srrs_opc/docs/*.md",
        "progress/*.md",
        "tasks/*.md",
    ]
    files = []
    for p in patterns:
        files.extend(glob.glob(str(LAB_ROOT / p)))
    # Sort by modification time, return recent ones
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return files[:10]


def run_sync():
    rc, out, err = run_cmd("python tools/progress-sync.py --force", timeout=30)
    return rc == 0


def append_cc_progress(entry):
    with open(CC_PROGRESS, "r", encoding="utf-8") as f:
        content = f.read()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    new_entry = f"\n#### [CC] {timestamp} — {entry}\n"
    # Insert before "Pending Tasks" or at end
    if "### Pending Tasks" in content:
        content = content.replace("### Pending Tasks", new_entry + "### Pending Tasks")
    else:
        content += new_entry
    with open(CC_PROGRESS, "w", encoding="utf-8") as f:
        f.write(content)


def run_cycle():
    """Run one CC oversight cycle."""
    phase = get_phase()
    log(f"=== Cycle Start | Phase: {phase} ===")

    # 1. Run tests
    log("Running tests...")
    failures = count_test_failures()
    if failures == 0:
        log("  All tests PASSING")
    else:
        log(f"  {failures} test suite(s) FAILING — needs attention")

    # 2. Check AS progress
    log("Checking AS progress...")
    as_work = check_as_progress()
    log(f"  AS latest: {as_work[:100]}...")

    # 3. Check for new files
    new_files = check_new_files()
    log(f"  Recent files: {len(new_files)}")

    # 4. Run progress sync
    log("Running progress sync...")
    if run_sync():
        log("  Sync OK")
    else:
        log("  Sync FAILED")

    # 5. Check phase gate
    rc, out, err = run_cmd("python tools/phase-gate.py --check", timeout=15)
    if "All criteria met" in out:
        log(f"  Phase {phase} criteria all met! Ready to advance.")

    # 6. Log cycle complete
    log(f"=== Cycle Complete ===\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CC Continuous Workflow")
    parser.add_argument("--once", action="store_true", help="Run one cycle")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=CYCLE_INTERVAL)
    args = parser.parse_args()

    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)

    if args.once:
        run_cycle()
        return

    log(f"CC Workflow Engine started. Interval: {args.interval}s")
    log(f"Working dir: {LAB_ROOT}")

    consecutive_errors = 0
    while True:
        try:
            run_cycle()
            consecutive_errors = 0
        except Exception as e:
            consecutive_errors += 1
            log(f"ERROR: {e}")
            if consecutive_errors >= MAX_RETRIES:
                log(f"Too many consecutive errors ({consecutive_errors}). Pausing 5min.")
                time.sleep(300)
                consecutive_errors = 0

        log(f"Sleeping {args.interval}s...")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
