"""
CTBT T4 — Forward shadow collection loop (watchdog style, PID-locked).

Poll the read-only provider feed for newly completed M5 bars, evaluate both
sealed candidates on synchronized snapshots, append forward events to the
per-candidate ledgers, and refresh the forward clock.

Read-only: no orders, no positions, no account mutation.  Runs until a
SIGTERM/SIGINT or stop marker.  Singleton enforced with a PID file (never
OS-level primitives).

Start (operator, after human review):
    python ctbt_runtime/run_shadow_loop.py --start

Stop:
    python ctbt_runtime/run_shadow_loop.py --stop
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from .config import BASIS_LEGS, RUNTIME  # noqa: E402
from .data_feed import CTBTDataFeed  # noqa: E402
from .forward_clock import ForwardClock  # noqa: E402
from .sealed_engine import SealedStrategyEngine  # noqa: E402
from .shadow_ledger import ShadowEventLedger  # noqa: E402

STOP = False


def _sig(signum, frame):
    global STOP
    STOP = True


signal.signal(signal.SIGTERM, _sig)
signal.signal(signal.SIGINT, _sig)


def _pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


class ShadowLoop:
    def __init__(self):
        self.feed = CTBTDataFeed()
        self.clock = ForwardClock()
        self.engines = {tri: SealedStrategyEngine(tri) for tri in BASIS_LEGS}
        self.ledgers = {tri: ShadowEventLedger(tri) for tri in BASIS_LEGS}
        self.last_bar: dict = {}   # triangle -> last processed M5 ts (iso)

    def start(self) -> int:
        if not self.clock.is_active():
            print("ERROR: no active activation seal. Refusing to run.", flush=True)
            return 2
        if not self.feed.init():
            print(f"ERROR: MT5 init failed: {self.feed.mt5.last_error()}", flush=True)
            return 2
        try:
            acct = self.feed.account_summary()
            print(f"feed connected: {acct}", flush=True)
            while not STOP:
                try:
                    self._tick()
                except Exception as e:  # noqa: BLE001 - keep the loop alive
                    print(f"tick error (non-fatal): {e}", flush=True)
                time.sleep(RUNTIME["poll_interval_seconds"])
        finally:
            self.feed.shutdown()
        print("shadow loop stopped cleanly.", flush=True)
        return 0

    def _tick(self) -> None:
        for tri, legs in BASIS_LEGS.items():
            # last completed M5 ts per leg must agree
            ts_per_leg = {leg: self.feed.last_completed_m5_ts(leg) for leg in legs}
            ts_set = set(ts_per_leg.values())
            if len(ts_set) != 1 or None in ts_set:
                # legs unsynchronized / feed incomplete: skip this tick
                continue
            ts = ts_set.pop()
            last = self.last_bar.get(tri)
            if last is not None and ts <= last:
                continue
            # fetch warmup + new bars from a safe start
            start = (datetime.fromisoformat(last) if last
                     else ts - timedelta(days=5))
            snapshots = self.feed.build_history(legs, start, ts)
            if len(snapshots) < 210:
                self.last_bar[tri] = ts
                continue
            events = self.engines[tri].evaluate(snapshots)
            for ev in events:
                if last is None or datetime.fromisoformat(ev["decision_bar_timestamp"]) > last:
                    self.ledgers[tri].append(ev)
            self.last_bar[tri] = ts
        self.clock.update_clock({tri: self.ledgers[tri].count()
                                 for tri in BASIS_LEGS})


def main(argv):
    if len(argv) >= 2 and argv[1] == "--stop":
        pid_file = RUNTIME["pid_file"]
        if pid_file.exists():
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            print(f"sent SIGTERM to {pid}")
        else:
            print("no pid file; nothing to stop")
        return 0
    if len(argv) >= 2 and argv[1] == "--start":
        pid_file = RUNTIME["pid_file"]
        if pid_file.exists() and _pid_running(int(pid_file.read_text().strip())):
            print("shadow loop already running")
            return 0
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(os.getpid()))
        try:
            return ShadowLoop().start()
        finally:
            pid_file.unlink(missing_ok=True)
    # single-tick mode (used for smoke tests / manual verification)
    loop = ShadowLoop()
    loop.feed.init()
    try:
        loop._tick()
    finally:
        loop.feed.shutdown()
    print("single tick complete (read-only)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
