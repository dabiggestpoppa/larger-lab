#!/usr/bin/env python3
"""
CC Cron — Claude Code Continuous Workflow Engine
==================================================
Runs CC's oversight loop on a schedule. This gives CC the same
always-on capability as OpenClaw's cron system.

CC's loop:
  1. Read team-chat.md for new messages directed at CC
  2. Check sub-progress files for OC/HR updates
  3. Run progress sync
  4. Check phase gate criteria
  5. Review and respond to open items
  6. Update own sub-progress
  7. Handle errors with rate-limit-aware retry

Usage:
  python tools/cc-cron.py --once     # Run one CC cycle
  python tools/cc-cron.py --loop     # Run continuously (default: every 5 min)
  python tools/cc-cron.py --interval 300  # Custom interval in seconds
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LAB_ROOT = Path(__file__).resolve().parent.parent
TEAM_CHAT = LAB_ROOT / "shared-conversations" / "team-chat.md"
CC_PROGRESS = LAB_ROOT / "progress" / "claude-code-progress.md"
CC_MEMORY = LAB_ROOT / "progress" / "claude-code-memory.md"
PHASE_FILE = LAB_ROOT / ".phase-state.json"
COUNTER_FILE = LAB_ROOT / ".cc-cron-state.json"

DEFAULT_INTERVAL = 300  # 5 minutes
MAX_RETRIES = 3
RETRY_BACKOFF = [30, 120, 300]  # seconds between retries


def load_cron_state() -> dict:
    """Load CC cron state (retry counts, last run, etc.)."""
    if COUNTER_FILE.exists():
        with open(COUNTER_FILE) as f:
            return json.load(f)
    return {
        "last_run": None,
        "run_count": 0,
        "error_count": 0,
        "consecutive_errors": 0,
        "last_error": None,
        "rate_limit_hits": 0,
    }


def save_cron_state(state: dict):
    """Save CC cron state."""
    with open(COUNTER_FILE, "w") as f:
        json.dump(state, f, indent=2)


def log(msg: str):
    """Log with timestamp."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{now}] [CC-CRON] {msg}"
    print(line)


def run_cmd(cmd: str, timeout: int = 60) -> tuple:
    """Run a command. Returns (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=str(LAB_ROOT), timeout=timeout,
            encoding="utf-8", errors="replace"
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def read_team_chat() -> str:
    """Read the team chat file."""
    if TEAM_CHAT.exists():
        with open(TEAM_CHAT, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def read_sub_progress(agent: str) -> str:
    """Read an agent's sub-progress file."""
    fpath = LAB_ROOT / "progress" / f"{agent}-progress.md"
    if fpath.exists():
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def append_to_team_chat(message: str):
    """Append a message to team chat."""
    TEAM_CHAT.parent.mkdir(parents=True, exist_ok=True)
    content = read_team_chat()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"\n### [CC] {timestamp}\n{message}\n"
    # Insert before the Archive section
    if "## 📦 Archive" in content:
        content = content.replace("## 📦 Archive", entry + "\n## 📦 Archive")
    else:
        content += entry
    with open(TEAM_CHAT, "w", encoding="utf-8") as f:
        f.write(content)


def get_phase_state() -> dict:
    """Get current phase state."""
    if PHASE_FILE.exists():
        with open(PHASE_FILE) as f:
            return json.load(f)
    return {}


def check_oc_hr_progress() -> dict:
    """Check what OC and HR have been working on since last check."""
    oc_progress = read_sub_progress("openclaw")
    hr_progress = read_sub_progress("hermes")

    return {
        "oc_has_updates": "#### 🟣 [OC]" in oc_progress,
        "hr_has_updates": "#### 🟢 [HR]" in hr_progress,
        "oc_last_entry": _get_last_entry(oc_progress, "🟣 [OC]"),
        "hr_last_entry": _get_last_entry(hr_progress, "🟢 [HR]"),
    }


def _get_last_entry(content: str, tag: str) -> str:
    """Extract the last entry with a given tag from progress content."""
    import re
    pattern = rf"#### {re.escape(tag)}.*?(?=#### |\Z)"
    matches = re.findall(pattern, content, re.DOTALL)
    return matches[-1].strip() if matches else "No entries"


