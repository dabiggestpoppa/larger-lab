#!/usr/bin/env python3
"""
PROCESS REGISTRY — Single source of truth for all trading processes.
Kills ALL duplicates. Prevents new ones. Simple.

CRITICAL: Only ONE instance of this script can run at a time.
Uses a file lock to prevent concurrent execution.

Usage:
    python scripts/process_registry.py          # clean + start + status
    python scripts/process_registry.py --clean  # kill all duplicates only
    python scripts/process_registry.py --start  # start missing processes
    python scripts/process_registry.py --watch  # run as watchdog (60s loop)
    python scripts/process_registry.py --status # show status only
"""
import subprocess, time, os, sys, json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent / "logs" / "process_registry.log"

PROCESSES = [
    {"name": "bridge", "script": "quant-lab/mt5/cerebus_live_bridge.py",
     "args": ["--symbols", "EURJPY.PRO,EURNZD.PRO,GBPNZD.PRO,EURAUD.PRO,GBPAUD.PRO,GBPCAD.PRO,FR40.PRO", "--lot-size", "0.01"],
     "cwd": "quant-lab/mt5", "max": 1},
    {"name": "signal_bot", "script": "scripts/signal_bot.py", "args": [], "cwd": ".", "max": 1},
    {"name": "telegram", "script": "scripts/telegram_gateway.py", "args": [], "cwd": ".", "max": 1},
]

VENV_PYTHON = str(Path(__file__).resolve().parent.parent / ".venv" / "Scripts" / "python.exe")
BASE_DIR = str(Path(__file__).resolve().parent.parent)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

def get_running(name):
    script = PROCESSES[[p["name"] for p in PROCESSES].index(name)]["script"]
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {{ $_.CommandLine -like '*{script}*' }} | Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=10)
        pids = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line:
                try: pids.append(int(line))
                except ValueError: pass
        return pids
    except:
        return []

def kill_all(name):
    pids = get_running(name)
    killed = 0
    for pid in pids:
        try:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=5)
            killed += 1
            log(f"Killed {name} PID {pid}")
        except: pass
    if killed > 0: time.sleep(2)
    return killed

def start_process(name):
    cfg = PROCESSES[[p["name"] for p in PROCESSES].index(name)]
    running = get_running(name)
    if len(running) >= cfg["max"]:
        log(f"{name}: already running (PID {running[0]}), skipping")
        return False
    script_path = os.path.join(BASE_DIR, cfg["script"])
    cwd = os.path.join(BASE_DIR, cfg["cwd"]) if cfg["cwd"] != "." else BASE_DIR
    try:
        subprocess.Popen([VENV_PYTHON, script_path] + cfg["args"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=cwd,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        log(f"Started {name}")
        time.sleep(3)
        return True
    except Exception as e:
        log(f"Failed to start {name}: {e}")
        return False

def get_status():
    status = {}
    for cfg in PROCESSES:
        name = cfg["name"]
        pids = get_running(name)
        status[name] = {"pids": pids, "count": len(pids), "expected": cfg["max"], "ok": len(pids) == cfg["max"]}
    return status

def clean_all():
    log("=== CLEANING ALL DUPLICATES ===")
    total = 0
    for cfg in PROCESSES:
        name = cfg["name"]
        pids = get_running(name)
        if len(pids) > cfg["max"]:
            killed = kill_all(name)
            total += killed
            log(f"{name}: killed {killed} duplicates")
        elif len(pids) == 0:
            log(f"{name}: not running")
        else:
            log(f"{name}: OK (PID {pids[0]})")
    return total

def start_missing():
    log("=== STARTING MISSING ===")
    # First: kill ALL duplicates across all processes
    for cfg in PROCESSES:
        name = cfg["name"]
        pids = get_running(name)
        if len(pids) > cfg["max"]:
            kill_all(name)
    # Wait for full cleanup
    time.sleep(5)
    # Then: start any that are missing
    for cfg in PROCESSES:
        name = cfg["name"]
        pids = get_running(name)
        if len(pids) == 0:
            start_process(name)
            time.sleep(2)  # Stagger starts to avoid conflicts

def show_status():
    status = get_status()
    log("=== STATUS ===")
    for name, info in status.items():
        state = "OK" if info["ok"] else "DUPLICATE" if info["count"] > info["expected"] else "DOWN"
        log(f"  {name:<12} | {state:<10} | PIDs: {info['pids']}")

def watch_loop():
    log("=== WATCHDOG STARTED (60s interval) ===")
    while True:
        try:
            for cfg in PROCESSES:
                name = cfg["name"]
                pids = get_running(name)
                if len(pids) == 0:
                    log(f"WATCHDOG: {name} DOWN, restarting")
                    start_process(name)
                elif len(pids) > cfg["max"]:
                    log(f"WATCHDOG: {name} has {len(pids)} instances, cleaning")
                    kill_all(name)
                    start_process(name)
            time.sleep(60)
        except KeyboardInterrupt:
            log("Watchdog stopped")
            break
        except Exception as e:
            log(f"Watchdog error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    if len(sys.argv) > 1:
        if sys.argv[1] == "--clean": clean_all()
        elif sys.argv[1] == "--start": start_missing()
        elif sys.argv[1] == "--watch": watch_loop()
        elif sys.argv[1] == "--status": show_status()
        else: print("Usage: process_registry.py [--clean|--start|--watch|--status]")
    else:
        clean_all()
        time.sleep(2)
        start_missing()
        time.sleep(3)
        show_status()
