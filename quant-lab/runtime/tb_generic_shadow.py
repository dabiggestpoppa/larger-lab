#!/usr/bin/env python3
"""QL-EXEC-R4.2 — generic TB shadow process (independent, observer only).

Consumes the legacy append-only export (Option B), drives the ShadowRuntime
(PRIMARY + CONTROL hypothetical parity), persists isolated state, and emits
heartbeat/telemetry. It has NO broker write capability, NO MT5 client, and is
never supervised by the active TB supervisor.

Lifecycle: manual start via shadowctl (no Task Scheduler / logon autostart in
G1). ``--once`` processes all currently available records and exits (used by
tests and drills).
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path

_QL = Path(__file__).resolve().parent.parent  # quant-lab/
for _p in (_QL, _QL / "runtime", _QL / "engines", _QL / "tb_live"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from execution_runtime.tb.adapters import TBStrategyAdapter  # noqa: E402
from execution_runtime.tb.shadow import (  # noqa: E402
    ReadOnlyBrokerSession,
    ShadowRuntimeAuthority,
)
from execution_runtime.tb.shadow_feed import ShadowExportFeed  # noqa: E402
from execution_runtime.tb.shadow_runner import ShadowRuntime  # noqa: E402
from execution_runtime.tb.shadow_store import ShadowStore  # noqa: E402
from engines.tb_forward_config import (  # noqa: E402
    PRIMARY_CONFIG,
    CONTROL_CONFIG,
)
from runtime.tb_shadow_config import (  # noqa: E402
    AUTO_START_ENABLED,
    DEPLOYMENT_GENERATION,
    HEARTBEAT_INTERVAL_S,
    LEGACY_AUTHORITY_SHA,
    PARITY_SCHEMA_VERSION,
    RUNTIME_ID,
    SHADOW_DB,
    SHADOW_PID_FILE,
    SHADOW_PROFILE_HASH,
    SHADOW_STATE_DIR,
    TOLERANCE_VERSION,
)


class ShadowPidLock:
    """Simple exclusive PID lock (one active shadow per runtime_id)."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def acquire(self, pid: int) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        with os.fdopen(fd, "w") as f:
            f.write(str(pid))
        return True

    def release(self) -> None:
        try:
            if self.path.exists():
                self.path.unlink()
        except OSError:
            pass

    @staticmethod
    def read_pid(path: str | Path) -> int | None:
        try:
            return int(Path(path).read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, default=str, indent=2), encoding="utf-8")


