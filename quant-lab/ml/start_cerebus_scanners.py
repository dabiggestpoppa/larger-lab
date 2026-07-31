"""
CEREBUS Scanner Launcher
=========================
Starts all three scanners as background jobs:
1. run_cerebus_live.py (Guardian + ST/P90, every 5 min)
2. mlr_scanner.py (MLR tier scan at London open)
3. signal_bot.py (relays signals to Telegram)

Usage:
    python start_cerebus_scanners.py          # Start all scanners
    python start_cerebus_scanners.py --check  # Check status
    python start_cerebus_scanners.py --stop   # Stop all scanners
"""
import os
import sys
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VENV_PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
SCANNERS = [
    {
        "name": "Guardian+ST/P90",
        "cmd": [str(VENV_PYTHON), "quant-lab/ml/run_cerebus_live.py", "--interval", "300", "--engine", "both"],
    },
    {
        "name": "MLR Scanner",
        "cmd": [str(VENV_PYTHON), "quant-lab/mlr_validation/mlr_scanner.py"],
    },
    {
        "name": "Signal Bot",
        "cmd": [str(VENV_PYTHON), "scripts/signal_bot.py"],
    },
]

PID_FILE = REPO_ROOT / ".cerebus_scanner.pids"


def load_env():
    """Load .env file into environment."""
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        import re
        content = env_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        if len(lines) <= 1:
            pairs = re.findall(r'([A-Z_][A-Z0-9_]*)=(.*?)(?=(?:[A-Z_][A-Z0-9_]*=|$))', content, re.DOTALL)
            lines = [f"{k}={v}" for k, v in pairs]
        for line in lines:
            line = line.strip().strip("\r")
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k:
                    os.environ.setdefault(k, v)


def start_scanners():
    """Start all scanners as background processes."""
    load_env()
    pids = []
    for scanner in SCANNERS:
        print(f"Starting {scanner['name']}...")
        env = os.environ.copy()
        proc = subprocess.Popen(
            scanner["cmd"],
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        pids.append(proc.pid)
        print(f"  PID: {proc.pid}")
        time.sleep(2)

    # Save PIDs
    PID_FILE.write_text("\n".join(map(str, pids)))
    print(f"\n✅ All {len(SCANNERS)} scanners started. PIDs saved to {PID_FILE}")
    print("   Use --check to verify status, --stop to kill all.")


def check_scanners():
    """Check if scanners are running."""
    import signal
    if not PID_FILE.exists():
        print("No PID file found. Scanners not started.")
        return

    pids = PID_FILE.read_text().strip().splitlines()
    running = 0
    for i, pid_str in enumerate(pids):
        pid = int(pid_str)
        try:
            os.kill(pid, 0)  # Check if process exists
            name = SCANNERS[i]["name"] if i < len(SCANNERS) else f"Unknown ({pid})"
            print(f"  ✅ {name} — PID {pid} running")
            running += 1
        except OSError:
            name = SCANNERS[i]["name"] if i < len(SCANNERS) else f"Unknown ({pid})"
            print(f"  ❌ {name} — PID {pid} NOT running")

    print(f"\n{running}/{len(pids)} scanners running")


def stop_scanners():
    """Kill all scanners."""
    import signal
    if not PID_FILE.exists():
        print("No PID file found.")
        return

    pids = PID_FILE.read_text().strip().splitlines()
    killed = 0
    for pid_str in pids:
        pid = int(pid_str)
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"  Killed PID {pid}")
            killed += 1
        except OSError:
            print(f"  PID {pid} already dead")

    PID_FILE.unlink(missing_ok=True)
    print(f"\n✅ Killed {killed}/{len(pids)} scanners")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            check_scanners()
        elif sys.argv[1] == "--stop":
            stop_scanners()
        else:
            print(f"Unknown arg: {sys.argv[1]}")
            print("Usage: python start_cerebus_scanners.py [--check|--stop]")
    else:
        start_scanners()
