"""
Windows Singleton Enforcement - No Duplicates, No Zeros
========================================================
Uses Windows named mutex (OS-level) to ensure only one instance runs.
Also kills any stale processes with same service name on startup.

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

# Global dict to keep mutex handles alive for process lifetime
_mutex_handles = {}


def enforce_singleton(name, kill_others=True):
    """
    Enforce singleton using Windows named mutex.
    If another instance is running, exit immediately.
    If kill_others=True, kill stale processes with same service name first.
    """
    mutex_name = "Global\\CEREBUS_" + name + "_SINGLETON"

    if kill_others:
        _kill_stale_instances(name)

    # Create named mutex - keep handle alive so mutex persists
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()

    if last_error == 183:  # ERROR_ALREADY_EXISTS
        # Another instance is running - exit silently
        if mutex:
            ctypes.windll.kernel32.CloseHandle(mutex)
        sys.exit(0)

    if not mutex:
        # Could not create mutex - exit to be safe
        sys.exit(0)

    # Store handle so it stays alive for the lifetime of this process
    _mutex_handles[name] = mutex


def _get_search_patterns(name):
    """Get command-line search patterns for a service name."""
    patterns = {
        "cerebus_scanner": ["run_cerebus_unified.py"],
        "oce_backend": ["oce.backend.main"],
    }
    return patterns.get(name, [])


def _kill_stale_instances(name):
    """Kill other processes that match our service name patterns."""
    my_pid = os.getpid()
    patterns = _get_search_patterns(name)
    if not patterns:
        return

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
                     "(Get-CimInstance Win32_Process -Filter 'ProcessId=" + str(pid) + "').CommandLine"],
                    capture_output=True, text=True, timeout=5
                )
                cmd_line = cmd_result.stdout.strip()
                for pattern in patterns:
                    if pattern in cmd_line:
                        handle = ctypes.windll.kernel32.OpenProcess(0x0001, False, pid)
                        if handle:
                            ctypes.windll.kernel32.TerminateProcess(handle, 1)
                            ctypes.windll.kernel32.CloseHandle(handle)
                            time.sleep(1)
                        break
            except (ValueError, OSError, IndexError):
                pass
    except Exception:
        pass


def release_singleton(name):
    """Release the singleton mutex (called on clean shutdown)."""
    if name in _mutex_handles:
        ctypes.windll.kernel32.CloseHandle(_mutex_handles[name])
        del _mutex_handles[name]
