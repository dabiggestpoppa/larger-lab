#!/usr/bin/env python3
"""
PO Watchdog — monitors telegram gateway and restarts if it dies.
Runs as a background process. Checks every 60 seconds.
"""
import subprocess
import time
import os
import sys
import signal
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GATEWAY_SCRIPT = os.path.join(SCRIPT_DIR, "telegram_gateway.py")
LOG_FILE = os.path.join(SCRIPT_DIR, "..", "logs", "po_watchdog.log")
CHECK_INTERVAL = 60  # seconds
MAX_RESTARTS = 10
RESTART_COOLDOWN = 300  # 5 minutes after max restarts

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

def _get_gateway_pids():
    """Get all running telegram_gateway.py PIDs."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*telegram_gateway*' } | Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=10
        )
        pids = []
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if line:
                try:
                    pids.append(int(line))
                except ValueError:
                    pass
        return pids
    except:
        return []

def _is_mutex_held():
    """Check if the Windows mutex is held by another process."""
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # Try to open existing mutex
        mutex = kernel32.OpenMutexW(0x00100000, False, "Global\\TelegramGateway_Singleton_Mutex")
        if mutex:
            kernel32.CloseHandle(mutex)
            return True
        return False
    except:
        return False

def is_gateway_running():
    """Check if telegram gateway is running.
    Uses Windows mutex as primary check (most reliable).
    Falls back to process scan. Cleans up stale PID file."""
    pid_file = os.path.join(SCRIPT_DIR, ".telegram_gateway.pid")

    # Primary: check Windows mutex (true singleton indicator)
    if _is_mutex_held():
        # Mutex exists — gateway is running. Update PID file to match.
        pids = _get_gateway_pids()
        if pids:
            try:
                with open(pid_file, "w") as f:
                    f.write(str(pids[0]))
            except:
                pass
        return True

    # Fallback: scan for gateway processes
    pids = _get_gateway_pids()
    if pids:
        # Gateway running but mutex not held (shouldn't happen, but handle it)
        try:
            with open(pid_file, "w") as f:
                f.write(str(pids[0]))
        except:
            pass
        return True

    # Nothing running — clean up stale PID file
    if os.path.exists(pid_file):
        try:
            os.remove(pid_file)
        except:
            pass
    return False

def kill_all_gateways():
    """Kill ALL telegram_gateway.py processes. Used before restart."""
    import ctypes
    kernel32 = ctypes.windll.kernel32
    PROCESS_TERMINATE = 0x0001
    killed = 0
    for pid in _get_gateway_pids():
        try:
            handle = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
            if handle:
                kernel32.TerminateProcess(handle, 1)
                kernel32.CloseHandle(handle)
                killed += 1
                log(f"Killed gateway PID {pid}")
        except:
            pass
    if killed > 0:
        time.sleep(3)  # Wait for full shutdown
    return killed

def start_gateway():
    """Start the telegram gateway process. Kills all existing instances first."""
    # Always kill all duplicates before starting fresh
    kill_all_gateways()
    try:
        subprocess.Popen(
            [sys.executable, GATEWAY_SCRIPT],
            cwd=SCRIPT_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        log("Gateway started (all duplicates killed first)")
        return True
    except Exception as e:
        log(f"Failed to start gateway: {e}")
        return False

def main():
    log("=" * 60)
    log("PO Watchdog started")
    log(f"Monitoring: {GATEWAY_SCRIPT}")
    log(f"Check interval: {CHECK_INTERVAL}s")
    log("=" * 60)

    restart_count = 0
    last_restart_time = 0

    def handle_signal(signum, frame):
        log(f"Watchdog received signal {signum}, shutting down")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while True:
        try:
            if not is_gateway_running():
                log("Gateway DOWN — restarting...")

                # Check restart cooldown
                now = time.time()
                if restart_count >= MAX_RESTARTS:
                    if now - last_restart_time < RESTART_COOLDOWN:
                        log(f"Max restarts ({MAX_RESTARTS}) reached, waiting {RESTART_COOLDOWN}s cooldown...")
                        time.sleep(RESTART_COOLDOWN)
                        restart_count = 0
                    else:
                        restart_count = 0

                if start_gateway():
                    restart_count += 1
                    last_restart_time = now
                    log(f"Restart #{restart_count}")
                    # Wait for gateway to initialize
                    time.sleep(10)
                else:
                    log("Failed to start gateway, retrying in 30s...")
                    time.sleep(30)
            else:
                # Reset restart count if gateway has been running fine
                if restart_count > 0 and time.time() - last_restart_time > 300:
                    restart_count = 0

        except Exception as e:
            log(f"Watchdog error: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
