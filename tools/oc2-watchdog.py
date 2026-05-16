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
    try:
        req = urllib.request.Request(HEALTH_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("ok", False)
    except Exception:
        return False

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
            capture_output=True, text=True, timeout=5
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
        # Use cmd /c to start in background (CREATE_NO_WINDOW doesn't work reliably from Python)
        cmd_line = f'node "{Path.home() / "AppData/Roaming/npm/node_modules/openclaw/dist/index.js"}" gateway run --port {OC2_PORT} --allow-unconfigured'
        subprocess.Popen(
            ["cmd", "/c", "start", "/B", cmd_line],
            env={**subprocess.os.environ, **env},
            cwd=str(OPENCLAW_HOME.parent),
            shell=True
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

    while True:
        try:
            healthy = check_health()
            
            if healthy:
                pid = get_oc2_pid()
                log(f"OC2 OK (PID {pid})")
                # Reset restart counter on successful run
                restart_count = 0
            else:
                log("OC2 UNHEALTHY — checking if process exists...")
                
                now = time.time()
                # Reset counter if more than 1 hour since last restart
                if now - last_restart_time > 3600:
                    restart_count = 0
                
                if restart_count >= MAX_RESTARTS_PER_HOUR:
                    log(f"MAX RESTARTS ({MAX_RESTARTS_PER_HOUR}/hr) reached. Waiting 5 min...")
                    time.sleep(300)
                    restart_count = 0
                    continue
                
                # Cooldown between restarts
                if now - last_restart_time < RESTART_COOLDOWN:
                    time.sleep(RESTART_COOLDOWN - (now - last_restart_time))
                
                kill_existing()
                success = start_gateway()
                last_restart_time = time.time()
                restart_count += 1
                
                if success:
                    log(f"OC2 restarted successfully (restart #{restart_count})")
                else:
                    log(f"OC2 restart FAILED (restart #{restart_count})")

        except KeyboardInterrupt:
            log("Watchdog stopped by user")
            break
        except Exception as e:
            log(f"Watchdog error: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
