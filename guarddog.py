"""
CEREBUS Guarddog — Process watchdog with duplicate prevention.
Uses PID file tracking to ensure only one instance of each service runs.

Usage:
    python guarddog.py              # Run watchdog (checks every 60s)
    python guarddog.py --once       # Check once and exit
    python guarddog.py --status     # Show running services
    python guarddog.py --stop       # Stop all CEREBUS services
"""
import sys, os, time, subprocess, signal, json, logging
from pathlib import Path
from datetime import datetime

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

REPO_ROOT = Path(__file__).parent
PID_FILE = Path(__file__).parent / ".guarddog_pids.json"
LOG_FILE = Path(__file__).parent / ".guarddog.log"

SERVICES = {
    "oce": {
        "cmd": [sys.executable, "-m", "oce.backend.main"],
        "window": "OCE",
    },
    "cerebus": {
        "cmd": [sys.executable, "quant-lab/ml/run_cerebus_unified.py", "--interval", "300"],
        "window": "CEREBUS",
    },
}

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [guarddog] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("guarddog")


def load_pids() -> dict:
    """Load tracked PIDs from file."""
    if PID_FILE.exists():
        try:
            with open(PID_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}


def save_pids(pids: dict):
    """Save tracked PIDs to file."""
    with open(PID_FILE, "w") as f:
        json.dump(pids, f, indent=2)


def is_process_alive(pid: int) -> bool:
    """Check if a process with given PID is still running."""
    try:
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
    except:
        pass
    return False


def find_running_service(service_name: str) -> list:
    """Find PIDs by checking which python processes have our script in their command line via PowerShell."""
    pids = []
    service = SERVICES.get(service_name, {})
    cmd_identifiers = []
    for arg in service.get("cmd", []):
        if arg.endswith(".py") or arg.startswith("-m"):
            cmd_identifiers.append(arg)

    if not cmd_identifiers:
        return pids

    try:
        # Use PowerShell to get reliable command lines
        ps_cmd = "Get-Process python -ErrorAction SilentlyContinue | ForEach-Object { $cmd = (Get-CimInstance Win32_Process -Filter \"ProcessId=$($_.Id)\").CommandLine; [PSCustomObject]@{Id=$_.Id; Cmd=$cmd} } | ConvertTo-Json"
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=15
        )
        if result.stdout.strip():
            processes = json.loads(result.stdout)
            if isinstance(processes, dict):
                processes = [processes]
            for proc in processes:
                cmd = proc.get("Cmd", "")
                pid = proc.get("Id", 0)
                if pid and cmd:
                    cmd_lower = cmd.lower()
                    for identifier in cmd_identifiers:
                        if identifier.lower() in cmd_lower:
                            pids.append(pid)
                            break
    except Exception as e:
        logger.error(f"Error finding {service_name}: {e}")
    return pids


def start_service(service_name: str) -> bool:
    """Start a service if not already running."""
    service = SERVICES.get(service_name)
    if not service:
        logger.error(f"Unknown service: {service_name}")
        return False

    # Check if already running
    running = find_running_service(service_name)
    if running:
        logger.debug(f"{service_name} already running (PIDs: {running})")
        return True

    # Start the service
    try:
        cmd = service["cmd"]
        cwd = str(REPO_ROOT)
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        # Write PID to tracking file
        pids = load_pids()
        pids[service_name] = proc.pid
        save_pids(pids)
        logger.info(f"Started {service_name} (PID {proc.pid})")
        return True
    except Exception as e:
        logger.error(f"Failed to start {service_name}: {e}")
        return False


def check_and_cleanup():
    """Check all services, kill zombies, restart missing."""
    pids = load_pids()
    changes = False

    for service_name in SERVICES:
        # Find running instances
        running = find_running_service(service_name)

        if not running:
            # Service not running — start it
            logger.info(f"{service_name} not found, starting...")
            start_service(service_name)
            changes = True
        elif len(running) > 1:
            # Multiple instances — kill all but one
            logger.warning(f"{service_name} has {len(running)} instances: {running}. Killing duplicates.")
            for pid in running[1:]:
                try:
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=5)
                    logger.info(f"Killed duplicate PID {pid}")
                except:
                    pass
            changes = True

    return changes


def show_status():
    """Show status of all services."""
    print("=" * 50)
    print("CEREBUS Guarddog — Service Status")
    print("=" * 50)
    for service_name in SERVICES:
        running = find_running_service(service_name)
        if running:
            print(f"  {service_name:15s}: RUNNING (PIDs: {running})")
        else:
            print(f"  {service_name:15s}: STOPPED")
    print("=" * 50)


def stop_all():
    """Stop all CEREBUS services."""
    for service_name in SERVICES:
        running = find_running_service(service_name)
        for pid in running:
            try:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=5)
                logger.info(f"Stopped {service_name} (PID {pid})")
            except:
                pass
    # Clean PID file
    if PID_FILE.exists():
        PID_FILE.unlink()
    logger.info("All services stopped")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CEREBUS Guarddog")
    parser.add_argument("--once", action="store_true", help="Check once and exit")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--stop", action="store_true", help="Stop all services")
    args = parser.parse_args()

    if args.stop:
        stop_all()
        return

    if args.status:
        show_status()
        return

    logger.info("Guarddog starting...")

    if args.once:
        check_and_cleanup()
        show_status()
        return

    # Main loop
    try:
        while True:
            check_and_cleanup()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Guarddog stopped")


if __name__ == "__main__":
    main()
