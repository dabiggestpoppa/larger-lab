"""
CTBT T4/T4.1 — Forward shadow collection loop (watchdog style, PID-locked).

Poll the read-only provider feed for newly completed M5 bars, evaluate both
sealed candidates on synchronized snapshots, append FORWARD events to the
per-candidate ledgers, and refresh the forward clock + operator status.

FORWARD EVIDENCE RULE:
    only events with decision_bar_timestamp >= first_eligible_m5_bar
    (from the activation seal, strictly after activation) may enter a
    ledger.  Pre-activation bars are never relabeled.

RESTART SAFETY:
    last-processed bar per triangle is persisted to state/processed_<tri>.json
    and seeded from the ledger's max entry on start, so a restart never
    duplicates signals, resets counts, rewrites the activation timestamp,
    or truncates ledgers.

Read-only: no orders, no positions, no account mutation.  Singleton via PID
file (never OS-level primitives).

Start (operator):
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

import subprocess
from .config import BASIS_LEGS, RUNTIME, T4_DIR, REPO  # noqa: E402
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
    except ProcessLookupError:
        return False
    except OSError:
        # Windows: os.kill(pid, 0) raises WinError 87 for a LIVE process
        # (signal 0 is unsupported there); a dead pid raises ProcessLookupError.
        return True


def _parse_ts(s: str) -> datetime:
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s)


# Runtime files whose absence means the checkout has drifted (branch switch /
# partial checkout).  The collector MUST refuse to run in a drifted checkout
# rather than silently degrade like the 2026-08-20 branch-switch incident.
REQUIRED_RUNTIME_FILES = [
    "CTBT_T4_ACTIVATION_SEAL.json",
    "CTBT_T4_FORWARD_CLOCK.json",
    "CTBT_T4_OPERATOR_STATUS.json",
    "ctbt_runtime/config.py",
    "ctbt_runtime/sealed_engine.py",
    "ctbt_runtime/run_shadow_loop.py",
]


def runtime_self_check() -> dict:
    """Verify this checkout is a complete CTBT runtime, not a drifted branch.

    Returns {ok, missing, runtime_root, git_head}.  The collector refuses to
    start (and alerts) if required runtime files are missing.
    """
    missing = [f for f in REQUIRED_RUNTIME_FILES if not (T4_DIR / f).exists()]
    head = "unknown"
    try:
        head = subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        pass
    return {"ok": not missing, "missing": missing,
            "runtime_root": str(T4_DIR), "git_head": head}


class ShadowLoop:
    def __init__(self):
        self.feed = CTBTDataFeed()
        self.clock = ForwardClock()
        self.engines = {tri: SealedStrategyEngine(tri) for tri in BASIS_LEGS}
        self.ledgers = {tri: ShadowEventLedger(tri) for tri in BASIS_LEGS}
        self.seal = json.loads(RUNTIME["activation_seal"].read_text(encoding="utf-8"))
        self.first_eligible = self.seal["first_eligible_m5_bar"]
        self.activation_ts = self.seal["activation_timestamp_utc"]
        self.last_bar: dict = {}   # triangle -> last processed M5 ts (iso)
        self.operator_status = T4_DIR / "CTBT_T4_OPERATOR_STATUS.json"
        self.runtime_check = runtime_self_check()

    # ── persistence ────────────────────────────────────────────────────────
    def _processed_path(self, tri: str) -> Path:
        return RUNTIME["ledger_dir"] / f"processed_{tri}.json"

    def _load_processed(self, tri: str) -> str | None:
        p = self._processed_path(tri)
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))["last_bar"]
            except Exception:
                pass
        # seed from the ledger's max entry (restart safety)
        entries = self.ledgers[tri].read_all()
        ts = [e["decision_bar_timestamp"] for e in entries if e.get("decision_bar_timestamp")]
        return max(ts) if ts else None

    def _save_processed(self, tri: str, ts: str) -> None:
        self._processed_path(tri).write_text(
            json.dumps({"last_bar": ts, "updated_utc": datetime.utcnow().isoformat() + "Z"}),
            encoding="utf-8")

    # ── forward evidence filter ────────────────────────────────────────────
    def _is_forward_eligible(self, ev: dict) -> bool:
        """Only events decided on bars at/after the first eligible M5 bar."""
        try:
            return _parse_ts(ev["decision_bar_timestamp"]) >= _parse_ts(self.first_eligible)
        except Exception:
            return False

    # ── main loop ──────────────────────────────────────────────────────────
    def start(self) -> int:
        if not self.runtime_check["ok"]:
            print("ERROR: runtime checkout drift detected — required files missing:",
                  self.runtime_check["missing"], flush=True)
            print(f"ERROR: refusing to run from drifted runtime root {T4_DIR}. "
                  "Restore the dedicated CTBT runtime worktree.", flush=True)
            self._write_operator_status(running=False)
            return 2
        if not self.clock.is_active():
            print("ERROR: no active activation seal. Refusing to run.", flush=True)
            return 2
        if not self.feed.init():
            print(f"ERROR: MT5 init failed: {self.feed.mt5.last_error()}", flush=True)
            return 2
        if self.feed.server_offset is None:
            print("ERROR: cannot measure broker server-time offset; refusing to "
                  "run on an unverified time axis.", flush=True)
            return 2
        try:
            acct = self.feed.account_summary()
            print(f"feed connected: {acct}", flush=True)
            for tri in BASIS_LEGS:
                self.last_bar[tri] = self._load_processed(tri)
                print(f"{tri}: resuming from last processed bar {self.last_bar[tri]}",
                      flush=True)
            while not STOP:
                try:
                    self._tick()
                except Exception as e:  # noqa: BLE001 - keep the loop alive
                    print(f"tick error (non-fatal): {e}", flush=True)
                self._write_operator_status()
                time.sleep(RUNTIME["poll_interval_seconds"])
        finally:
            self.feed.shutdown()
            self._write_operator_status(running=False)
        print("shadow loop stopped cleanly.", flush=True)
        return 0

    def _tick(self) -> None:
        for tri, legs in BASIS_LEGS.items():
            # last completed M5 ts per leg must agree
            ts_per_leg = {leg: self.feed.last_completed_m5_ts(leg) for leg in legs}
            ts_set = set(ts_per_leg.values())
            if len(ts_set) != 1 or None in ts_set:
                continue  # legs unsynchronized / feed incomplete
            ts = ts_set.pop()
            ts_str = ts.isoformat()
            last = self.last_bar.get(tri)
            if last is not None and _parse_ts(ts_str) <= _parse_ts(last):
                continue
            start = (_parse_ts(last) if last
                     else _parse_ts(self.first_eligible) - timedelta(days=5))
            snapshots = self.feed.build_history(legs, start, ts)
            if len(snapshots) < 210:
                self.last_bar[tri] = ts_str
                self._save_processed(tri, ts_str)
                continue
            events = self.engines[tri].evaluate(snapshots)
            n_appended = 0
            for ev in events:
                if not self._is_forward_eligible(ev):
                    continue  # pre-activation / pre-first-eligible bar: never relabeled
                if last is None or _parse_ts(ev["decision_bar_timestamp"]) > _parse_ts(last):
                    self.ledgers[tri].append(ev)
                    n_appended += 1
            if n_appended:
                print(f"{tri}: +{n_appended} forward event(s) @ {ts_str}", flush=True)
            self.last_bar[tri] = ts_str
            self._save_processed(tri, ts_str)
        self.clock.update_clock({tri: self.ledgers[tri].count()
                                 for tri in BASIS_LEGS})

    # ── operator status (authoritative operational state artifact) ─────────
    def _write_operator_status(self, running: bool = True) -> None:
        counts = {tri: self.ledgers[tri].count() for tri in BASIS_LEGS}
        status = {
            "collector_running": running,
            "collector_pid": os.getpid() if running else None,
            "provider_connected": bool(self.feed.initialized),
            "last_bar_timestamp": {tri: self.last_bar.get(tri) for tri in BASIS_LEGS},
            "last_heartbeat_utc": datetime.utcnow().isoformat() + "Z",
            "EUR_GBP_USD_events": counts["EUR_GBP_USD"],
            "GBP_NZD_USD_events": counts["GBP_NZD_USD"],
            "signal_recognition_rate": self._recognition_rate(),
            "dashboard_data_freshness": datetime.utcnow().isoformat() + "Z",
            "order_prevention_pass": True,
            "forward_rule": f"events only at/after {self.first_eligible}",
            "activation_timestamp_utc": self.activation_ts,
            "runtime_root": self.runtime_check.get("runtime_root"),
            "runtime_git_head": self.runtime_check.get("git_head"),
            "runtime_self_check_ok": self.runtime_check.get("ok"),
        }
        self.operator_status.write_text(
            json.dumps(status, indent=2, default=str), encoding="utf-8")

    def _recognition_rate(self) -> float:
        """MATCHED_SHADOW + VALID_RUNTIME_BLOCK share of classified events."""
        total = matched = 0
        for tri in BASIS_LEGS:
            ap = self.ledgers[tri].path.with_suffix(".audit.jsonl")
            if not ap.exists():
                continue
            for line in open(ap, encoding="utf-8"):
                if not line.strip():
                    continue
                cls = json.loads(line).get("classification")
                if cls in ("MATCHED_SHADOW", "VALID_RUNTIME_BLOCK"):
                    matched += 1
                    total += 1
                elif cls in ("MISSED_SIGNAL", "RUNTIME_ONLY_SIGNAL",
                             "DATA_DIVERGENCE"):
                    total += 1
        return round(100.0 * matched / total, 2) if total else 100.0


def main(argv):
    if len(argv) >= 2 and argv[1] == "--stop":
        pid_file = RUNTIME["pid_file"]
        if pid_file.exists():
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            print(f"sent SIGTERM to {pid}")
            # wait briefly for a clean exit; remove stale pid if the process died
            for _ in range(10):
                if not pid_file.exists():
                    break
                if not _pid_running(pid):
                    pid_file.unlink(missing_ok=True)
                    break
                time.sleep(0.5)
            if pid_file.exists() and not _pid_running(pid):
                pid_file.unlink(missing_ok=True)
        else:
            print("no pid file; nothing to stop")
        return 0
    if len(argv) >= 2 and argv[1] == "--start":
        pid_file = RUNTIME["pid_file"]
        if pid_file.exists():
            stale = int(pid_file.read_text().strip())
            if _pid_running(stale):
                print("shadow loop already running")
                return 0
            print(f"removing stale pid file ({stale} not running)")
            pid_file.unlink(missing_ok=True)
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(os.getpid()))
        try:
            return ShadowLoop().start()
        finally:
            pid_file.unlink(missing_ok=True)
    # single-tick mode (smoke / manual verification)
    loop = ShadowLoop()
    loop.feed.init()
    try:
        loop._tick()
        loop._write_operator_status()
    finally:
        loop.feed.shutdown()
    print("single tick complete (read-only)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
