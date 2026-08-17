#!/usr/bin/env python3
"""
TB-R6.1 — tbctl — RUNTIME CONTROL CLI
======================================

    tbctl status
    tbctl start
    tbctl stop
    tbctl restart

`tbctl stop` is an INTENTIONAL STOP: it persists desired-state
STOPPED_BY_USER, so the supervisor (and the logon task on the next boot)
will NOT restart the worker until `tbctl start` is issued.
"""

from __future__ import annotations

import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

QUANT_LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(QUANT_LAB / "runtime"))

from tb_runtime_config import (  # noqa: E402
    SUPERVISOR_PID_FILE, WORKER_PID_FILE, SUPERVISOR_LOG, RUNNING,
    STOPPED_BY_USER, REQUIRED_SERVER,
)
from tb_runtime_db import RuntimeDB  # noqa: E402
from tb_proc import PidLock, pid_alive, spawn_detached  # noqa: E402


def _read_pid(path: Path) -> int | None:
    try:
        p = int(path.read_text().strip())
        return p if pid_alive(p) else None
    except Exception:
        return None


def _kill(pid: int | None, label: str) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(20):
            if not pid_alive(pid):
                return True
            time.sleep(0.25)
    except Exception:
        pass
    try:
        os.kill(pid, signal.SIGKILL)  # force (Windows: TerminateProcess)
    except Exception:
        pass
    return True


def cmd_status() -> int:
    rdb = RuntimeDB()
    hb = rdb.latest_heartbeat()
    age = rdb.heartbeat_age_s()
    desired = rdb.desired_state()
    sup = _read_pid(SUPERVISOR_PID_FILE)
    wrk = _read_pid(WORKER_PID_FILE)

    if desired == STOPPED_BY_USER:
        runtime = "STOPPED"
    elif hb is None:
        runtime = "OFFLINE"
    elif age is None or age > 90:
        runtime = "OFFLINE"
    elif age > 30:
        runtime = "DEGRADED"
    else:
        runtime = "ONLINE"

    dep_ts = rdb.get_status("deployment_start_timestamp", "")
    up = ""
    try:
        if dep_ts:
            d = datetime.fromisoformat(dep_ts)
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            s = (datetime.now(timezone.utc) - d).total_seconds()
            up = (f"{int(s//86400)}d {int(s%86400//3600):02d}:"
                  f"{int(s%3600//60):02d}")
    except Exception:
        pass

    mt5 = "OFFLINE"
    gate = "FAIL"
    state = "n/a"
    last_bar = ""
    basket = "none"
    today = 0.0
    deploy = 0.0
    if hb:
        mt5 = "CONNECTED" if hb["mt5_connected"] else "DEGRADED"
        gate = "PASS" if hb["account_gate"] else "FAIL"
        state = hb["state"]
        last_bar = hb["last_closed_bar"]
        basket = hb["open_basket_id"] or "none"
        today = hb["today_pnl"]
        deploy = hb["deploy_pnl"]

    print(f"TB Runtime: {runtime}")
    print(f"PID: {wrk or '-'} (supervisor: {sup or '-'})")
    print(f"Uptime: {up or 'n/a'}")
    print(f"Heartbeat: {f'{age:.0f}s ago' if age is not None else 'never'}")
    print(f"Desired: {desired}")
    print(f"MT5: {mt5}")
    print(f"Account: {'DEMO / ' + REQUIRED_SERVER if gate == 'PASS' else 'GATE ' + gate}")
    print(f"State: {state}")
    print(f"Last M5: {last_bar or 'n/a'}")
    print(f"Open basket: {basket}")
    print(f"Today TB PnL: ${today:,.2f}")
    print(f"Since deploy: ${deploy:,.2f}")
    rdb.close()
    return 0


def cmd_start() -> int:
    rdb = RuntimeDB()
    rdb.set_desired_state(RUNNING)
    rdb.close()
    # spawn supervisor if not already running
    if _read_pid(SUPERVISOR_PID_FILE):
        print("supervisor already running")
        return 0
    lock = PidLock(SUPERVISOR_PID_FILE, "supervisor")
    if not lock.try_acquire()["ok"]:
        print("supervisor start blocked (lock held by live process)")
        return 2
    lock.release()  # supervisor re-acquires inside its own process
    p = spawn_detached([sys.executable, "-u",
                        str(QUANT_LAB / "runtime" / "tb_supervisor.py")],
                       SUPERVISOR_LOG)
    print(f"supervisor starting (pid {p.pid}); desired=RUNNING")
    return 0


def cmd_stop() -> int:
    rdb = RuntimeDB()
    rdb.set_desired_state(STOPPED_BY_USER)
    rdb.close()
    sup = _read_pid(SUPERVISOR_PID_FILE)
    wrk = _read_pid(WORKER_PID_FILE)
    if sup:
        _kill(sup, "supervisor")
    if wrk:  # belt and braces: ensure the worker is down too
        _kill(wrk, "worker")
    print("stop requested; desired=STOPPED_BY_USER (no auto-restart)")
    return 0


def cmd_restart() -> int:
    cmd_stop()
    time.sleep(2)
    return cmd_start()


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        return cmd_status()
    if cmd == "start":
        return cmd_start()
    if cmd == "stop":
        return cmd_stop()
    if cmd == "restart":
        return cmd_restart()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
