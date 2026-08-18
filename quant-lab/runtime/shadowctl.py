#!/usr/bin/env python3
"""QL-EXEC-R4.2 — shadowctl: independent control for the generic TB shadow.

Controls ONLY the generic shadow process (start/stop/status/tail/parity).
Never touches tbctl, the active supervisor/worker/watcher/dashboard, active
TB state, or the Task Scheduler.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

_QL = Path(__file__).resolve().parent.parent  # quant-lab/
for _p in (_QL, _QL / "runtime"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from runtime.tb_shadow_config import (  # noqa: E402
    HEARTBEAT_JSON,
    MISMATCH_JSONL,
    PARITY_JSONL,
    SHADOW_DESIRED_STATE_FILE,
    SHADOW_LOG,
    SHADOW_PID_FILE,
    SHADOW_STATE_DIR,
    TELEMETRY_JSON,
)

PROCESS_MODULE = "runtime.tb_generic_shadow"
_STOP_TIMEOUT_S = 15


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _pid() -> int | None:
    try:
        return int(SHADOW_PID_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _process_alive(pid: int) -> bool:
    """True if the PID is a RUNNING process.

    On Windows, os.kill(pid, 0) returns True for a terminated-but-unreaped
    child (the OS keeps the entry until the parent waits). GetExitCodeProcess
    distinguishes STILL_ACTIVE (259) from a real exit code, so stop/status are
    truthful even for our own short-lived children.
    """
    try:
        import ctypes  # noqa: PLC0415

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        SYNCHRONIZE = 0x00100000
        STILL_ACTIVE = 259
        h = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, int(pid))
        if not h:
            return False
        try:
            code = ctypes.c_ulong()
            ok = ctypes.windll.kernel32.GetExitCodeProcess(
                h, ctypes.byref(code))
            return bool(ok) and code.value == STILL_ACTIVE
        finally:
            ctypes.windll.kernel32.CloseHandle(h)
    except Exception:  # noqa: BLE001 — non-Windows / no ctypes fallback
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def _start(state_dir: str | Path | None, wait: bool) -> int:
    state_dir = Path(state_dir) if state_dir else SHADOW_STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
    existing = _pid()
    if existing and _process_alive(existing):
        print(f"SHADOW_ALREADY_RUNNING pid={existing}")
        return 2
    log_f = open(SHADOW_LOG, "a", encoding="utf-8")
    cmd = [sys.executable, "-m", PROCESS_MODULE,
           "--state-dir", str(state_dir)]
    try:
        proc = subprocess.Popen(cmd, cwd=str(_QL), stdout=log_f, stderr=log_f)
    except OSError as e:
        log_f.close()
        print(f"SHADOW_START_FAILED {e}")
        return 1
    print(f"SHADOW_STARTED pid={proc.pid}")
    if wait:
        # Wait for the child's own PID lock (written after boot) with a
        # generous window; a dead child reports failure, never a false start.
        for _ in range(60):
            if not _process_alive(proc.pid):
                print(f"SHADOW_START_FAILED pid={proc.pid} exited early")
                return 1
            if _pid() == proc.pid:
                return 0
            time.sleep(0.5)
        print(f"SHADOW_START_TIMEOUT pid={proc.pid}")
        return 1
    return 0


def _stop() -> int:
    pid = _pid()
    if pid is None or not _process_alive(pid):
        print("SHADOW_NOT_RUNNING")
        return 0
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as e:
        print(f"SHADOW_STOP_FAILED {e}")
        return 1
    for _ in range(_STOP_TIMEOUT_S * 2):
        if not _process_alive(pid):
            break
        time.sleep(0.5)
    if _process_alive(pid):
        print(f"SHADOW_STOP_TIMEOUT pid={pid}")
        return 1
    print(f"SHADOW_STOPPED pid={pid}")
    return 0


def _status() -> int:
    pid = _pid()
    alive = pid is not None and _process_alive(pid)
    telemetry = _read_json(TELEMETRY_JSON)
    heartbeat = _read_json(HEARTBEAT_JSON)
    out = {
        "pid": pid,
        "alive": alive,
        "telemetry": telemetry,
        "heartbeat": heartbeat,
    }
    print(json.dumps(out, indent=2, default=str))
    return 0


def _tail(path: Path, n: int) -> int:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        print("SHADOW_STREAM_EMPTY")
        return 0
    for line in lines[-n:]:
        print(line)
    return 0


def _parity() -> int:
    telemetry = _read_json(TELEMETRY_JSON)
    counters = telemetry.get("counters", {})
    out = {
        "bars_compared": counters.get("bars_compared", 0),
        "decision_opportunities": counters.get("decision_opportunities", 0),
        "parity_exact": counters.get("parity_exact", 0),
        "parity_normalized": counters.get("parity_normalized", 0),
        "mismatches": counters.get("mismatches", 0),
        "hypothetical_intents": counters.get("hypothetical_intents", 0),
        "execution_gate_denials": counters.get("execution_gate_denials", 0),
        "broker_write_calls": telemetry.get("broker_write_calls", 0),
    }
    print(json.dumps(out, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="generic TB shadow control")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_start = sub.add_parser("start")
    p_start.add_argument("--state-dir", default=None)
    p_start.add_argument("--wait", action="store_true")

    sub.add_parser("stop")
    sub.add_parser("status")
    p_tail = sub.add_parser("tail")
    p_tail.add_argument("--n", type=int, default=50)
    sub.add_parser("parity")

    args = ap.parse_args(argv)
    if args.cmd == "start":
        return _start(args.state_dir, args.wait)
    if args.cmd == "stop":
        return _stop()
    if args.cmd == "status":
        return _status()
    if args.cmd == "tail":
        return _tail(PARITY_JSONL, args.n)
    if args.cmd == "parity":
        return _parity()
    return 2


if __name__ == "__main__":
    sys.exit(main())
