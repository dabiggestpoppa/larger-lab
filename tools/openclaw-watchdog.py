#!/usr/bin/env python3
"""
OpenClaw Gateway Watchdog
=========================
Simple, single watchdog. Checks gateway health every 30s.
Restarts if down. Prevents duplicate instances via PID file.

Usage:
    python tools/openclaw-watchdog.py          # Run continuously
    python tools/openclaw-watchdog.py --once   # Single check
    python tools/openclaw-watchdog.py --stop   # Stop running watchdog
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = 18790
HEALTH_URL = f"http://{GATEWAY_HOST}:{GATEWAY_PORT}/health"
PID_FILE = Path(__file__).parent.parent / ".openclaw-watchdog.pid"
LOG_FILE = Path(os.environ.get("TEMP", "/tmp")) / "openclaw" / "watchdog.log"
CHECK_INTERVAL = 30  # seconds
MAX_RESTARTS_PER_HOUR = 5

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def is_gateway_up():
    try:
        import urllib.request
        req = urllib.request.Request(HEALTH_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode()
            data = json.loads(body) if body else {}
            return data.get("ok", False)
    except Exception:
        return False

def start_gateway():
    workspace = Path(__file__).parent.parent
    node_exe = r"C:\Program Files\nodejs\node.exe"
    openclaw_js = Path(os.environ.get("APPDATA", "")) / "npm" / "node_modules" / "openclaw" / "dist" / "index.js"
    
    if not openclaw_js.exists():
        log(f"ERROR: OpenClaw not found at {openclaw_js}")
        return False
    
    log("Starting OpenClaw gateway...")
    proc = subprocess.Popen(
        [node_exe, str(openclaw_js), "gateway", "run", "--port", str(GATEWAY_PORT), "--allow-unconfigured"],
        cwd=str(workspace),
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    log(f"Gateway started (PID {proc.pid})")
    
    # Wait for it to come up
    for i in range(10):
        time.sleep(2)
        if is_gateway_up():
            log("Gateway is up and healthy")
            return True
    log("WARNING: Gateway started but health check failed")
    return False

def check_once():
    if is_gateway_up():
        log("Gateway: OK")
        return True
    else:
        log("Gateway: DOWN — attempting restart")
        return start_gateway()

def run_watchdog():
    # Write PID file
    PID_FILE.write_text(str(os.getpid()))
    log(f"Watchdog started (PID {os.getpid()}), checking every {CHECK_INTERVAL}s")
    
    restart_count = 0
    last_restart_time = 0
    
    def cleanup(signum=None, frame=None):
        log("Watchdog stopping")
        PID_FILE.unlink(missing_ok=True)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    try:
        while True:
            if not is_gateway_up():
                now = time.time()
                # Reset counter if more than an hour since last restart
                if now - last_restart_time > 3600:
                    restart_count = 0
                
                if restart_count >= MAX_RESTARTS_PER_HOUR:
                    log(f"ERROR: Max restarts ({MAX_RESTARTS_PER_HOUR}/hour) reached. Manual intervention needed.")
                else:
                    log(f"Gateway down — restart attempt {restart_count + 1}/{MAX_RESTARTS_PER_HOUR}")
                    start_gateway()
                    restart_count += 1
                    last_restart_time = now
            
            time.sleep(CHECK_INTERVAL)
    finally:
        PID_FILE.unlink(missing_ok=True)

def stop_watchdog():
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text().strip())
        try:
            os.kill(pid, signal.SIGTERM)
            log(f"Watchdog stopped (PID {pid})")
        except ProcessLookupError:
            log(f"Watchdog not running (stale PID file removed)")
        except Exception as e:
            log(f"Error stopping watchdog: {e}")
        PID_FILE.unlink(missing_ok=True)
    else:
        log("Watchdog not running (no PID file)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenClaw Gateway Watchdog")
    parser.add_argument("--once", action="store_true", help="Single check")
    parser.add_argument("--stop", action="store_true", help="Stop running watchdog")
    args = parser.parse_args()
    
    if args.stop:
        stop_watchdog()
    elif args.once:
        check_once()
    else:
        run_watchdog()
