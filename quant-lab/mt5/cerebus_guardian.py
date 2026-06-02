"""
CEREBUS GUARDIAN — Process Watchdog
===================================
Monitors all Cerebus processes and auto-restarts them on failure.
Runs as a single persistent process. Lightweight — just checks PIDs.

Processes monitored:
  1. cerebus_live_bridge.py
  2. p90_cascade_executor.py
  3. symmetry_trap_executor.py

Logic:
  - Every 60 seconds, check if each process is alive
  - If dead, restart it immediately
  - If a process just started (grace period), skip check
  - Log all restarts to live_logs/guardian.log
  - Self-protect: if guardian itself should die, cron restarts it

Usage:
  python cerebus_guardian.py
"""

from __future__ import annotations

import os
import sys
import time
import subprocess
import logging
from datetime import datetime
from typing import Optional

# ─── Config ───────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "live_logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "guardian.log")
CHECK_INTERVAL = 60       # seconds between health checks
GRACE_PERIOD = 30         # seconds after a restart before we check again
PYTHON_EXE = r"C:\Users\wifik\AppData\Local\Programs\Python\Python311\python.exe"

PROCESSES = {
    "bridge": {
        "script": os.path.join(SCRIPT_DIR, "cerebus_live_bridge.py"),
        "args": ["--symbols", "GBPJPY.PRO,CHFJPY.PRO,GBPNZD.PRO,GBPAUD.PRO,NZDUSD.PRO,EURUSD.PRO,USDCHF.PRO", "--lot-size", "0.01"],
    },
}

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("guardian")

# ─── Helpers ──────────────────────────────────────────────────────────────────

def is_process_alive(script_name: str) -> bool:
    """Check if a Python process with the given script name is running."""
    try:
        import subprocess
        result = subprocess.run(
            ["powershell", "-Command",
             f"Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | "
             f"Where-Object {{ $_.CommandLine -match '{script_name}' }} | "
             f"Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() != ""
    except Exception:
        return False


def start_process(name: str, script: str, args: list) -> bool:
    """Start a Python script in the background. Returns True if started."""
    try:
        cmd = [PYTHON_EXE, script] + args
        subprocess.Popen(
            cmd,
            cwd=SCRIPT_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        log.info(f"Started {name}: {script} {' '.join(args)}")
        return True
    except Exception as e:
        log.error(f"Failed to start {name}: {e}")
        return False


# ─── Main Loop ────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("CEREBUS GUARDIAN — Starting")
    log.info(f"Monitoring: {', '.join(PROCESSES.keys())}")
    log.info(f"Check interval: {CHECK_INTERVAL}s | Grace period: {GRACE_PERIOD}s")
    log.info("=" * 60)

    # Track when we last restarted each process (grace period)
    last_restart: dict[str, float] = {}

    # Start all processes initially
    for name, cfg in PROCESSES.items():
        if not is_process_alive(os.path.basename(cfg["script"])):
            log.info(f"{name} not running — starting...")
            start_process(name, cfg["script"], cfg["args"])
            last_restart[name] = time.time()
        else:
            log.info(f"{name} already running — OK")

    # Monitor loop
    while True:
        try:
            time.sleep(CHECK_INTERVAL)
            now = time.time()

            for name, cfg in PROCESSES.items():
                script_basename = os.path.basename(cfg["script"])

                # Skip if in grace period
                if name in last_restart and (now - last_restart[name]) < GRACE_PERIOD:
                    continue

                if not is_process_alive(script_basename):
                    log.warning(f"⚠ {name} is DEAD — restarting...")
                    if start_process(name, cfg["script"], cfg["args"]):
                        last_restart[name] = now
                        log.info(f"✅ {name} restarted")
                    else:
                        log.error(f"❌ Failed to restart {name}")
                else:
                    log.debug(f"  {name} — alive")

        except KeyboardInterrupt:
            log.info("Guardian stopped by user")
            break
        except Exception as e:
            log.error(f"Guardian error: {e}")
            time.sleep(10)  # brief pause before retrying


if __name__ == "__main__":
    main()
