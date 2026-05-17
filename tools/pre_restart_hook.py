"""
Pre-Restart Hook — Kill stale sub-agents before gateway restart.

Problem: Gateway restart gets stuck draining because sub-agents are still running.
The drain timeout is 5 minutes, but sub-agents often take longer or never finish.
Then the in-process restart fails because the old gateway process still holds the lock.

Solution: Before any gateway restart, kill all active sub-agents first so drain completes instantly.

Usage:
    python tools/pre_restart_hook.py          # Kill all sub-agents, then restart
    python tools/pre_restart_hook.py --check  # Just list active sub-agents
    python tools/pre_restart_hook.py --kill   # Kill all sub-agents, don't restart
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

WORKSPACE = r"C:\Users\wifik\Desktop\projects\larger-lab"
STATE_FILE = os.path.join(WORKSPACE, ".openclaw-2", ".openclaw", "restart-state.json")
LOG_FILE = os.path.join(WORKSPACE, "logs", "pre-restart-hook.log")


def log(msg):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_active_subagents():
    """Query OpenClaw for active sub-agents via the sessions API."""
    try:
        result = subprocess.run(
            ["openclaw", "sessions", "list", "--json"],
            capture_output=True, text=True, timeout=15,
            cwd=WORKSPACE
        )
        if result.returncode == 0 and result.stdout.strip():
            sessions = json.loads(result.stdout)
            # Filter for active sub-agent sessions
            subagents = [
                s for s in sessions
                if s.get("kind") == "subagent" and s.get("status") == "active"
            ]
            return subagents
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass
    return []


def kill_subagent(session_key):
    """Kill a sub-agent session."""
    try:
        result = subprocess.run(
            ["openclaw", "sessions", "kill", session_key],
            capture_output=True, text=True, timeout=10,
            cwd=WORKSPACE
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def restart_gateway():
    """Restart the OpenClaw gateway."""
    log("Restarting gateway...")
    try:
        # Use openclaw gateway restart
        result = subprocess.run(
            ["openclaw", "gateway", "restart"],
            capture_output=True, text=True, timeout=30,
            cwd=WORKSPACE
        )
        if result.returncode == 0:
            log("Gateway restart initiated successfully")
            return True
        else:
            log(f"Gateway restart failed: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        log("Gateway restart timed out")
        return False


def save_state(data):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def main():
    args = sys.argv[1:]
    check_only = "--check" in args
    kill_only = "--kill" in args

    log("=" * 60)
    log("Pre-Restart Hook starting")

    # Step 1: Find active sub-agents
    subagents = get_active_subagents()
    log(f"Found {len(subagents)} active sub-agent(s)")

    if check_only:
        for sa in subagents:
            log(f"  - {sa.get('label', 'unknown')}: {sa.get('sessionKey', 'no key')}")
        return

    # Step 2: Kill all sub-agents
    killed = []
    failed = []
    for sa in subagents:
        label = sa.get("label", "unknown")
        key = sa.get("sessionKey", "")
        if key:
            log(f"Killing sub-agent: {label} ({key})")
            if kill_subagent(key):
                killed.append(label)
                log(f"  Killed: {label}")
            else:
                failed.append(label)
                log(f"  FAILED to kill: {label}")
        else:
            log(f"  Skipping {label}: no session key")

    # Wait briefly for kills to propagate
    if killed:
        log(f"Waiting 3s for {len(killed)} kill(s) to propagate...")
        time.sleep(3)

    # Step 3: Save state
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "killed": killed,
        "failed": failed,
        "total_active": len(subagents),
    }
    save_state(state)
    log(f"State saved: {len(killed)} killed, {len(failed)} failed")

    if kill_only:
        log("Kill-only mode — skipping gateway restart")
        return

    # Step 4: Restart gateway
    if failed:
        log(f"WARNING: {len(failed)} sub-agent(s) could not be killed. Restart may still hang on drain.")
        log("Proceeding anyway — drain timeout will handle stragglers.")

    restart_gateway()
    log("Pre-Restart Hook complete")


if __name__ == "__main__":
    main()
