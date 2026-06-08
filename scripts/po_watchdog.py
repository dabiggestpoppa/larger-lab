#!/usr/bin/env python3
"""
PO Watchdog — monitors telegram gateway and restarts if it dies.
Runs as a background process. Checks every 60 seconds.
"""
import subprocess
import time
import os
import sys
import signal
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GATEWAY_SCRIPT = os.path.join(SCRIPT_DIR, "telegram_gateway.py")
LOG_FILE = os.path.join(SCRIPT_DIR, "..", "logs", "po_watchdog.log")
CHECK_INTERVAL = 60  # seconds
MAX_RESTARTS = 10
RESTART_COOLDOWN = 300  # 5 minutes after max restarts

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

def is_gateway_running():
    """Check if telegram_gateway.py process is alive."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*telegram*' } | Select-Object -ExpandProperty Id"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() != ""
    except:
        return False

def start_gateway():
    """Start the telegram gateway process."""
    try:
        subprocess.Popen(
            [sys.executable, GATEWAY_SCRIPT],
            cwd=SCRIPT_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        log("Gateway started")
        return True
    except Exception as e:
        log(f"Failed to start gateway: {e}")
        return False

def main():
    log("=" * 60)
    log("PO Watchdog started")
    log(f"Monitoring: {GATEWAY_SCRIPT}")
    log(f"Check interval: {CHECK_INTERVAL}s")
    log("=" * 60)

    restart_count = 0
    last_restart_time = 0

    def handle_signal(signum, frame):
        log(f"Watchdog received signal {signum}, shutting down")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while True:
        try:
            if not is_gateway_running():
                log("Gateway DOWN — restarting...")

                # Check restart cooldown
                now = time.time()
                if restart_count >= MAX_RESTARTS:
                    if now - last_restart_time < RESTART_COOLDOWN:
                        log(f"Max restarts ({MAX_RESTARTS}) reached, waiting {RESTART_COOLDOWN}s cooldown...")
                        time.sleep(RESTART_COOLDOWN)
                        restart_count = 0
                    else:
                        restart_count = 0

                if start_gateway():
                    restart_count += 1
                    last_restart_time = now
                    log(f"Restart #{restart_count}")
                    # Wait for gateway to initialize
                    time.sleep(10)
                else:
                    log("Failed to start gateway, retrying in 30s...")
                    time.sleep(30)
            else:
                # Reset restart count if gateway has been running fine
                if restart_count > 0 and time.time() - last_restart_time > 300:
                    restart_count = 0

        except Exception as e:
            log(f"Watchdog error: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
