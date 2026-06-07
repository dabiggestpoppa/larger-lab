#!/usr/bin/env python3
"""
OC2 State Tracker — simple monitor, NO auto-restarts.

Just logs when OC2 goes down and why. That's it.
Run: python tools/oc2_state_tracker.py
"""
import json
import time
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

GATEWAY_URL = "http://127.0.0.1:18790/health"
LOG_FILE = Path("logs/oc2_state.log")
STATE_FILE = Path("logs/oc2_state.json")
CHECK_INTERVAL = 120  # 2 minutes — don't spam

def log(msg):
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def check_health():
    try:
        import urllib.request
        with urllib.request.urlopen(GATEWAY_URL, timeout=8) as r:
            return True, json.loads(r.read().decode()).get("status", "live")
    except Exception as e:
        return False, str(e)

def check_port():
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command",
             "Get-NetTCPConnection -State Listen -LocalPort 18790 -ErrorAction SilentlyContinue | Select-Object -First 1 OwningProcess"],
            text=True, timeout=10
        ).strip()
        if out and out.isdigit():
            return True, int(out)
        return False, None
    except Exception:
        return False, None

def get_last_log_lines(n=5):
    log_path = Path.home() / "AppData/Local/Temp/openclaw/openclaw-2026-06-06.log"
    if not log_path.exists():
        return []
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-n:]
        result = []
        for line in lines:
            try:
                obj = json.loads(line)
                result.append(f"  {obj.get('time','')} {obj.get('message','')[:120]}")
            except:
                result.append(f"  {line.strip()[:120]}")
        return result
    except Exception:
        return []

def main():
    log("=== OC2 State Tracker started (NO auto-restart, logging only) ===")
    log(f"Check interval: {CHECK_INTERVAL}s")

    state = {"last_status": "unknown", "last_change": None, "downtime_count": 0}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
        except:
            pass

    while True:
        try:
            healthy, health_msg = check_health()
            port_listening, pid = check_port()

            now = datetime.now().isoformat(timespec="seconds")

            if healthy and port_listening:
                status = f"UP (PID {pid}, {health_msg})"
            elif port_listening and not healthy:
                status = f"DEGRADED (PID {pid}, health: {health_msg})"
            else:
                status = f"DOWN ({health_msg})"

            # Only log on state change
            if status != state["last_status"]:
                state["last_status"] = status
                state["last_change"] = now
                if "DOWN" in status:
                    state["downtime_count"] = state.get("downtime_count", 0) + 1
                    log(f"🔴 OC2 {status} — downtime #{state['downtime_count']}")
                    # Log last few gateway lines for context
                    for line in get_last_log_lines(5):
                        log(line)
                elif "DEGRADED" in status:
                    log(f"🟡 OC2 {status}")
                else:
                    log(f"🟢 OC2 {status}")

                STATE_FILE.write_text(json.dumps(state, indent=2))

        except KeyboardInterrupt:
            log("Interrupted, exiting")
            break
        except Exception as e:
            log(f"Tracker error: {e}")

        try:
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
