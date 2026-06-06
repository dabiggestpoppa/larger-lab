"""
CEREBUS GUARDIAN v2 — Process Watchdog
======================================
Monitors all Cerebus trading processes and auto-restarts on failure.
Lightweight — just checks PIDs via PowerShell.

Processes monitored:
  1. cerebus_live_bridge.py (PRIMARY — executes all trades)
  2. symmetry_trap_executor.py (ST standalone executor)

Policy:
  - Bridge is SOLE executor. ST executor is backup/satellite.
  - If bridge dies → restart immediately
  - If ST executor dies → restart (it should be decommissioned but kept for safety)
  - Grace period after restart to avoid flapping
  - Self-protect: cron job restarts guardian if it dies
  - Max restart attempts per hour to prevent infinite loops

Usage:
  python cerebus_guardian.py [--once]
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
GRACE_PERIOD = 30         # seconds after restart before checking again
MAX_RESTARTS_PER_HOUR = 5 # prevent infinite restart loops
PYTHON_EXE = r"C:\Users\wifik\AppData\Local\Programs\Python\Python311\python.exe"
PYTHONW_EXE = r"C:\Users\wifik\AppData\Local\Programs\Python\Python311\pythonw.exe"

PROCESSES = {
    "bridge": {
        "exe": PYTHONW_EXE,
        "script": os.path.join(SCRIPT_DIR, "cerebus_live_bridge.py"),
        "args": ["--symbols", "EURJPY.PRO,EURNZD.PRO,GBPNZD.PRO,EURAUD.PRO,GBPAUD.PRO,GBPCAD.PRO", "--lot-size", "0.01"],
        "critical": True,  # Alert if this dies
    },
    "st_executor": {
        "exe": PYTHON_EXE,
        "script": os.path.join(SCRIPT_DIR, "symmetry_trap_executor.py"),
        "args": ["--loop", "--interval", "30"],
        "critical": False,
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
        result = subprocess.run(
            ["powershell", "-Command",
             f"Get-CimInstance Win32_Process -Filter \"name='python.exe' OR name='pythonw.exe'\" | "
             f"Where-Object {{ $_.CommandLine -match '{script_name}' }} | "
             f"Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() != ""
    except Exception:
        return False


def get_process_pid(script_name: str) -> Optional[int]:
    """Get PID of a running process by script name."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"Get-CimInstance Win32_Process -Filter \"name='python.exe' OR name='pythonw.exe'\" | "
             f"Where-Object {{ $_.CommandLine -match '{script_name}' }} | "
             f"Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=10
        )
        pid_str = result.stdout.strip()
        return int(pid_str) if pid_str else None
    except Exception:
        return None


def kill_process(script_name: str) -> bool:
    """Kill a process by script name."""
    try:
        subprocess.run(
            ["powershell", "-Command",
             f"Get-CimInstance Win32_Process -Filter \"name='python.exe' OR name='pythonw.exe'\" | "
             f"Where-Object {{ $_.CommandLine -match '{script_name}' }} | "
             f"ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}"],
            capture_output=True, text=True, timeout=10
        )
        return True
    except Exception:
        return False


