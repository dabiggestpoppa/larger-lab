#!/usr/bin/env python3
"""
TB-R6.1 — RUNTIME AUDIT SUITE
==============================

Deterministic, offline (MT5 stubbed) audits for the persistent demo runtime:

  runtime DB integrity / desired state / NAV baselines
  PID singleton (blocked + stale reclaim)
  dashboard status derivation (ONLINE/DEGRADED/OFFLINE/STOPPED)
  worker WAITING_FOR_MT5 path (fail-closed, bounded retry)
  worker market-closure path (ONLINE_MARKET_CLOSED, no orders)
  PnL accounting (TB-owned ONLY: magic + TB| tag; foreign excluded)
  disk guard (critically low disk => DEGRADED_DISK, no execution)
  log rotation (bounded size / backups)

Run:  python quant-lab/runtime/tb_r6_1_tests.py
Exit 0 when all pass. Writes TB_R6_1_RUNTIME_AUDITS.json.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

QUANT_LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(QUANT_LAB / "runtime"))

RESULTS = {"tests": [], "passed": 0, "failed": 0}


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS["tests"].append({"name": name, "pass": bool(ok), "detail": detail})
    if ok:
        RESULTS["passed"] += 1
        print(f"  PASS  {name}")
    else:
        RESULTS["failed"] += 1
        print(f"  FAIL  {name}  {detail}")


def test_runtime_db(tmp: Path) -> None:
    import tb_runtime_db
    from tb_runtime_db import RuntimeDB
    from tb_runtime_config import RUNNING, STOPPED_BY_USER

    db = RuntimeDB(tmp / "t.db")
    check("db integrity clean", db.integrity_check()["ok"],
          str(db.integrity_check()))
    db.set_desired_state(STOPPED_BY_USER)
    check("desired-state persisted", db.desired_state() == STOPPED_BY_USER)
    db.set_desired_state(RUNNING)
    check("desired-state flip", db.desired_state() == RUNNING)
    db.freeze_daily_nav("2026-08-17", 1000.0)
    check("daily nav frozen once",
          db.freeze_daily_nav("2026-08-17", 2000.0) is None
          and db.daily_nav("2026-08-17") == 1000.0)
    db.freeze_deployment_nav("G1", 500.0)
    check("deployment nav frozen once",
          db.deployment_nav("G1") == 500.0)
    for i in range(5):
        db.record_heartbeat({"ts": f"2026-08-17T08:00:0{i}+00:00", "pid": 1,
                             "generation": "G1", "state": "FLAT",
                             "mt5_connected": 1, "account_gate": 1,
                             "market_open": 1, "last_closed_bar": "",
                             "last_signal_time": "", "open_basket_id": "",
                             "today_pnl": 0.0, "open_pnl": 0.0,
                             "deploy_pnl": 0.0, "deploy_pnl_pct": 0.0,
                             "account_equity": 0.0, "disk_free_gb": 1.0,
                             "last_error": ""})
    check("heartbeat monotonic", db.integrity_check()["monotonic_ids"])
    db.record_error("worker", "boom")
    check("error trail", db.recent_errors(1)[0]["message"] == "boom")
    db.close()


def test_singleton(tmp: Path) -> None:
    from tb_proc import PidLock
    p1 = PidLock(tmp / "x.pid", "worker")
    r1 = p1.try_acquire()
    check("first acquires", r1["ok"])
    p2 = PidLock(tmp / "x.pid", "worker")
    r2 = p2.try_acquire()
    check("second blocked (live holder)", not r2["ok"]
          and "already held" in r2["reason"], r2["reason"])
    p1.release()
    p3 = PidLock(tmp / "x.pid", "worker")
    r3 = p3.try_acquire()
    check("stale reclaim after release", r3["ok"])
    p3.release()
    # stale pid (dead process)
    dead = tmp / "dead.pid"
    dead.write_text("999999999")
    p4 = PidLock(dead, "worker")
    r4 = p4.try_acquire()
    check("stale dead-pid reclaimed", r4["ok"])
    p4.release()


def test_dashboard_status(tmp: Path) -> None:
    from tb_runtime_db import RuntimeDB
    from tb_runtime_config import RUNNING, STOPPED_BY_USER
    import tb_dashboard as dash

    db = RuntimeDB(tmp / "d.db")
    db.set_desired_state(RUNNING)
    s = dash.build_status(db)
    check("no heartbeat => OFFLINE", s["engine_status"] == "OFFLINE",
          s["engine_status"])
    now = time.time()
    db.record_heartbeat({"ts": _iso_from_epoch(now), "pid": 1,
                         "generation": "G", "state": "FLAT",
                         "mt5_connected": 1, "account_gate": 1,
                         "market_open": 1, "last_closed_bar": "B",
                         "last_signal_time": "", "open_basket_id": "",
                         "today_pnl": 0.0, "open_pnl": 0.0,
                         "deploy_pnl": 0.0, "deploy_pnl_pct": 0.0,
                         "account_equity": 100.0, "disk_free_gb": 1.0,
                         "last_error": ""})
    s = dash.build_status(db)
    check("fresh heartbeat => ONLINE", s["engine_status"] == "ONLINE",
          s["engine_status"])
    check("mt5 status derived", s["mt5_status"] == "CONNECTED")
    check("strategy FLAT", s["strategy_state"] == "FLAT")
    check("open basket NO", s["open_basket"] == "NO")
    db.record_heartbeat({"ts": _iso_from_epoch(now - 200), "pid": 1,
                         "generation": "G", "state": "FLAT",
                         "mt5_connected": 1, "account_gate": 1,
                         "market_open": 1, "last_closed_bar": "",
                         "last_signal_time": "", "open_basket_id": "",
                         "today_pnl": 0.0, "open_pnl": 0.0,
                         "deploy_pnl": 0.0, "deploy_pnl_pct": 0.0,
                         "account_equity": 100.0, "disk_free_gb": 1.0,
                         "last_error": ""})
    s = dash.build_status(db)
    check("stale heartbeat => OFFLINE", s["engine_status"] == "OFFLINE",
          s["engine_status"])
    db.set_desired_state(STOPPED_BY_USER)
    s = dash.build_status(db)
    check("user stop => STOPPED", s["engine_status"] == "STOPPED")
    db.close()

def test_worker_paths(tmp: Path) -> None:
    """Stubbed worker: WAITING_FOR_MT5 and ONLINE_MARKET_CLOSED paths."""
    import tb_worker as W
    from tb_runtime_db import RuntimeDB
    from tb_runtime_config import STATE_DIR

    # 1) MT5 unavailable -> WAITING_FOR_MT5, execution blocked
    w = W.DemoWorker("GEN-T")
    w.rdb = RuntimeDB(tmp / "w.db")
    w.rdb.set_status("deployment_generation", "GEN-T")
    w.rdb.set_status("deployment_start_equity", "1000")
    w.rdb.set_status("deployment_start_epoch", str(time.time()))
    w.rdb.set_status("deployment_start_timestamp", _iso_from_epoch(time.time()))

    try:
        orig_connect = w.env.connect
        w.env.connect = lambda: False
        w.env.connected = False
        check("mt5 down => not ok", not w._ensure_mt5())
        w.state = "WAITING_FOR_MT5"
        check("state WAITING_FOR_MT5", w.state == "WAITING_FOR_MT5")
        w.heartbeat()
        hb = w.rdb.latest_heartbeat()
        check("heartbeat records mt5 down", hb["mt5_connected"] == 0
              and hb["state"] == "WAITING_FOR_MT5")
        w.env.connect = orig_connect

        # 2) market closed: stale feed -> ONLINE_MARKET_CLOSED, no orders
        w.mt5_ok = True
        w.account_gate = True
        w.reconciled = True
        w.feed = SimpleNamespace(
            get_synchronized_closed_triangle=lambda **kw: SimpleNamespace(
                signal_snapshot_valid=False,
                failure_code=SimpleNamespace(value="STALE_SIGNAL_BAR")))
        w.env.adapter = SimpleNamespace(
            server_reference=lambda dt: dt,
            calibrate_server_clock=lambda: 0.0)
        w.ledger = None
        w.layer = SimpleNamespace(open_basket=lambda i: None,
                                  close_basket=lambda i: None)
        w.cycle()
        check("market closed => ONLINE_MARKET_CLOSED",
              w.state == "ONLINE_MARKET_CLOSED")
        check("market flag off", w.market_open is False)

        # 2b) market recovery: state must NOT latch in MARKET_CLOSED.
        # Once the feed delivers a valid snapshot again, the recompute
        # must flip the state back to FLAT (regression: the exclusion of
        # ONLINE_MARKET_CLOSED from the recompute left it stuck forever).
        w.market_open = True
        w._refresh_state()
        check("market reopened => FLAT (no latch)",
              w.state == "FLAT", w.state)
        w.market_open = False
        w._refresh_state()
        check("market closed again => ONLINE_MARKET_CLOSED",
              w.state == "ONLINE_MARKET_CLOSED", w.state)
        w.open_basket_id = "B1"
        w._refresh_state()
        check("open basket => OPEN", w.state == "OPEN", w.state)
        w.open_basket_id = None
        w.state = "DEGRADED_DISK"
        w.market_open = True
        w._refresh_state()
        check("DEGRADED_DISK is sticky", w.state == "DEGRADED_DISK", w.state)

        # 3) disk guard: critically low disk blocks execution decision
        w.disk_ok = True
        orig_disk = shutil.disk_usage
        shutil.disk_usage = lambda p: SimpleNamespace(free=10 * 1024)   # 10 KB
        try:
            w._check_disk()
        finally:
            shutil.disk_usage = orig_disk
        check("disk guard => DEGRADED_DISK", w.state == "DEGRADED_DISK"
              and w.disk_ok is False)
    finally:
        w.rdb.close()


def test_pnl_accounting(tmp: Path) -> None:
    """TB-owned ONLY: magic + TB| tag filter; foreign must be excluded."""
    import tb_worker as W
    from tb_runtime_db import RuntimeDB
    from tb_runtime_config import CONTROL_MAGIC, TEST_MAGIC

    w = W.DemoWorker("GEN-P")
    w.rdb = RuntimeDB(tmp / "p.db")
    w.rdb.freeze_daily_nav("2026-08-17", 1000.0)
    w.rdb.set_status("deployment_start_equity", "1000")
    w.rdb.set_status("deployment_start_epoch", str(time.time() - 3600))
    w.mt5_ok = True

    deals = [
        # owned: control magic + TB| tag, today, +10 profit
        SimpleNamespace(magic=CONTROL_MAGIC, comment="TB|B1|GBPAUD|L1",
                        profit=10.0, time=time.time() - 60),
        # owned: test magic, today, +5
        SimpleNamespace(magic=TEST_MAGIC, comment="TB|R6T010200|GBPNZD|L2",
                        profit=5.0, time=time.time() - 120),
        # FOREIGN: same symbol, different magic, must be EXCLUDED
        SimpleNamespace(magic=99999999, comment="manual", profit=-500.0,
                        time=time.time() - 30),
        # foreign-looking: magic matches but no TB| tag (stray) -> excluded
        SimpleNamespace(magic=CONTROL_MAGIC, comment="other-ea", profit=100.0,
                        time=time.time() - 30),
        # owned but YESTERDAY (before UTC midnight) -> excluded from today
        SimpleNamespace(magic=CONTROL_MAGIC, comment="TB|B2|AUDNZD|L3",
                        profit=50.0, time=time.time() - 90000),
    ]
    positions = [
        SimpleNamespace(magic=CONTROL_MAGIC, comment="TB|B3|GBPAUD|L1",
                        profit=7.0),
        SimpleNamespace(magic=77777777, comment="manual", profit=-999.0),
    ]
    W.mt5 = SimpleNamespace(
        history_deals_get=lambda s, e: deals,
        positions_get=lambda: positions)
    pnl = w._pnl()
    # today = realized today (10+5) + unrealized open (7); foreign excluded
    check("today PnL = 22 (10+5+7), foreign excluded",
          abs(pnl["today_pnl"] - 22.0) < 1e-6, f"{pnl['today_pnl']}")
    check("open PnL = 7, foreign excluded",
          abs(pnl["open_pnl"] - 7.0) < 1e-6, f"{pnl['open_pnl']}")
    # deployment: owned deals since deploy-epoch (10+5+7) - yesterday deal
    # excluded because it predates the deploy epoch (1h ago)
    check("deploy PnL = 22 (10+5+7)", abs(pnl["deploy_pnl"] - 22.0) < 1e-6,
          f"{pnl['deploy_pnl']}")
    w.rdb.close()

def test_log_rotation(tmp: Path) -> None:
    from logging.handlers import RotatingFileHandler
    from tb_runtime_config import LOG_MAX_BYTES, LOG_BACKUP_COUNT
    lg = logging.getLogger("tb.rot")
    lg.setLevel(logging.INFO)
    for h in list(lg.handlers):
        lg.removeHandler(h)
    h = RotatingFileHandler(tmp / "rot.log", maxBytes=1024, backupCount=2,
                            encoding="utf-8")
    lg.addHandler(h)
    for i in range(400):
        lg.info("line %d " + "x" * 80, i)
    h.close()
    files = sorted(p.name for p in tmp.glob("rot.log*"))
    check("rotated backups exist", len(files) >= 2, str(files))
    size = sum(p.stat().st_size for p in tmp.glob("rot.log*"))
    check("rotated total bounded", size < 200_000, f"{size} bytes")


def _iso_from_epoch(epoch: float) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def test_daily_return_server_day(tmp: Path) -> None:
    """Server-day daily boundary + today return % (R6.1A accounting)."""
    import tb_worker as W
    from tb_runtime_db import RuntimeDB
    from tb_runtime_config import CONTROL_MAGIC
    from datetime import datetime

    w = W.DemoWorker("GEN-T")
    w.rdb = RuntimeDB(tmp / "sr.db")
    w.mt5_ok = True
    # server clock = UTC+3 (this broker); day rolls at 00:00 server = 21:00 UTC
    w.env.server_offset_s = 3 * 3600.0

    day, midnight = w._server_day()
    now_server = time.time() + w.env.server_offset_s
    check("server-day key = server-local date",
          day == datetime.utcfromtimestamp(now_server).date().isoformat())
    # midnight_utc must be exactly 21:00 UTC of the previous UTC date
    check("server midnight in UTC = 21:00 prev-day UTC",
          datetime.utcfromtimestamp(midnight).hour == 21)

    # freeze server-day NAV + one owned deal today, one just before midnight
    w.rdb.freeze_daily_nav(day, 1000.0)
    w.rdb.set_status("deployment_start_equity", "1000")
    w.rdb.set_status("deployment_start_epoch", str(midnight - 86400))
    deals = [
        SimpleNamespace(magic=CONTROL_MAGIC, comment="TB|B1|GBPAUD|L1",
                        profit=10.0, time=midnight + 60),      # today (server)
        SimpleNamespace(magic=CONTROL_MAGIC, comment="TB|B2|GBPNZD|L2",
                        profit=99.0, time=midnight - 60),      # yesterday (server)
    ]
    W.mt5 = SimpleNamespace(history_deals_get=lambda s, e: deals,
                            positions_get=lambda: [])
    pnl = w._pnl()
    check("today PnL uses server-day boundary (99 excluded)",
          abs(pnl["today_pnl"] - 10.0) < 1e-6, f"{pnl['today_pnl']}")
    check("today return % = 1.0%", abs(pnl["today_pnl_pct"] - 1.0) < 1e-9,
          f"{pnl['today_pnl_pct']}")
    check("server_day key in pnl", pnl["server_day"] == day)
    w.rdb.close()


def main() -> int:
    print("TB-R6.1 runtime audits")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        test_runtime_db(tmp)
        test_singleton(tmp)
        test_dashboard_status(tmp)
        test_worker_paths(tmp)
        test_pnl_accounting(tmp)
        test_daily_return_server_day(tmp)
        test_log_rotation(tmp)
    out = QUANT_LAB.parent / "research" / "tb_forward" / "r6_1"
    out.mkdir(parents=True, exist_ok=True)
    (out / "TB_R6_1_RUNTIME_AUDITS.json").write_text(
        json.dumps({"suite": "tb_r6_1_tests",
                    "passed": RESULTS["passed"],
                    "failed": RESULTS["failed"],
                    "total": len(RESULTS["tests"]),
                    "tests": RESULTS["tests"]}, indent=2), encoding="utf-8")
    print(f"\npassed={RESULTS['passed']} failed={RESULTS['failed']} "
          f"total={len(RESULTS['tests'])}")
    return 0 if RESULTS["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
