"""
Drain Watchdog — Monitors gateway for stuck restart/drain cycles and kills sub-agents.

Runs as a cron job every 2 minutes. Detects when the gateway is trying to drain
but sub-agents are blocking it, and force-kills them so the restart can complete.

This prevents the cycle: restart → drain blocked → timeout → lock conflict → manual restart.
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone

WORKSPACE = r"C:\Users\wifik\Desktop\projects\larger-lab"
GLOB_LOG_DIR = r"C:\Users\wifik\AppData\Local\Temp\openclaw"
LOG_FILE = os.path.join(WORKSPACE, "logs", "drain-watchdog.log")
STATE_FILE = os.path.join(WORKSPACE, ".openclaw-2", ".openclaw", "drain-watchdog-state.json")

# How many "still draining" lines before we intervene
DRAIN_THRESHOLD = 3
# Minimum seconds between interventions (don't spam kills)
COOLDOWN_SECONDS = 120


def log(msg):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_today_log():
    today = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(GLOB_LOG_DIR, f"openclaw-{today}.log")
    if os.path.exists(path):
        return path
    logs = sorted(
        [f for f in os.listdir(GLOB_LOG_DIR) if f.startswith("openclaw-") and f.endswith(".log")]
    )
    if logs:
        return os.path.join(GLOB_LOG_DIR, logs[-1])
    return None


def count_drain_stalls(log_path):
    """Count 'still draining' messages in the last N lines of the log."""
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        # Check last 200 lines
        recent = lines[-200:]
        drain_count = sum(1 for l in recent if "still draining" in l.lower())
        has_drain_timeout = any("drain timeout reached" in l.lower() for l in recent)
        has_lock_conflict = any("failed to reacquire gateway lock" in l.lower() for l in recent)
        return drain_count, has_drain_timeout, has_lock_conflict
    except Exception:
        return 0, False, False


def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_intervention": 0, "total_interventions": 0}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def main():
    log("Drain Watchdog check...")

    state = load_state()
    now = time.time()

    # Cooldown check
    if now - state.get("last_intervention", 0) < COOLDOWN_SECONDS:
        log(f"Cooldown active ({int(now - state['last_intervention'])}s since last intervention)")
        return

    log_path = get_today_log()
    if not log_path:
        log("No gateway log found")
        return

    drain_count, has_timeout, has_lock = count_drain_stalls(log_path)
    log(f"Drain stalls: {drain_count}, timeout: {has_timeout}, lock conflict: {has_lock}")

    if drain_count >= DRAIN_THRESHOLD or has_timeout or has_lock:
        log(f"INTERVENTION: Gateway drain is stuck (stalls={drain_count}, timeout={has_timeout}, lock={has_log})")
        log("Signal: Sub-agents should be killed. Setting intervention flag.")
        # The actual kill happens via the subagents tool in the main session
        # This watchdog sets a flag file that the main session checks
        flag_file = os.path.join(WORKSPACE, ".openclaw-2", ".openclaw", "KILL_SUBAGENTS_FLAG")
        with open(flag_file, "w") as f:
            f.write(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": f"drain_stalled:{drain_count},timeout:{has_timeout},lock:{has_lock}",
                "action": "kill_all_subagents"
            }))
        state["last_intervention"] = now
        state["total_interventions"] = state.get("total_interventions", 0) + 1
        save_state(state)
        log(f"Intervention #{state['total_interventions']} recorded")
    else:
        log("No intervention needed — drain state healthy")


if __name__ == "__main__":
    main()
