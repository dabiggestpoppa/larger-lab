"""
HEALTH CHECK — Lightweight process monitor
==========================================
Checks if critical processes are alive by looking for the uv-child
(the actual running process). The venv-shim is just a launcher.

Usage: python health_check.py [--fix]

Logged to: logs/health_check.log
"""
import subprocess
import sys
import os
import time
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "health_check.log")

# Processes to check: (name, script_name_to_find_in_cmdline)
PROCESSES = [
    ("live_bridge", "cerebus_live_bridge.py"),
    ("guardian", "cerebus_guardian.py"),
    ("session_cleanup", "oc2_session_cleanup.py"),
]

# Restart commands — use SYSTEM Python (Python311), not venv
# System Python directly runs the script without uv shim complications
SYS_PYTHON = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Python", "Python311", "python.exe")

RESTART_CMDS = {
    "live_bridge": [
        SYS_PYTHON, os.path.join(BASE, "quant-lab", "mt5", "cerebus_live_bridge.py"),
        "--symbols", "EURJPY.PRO,EURNZD.PRO,GBPNZD.PRO,EURAUD.PRO,GBPAUD.PRO,GBPCAD.PRO",
        "--lot-size", "0.01"
    ],
    "guardian": [
        SYS_PYTHON, os.path.join(BASE, "quant-lab", "mt5", "cerebus_guardian.py")
    ],
    "session_cleanup": [
        SYS_PYTHON, os.path.join(BASE, "scripts", "oc2_session_cleanup.py"), "--watch"
    ],
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

def get_all_python_processes():
    """Get all Python processes with their full command lines using PowerShell."""
    procs = []
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process python -ErrorAction SilentlyContinue | ForEach-Object { $cmd = (Get-CimInstance Win32_Process -Filter \"ProcessId=$($_.Id)\").CommandLine; \"$($_.Id)|$cmd\" }"],
            capture_output=True, text=True, timeout=15
        )
        for line in result.stdout.strip().splitlines():
            if "|" in line:
                parts = line.split("|", 1)
                try:
                    pid = int(parts[0].strip())
                    cmd = parts[1].strip()
                    procs.append((pid, cmd))
                except ValueError:
                    pass
    except Exception as e:
        log(f"Error enumerating processes: {e}")
    return procs

def count_processes(script_name):
    """Count how many instances of a script are running (uv-child or system python)."""
    count = 0
    for pid, cmd in get_all_python_processes():
        if script_name.lower() in cmd.lower():
            count += 1
    return count

def check_port(port):
    try:
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                return True
        return False
    except:
        return False

def start_process(name, cmd):
    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=BASE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        log(f"  -> Started {name}")
        return True
    except Exception as e:
        log(f"  -> FAILED to start {name}: {e}")
        return False

def main():
    do_fix = "--fix" in sys.argv
    log("=" * 50)
    log(f"HEALTH CHECK STARTED (fix={'YES' if do_fix else 'NO'})")
    log("=" * 50)

    issues = []

    # Check processes
    for name, script in PROCESSES:
        count = count_processes(script)
        if count == 0:
            log(f"  CRITICAL: {name} is DOWN!")
            issues.append(name)
            if do_fix and name in RESTART_CMDS:
                log(f"  -> Attempting restart...")
                time.sleep(2)
                start_process(name, RESTART_CMDS[name])
        elif count == 1:
            log(f"  OK: {name} (1 process)")
        else:
            # Count > 1 means duplicates — flag but don't kill (might be uv shim pair)
            log(f"  WARN: {name} has {count} processes (likely uv shim pair)")

    # Check MT5 terminal
    mt5_running = False
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq terminal64.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        mt5_running = "terminal64.exe" in result.stdout
    except:
        pass

    if mt5_running:
        log(f"  OK: MT5 terminal running")
    else:
        log(f"  CRITICAL: MT5 terminal is DOWN!")
        issues.append("mt5_terminal")

    # Check key ports
    ports = {
        "oc2_gateway": 18790,
        "oce_backend": 8000,
        "srra_api": 3000,
    }
    for name, port in ports.items():
        if check_port(port):
            log(f"  OK: {name} (port {port})")
        else:
            log(f"  WARN: {name} port {port} not listening")
            issues.append(name)

    # Summary
    if issues:
        log(f"\n  ISSUES FOUND: {', '.join(issues)}")
    else:
        log(f"\n  ALL CLEAR — systems nominal")

    log("=" * 50)
    return len(issues)

if __name__ == "__main__":
    exit(main())
