#!/usr/bin/env python3
"""
OWL Autopilot v3 — Standby Monitor with Rate Limit Recovery
- Monitors team-chat.md for agent requests every 15 minutes
- Checks running processes (chaos test, 72h test, sync daemon)
- Posts status updates to team chat
- Handles rate limit errors with exponential backoff
- Auto-recovers from errors without operator intervention
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
CHAT_FILE = WORKSPACE / "shared-conversations" / "team-chat.md"
STATE_FILE = WORKSPACE / "progress" / "owl-autopilot-state.md"
LOG_FILE = WORKSPACE / "logs" / "owl-autopilot.log"

CHECK_INTERVAL = 900  # 15 minutes
RATE_LIMIT_BACKOFF = [60, 120, 300, 600, 1800]  # exponential backoff seconds
MAX_BACKOFF = 3600  # max 1 hour

# ─── Helpers ──────────────────────────────────────────────────────────────────

def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def log(msg):
    ts = now_utc()
    line = f"[{ts}] {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def read_chat():
    try:
        return CHAT_FILE.read_text(encoding="utf-8")
    except Exception:
        return ""

def append_chat(entry):
    try:
        content = read_chat()
        # Insert before the "Next Steps" section or at end
        marker = "\n## Next Steps"
        if marker in content:
            content = content.replace(marker, entry + "\n" + marker)
        else:
            content = content.rstrip() + "\n" + entry + "\n"
        CHAT_FILE.write_text(content, encoding="utf-8")
        log("Posted to team chat")
    except Exception as e:
        log(f"ERROR writing chat: {e}")

def get_python_processes():
    """Get list of running python processes with details."""
    procs = []
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-Process python -ErrorAction SilentlyContinue | "
             "Select-Object Id, ProcessName, @{N='Memory(MB)';Expression={[math]::Round($_.WorkingSet64/1MB,1)}}, "
             "CPU, @{N='CmdLine';Expression={(Get-CimInstance Win32_Process -Filter \"ProcessId=$($_.Id)\").CommandLine}} | "
             "ConvertTo-Json"],
            capture_output=True, text=True, timeout=15
        )
        if result.stdout.strip():
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                procs = [data]
            elif isinstance(data, list):
                procs = data
    except Exception as e:
        log(f"ERROR getting processes: {e}")
    return procs

def check_chaos_test(procs):
    """Check chaos test status from trace log."""
    trace = WORKSPACE / "stability" / "chaos_20x_trace.log"
    lines = []
    if trace.exists():
        try:
            with open(trace, "r") as f:
                all_lines = f.readlines()
                lines = all_lines[-5:]
        except Exception:
            pass
    return lines

def check_72h_test():
    """Check 72h test checkpoint status."""
    cp_file = WORKSPACE / "progress" / "11-1-b-checkpoints.json"
    if cp_file.exists():
        try:
            data = json.loads(cp_file.read_text())
            checkpoints = data.get("checkpoints", [])
            if checkpoints:
                last = checkpoints[-1]
                return {
                    "total": data.get("total_checkpoints", 0),
                    "passed": data.get("passed_checkpoints", 0),
                    "failed": data.get("failed_checkpoints", 0),
                    "last_status": last.get("status", "?"),
                    "last_drift": last.get("drift_score", 0),
                    "last_elapsed": last.get("elapsed_hours", 0),
                    "observers_alive": last.get("observer_health", {}).get("alive", 0),
                    "observers_degraded": last.get("observer_health", {}).get("degraded", 0),
                    "observers_dead": last.get("observer_health", {}).get("dead", 0),
                }
        except Exception:
            pass
    return None

def check_git_status():
    """Check if there are uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(WORKSPACE), capture_output=True, text=True, timeout=10
        )
        changed = [l for l in result.stdout.strip().split("\n") if l.strip()]
        return len(changed)
    except Exception:
        return -1

# ─── Main Loop ────────────────────────────────────────────────────────────────

