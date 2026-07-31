"""
CEREBUS LIVE GUARDIAN v3 — Process Watchdog
===========================================
Monitors live bridge and auto-restarts on failure.
Uses PID file for reliable process detection.

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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "live_logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "guardian.log")
CHECK_INTERVAL = 60
GRACE_PERIOD = 60
MAX_RESTARTS_PER_HOUR = 5
PYTHON_EXE = r"C:\Users\wifik\AppData\Local\Programs\Python\Python311\python.exe"

PROCESSES = {
    "bridge": {
        "script": os.path.join(SCRIPT_DIR, "cerebus_live_bridge.py"),
        "args": ["--symbols", "EURJPY.PRO,EURNZD.PRO,GBPNZD.PRO,EURAUD.PRO,GBPAUD.PRO,GBPCAD.PRO", "--lot-size", "0.01"],
        "pid_file": os.path.join(LOG_DIR, "bridge.pid"),
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
log = logging.getLogger("live_guardian")


def is_pid_alive(pid: int) -> bool:
    """Check if a process with the given PID is still running."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"Get-Process -Id {pid} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() == str(pid)
    except Exception:
        return False


def read_pid_file(pid_file: str) -> Optional[int]:
    """Read PID from file."""
    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
            return pid if pid > 0 else None
    except Exception:
        return None


def find_process_pid(script_name: str) -> Optional[int]:
    """Find PID of a Python process running the given script."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | "
             f"Where-Object {{ $_.CommandLine -like '*{script_name}*' }} | "
             f"Select-Object -First 1 -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=10
        )
        pid_str = result.stdout.strip()
        return int(pid_str) if pid_str else None
    except Exception:
        return None


def kill_by_pid(pid: int):
    """Kill a process by PID."""
    try:
        subprocess.run(
            ["powershell", "-Command", f"Stop-Process -Id {pid} -Force"],
            capture_output=True, text=True, timeout=5
        )
    except Exception:
        pass


def start_process(cfg: dict) -> bool:
    """Start a Python script in the background."""
    try:
        cmd = [PYTHON_EXE, cfg["script"]] + cfg["args"]
        proc = subprocess.Popen(
            cmd,
            cwd=SCRIPT_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        log.info(f"Started PID {proc.pid}: {cfg['script']} {' '.join(cfg['args'])}")
        return True
    except Exception as e:
        log.error(f"Failed to start: {e}")
        return False


def is_process_alive(script_name: str, pid_file: str) -> bool:
    """
    Check if a process is alive using PID file first, then fallback to process scan.
    """
    pid = read_pid_file(pid_file)
    if pid:
        if is_pid_alive(pid):
            return True
        # PID file stale, remove it
        try:
            os.remove(pid_file)
        except Exception:
            pass

    # Fallback: scan for process by script name
    pid = find_process_pid(script_name)
    if pid and is_pid_alive(pid):
        # Found it, write PID file
        try:
            with open(pid_file, "w") as f:
                f.write(str(pid))
        except Exception:
            pass
        return True

    return False


def main(run_once: bool = False):
    log.info("=" * 60)
    log.info("CEREBUS LIVE GUARDIAN v3 — Starting")
    log.info(f"Monitoring: {', '.join(PROCESSES.keys())}")
    log.info(f"Check interval: {CHECK_INTERVAL}s | Grace: {GRACE_PERIOD}s")
    log.info("=" * 60)

    last_restart: dict[str, float] = {}
    restart_count: dict[str, int] = {}
    restart_window_start: dict[str, float] = {}

    for name, cfg in PROCESSES.items():
        script_basename = os.path.basename(cfg["script"])
        alive = is_process_alive(script_basename, cfg["pid_file"])
        if alive:
            pid = read_pid_file(cfg["pid_file"]) or find_process_pid(script_basename)
            log.info(f"{name} already running — OK (PID {pid})")
        else:
            log.info(f"{name} not running — starting...")
            start_process(cfg)
            last_restart[name] = time.time()

    if run_once:
        time.sleep(5)
        dead = []
        for name, cfg in PROCESSES.items():
            script_basename = os.path.basename(cfg["script"])
            if not is_process_alive(script_basename, cfg["pid_file"]):
                dead.append(name)
        if dead:
            log.warning(f"Processes not running: {dead}")
            sys.exit(1)
        log.info("All processes running.")
        sys.exit(0)

    while True:
        try:
            time.sleep(CHECK_INTERVAL)
            now = time.time()

            for name in PROCESSES:
                if name not in restart_window_start or (now - restart_window_start[name]) > 3600:
                    restart_count[name] = 0
                    restart_window_start[name] = now

            for name, cfg in PROCESSES.items():
                script_basename = os.path.basename(cfg["script"])

                if name in last_restart and (now - last_restart[name]) < GRACE_PERIOD:
                    continue

                if is_process_alive(script_basename, cfg["pid_file"]):
                    continue

                # Process is dead
                is_critical = cfg.get("critical", False)
                log.warning(f"{'CRITICAL' if is_critical else 'WARNING'} {name} is DEAD — restarting...")

                if restart_count.get(name, 0) >= MAX_RESTARTS_PER_HOUR:
                    log.error(f"{name} exceeded {MAX_RESTARTS_PER_HOUR}/hour restarts — SKIPPING. Manual intervention needed.")
                    if is_critical:
                        log.error(f"CRITICAL PROCESS {name} IS DOWN")
                    continue

                # Kill any stale PID
                old_pid = read_pid_file(cfg["pid_file"])
                if old_pid:
                    kill_by_pid(old_pid)

                if start_process(cfg):
                    last_restart[name] = now
                    restart_count[name] = restart_count.get(name, 0) + 1
                    log.info(f"{name} restarted (attempt {restart_count[name]}/{MAX_RESTARTS_PER_HOUR})")

        except KeyboardInterrupt:
            log.info("Guardian stopped by user")
            break
        except Exception as e:
            log.error(f"Guardian error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cerebus Live Guardian v3")
    parser.add_argument("--once", action="store_true", help="Single check, then exit")
    args = parser.parse_args()
    main(run_once=args.once)
