"""
CEREBUS 24/7 Watchdog
======================
Monitors and auto-restarts all scanner processes.
Runs as a persistent background process.

Usage:
    python cerebus_watchdog.py          # Start watchdog (foreground)
    python cerebus_watchdog.py --check  # Check scanner status
    python cerebus_watchdog.py --stop   # Stop all scanners
"""
import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VENV_PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
PID_FILE = REPO_ROOT / ".cerebus_watchdog.pids"
LOG_FILE = REPO_ROOT / "logs" / "cerebus_watchdog.log"

# Ensure log directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Scanner definitions
SCANNERS = [
    {
        "name": "CEREBUS_Live",
        "cmd": [str(VENV_PYTHON), "quant-lab/ml/run_cerebus_live.py", "--interval", "300", "--engine", "both"],
        "critical": True,
    },
    {
        "name": "MLR_Scanner",
        "cmd": [str(VENV_PYTHON), "quant-lab/mlr_validation/mlr_scanner.py"],
        "critical": True,
    },
    {
        "name": "Signal_Bot",
        "cmd": [str(VENV_PYTHON), "scripts/signal_bot.py"],
        "critical": True,
    },
    {
        "name": "OCE_Backend",
        "cmd": [str(VENV_PYTHON), "-m", "oce.backend.main"],
        "critical": False,
    },
    {
        "name": "Telegram_Gateway",
        "cmd": [str(VENV_PYTHON), "scripts/telegram_gateway.py"],
        "critical": False,
    },
]

CHECK_INTERVAL = 30  # seconds between health checks
MAX_RESTARTS = 5     # max restarts per scanner within cooldown
RESTART_COOLDOWN = 300  # 5 minutes between restarts


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def is_running(pid):
    """Check if a process is still running."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def start_scanner(scanner):
    """Start a scanner process and return its PID."""
    # Use DETACHED_PROCESS to prevent console window popup and zombie processes
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
    proc = subprocess.Popen(
        scanner["cmd"],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )
    return proc.pid


def stop_scanner(pid):
    """Stop a scanner process."""
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
        # Force kill if still running
        try:
            os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass  # Already dead
    except (OSError, ProcessLookupError):
        pass  # Already dead


def watchdog_loop():
    """Main watchdog loop — monitors and restarts scanners."""
    log("=" * 60)
    log("CEREBUS 24/7 WATCHDOG — Starting")
    log(f"Scanners: {len(SCANNERS)}")
    log(f"Check interval: {CHECK_INTERVAL}s")
    log("=" * 60)

    # Start all scanners
    pids = {}
    restart_counts = {}
    last_restart = {}

    for scanner in SCANNERS:
        pid = start_scanner(scanner)
        pids[scanner["name"]] = pid
        restart_counts[scanner["name"]] = 0
        last_restart[scanner["name"]] = 0
        log(f"  Started {scanner['name']} — PID {pid}")
        time.sleep(2)

    # Save PIDs
    all_pids = list(pids.values())
    PID_FILE.write_text("\n".join(map(str, all_pids)))
    log(f"All {len(SCANNERS)} scanners started. PIDs: {all_pids}")

    # Monitor loop
    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            now = time.time()

            for scanner in SCANNERS:
                name = scanner["name"]
                pid = pids.get(name)

                if pid and is_running(pid):
                    continue  # Healthy

                # Scanner is down — restart it
                if not scanner["critical"]:
                    log(f"  ⚠ {name} (PID {pid}) is down — not critical, skipping restart")
                    continue

                # Check restart cooldown
                if now - last_restart.get(name, 0) < RESTART_COOLDOWN:
                    restart_counts[name] = restart_counts.get(name, 0) + 1
                    if restart_counts[name] >= MAX_RESTARTS:
                        log(f"  ❌ {name} exceeded max restarts ({MAX_RESTARTS}) — waiting for cooldown")
                        continue

                log(f"  🔄 Restarting {name} (was PID {pid})...")
                new_pid = start_scanner(scanner)
                pids[name] = new_pid
                last_restart[name] = now
                log(f"  ✅ {name} restarted — new PID {new_pid}")

                # Update PID file
                all_pids = list(pids.values())
                PID_FILE.write_text("\n".join(map(str, all_pids)))

    except KeyboardInterrupt:
        log("\n🛑 Watchdog stopped by user. Shutting down scanners...")
        for name, pid in pids.items():
            log(f"  Stopping {name} (PID {pid})...")
            stop_scanner(pid)
        PID_FILE.unlink(missing_ok=True)
        log("All scanners stopped. Watchdog exiting.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            if PID_FILE.exists():
                pids = PID_FILE.read_text().strip().splitlines()
                for pid_str in pids:
                    pid = int(pid_str)
                    status = "✅" if is_running(pid) else "❌"
                    print(f"  {status} PID {pid}")
            else:
                print("No PID file found.")
        elif sys.argv[1] == "--stop":
            if PID_FILE.exists():
                pids = PID_FILE.read_text().strip().splitlines()
                for pid_str in pids:
                    stop_scanner(int(pid_str))
                PID_FILE.unlink(missing_ok=True)
                print("All scanners stopped.")
            else:
                print("No PID file found.")
        else:
            print(f"Unknown arg: {sys.argv[1]}")
    else:
        watchdog_loop()
