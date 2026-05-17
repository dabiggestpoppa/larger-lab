"""
OC2 Watchdog — Self-healing monitor for OpenClaw 2 Gateway
==========================================================
Runs as a background process. Checks OC2 health every 60 seconds.
Restarts gateway if it goes down. Logs all actions.

Usage: python tools/oc2-watchdog.py
"""
import subprocess
import sys
import time
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
OC2_PORT = 18790
OC2_HOST = "127.0.0.1"
HEALTH_URL = f"http://{OC2_HOST}:{OC2_PORT}/health"
GATEWAY_CMD = [
    "node",
    str(Path.home() / "AppData/Roaming/npm/node_modules/openclaw/dist/index.js"),
    "gateway", "run", "--port", str(OC2_PORT), "--allow-unconfigured"
]
OPENCLAW_HOME = Path(__file__).parent.parent / ".openclaw-2"
LOG_FILE = Path(__file__).parent.parent / "logs" / "oc2-watchdog.log"
CHECK_INTERVAL = 60  # seconds
RESTART_COOLDOWN = 10  # seconds between restart attempts
MAX_RESTARTS_PER_HOUR = 10

# ─── Helpers ──────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def check_health() -> bool:
    """Basic health check — is the gateway responding?"""
    try:
        req = urllib.request.Request(HEALTH_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("ok", False)
    except Exception:
        return False

def check_deep_health() -> tuple[bool, str]:
    """
    Deep health check — verify OC2 is actually processing messages, not just alive.
    Returns (healthy, reason).
    
    Checks:
    1. Health endpoint returns ok=true
    2. Gateway status is 'live' (not 'starting', 'error', etc.)
    3. No zombie state — process is actually responding to requests
    """
    # Layer 1: Basic health
    try:
        req = urllib.request.Request(HEALTH_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            if not data.get("ok", False):
                return False, f"Health endpoint returned ok=false: {data}"
            status = data.get("status", "unknown")
            if status != "live":
                return False, f"Gateway status is '{status}', expected 'live'"
    except Exception as e:
        return False, f"Health endpoint unreachable: {e}"
    
    # Layer 2: Verify it's not a stale/cached response by checking twice
    time.sleep(1)
    try:
        req2 = urllib.request.Request(HEALTH_URL, method="GET")
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            data2 = json.loads(resp2.read())
            if not data2.get("ok", False):
                return False, "Health check flaky — second check failed"
    except Exception as e:
        return False, f"Health check flaky — second request failed: {e}"
    
    return True, "All checks passed"

def is_node_running() -> bool:
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq node.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        return "node.exe" in result.stdout
    except Exception:
        return False

def get_oc2_pid() -> int | None:
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"Get-Process -Name node -ErrorAction SilentlyContinue | "
             f"Where-Object {{ $_.CommandLine -like '*18790*' }} | "
             f"Select-Object -ExpandProperty Id"],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        pid_str = result.stdout.strip()
        return int(pid_str) if pid_str else None
    except Exception:
        return None

def kill_existing():
    pid = get_oc2_pid()
    if pid:
        log(f"Killing existing OC2 process (PID {pid})")
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                          capture_output=True, timeout=10)
            time.sleep(2)
        except Exception as e:
            log(f"Failed to kill PID {pid}: {e}")

def start_gateway() -> bool:
    log("Starting OC2 Gateway...")
    try:
        env = {
            "OPENCLAW_HOME": str(OPENCLAW_HOME),
            "TMPDIR": str(Path.home() / "AppData/Local/Temp"),
            "PATH": str(Path.home() / "AppData/Roaming/npm") + ";" + 
                    str(Path("C:/Program Files/nodejs")) + ";" + 
                    subprocess.os.environ.get("PATH", "")
        }
        node_exe = str(Path.home() / "AppData/Roaming/npm/node_modules/openclaw/dist/index.js")
        # Use DETACHED_PROCESS + CREATE_NO_WINDOW for silent background execution
        subprocess.Popen(
            ["node", node_exe, "gateway", "run", "--port", str(OC2_PORT), "--allow-unconfigured"],
            env={**subprocess.os.environ, **env},
            cwd=str(OPENCLAW_HOME.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
            close_fds=True
        )
        # Wait for it to come up
        for i in range(15):
            time.sleep(1)
            if check_health():
                log(f"OC2 Gateway started successfully (attempt {i+1}s)")
                return True
        log("OC2 Gateway started but health check failed")
        return False
    except Exception as e:
        log(f"Failed to start gateway: {e}")
        return False

# ─── Restart Logic ────────────────────────────────────────────────────────────
def _do_restart(restart_count: int, last_restart_time: float):
    """Kill existing OC2 and restart it."""
    now = time.time()
    
    # Reset counter if more than 1 hour since last restart
    if now - last_restart_time > 3600:
        restart_count = 0
    
    if restart_count >= MAX_RESTARTS_PER_HOUR:
        log(f"MAX RESTARTS ({MAX_RESTARTS_PER_HOUR}/hr) reached. Waiting 5 min...")
        time.sleep(300)
        return
    
    # Cooldown between restarts
    if now - last_restart_time < RESTART_COOLDOWN:
        time.sleep(RESTART_COOLDOWN - (now - last_restart_time))
    
    kill_existing()
    success = start_gateway()
    
    if success:
        log(f"OC2 restarted successfully (restart #{restart_count + 1})")
    else:
        log(f"OC2 restart FAILED (restart #{restart_count + 1})")

# ─── Main Loop ────────────────────────────────────────────────────────────────
def main():
    log("=" * 60)
    log("OC2 Watchdog started")
    log(f"Health URL: {HEALTH_URL}")
    log(f"Check interval: {CHECK_INTERVAL}s")
    log(f"OpenClaw Home: {OPENCLAW_HOME}")
    log("=" * 60)

    restart_count = 0
    last_restart_time = 0.0

    # Track consecutive "healthy but not really" checks for flaky detection
    deep_fail_count = 0
    
    while True:
        try:
            # Layer 1: Quick basic check
            basic_healthy = check_health()
            
            if not basic_healthy:
                # OC2 is completely down — restart immediately
                log("OC2 DOWN — basic health check failed")
                _do_restart(restart_count, last_restart_time)
                restart_count += 1
                last_restart_time = time.time()
                time.sleep(CHECK_INTERVAL)
                continue
            
            # Layer 2: Deep health check — is OC2 actually processing?
            deep_ok, reason = check_deep_health()
            
            if deep_ok:
                pid = get_oc2_pid()
                log(f"OC2 OK (PID {pid}) — {reason}")
                restart_count = 0
                deep_fail_count = 0
            else:
                deep_fail_count += 1
                log(f"OC2 DEADLOCK DETECTED (streak: {deep_fail_count}) — {reason}")
                
                # If deep check fails 2+ times in a row, OC2 is zombie — restart it
                if deep_fail_count >= 2:
                    log(f"OC2 ZOMBIE STATE — restarting (consecutive failures: {deep_fail_count})")
                    _do_restart(restart_count, last_restart_time)
                    restart_count += 1
                    last_restart_time = time.time()
                    deep_fail_count = 0
                else:
                    log(f"Waiting for next check before restarting (failure {deep_fail_count}/2)")

        except KeyboardInterrupt:
            log("Watchdog stopped by user")
            break
        except Exception as e:
            log(f"Watchdog error: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
