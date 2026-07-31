"""
PM2 WATCHDOG — Safety layer for OC2 + Live Trading
===================================================
Monitors critical processes and restarts them if they die.
Runs silently in background. Logs to logs/pm2_watchdog.log.

Processes monitored:
1. OC2 Gateway (openclaw) — ws://127.0.0.1:18790
2. Live Bridge (cerebus_live_bridge.py) — trading execution
3. Guardian (cerebus_guardian.py) — process monitor
4. Telegram Gateway (telegram_gateway.py) — bot
5. Session Cleanup (oc2_session_cleanup.py) — session management
6. OCE Backend (uvicorn) — API server
7. SRRA-OPC API (api_server.py) — frontend API
"""
import subprocess
import time
import os
import sys
import json
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "pm2_watchlog.log")
PID_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "pm2_watchdog.pid")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_PYTHON = os.path.join(BASE, ".venv", "Scripts", "python.exe")

# ── PROCESS DEFINITIONS ──────────────────────────────────────────
PROCESSES = {
    "oc2_gateway": {
        "check": "port",
        "port": 18790,
        "start_cmd": ["openclaw", "gateway", "start"],
        "critical": True,
    },
    "live_bridge": {
        "check": "process_name",
        "name": "cerebus_live_bridge.py",
        "start_cmd": [VENV_PYTHON, os.path.join(BASE, "quant-lab", "mt5", "cerebus_live_bridge.py"),
                       "--symbols", "EURJPY.PRO,EURNZD.PRO,GBPNZD.PRO,EURAUD.PRO,GBPAUD.PRO,GBPCAD.PRO",
                       "--lot-size", "0.01"],
        "critical": True,
    },
    "guardian": {
        "check": "process_name",
        "name": "cerebus_guardian.py",
        "start_cmd": [VENV_PYTHON, os.path.join(BASE, "quant-lab", "mt5", "cerebus_guardian.py")],
        "critical": True,
    },
    "telegram_gateway": {
        "check": "process_name",
        "name": "telegram_gateway.py",
        "start_cmd": [VENV_PYTHON, os.path.join(BASE, "scripts", "telegram_gateway.py")],
        "critical": False,
    },
    "session_cleanup": {
        "check": "process_name",
        "name": "oc2_session_cleanup.py",
        "start_cmd": [VENV_PYTHON, os.path.join(BASE, "scripts", "oc2_session_cleanup.py"), "--watch"],
        "critical": False,
    },
    "oce_backend": {
        "check": "port",
        "port": 8000,
        "start_cmd": None,  # Don't auto-restart, managed separately
        "critical": False,
    },
}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

def check_port(port):
    """Check if a port is listening."""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                return True
        return False
    except:
        return False

def check_process(name):
    """Check if a process with given name is running."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        return name.lower() in result.stdout.lower()
    except:
        return False

def check_oc2_health():
    """Check OC2 gateway health via HTTP."""
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:18790/health", timeout=3)
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        return data.get("ok", False)
    except:
        return False

def start_process(name, cmd):
    """Start a process."""
    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        log(f"  ✅ Started {name}")
        return True
    except Exception as e:
        log(f"  ❌ Failed to start {name}: {e}")
        return False

def check_process_status(name, cfg):
    """Check if a process is healthy."""
    if cfg["check"] == "port":
        return check_port(cfg["port"])
    elif cfg["check"] == "process_name":
        return check_process(cfg["name"])
    return False

def main():
    # Write PID
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    log("=" * 60)
    log("PM2 WATCHDOG STARTED")
    log(f"Monitoring {len(PROCESSES)} processes")
    log("=" * 60)

    restart_counts = {name: 0 for name in PROCESSES}
    max_restarts = 5  # Don't restart more than 5 times per cycle

    while True:
        try:
            status_lines = []
            any_critical_down = False

            for name, cfg in PROCESSES.items():
                alive = check_process_status(name, cfg)
                status = "✅" if alive else "❌"
                status_lines.append(f"  {status} {name}")

                if not alive:
                    is_critical = cfg.get("critical", False)
                    if is_critical:
                        any_critical_down = True

                    # Try to restart if we have a start command and haven't exceeded max restarts
                    if cfg.get("start_cmd") and restart_counts[name] < max_restarts:
                        log(f"⚠️ {name} is DOWN (critical={is_critical}), restarting... (attempt {restart_counts[name]+1}/{max_restarts})")
                        if start_process(name, cfg["start_cmd"]):
                            restart_counts[name] += 1
                            time.sleep(5)  # Give it time to start
                    elif restart_counts[name] >= max_restarts:
                        log(f"🚨 {name} exceeded max restarts ({max_restarts}) — manual intervention needed!")

            # Log status every 5 minutes
            now = datetime.now()
            if now.second < 10:  # Log once per minute at :00
                log("STATUS CHECK:")
                for line in status_lines:
                    log(line)
                if any_critical_down:
                    log("⚠️ CRITICAL PROCESS DOWN — check logs!")

            # Reset restart counts every hour
            if now.minute == 0 and now.second < 10:
                restart_counts = {name: 0 for name in PROCESSES}
                log("Restart counters reset")

            time.sleep(10)  # Check every 10 seconds

        except KeyboardInterrupt:
            log("Watchdog stopped by user")
            break
        except Exception as e:
            log(f"Watchdog error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
