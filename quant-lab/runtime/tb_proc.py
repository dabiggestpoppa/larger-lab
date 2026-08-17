#!/usr/bin/env python3
"""
TB-R6.1 — PROCESS / SINGLETON HELPERS
=====================================

PID-file singleton enforcement (never OS-level primitives): the worker and
the supervisor each hold a PID lock. A second instance fails closed.

Stale-PID handling: if the owning process is no longer alive, the lock is
reclaimable (crash recovery). If it IS alive, the lock is held -> BLOCKED.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

_WINDOWS = sys.platform.startswith("win")


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if _WINDOWS:
            # tasklist is slower; use os.kill(pid, 0) equivalent on Windows
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not h:
                return False
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


class PidLock:
    """Exclusive PID-file lock with stale reclaim."""

    def __init__(self, path: Path, role: str):
        self.path = Path(path)
        self.role = role
        self.acquired = False

    def try_acquire(self) -> dict:
        """Returns {ok: bool, reason: str, holder_pid: int|None}.
        Fails closed when the lock is held by a live process."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                holder = int(self.path.read_text().strip())
            except Exception:
                holder = None
            if holder and pid_alive(holder):
                return {"ok": False,
                        "reason": f"{self.role} singleton already held by "
                                  f"live pid {holder}",
                        "holder_pid": holder}
            # stale lock (owner dead) -> reclaim
            try:
                self.path.unlink()
            except OSError:
                pass
        try:
            self.path.write_text(str(os.getpid()))
            self.acquired = True
            return {"ok": True, "reason": "", "holder_pid": os.getpid()}
        except OSError as e:
            return {"ok": False, "reason": str(e), "holder_pid": None}

    def release(self) -> None:
        if self.acquired:
            try:
                if self.path.exists() and \
                        self.path.read_text().strip() == str(os.getpid()):
                    self.path.unlink()
            except OSError:
                pass
            self.acquired = False


def spawn_detached(args, log_path: Path) -> subprocess.Popen:
    """Spawn a detached background process (supervisor / dashboard) whose
    stdout/stderr go to a log file. On Windows: CREATE_NO_WINDOW +
    DETACHED_PROCESS so the console is not blocked."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    flags = 0
    if _WINDOWS:
        flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
    with open(log_path, "ab") as f:
        return subprocess.Popen(
            args, stdout=f, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, creationflags=flags,
            cwd=str(Path(args[0]).resolve().parent.parent
                    if len(args) > 0 else "."))