def run_check():
    """Run a single monitoring check."""
    log("=== CHECK START ===")

    # 1. Check running processes
    procs = get_python_processes()
    proc_summary = []
    chaos_running = False
    test72_running = False
    sync_running = False
    pm2_demo_running = False

    for p in procs:
        cmd = p.get("CmdLine", "")
        pid = p.get("Id", "?")
        mem = p.get("Memory(MB)", "?")
        cpu = p.get("CPU", "?")

        if "chaos_20x_test" in cmd:
            chaos_running = True
            proc_summary.append(f"  chaos_20x  PID={pid} CPU={cpu}s MEM={mem}MB ✅")
        elif "test_11_1_b" in cmd:
            test72_running = True
            proc_summary.append(f"  72h_test   PID={pid} CPU={cpu}s MEM={mem}MB ✅")
        elif "progress-sync" in cmd:
            sync_running = True
            proc_summary.append(f"  progress-sync PID={pid} CPU={cpu}s MEM={mem}MB ✅")
        elif "integrated_demo" in cmd:
            pm2_demo_running = True
            proc_summary.append(f"  PM2_demo   PID={pid} CPU={cpu}s MEM={mem}MB ⚠️(low CPU)")

    if proc_summary:
        log("Running processes:\n" + "\n".join(proc_summary))
    else:
        log("No relevant Python processes running")

    # 2. Check chaos test trace
    if chaos_running:
        trace_lines = check_chaos_test(procs)
        if trace_lines:
            log("Chaos trace (last 5 lines):\n" + "".join(trace_lines).strip())

    # 3. Check 72h test
    cp = check_72h_test()
    if cp:
        log(f"72H Test: {cp['passed']}/{cp['total']} passed, "
            f"last={cp['last_status']}, drift={cp['last_drift']}, "
            f"observers: {cp['observers_alive']}A/{cp['observers_degraded']}D/{cp['observers_dead']}X")
        if cp["observers_dead"] > 0 or cp["last_status"] == "FAIL":
            log("⚠️ 72H TEST ISSUE — observer death or checkpoint failure detected")

    # 4. Check git status
    changes = check_git_status()
    if changes > 0:
        log(f"Git: {changes} uncommitted changes")
    elif changes == 0:
        log("Git: clean")

    # 5. Check if chat has been updated since last check
    chat_mtime = CHAT_FILE.stat().st_mtime if CHAT_FILE.exists() else 0
    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
        except Exception:
            state = {}

    last_mtime = state.get("chat_mtime", 0)
    if chat_mtime > last_mtime and last_mtime > 0:
        log("📢 Team chat has new content since last check")
        # Read last few entries to see if anyone needs help
        chat_content = read_chat()
        # Check for help requests
        help_keywords = ["help", "need", "stuck", "error", "failed", "issue", "problem", "broken"]
        recent = chat_content[-3000:]  # last 3000 chars
        for kw in help_keywords:
            if kw in recent.lower():
                log(f"⚠️ Possible help request detected (keyword: '{kw}')")
                break

    # Save state
    state["chat_mtime"] = chat_mtime
    state["last_check"] = now_utc()
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception:
        pass

    # 6. Post periodic status to chat (every 4 checks = ~1 hour)
    check_count = state.get("check_count", 0) + 1
    state["check_count"] = check_count

    if check_count % 4 == 0:
        # Hourly status post
        status_lines = [
            f"\n---\n",
            f"## [OWL] {now_utc()} — Autopilot Status Update\n",
            f"### System Health\n",
        ]
        status_lines.append(f"| Process | Status |")
        status_lines.append(f"|---------|--------|")
        status_lines.append(f"| Chaos 20x Test | {'✅ Running' if chaos_running else '❌ Stopped'} |")
        status_lines.append(f"| 72H Test | {'✅ Running' if test72_running else '❌ Stopped'} |")
        status_lines.append(f"| Progress Sync | {'✅ Running' if sync_running else '❌ Stopped'} |")
        if cp:
            status_lines.append(f"| 72H Checkpoints | {cp['passed']}✅ / {cp['failed']}❌ |")
            status_lines.append(f"| Observers | {cp['observers_alive']} alive / {cp['observers_degraded']} degraded / {cp['observers_dead']} dead |")
        status_lines.append(f"\n*OWL monitoring active. Post requests in chat for assistance.*\n")

        entry = "\n".join(status_lines)
        append_chat(entry)

    try:
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception:
        pass

    log("=== CHECK COMPLETE ===\n")


def main():
    log("🦉 OWL Autopilot v3 Starting")
    log(f"Workspace: {WORKSPACE}")
    log(f"Chat file: {CHAT_FILE}")
    log(f"Check interval: {CHECK_INTERVAL}s ({CHECK_INTERVAL//60} min)")
    log(f"Rate limit backoff: {RATE_LIMIT_BACKOFF}")

    backoff_idx = 0
    consecutive_errors = 0

    while True:
        try:
            run_check()
            # Reset backoff on success
            backoff_idx = 0
            consecutive_errors = 0
            sleep_time = CHECK_INTERVAL

        except KeyboardInterrupt:
            log("Autopilot stopped by user")
            break

        except Exception as e:
            consecutive_errors += 1
            log(f"ERROR in check #{consecutive_errors}: {e}")

            # Exponential backoff on repeated errors (rate limits, etc.)
            if consecutive_errors >= 2:
                backoff_idx = min(backoff_idx + 1, len(RATE_LIMIT_BACKOFF) - 1)
                sleep_time = RATE_LIMIT_BACKOFF[backoff_idx]
                log(f"Rate limit backoff: sleeping {sleep_time}s (level {backoff_idx})")
            else:
                sleep_time = CHECK_INTERVAL

        log(f"Sleeping {sleep_time}s until next check...")
        time.sleep(sleep_time)


if __name__ == "__main__":
    main()