def start_process(name: str, cfg: dict) -> bool:
    """Start a Python script in the background. Returns True if started."""
    try:
        cmd = [cfg["exe"], cfg["script"]] + cfg["args"]
        subprocess.Popen(
            cmd,
            cwd=SCRIPT_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        log.info(f"Started {name}: {cfg['script']} {' '.join(cfg['args'])}")
        return True
    except Exception as e:
        log.error(f"Failed to start {name}: {e}")
        return False


def check_mt5_connection() -> bool:
    """Quick check if MT5 terminal is responsive."""
    try:
        result = subprocess.run(
            [PYTHON_EXE, "-c",
             "import MetaTrader5 as mt5; "
             "mt5.initialize(); "
             "print(mt5.account_info().balance if mt5.account_info() else 'FAIL'); "
             "mt5.shutdown()"],
            capture_output=True, text=True, timeout=15,
            cwd=SCRIPT_DIR
        )
        return "FAIL" not in result.stdout and result.stdout.strip() != ""
    except Exception:
        return False


# ─── Main Loop ────────────────────────────────────────────────────────────────

def main(run_once: bool = False):
    log.info("=" * 60)
    log.info("CEREBUS GUARDIAN v2 - Starting")
    log.info(f"Monitoring: {', '.join(PROCESSES.keys())}")
    log.info(f"Check interval: {CHECK_INTERVAL}s | Grace period: {GRACE_PERIOD}s")
    log.info(f"Max restarts/hour per process: {MAX_RESTARTS_PER_HOUR}")
    log.info("=" * 60)

    last_restart: dict[str, float] = {}
    restart_count: dict[str, int] = {}
    restart_window_start: dict[str, float] = {}

    # Initial check — start anything missing
    for name, cfg in PROCESSES.items():
        script_basename = os.path.basename(cfg["script"])
        pid = get_process_pid(script_basename)
        if pid:
            log.info(f"{name} already running - OK (PID {pid})")
        else:
            log.info(f"{name} not running - starting...")
            start_process(name, cfg)
            last_restart[name] = time.time()

    if run_once:
        # Single check pass, then exit
        dead = [n for n, c in PROCESSES.items() if not is_process_alive(os.path.basename(c["script"]))]
        if dead:
            log.warning(f"Processes not running after start attempt: {dead}")
            sys.exit(1)
        else:
            log.info("All processes running.")
            sys.exit(0)

    # Monitor loop
    while True:
        try:
            time.sleep(CHECK_INTERVAL)
            now = time.time()

            # Reset restart counters every hour
            for name in PROCESSES:
                if name not in restart_window_start or (now - restart_window_start[name]) > 3600:
                    restart_count[name] = 0
                    restart_window_start[name] = now

            for name, cfg in PROCESSES.items():
                script_basename = os.path.basename(cfg["script"])

                # Skip if in grace period
                if name in last_restart and (now - last_restart[name]) < GRACE_PERIOD:
                    continue

                pid = get_process_pid(script_basename)
                if pid:
                    log.debug(f"  {name} - alive (PID {pid})")
                    continue

                # Process is dead
                is_critical = cfg.get("critical", False)
                level = "CRITICAL" if is_critical else "WARNING"
                log.warning(f"{level} {name} is DEAD (was PID {pid}) - restarting...")

                # Check restart rate limit
                if restart_count.get(name, 0) >= MAX_RESTARTS_PER_HOUR:
                    log.error(f"  {name} exceeded {MAX_RESTARTS_PER_HOUR}/hour restarts - SKIPPING. Manual intervention needed.")
                    if is_critical:
                        log.error(f"  CRITICAL PROCESS {name} IS DOWN - SEND ALERT TO MAD")
                    continue

                # Kill any zombie processes first
                kill_process(script_basename)
                time.sleep(2)

                if start_process(name, cfg):
                    last_restart[name] = now
                    restart_count[name] = restart_count.get(name, 0) + 1
                    log.info(f"{name} restarted (attempt {restart_count[name]}/{MAX_RESTARTS_PER_HOUR} this hour)")
                else:
                    log.error(f"Failed to restart {name}")

            # Periodic MT5 health check (every 5 cycles)
            if int(now) % (CHECK_INTERVAL * 5) < CHECK_INTERVAL:
                if check_mt5_connection():
                    log.debug("  MT5 connection - OK")
                else:
                    log.warning("  MT5 connection - FAIL (terminal may need manual restart)")

        except KeyboardInterrupt:
            log.info("Guardian stopped by user")
            break
        except Exception as e:
            log.error(f"Guardian error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cerebus Guardian v2")
    parser.add_argument("--once", action="store_true", help="Single check pass, then exit")
    args = parser.parse_args()
    main(run_once=args.once)