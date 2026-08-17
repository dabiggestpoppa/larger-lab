#!/usr/bin/env python3
"""
TB-R6.1 — TB SUPERVISOR
=======================

Owns the WORKER process lifecycle ONLY (never strategy logic):

  * spawn the worker when desired-state == RUNNING
  * bounded exponential backoff restart after unexpected worker failure
  * kill + restart a worker whose heartbeat is dead while the process lives
  * NEVER restart after an intentional `tbctl stop` (durable desired state)
  * singleton: a second supervisor fails closed (split-brain protection)

The supervisor itself is started by tbctl, or by the Windows Task Scheduler
entry at logon (see install_windows_runtime.ps1). It stays alive across
market closures and PC reboots (via the scheduled task); the worker is
started/stopped underneath it.

    python -u quant-lab/runtime/tb_supervisor.py
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

QUANT_LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(QUANT_LAB / "runtime"))

from tb_runtime_config import (  # noqa: E402
    RESTART_BACKOFF_S, STALE_HEARTBEAT_RESTART_S, SUPERVISOR_PID_FILE,
    WORKER_PID_FILE, SUPERVISOR_LOG, LOG_MAX_BYTES, LOG_BACKUP_COUNT,
    RUNNING, STOPPED_BY_USER,
)
from tb_runtime_db import RuntimeDB  # noqa: E402
from tb_proc import PidLock, pid_alive  # noqa: E402

log = logging.getLogger("tb.supervisor")
POLL_S = 5
WORKER_ALIVE_RESET_S = 120   # survive this long => reset the backoff counter


def _setup_logging() -> None:
    h = RotatingFileHandler(SUPERVISOR_LOG, maxBytes=LOG_MAX_BYTES,
                            backupCount=LOG_BACKUP_COUNT, encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(h)
    c = logging.StreamHandler()
    c.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    root.addHandler(c)


class Supervisor:
    def __init__(self):
        self.rdb = RuntimeDB()
        self.lock = PidLock(SUPERVISOR_PID_FILE, "supervisor")
        self.worker_proc: subprocess.Popen | None = None
        self.failures = 0
        self.last_spawn_ts = 0.0
        self.worker_spawned_at = 0.0
        self.stop_requested = False

    # ── worker helpers ──────────────────────────────────────────────────
    def _worker_pid(self) -> int | None:
        try:
            p = int(WORKER_PID_FILE.read_text().strip())
            return p if pid_alive(p) else None
        except Exception:
            return None

    def _spawn_worker(self) -> None:
        gen = datetime.now(timezone.utc).strftime("GEN-%Y%m%dT%H%M%S")
        args = [sys.executable, "-u",
                str(QUANT_LAB / "runtime" / "tb_worker.py"),
                "--generation", gen]
        with open(SUPERVISOR_LOG, "ab") as f:
            self.worker_proc = subprocess.Popen(
                args, stdout=f, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=(subprocess.CREATE_NO_WINDOW
                               | subprocess.DETACHED_PROCESS)
                if sys.platform.startswith("win") else 0)
        self.last_spawn_ts = time.time()
        self.worker_spawned_at = time.time()
        log.info("worker spawned pid=%d", self.worker_proc.pid)

    def _terminate_worker(self, reason: str) -> None:
        pid = self._worker_pid() or (
            self.worker_proc.pid if self.worker_proc else None)
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)
            except Exception:
                pass
        log.info("worker stopped (%s)", reason)
        self.worker_proc = None

    # ── main loop ───────────────────────────────────────────────────────
    def run(self) -> int:
        got = self.lock.try_acquire()
        if not got["ok"]:
            log.error("SUPERVISOR SINGLETON BLOCKED: %s", got["reason"])
            print(f"SINGLETON_BLOCKED: {got['reason']}", flush=True)
            return 2
        self.rdb.set_status("supervisor_pid", str(os.getpid()))
        self.rdb.set_status("supervisor_state", "RUNNING")
        log.info("supervisor start pid=%d", os.getpid())

        def _sig(signum, frame):  # noqa: ARG001
            self.stop_requested = True
        signal.signal(signal.SIGINT, _sig)
        signal.signal(signal.SIGTERM, _sig)

        try:
            while not self.stop_requested:
                desired = self.rdb.desired_state()
                self.rdb.set_status("desired_state", desired)

                if desired == STOPPED_BY_USER:
                    if self._worker_pid() or self.worker_proc:
                        self._terminate_worker("intentional user stop")
                    self.rdb.set_status("supervisor_state", "STOPPED_BY_USER")
                    time.sleep(POLL_S)
                    continue

                # RUNNING
                worker_pid = self._worker_pid()
                if not worker_pid:
                    delay = RESTART_BACKOFF_S[
                        min(self.failures, len(RESTART_BACKOFF_S) - 1)]
                    if time.time() - self.last_spawn_ts >= delay:
                        self._spawn_worker()
                    else:
                        self.rdb.set_status(
                            "supervisor_state",
                            f"BACKOFF_{delay}s_failures={self.failures}")
                else:
                    # alive: reset backoff once it has survived a while
                    if (self.worker_spawned_at
                            and time.time() - self.worker_spawned_at
                            > WORKER_ALIVE_RESET_S):
                        self.failures = 0
                    # heartbeat health
                    age = self.rdb.heartbeat_age_s()
                    if age is not None and age > STALE_HEARTBEAT_RESTART_S:
                        log.warning("heartbeat stale (%.0fs); restarting worker",
                                    age)
                        self.failures += 1
                        self._terminate_worker("stale heartbeat")
                        self.rdb.record_error("supervisor",
                                              f"stale heartbeat {age:.0f}s")
                    elif age is None:
                        # worker alive but never heartbeated yet -> give it time
                        pass
                    self.rdb.set_status("supervisor_state", "RUNNING")
                time.sleep(POLL_S)
        finally:
            self._terminate_worker("supervisor shutdown")
            self.rdb.set_status("supervisor_state", "STOPPED")
            self.lock.release()
            self.rdb.close()
        log.info("supervisor exit")
        return 0


def main() -> int:
    _setup_logging()
    return Supervisor().run()


if __name__ == "__main__":
    sys.exit(main())
