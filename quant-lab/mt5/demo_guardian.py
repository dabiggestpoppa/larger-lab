"""
CEREBUS DEMO GUARDIAN — Process Watchdog
=========================================
Monitors demo bridge and auto-restarts on failure.
Lightweight — checks PIDs via PowerShell.

Usage:
  python demo_guardian.py [--once]
"""

from __future__ import annotations

import os
import sys
import time
import subprocess
import logging
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "demo_logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "demo_guardian.log")
CHECK_INTERVAL = 60
GRACE_PERIOD = 30
MAX_RESTARTS_PER_HOUR = 5
PYTHONW_EXE = r"C:\Users\wifik\AppData\Local\Programs\Python\Python311\pythonw.exe"

PROCESSES = {
    "demo_bridge": {
        "exe": PYTHONW_EXE,
        "script": os.path.join(SCRIPT_DIR, "demo_bridge.py"),
        "args": [],
        "critical": True,
    },
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("demo_guardian")


def is_process_alive(script_name: str) -> bool:
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"Get-CimInstance Win32_Process -Filter \"name='python.exe' OR name='pythonw.exe'\" | "
             f"Where-Object {{ $_.CommandLine -match '{script_name}' }} | "
             f"Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=10
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def start_process(proc_config: dict) -> bool:
    try:
        cmd = [proc_config["exe"], proc_config["script"]] + proc_config["args"]
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception as e:
        log.error(f"Failed to start {proc_config['script']}: {e}")
        return False


def main():
    log.info("=" * 60)
    log.info("CEREBUS DEMO GUARDIAN — STARTING")
    log.info(f"Monitoring: {list(PROCESSES.keys())}")
    log.info(f"Check interval: {CHECK_INTERVAL}s | Grace: {GRACE_PERIOD}s")
    log.info("=" * 60)

    restart_counts = {}
    last_restart_time = {}

    while True:
        for name, config in PROCESSES.items():
            script_name = os.path.basename(config["script"])
            alive = is_process_alive(script_name)

            if not alive:
                now = datetime.now()
                hour_key = now.strftime("%Y%m%d%H")
                count = restart_counts.get(hour_key, 0)

                if count >= MAX_RESTARTS_PER_HOUR:
                    log.error(f"{name}: MAX RESTARTS ({MAX_RESTARTS_PER_HOUR}/hr) — skipping")
                    continue

                last_restart = last_restart_time.get(name)
                if last_restart and (now - last_restart).seconds < GRACE_PERIOD:
                    log.warning(f"{name}: in grace period, skipping restart")
                    continue

                log.warning(f"{name}: DEAD — restarting (attempt {count + 1}/{MAX_RESTARTS_PER_HOUR})")
                if start_process(config):
                    restart_counts[hour_key] = count + 1
                    last_restart_time[name] = now
                    log.info(f"{name}: restarted successfully")
                else:
                    log.error(f"{name}: restart FAILED")
            else:
                log.debug(f"{name}: alive")

        if "--once" in sys.argv:
            break

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
