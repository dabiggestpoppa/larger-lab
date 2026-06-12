"""
Windows Singleton Enforcement — No Duplicates, No Zombies
=========================================================
Uses Windows named mutex (OS-level) to ensure only one instance runs.
Also kills any stale processes with the same script name on startup.

Usage:
    from singleton import enforce_singleton
    enforce_singleton("my_service_name")  # Exits if another instance is running

    # Or with auto-kill:
    enforce_singleton("my_service_name", kill_others=True)
"""
import os
import sys
import time
import ctypes
import subprocess
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def enforce_singleton(name: str, kill_others: bool = True) -> None:
    """
    Enforce singleton using Windows named mutex.
    If another instance is running, exit immediately.
    If kill_others=True, kill stale processes with same script name first.
    """
    mutex_name = f"Global\\CEREBUS_{name}_SINGLETON"

    if kill_others:
        _kill_stale_instances()

    # Create named mutex
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()

    if last_error == 183:  # ERROR_ALREADY_EXISTS
        # Another instance is running — exit silently
        sys.exit(0)

    if not mutex:
        # Could not create mutex — exit to be safe
        sys.exit(0)


def _kill_stale_instances():
    """Kill other processes running the same script."""
    my_pid = os.getpid()
    script_name = Path(sys.argv[0]).name

    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if not line or 'python.exe' not in line.lower():
                continue
            parts = line.split(',')
            if len(parts) < 2:
                continue
            try:
                pid = int(parts[1].strip('"'))
                if pid == my_pid:
                    continue
                # Check command line
                cmd_result = subprocess.run(
                    ["powershell", "-Command",
                     f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid}').CommandLine"],
                    capture_output=True, text=True, timeout=5
                )
                cmd_line = cmd_result.stdout.strip()
                if script_name in cmd_line:
                    handle = ctypes.windll.kernel32.OpenProcess(0x0001, False, pid)
                    if handle:
                        ctypes.windll.kernel32.TerminateProcess(handle, 1)
                        ctypes.windll.kernel32.CloseHandle(handle)
                        time.sleep(1)
            except (ValueError, OSError, IndexError):
                pass
    except Exception:
        pass


def release_singleton(name: str) -> None:
    """Release the singleton mutex (called on clean shutdown)."""
    mutex_name = f"Global\\CEREBUS_{name}_SINGLETON"
    mutex = ctypes.windll.kernel32.OpenMutexW(0x0001, False, mutex_name)
    if mutex:
        ctypes.windll.kernel32.CloseHandle(mutex)