def run_once(*, state_dir: str | Path, export_path: str | Path) -> dict:
    """Process all currently available export records once; return telemetry.

    Used by tests, drills, and shadowctl parity. Never touches active TB.
    """
    state_dir = Path(state_dir)
    store = ShadowStore(state_dir / "runtime.sqlite")
    store.open()
    store.initialize(
        runtime_id=RUNTIME_ID,
        deployment_generation=DEPLOYMENT_GENERATION,
        profile_hash="shadow-profile",
        shadow_profile_hash=SHADOW_PROFILE_HASH,
        parity_schema_version=PARITY_SCHEMA_VERSION,
        tolerance_version=TOLERANCE_VERSION,
    )
    if store.desired_state(default="RUNNING") == "STOPPED_BY_USER":
        store.close()
        return {"started": False, "reason": "STOPPED_BY_USER",
                "broker_write_calls": 0}

    primary = TBStrategyAdapter(PRIMARY_CONFIG)
    control = TBStrategyAdapter(CONTROL_CONFIG)
    runtime = ShadowRuntime(
        runtime_id=RUNTIME_ID,
        deployment_generation=DEPLOYMENT_GENERATION,
        profile_hash="shadow-profile",
        shadow_profile_hash=SHADOW_PROFILE_HASH,
        store=store,
        feed=ShadowExportFeed(export_path),
        primary=primary,
        control=control,
        broker=ReadOnlyBrokerSession(truth={}),
        authority=ShadowRuntimeAuthority(),
        parity_path=state_dir / "parity.jsonl",
        mismatch_path=state_dir / "mismatches.jsonl",
    )
    runtime.start()
    if runtime.state == "STOPPED":
        store.close()
        return {"started": False, "reason": "STOPPED_BY_USER",
                "broker_write_calls": 0}

    from_seq = store.last_processed_seq()
    records, gaps, corrupt = runtime.feed.read_all_after(from_seq)
    for gap in gaps:
        runtime.record_feed_gap(gap["expected"], gap["found"])
    for c in corrupt:
        runtime.record_feed_corrupt(c.get("seq"), c.get("error", ""))
    for rec in records:
        runtime.step(rec)

    runtime.heartbeat()
    telemetry = runtime.telemetry()
    _write_json(state_dir / "telemetry.json", telemetry)
    _write_json(state_dir / "heartbeat.json",
                store.latest_heartbeat() or {})
    store.close()
    return telemetry


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="generic TB shadow (observer only)")
    ap.add_argument("--state-dir", default=str(SHADOW_STATE_DIR))
    ap.add_argument("--export", default=str(SHADOW_STATE_DIR / "legacy_export.jsonl"))
    ap.add_argument("--once", action="store_true",
                    help="process available records once, then exit")
    ap.add_argument("--heartbeat-interval", type=float, default=HEARTBEAT_INTERVAL_S)
    args = ap.parse_args(argv)

    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)

    if args.once:
        telemetry = run_once(state_dir=state_dir, export_path=args.export)
        print(json.dumps(telemetry, default=str))
        return 0

    lock = ShadowPidLock(state_dir / "shadow.pid")
    if not lock.acquire(os.getpid()):
        print("SHADOW_ALREADY_RUNNING", flush=True)
        return 2

    stop = {"flag": False}

    def _on_signal(signum, frame):  # noqa: ARG001
        stop["flag"] = True

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    store = ShadowStore(state_dir / "runtime.sqlite")
    store.open()
    store.initialize(
        runtime_id=RUNTIME_ID,
        deployment_generation=DEPLOYMENT_GENERATION,
        profile_hash="shadow-profile",
        shadow_profile_hash=SHADOW_PROFILE_HASH,
        parity_schema_version=PARITY_SCHEMA_VERSION,
        tolerance_version=TOLERANCE_VERSION,
    )
    primary = TBStrategyAdapter(PRIMARY_CONFIG)
    control = TBStrategyAdapter(CONTROL_CONFIG)
    runtime = ShadowRuntime(
        runtime_id=RUNTIME_ID,
        deployment_generation=DEPLOYMENT_GENERATION,
        profile_hash="shadow-profile",
        shadow_profile_hash=SHADOW_PROFILE_HASH,
        store=store,
        feed=ShadowExportFeed(args.export),
        primary=primary,
        control=control,
        broker=ReadOnlyBrokerSession(truth={}),
        authority=ShadowRuntimeAuthority(),
        parity_path=state_dir / "parity.jsonl",
        mismatch_path=state_dir / "mismatches.jsonl",
    )
    runtime.start()
    if runtime.state == "STOPPED":
        store.close()
        lock.release()
        print("SHADOW_STOPPED_BY_USER", flush=True)
        return 0

    print(f"SHADOW_STARTED pid={os.getpid()} state_dir={state_dir}", flush=True)
    try:
        while not stop["flag"]:
            from_seq = store.last_processed_seq()
            records, gaps, corrupt = runtime.feed.read_all_after(from_seq)
            for gap in gaps:
                runtime.record_feed_gap(gap["expected"], gap["found"])
            for c in corrupt:
                runtime.record_feed_corrupt(c.get("seq"), c.get("error", ""))
            for rec in records:
                runtime.step(rec)
            runtime.heartbeat()
            _write_json(state_dir / "telemetry.json", runtime.telemetry())
            _write_json(state_dir / "heartbeat.json",
                        store.latest_heartbeat() or {})
            time.sleep(args.heartbeat_interval)
    finally:
        runtime.stop()
        store.close()
        lock.release()
    print("SHADOW_STOPPED", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
