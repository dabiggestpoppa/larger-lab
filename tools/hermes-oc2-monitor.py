"""
Hermes OC2 Monitor — Cron-style monitoring script for OC2 gateway.
=============================================================
Run by Hermes agent on schedule (every 30 min).
Checks health, detects errors, performs repairs, logs results.

Usage: python tools/hermes-oc2-monitor.py [--repair] [--full-reset]
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
OC2_PORT = 18790
OC2_HOST = "127.0.0.1"
HEALTH_URL = f"http://{OC2_HOST}:{OC2_PORT}/health"
WORKSPACE = Path(__file__).parent.parent
OPENCLAW_HOME = WORKSPACE / ".openclaw-2"
GATEWAY_CMD = OPENCLAW_HOME / "gateway.cmd"
SESSIONS_FILE = OPENCLAW_HOME / ".openclaw" / "agents" / "main" / "sessions" / "sessions.json"
LOG_DIR = WORKSPACE / "logs"
MONITOR_LOG = LOG_DIR / "hermes-oc2-monitor.log"
WATCHDOG_LOG = LOG_DIR / "oc2-watchdog.log"
TEAM_CHAT = WORKSPACE / "shared-conversations" / "team-chat.md"
MAX_RESTARTS_PER_HOUR = 5
STALE_SESSION_HOURS = 1
MEMORY_WARNING_MB = 500
MEMORY_CRITICAL_MB = 1000

# ─── Logging ──────────────────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(MONITOR_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def log_team_chat(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"\n## [HR] {ts} — OC2 Maintenance\n{msg}\n"
    with open(TEAM_CHAT, "a", encoding="utf-8") as f:
        f.write(entry)

# ─── Health Checks ─────────────────────────────────────────────────────────────
def check_health() -> dict:
    """Check OC2 gateway health endpoint."""
    try:
        req = urllib.request.Request(HEALTH_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return {"ok": True, "status": data.get("status", "unknown"), "data": data}
    except Exception as e:
        return {"ok": False, "status": "unreachable", "error": str(e)}

def check_node_process() -> dict:
    """Check if OC2 node process is running via netstat."""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=10
        )
        pid = None
        for line in result.stdout.splitlines():
            if f":{OC2_PORT}" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = int(parts[-1])
                break
        if pid:
            # Get memory for this PID
            mem_result = subprocess.run(
                ["powershell", "-Command",
                 f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue).WorkingSet64 / 1MB"],
                capture_output=True, text=True, timeout=5
            )
            mem = float(mem_result.stdout.strip()) if mem_result.stdout.strip() else 0
            return {"running": True, "pid": pid, "memory_mb": round(mem, 1)}
        return {"running": False}
    except Exception as e:
        return {"running": False, "error": str(e)}

def check_sessions() -> dict:
    """Check for stale sessions."""
    if not SESSIONS_FILE.exists():
        return {"count": 0, "stale": []}
    try:
        with open(SESSIONS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        sessions = data.get("sessions", data)  # Handle both formats
        count = len(sessions) if isinstance(sessions, dict) else 0
        stale = []
        now = datetime.now(timezone.utc)
        for key, val in (sessions.items() if isinstance(sessions, dict) else {}):
            ts = val.get("updatedAt") or val.get("timestamp") if isinstance(val, dict) else None
            if ts:
                try:
                    from datetime import datetime as dt
                    session_time = dt.fromisoformat(ts.replace("Z", "+00:00"))
                    age_hours = (now - session_time).total_seconds() / 3600
                    if age_hours > STALE_SESSION_HOURS:
                        stale.append({"key": key, "age_hours": round(age_hours, 1)})
                except Exception:
                    pass
        return {"count": count, "stale": stale}
    except Exception as e:
        return {"count": 0, "stale": [], "error": str(e)}

def check_watchdog_log() -> list:
    """Check recent watchdog log for errors."""
    if not WATCHDOG_LOG.exists():
        return []
    try:
        with open(WATCHDOG_LOG, encoding="utf-8") as f:
            lines = f.readlines()
        recent = lines[-50:]  # Last 50 lines
        errors = [l.strip() for l in recent if any(kw in l.lower() for kw in ["error", "restart", "stuck", "timeout", "fail"])]
        return errors[-10:]  # Last 10 errors
    except Exception:
        return []

# ─── Repairs ──────────────────────────────────────────────────────────────────
def kill_oc2():
    """Kill OC2 node process."""
    try:
        subprocess.run(
            ["powershell", "-Command",
             f"Get-Process -Name node -ErrorAction SilentlyContinue | "
             f"Where-Object {{ $_.CommandLine -like '*{OC2_PORT}*' }} | "
             f"Stop-Process -Force"],
            capture_output=True, timeout=10
        )
        time.sleep(3)
        log("Killed OC2 process")
        return True
    except Exception as e:
        log(f"Failed to kill OC2: {e}", "ERROR")
        return False

def start_oc2():
    """Start OC2 gateway."""
    try:
        env = os.environ.copy()
        env["OPENCLAW_HOME"] = str(OPENCLAW_HOME)
        subprocess.Popen(
            ["cmd", "/c", str(GATEWAY_CMD)],
            env=env,
            cwd=str(OPENCLAW_HOME.parent),
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Wait for health
        for i in range(15):
            time.sleep(1)
            health = check_health()
            if health["ok"]:
                log(f"OC2 started successfully (attempt {i+1}s)")
                return True
        log("OC2 started but health check failed", "WARN")
        return False
    except Exception as e:
        log(f"Failed to start OC2: {e}", "ERROR")
        return False

def clean_stale_sessions(stale: list) -> int:
    """Remove stale sessions from sessions.json."""
    if not stale:
        return 0
    try:
        with open(SESSIONS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        sessions = data.get("sessions", data)
        removed = 0
        for s in stale:
            key = s["key"]
            if key in sessions:
                del sessions[key]
                removed += 1
                log(f"Removed stale session: {key} (age: {s['age_hours']}h)")
        if "sessions" in data:
            data["sessions"] = sessions
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return removed
    except Exception as e:
        log(f"Failed to clean sessions: {e}", "ERROR")
        return 0

def full_reset():
    """Nuclear option: kill everything, clear sessions, restart."""
    log("Performing FULL RESET", "WARN")
    kill_oc2()
    time.sleep(2)
    # Clear sessions
    try:
        empty = {"version": 1, "sessions": {}}
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(empty, f, indent=2)
        log("Cleared sessions.json")
    except Exception as e:
        log(f"Failed to clear sessions: {e}", "ERROR")
    # Clear lock files
    for lock in OPENCLAW_HOME.rglob("*.lock"):
        try:
            lock.unlink()
            log(f"Removed lock: {lock.name}")
        except Exception:
            pass
    return start_oc2()

# ─── Main Monitor Loop ────────────────────────────────────────────────────────
def run_cycle(repair: bool = True, full_reset: bool = False) -> dict:
    """Run one monitoring cycle. Returns status dict."""
    log("=" * 60)
    log("Starting OC2 monitoring cycle")

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "health": None,
        "process": None,
        "sessions": None,
        "errors": [],
        "action": "none",
        "status": "OK"
    }

    # 1. Health check
    health = check_health()
    result["health"] = health
    if health["ok"]:
        log(f"Health: {health['status']} ✓")
    else:
        log(f"Health: DOWN — {health.get('error', 'unknown')}", "ERROR")
        result["errors"].append("health_down")

    # 2. Process check
    proc = check_node_process()
    result["process"] = proc
    if proc["running"]:
        mem = proc.get("memory_mb", 0)
        log(f"Process: PID {proc.get('pid')}, Memory: {mem}MB")
        if mem > MEMORY_CRITICAL_MB:
            log(f"CRITICAL: Memory {mem}MB > {MEMORY_CRITICAL_MB}MB", "ERROR")
            result["errors"].append("memory_critical")
        elif mem > MEMORY_WARNING_MB:
            log(f"WARNING: Memory {mem}MB > {MEMORY_WARNING_MB}MB", "WARN")
    else:
        log("Process: NOT RUNNING", "ERROR")
        result["errors"].append("process_down")

    # 3. Session check
    sessions = check_sessions()
    result["sessions"] = sessions
    log(f"Sessions: {sessions['count']} total, {len(sessions.get('stale', []))} stale")
    if sessions.get("stale"):
        for s in sessions["stale"]:
            log(f"  Stale: {s['key']} (age: {s['age_hours']}h)", "WARN")

    # 4. Watchdog log check
    wd_errors = check_watchdog_log()
    if wd_errors:
        log(f"Watchdog errors (recent): {len(wd_errors)}", "WARN")
        for e in wd_errors[-3:]:
            log(f"  {e[:100]}")

    # ─── Decision & Repair ──────────────────────────────────────────────────
    needs_restart = "health_down" in result["errors"] or "process_down" in result["errors"]
    needs_session_clean = bool(sessions.get("stale"))

    if full_reset and needs_restart:
        result["action"] = "full_reset"
        if repair:
            success = full_reset()
            result["status"] = "RECOVERED" if success else "FAILED"
            log(f"Full reset: {'SUCCESS' if success else 'FAILED'}", "INFO" if success else "ERROR")
        else:
            log("Full reset needed but --repair not specified", "WARN")

    elif needs_restart:
        result["action"] = "restart"
        if repair:
            kill_oc2()
            success = start_oc2()
            result["status"] = "RECOVERED" if success else "FAILED"
            log(f"Restart: {'SUCCESS' if success else 'FAILED'}", "INFO" if success else "ERROR")
        else:
            log("Restart needed but --repair not specified", "WARN")

    elif needs_session_clean:
        result["action"] = "clean_sessions"
        if repair:
            removed = clean_stale_sessions(sessions["stale"])
            result["status"] = f"CLEANED_{removed}_SESSIONS"
            log(f"Cleaned {removed} stale sessions")
        else:
            log("Session cleanup needed but --repair not specified", "WARN")

    # ─── Escalation ────────────────────────────────────────────────────────
    if result["status"] == "FAILED":
        msg = f"- **Issue:** OC2 gateway down + restart failed\n- **Action:** Hermes attempted restart\n- **Result:** FAILED — needs manual intervention\n- **Errors:** {', '.join(result['errors'])}"
        log_team_chat(msg)
        log("ESCALATED to team-chat", "ERROR")

    elif result["action"] != "none":
        msg = f"- **Issue:** {', '.join(result['errors']) if result['errors'] else 'Stale sessions'}\n- **Action:** {result['action']}\n- **Result:** {result['status']}"
        log_team_chat(msg)

    # Final log line
    log(f"Cycle complete: status={result['status']}, action={result['action']}")
    return result

# ─── Entry Point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Hermes OC2 Monitor")
    parser.add_argument("--repair", action="store_true", help="Auto-repair issues")
    parser.add_argument("--full-reset", action="store_true", help="Full reset if needed")
    parser.add_argument("--loop", action="store_true", help="Run in loop every 30 min")
    args = parser.parse_args()

    if args.loop:
        log("Starting continuous monitoring (30 min interval)")
        while True:
            run_cycle(repair=args.repair, full_reset=args.full_reset)
            time.sleep(1800)  # 30 minutes
    else:
        result = run_cycle(repair=args.repair, full_reset=args.full_reset)
        print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