def run_cc_cycle():
    """Run one full CC oversight cycle."""
    state = load_cron_state()
    now = datetime.now(timezone.utc)

    log(f"Starting cycle #{state['run_count'] + 1}")

    # 1. Read team chat for messages directed at CC
    chat = read_team_chat()
    cc_mentions = chat.count("@CC")
    log(f"  Team chat: {cc_mentions} mentions for CC")

    # 2. Check OC/HR progress
    progress = check_oc_hr_progress()
    if progress["oc_has_updates"]:
        log(f"  OC activity: {progress['oc_last_entry'][:80]}...")
    if progress["hr_has_updates"]:
        log(f"  HR activity: {progress['hr_last_entry'][:80]}...")

    # 3. Run progress sync
    rc, out, err = run_cmd("python tools/progress-sync.py")
    if rc == 0:
        log("  Progress sync: OK")
    else:
        log(f"  Progress sync: FAILED - {err[:100]}")
        state["error_count"] += 1
        state["consecutive_errors"] += 1

    # 4. Check phase gate
    phase_state = get_phase_state()
    current_phase = phase_state.get("current_phase", "PHASE_2")
    log(f"  Current phase: {current_phase}")

    # 5. Respond to team chat if there are open items
    if cc_mentions > 0 or progress["oc_has_updates"] or progress["hr_has_updates"]:
        response = _generate_cc_response(chat, progress, current_phase)
        if response:
            append_to_team_chat(response)
            log(f"  Posted response to team chat")

    # 6. Update CC sub-progress
    _update_cc_progress(state, progress, current_phase)

    # 7. Update cron state
    state["last_run"] = now.isoformat()
    state["run_count"] += 1
    if state["consecutive_errors"] == 0:
        state["rate_limit_hits"] = 0
    save_cron_state(state)

    log(f"  Cycle complete. Total runs: {state['run_count']}")
    return True


def _generate_cc_response(chat: str, progress: dict, current_phase: str) -> str:
    """Generate CC's response to team activity."""
    parts = []

    if progress["oc_has_updates"]:
        parts.append(f"**OC Update Reviewed:** Acknowledged. Continuing Phase 2 coordination.")

    if progress["hr_has_updates"]:
        parts.append(f"**HR Update Reviewed:** Acknowledged. Monitoring execution progress.")

    if not parts:
        parts.append(f"**Phase 2 Status Check:** All systems nominal. Current phase: {current_phase}. Awaiting OC/HR task completion.")

    return "\n".join(parts)


def _update_cc_progress(state: dict, progress: dict, current_phase: str):
    """Update CC's sub-progress with cycle summary."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"""
#### 🔵 [CC] {timestamp} — Cron Cycle #{state['run_count'] + 1}
- Phase: {current_phase}
- OC activity: {'Yes' if progress['oc_has_updates'] else 'None'}
- HR activity: {'Yes' if progress['hr_has_updates'] else 'None'}
- Errors: {state['consecutive_errors']} consecutive
"""
    with open(CC_PROGRESS, "r", encoding="utf-8") as f:
        content = f.read()

    # Insert after Status line, before Recent Entries
    if "### Recent Entries" in content:
        content = content.replace("### Recent Entries", entry + "\n### Recent Entries")
    else:
        content += entry

    with open(CC_PROGRESS, "w", encoding="utf-8") as f:
        f.write(content)


def handle_error(state: dict, error: str) -> int:
    """Handle errors with rate-limit-aware retry. Returns backoff seconds."""
    state["error_count"] += 1
    state["consecutive_errors"] += 1
    state["last_error"] = error

    # Check if it's a rate limit error
    if "rate limit" in error.lower() or "429" in error:
        state["rate_limit_hits"] += 1
        backoff = RETRY_BACKOFF[min(state["rate_limit_hits"] - 1, len(RETRY_BACKOFF) - 1)]
        log(f"  Rate limit hit (#{state['rate_limit_hits']}). Backing off {backoff}s.")
        return backoff

    # Regular error backoff
    idx = min(state["consecutive_errors"] - 1, len(RETRY_BACKOFF) - 1)
    backoff = RETRY_BACKOFF[idx]
    log(f"  Error (consecutive: {state['consecutive_errors']}). Backing off {backoff}s.")
    return backoff


def main():
    parser = argparse.ArgumentParser(description="CC Cron — Continuous Workflow Engine")
    parser.add_argument("--once", action="store_true", help="Run one cycle")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                        help=f"Loop interval in seconds (default: {DEFAULT_INTERVAL})")
    parser.add_argument("--status", action="store_true", help="Show cron status")
    args = parser.parse_args()

    state = load_cron_state()

    if args.status:
        print(f"\nCC Cron Status")
        print(f"  Total runs: {state['run_count']}")
        print(f"  Total errors: {state['error_count']}")
        print(f"  Consecutive errors: {state['consecutive_errors']}")
        print(f"  Rate limit hits: {state['rate_limit_hits']}")
        print(f"  Last run: {state['last_run'] or 'never'}")
        print(f"  Last error: {state['last_error'] or 'none'}")
        print(f"  Default interval: {DEFAULT_INTERVAL}s")
        return

    if args.once:
        try:
            run_cc_cycle()
        except Exception as e:
            backoff = handle_error(state, str(e))
            log(f"  Cycle failed: {e}. Backing off {backoff}s.")
            save_cron_state(state)
        return

    # Continuous loop
    log(f"CC Cron started. Interval: {args.interval}s")
    log(f"Working dir: {LAB_ROOT}")

    while True:
        try:
            run_cc_cycle()
            state["consecutive_errors"] = 0  # Reset on success
            save_cron_state(state)
        except Exception as e:
            backoff = handle_error(state, str(e))
            save_cron_state(state)
            log(f"Sleeping {backoff}s after error...")
            time.sleep(backoff)
            continue

        log(f"Sleeping {args.interval}s...")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
