"""
CEREBUS 24/7 All-in-One Scanner
=================================
Run this single file. It starts all 5 scanners as subprocesses.
No extra windows. No duplicates. Auto-restarts on crash.

Usage: python start_all.py
"""
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parent
VENV_PYTHON = str(REPO_ROOT / ".venv" / "Scripts" / "python.exe")
LOG_FILE = REPO_ROOT / "logs" / "start_all.log"
PID_FILE = REPO_ROOT / ".start_all.pids"

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

SCANNERS = [
    {"name": "OCE",     "cmd": [VENV_PYTHON, "-m", "oce.backend.main"]},
    {"name": "TG",      "cmd": [VENV_PYTHON, "scripts/telegram_gateway.py"]},
    {"name": "CEREBUS", "cmd": [VENV_PYTHON, "quant-lab/ml/run_cerebus_live.py", "--interval", "300", "--engine", "both"]},
    {"name": "MLR",     "cmd": [VENV_PYTHON, "quant-lab/mlr_validation/mlr_scanner.py"]},
    {"name": "SIGNAL",  "cmd": [VENV_PYTHON, "scripts/signal_bot.py"]},
]

CHECK_INTERVAL = 30
MAX_RESTARTS = 5
RESTART_COOLDOWN = 300


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def is_running(proc):
    return proc is not None and proc.poll() is None


def start_scanner(scanner):
    proc = subprocess.Popen(
        scanner["cmd"],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc


def main():
    log("=" * 60)
    log("CEREBUS 24/7 — Starting all scanners")
    log("=" * 60)
    procs = {}
    restart_counts = {}
    for s in SCANNERS:
        proc = start_scanner(s)
        procs[s["name"]] = proc
        restart_counts[s["name"]] = 0
        log(f"  Started {s['name']} — PID {proc.pid}")
        time.sleep(2)
    all_pids = [str(p.pid) for p in procs.values() if p]
    PID_FILE.write_text("\n".join(all_pids))
    log(f"All {len(SCANNERS)} scanners started")
    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            for s in SCANNERS:
                name = s["name"]
                proc = procs.get(name)
                if is_running(proc):
                    continue
                restart_counts[name] = restart_counts.get(name, 0) + 1
                if restart_counts[name] > MAX_RESTARTS:
                    log(f"  {name}: max restarts exceeded, waiting {RESTART_COOLDOWN}s")
                    time.sleep(RESTART_COOLDOWN)
                    restart_counts[name] = 0
                log(f"  Restarting {name} (was PID {proc.pid})...")
                new_proc = start_scanner(s)
                procs[name] = new_proc
                log(f"  {name} restarted — PID {new_proc.pid}")
    except KeyboardInterrupt:
        log("Shutting down...")
        for name, proc in procs.items():
            if is_running(proc):
                proc.terminate()
        PID_FILE.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
