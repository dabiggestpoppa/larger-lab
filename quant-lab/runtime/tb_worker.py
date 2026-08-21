#!/usr/bin/env python3
"""
TB-R6.1 — PERSISTENT DEMO WORKER
================================

The strategy/data/execution/persistence process. It does NOT supervise
itself — the TB supervisor owns process lifecycle. It runs continuously:

    MT5 connect -> identity gate -> ledger integrity -> reconstruct ->
    broker read -> reconcile -> warm rolling window -> monitor loop

Monitor loop (every HEARTBEAT_INTERVAL_S):

    calibrated synchronized closed M5 triangle
      -> TB-FWD-V1 PRIMARY   (SHADOW ONLY; decisions logged, never executes)
      -> TB-FROZEN-CONTROL   (EXECUTABLE on approved DEMO, z > 2.5 / z0 exit)

    control OPEN signal -> frozen preflight gates -> write-ahead intent ->
    real 3-leg demo basket (R6-validated layer) -> OPEN_VERIFIED (broker truth)
    control CLOSE signal -> write-ahead exit -> atomic close -> flat verified

Heartbeat written durably every interval; daily/deployment NAV baselines
frozen once; TB PnL computed ONLY from owned (magic + TB| tag) positions
and deals. Foreign/manual positions are never touched.

SAFETY:
  * identity gate (server OxSecurities-Demo / trade_mode DEMO / ccy USD)
    must pass before ANY order; otherwise ONLINE but EXECUTION BLOCKED.
  * singleton PID lock: a second worker fails closed.
  * disk guard: critically low free disk blocks ledger writes / execution.
  * mt5.order_send wrapped by the R6 accounting guard (attribution counts).
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

QUANT_LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(QUANT_LAB))
sys.path.insert(0, str(QUANT_LAB / "engines"))
sys.path.insert(0, str(QUANT_LAB / "runtime"))
sys.path.insert(0, str(QUANT_LAB / "tb_live"))

from tb_runtime_config import (  # noqa: E402
    CANONICAL, BROKER_SYMBOLS, CANON_TO_BROKER, CONTROL_STRATEGY_ID,
    PRIMARY_STRATEGY_ID, CONTROL_MAGIC, HEARTBEAT_INTERVAL_S,
    MT5_RETRY_INTERVAL_S, WORKER_PID_FILE, WORKER_LOG, LOG_MAX_BYTES,
    LOG_BACKUP_COUNT, MIN_FREE_DISK_GB, BASKET_NOTIONAL_USD, STATE_DIR,
    CUR_TO_USD, DEPLOYMENT_PROFILE,
)
from tb_runtime_db import RuntimeDB  # noqa: E402
from tb_proc import PidLock  # noqa: E402

import MetaTrader5 as mt5  # noqa: E402

from tb_live.market_data import TBMarketDataConfig  # noqa: E402
from tb_live.snapshot import SynchronizedTriangleFeed  # noqa: E402
from tb_live.persistence import BasketLedger, EventType  # noqa: E402
from engines.tb_forward_config import PRIMARY_CONFIG, CONTROL_CONFIG  # noqa: E402
from engines.triangular_basis_live import (  # noqa: E402
    TriangularBasisLiveEngine, BasketDecision,
)
from engines.triangular_basis_engine import TriangularBar  # noqa: E402
from engines.tb_r6_demo_canary import (  # noqa: E402
    DemoEnvironment, quote_health, wait_for_quote_health, broker_truth,
    _new_layer, _ledger, _log_event, _install_order_send_accounting,
    _attribution, ORDER_SEND_COUNTS, TEST_MAGIC,
)
from mt5.triangular_execution_layer import BasketState  # noqa: E402
from tb_live.full_engine import translate_intent  # noqa: E402

log = logging.getLogger("tb.worker")


def _setup_logging() -> None:
    h = RotatingFileHandler(WORKER_LOG, maxBytes=LOG_MAX_BYTES,
                            backupCount=LOG_BACKUP_COUNT, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    h.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(h)
    # also console (supervisor captures subprocess output)
    c = logging.StreamHandler()
    c.setFormatter(fmt)
    root.addHandler(c)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DemoWorker:
    def __init__(self, generation: str):
        self.generation = generation
        self.rdb = RuntimeDB()
        self.env = DemoEnvironment()
        self.feed: SynchronizedTriangleFeed | None = None
        self.control = TriangularBasisLiveEngine(model_config=CONTROL_CONFIG)
        self.primary = TriangularBasisLiveEngine(model_config=PRIMARY_CONFIG)
        self.layer = None
        self.ledger: BasketLedger | None = None

        self.mt5_ok = False
        self.account_gate = False
        self.reconciled = False
        self.warmed = False
        self.market_open = False
        self.disk_ok = True

        self.open_basket_id: str | None = None
        self.last_bar_key = ""
        self.last_signal_time = ""
        self.last_error = ""
        self.state = "STARTING"

        self.bars_processed = 0
        self.cycles = 0
        self.control_open_signals = 0
        self.control_baskets_completed = 0
        self.primary_open_signals = 0
        self.foreign_positions_seen = 0
        self.singleton_ok = False

    # ── connection / reconciliation ─────────────────────────────────────
    def _ensure_mt5(self) -> bool:
        if self.env.connected:
            try:
                ti = mt5.terminal_info()
                if ti is None:  # terminal went away
                    self.env.connected = False
            except Exception:
                self.env.connected = False
        if not self.env.connected:
            self.env.connect()
        self.mt5_ok = self.env.connected
        if self.mt5_ok:
            self.identity = self.env.identity_check()
            self.account_gate = bool(self.identity.get("identity_gate_pass"))
            if not self.account_gate:
                self.last_error = (self.identity.get("fail_reason")
                                   or "account identity gate failed")
                log.warning("ACCOUNT_GATE_FAILED: %s", self.last_error)
        return self.mt5_ok

    def _post_connect_setup(self) -> None:
        """Run once per (re)connection: ledger integrity -> reconstruct ->
        broker read -> reconcile -> warm the rolling window."""
        self.env.symbol_contracts()
        self.ledger = _ledger(str(STATE_DIR / "tb_control.db"))
        issues = self.ledger.integrity_check()
        if issues:
            self.state = "BLOCKED_LEDGER"
            self.last_error = f"ledger integrity issues: {issues[:3]}"
            self.rdb.record_error("worker", self.last_error)
            log.error("LEDGER INTEGRITY FAILED: %s", issues[:5])
            return
        states = self.ledger.reconstruct_all()
        truth = broker_truth(self.env, CONTROL_MAGIC)
        owned_pos = truth["positions"]
        ledger_open = {b: s for b, s in states.items()
                       if s.get("strategy_id") == CONTROL_STRATEGY_ID
                       and s.get("state") in ("OPEN_VERIFIED", "CLOSE_REQUESTED",
                                              "CLOSE_SUBMITTING", "PARTIALLY_CLOSED",
                                              "BROKEN_HEDGE", "FLATTENING")}
        if owned_pos and not ledger_open:
            # positions exist but no durable intent: unknown/ambiguous TB basket
            self.state = "BLOCKED_RECONCILIATION"
            self.last_error = ("broker has TB-magic positions with no matching "
                               "ledger open basket; blocked (never flatten "
                               "without ownership evidence)")
            self.rdb.record_error("worker", self.last_error)
            log.error("BLOCKED_RECONCILIATION: %d owned positions, no ledger intent",
                      len(owned_pos))
        elif owned_pos and len(ledger_open) == 1:
            bid = next(iter(ledger_open))
            self.open_basket_id = bid
            self.state = "OPEN_VERIFIED"
            log.info("RECONCILE: adopted open basket %s (%d positions)",
                     bid, len(owned_pos))
            try:
                self.layer.reconcile_open_baskets()   # rebuild registry from comments
            except Exception as e:  # pragma: no cover
                log.warning("reconcile_open_baskets: %s", e)
        elif not owned_pos and ledger_open:
            for bid, st in ledger_open.items():
                log.info("RECONCILE: ledger %s open but broker flat -> closed", bid)
        else:
            self.state = "FLAT"
            log.info("RECONCILE: flat / clean")
        self.reconciled = self.state not in ("BLOCKED_LEDGER",
                                             "BLOCKED_RECONCILIATION")
        # engine + feed
        self.feed = SynchronizedTriangleFeed(
            adapter=self.env.adapter, config=TBMarketDataConfig(bar_seconds=300))
        for broker in BROKER_SYMBOLS:
            try:
                self.env.adapter.select_symbol(broker)
            except Exception:
                pass
        self.layer = _new_layer(self.env, CONTROL_MAGIC, CONTROL_STRATEGY_ID)
        self._warm_engines()

    def _warm_engines(self) -> None:
        """Seed the frozen rolling window from REAL terminal history so z is
        computable on the first live bar (mechanical; canonical math intact)."""
        try:
            per = {}
            for canon in CANONICAL:
                bars = self.env.adapter.get_recent_bars(
                    CANON_TO_BROKER[canon], "M5", 240) or []
                per[canon] = {b.bar_open_time: b for b in bars if b.is_closed}
            common = sorted(set.intersection(*(set(d) for d in per.values())))
            if not common:
                log.warning("WARM: no common historical bars (fresh account?)")
                return
            tri = []
            for t in common[-220:]:
                g, n, a = per["GBPAUD"][t], per["GBPNZD"][t], per["AUDNZD"][t]
                tri.append(TriangularBar(
                    timestamp=t, gbp_aud=g.close, gbp_nzd=n.close, aud_nzd=a.close,
                    gbp_aud_high=g.high, gbp_aud_low=g.low,
                    gbp_nzd_high=n.high, gbp_nzd_low=n.low,
                    aud_nzd_high=a.high, aud_nzd_low=a.low))
            self.control.load_historical_bars(tri)
            self.primary.load_historical_bars(tri)
            self.warmed = True
            log.info("WARM: %d synchronized historical M5 bars loaded", len(tri))
        except Exception as e:
            log.warning("WARM failed (engine will accumulate live): %s", e)

    # ── PnL accounting (owned only) ─────────────────────────────────────
    def _owned_deals(self, since_epoch: float) -> list:
        if not self.mt5_ok:
            return []
        try:
            end = datetime.utcnow() + timedelta(seconds=3600)
            start = datetime.utcfromtimestamp(since_epoch)
            deals = mt5.history_deals_get(start, end) or []
            out = []
            for d in deals:
                if d.magic in (CONTROL_MAGIC, TEST_MAGIC) \
                        and "TB|" in (d.comment or "") \
                        and float(d.time or 0) >= since_epoch:
                    out.append(d)
            return out
        except Exception:
            return []

    def _owned_positions(self) -> list:
        if not self.mt5_ok:
            return []
        try:
            return [p for p in (mt5.positions_get() or [])
                    if p.magic in (CONTROL_MAGIC, TEST_MAGIC)
                    and "TB|" in (p.comment or "")]
        except Exception:
            return []

    def _server_day(self) -> tuple:
        """Broker/server account day (execution accounting boundary).

        Server time = calibrated broker clock (this broker: UTC+3). The day
        rolls at 00:00 SERVER time; the epoch of that midnight in UTC is
        returned so deal windows and the daily NAV key are consistent.
        Falls back to UTC when calibration is unavailable (fail-safe).
        """
        off = float(self.env.server_offset_s or 0.0)
        server_now = time.time() + off
        day = datetime.utcfromtimestamp(server_now).date().isoformat()
        midnight_utc = int(server_now // 86400) * 86400 - off
        return day, midnight_utc

    def _pnl(self) -> dict:
        day, day_start = self._server_day()
        dep_epoch = float(self.rdb.get_status("deployment_start_epoch", "0") or 0)
        day_deals = [d for d in self._owned_deals(day_start)
                     if d.time >= day_start]
        dep_deals = [d for d in self._owned_deals(dep_epoch or day_start)]
        open_pos = self._owned_positions()
        today_realized = sum(float(d.profit) for d in day_deals)
        open_pnl = sum(float(p.profit) for p in open_pos)
        dep_realized = sum(float(d.profit) for d in dep_deals)
        today_pnl = today_realized + open_pnl
        deploy_pnl = dep_realized + open_pnl
        daily_eq = self.rdb.daily_nav(day) or 0.0
        dep_eq = float(self.rdb.get_status("deployment_start_equity", "0") or 0)
        return {
            "server_day": day,
            "today_pnl": today_pnl,
            "today_pnl_pct": (today_pnl / daily_eq * 100.0) if daily_eq else 0.0,
            "open_pnl": open_pnl,
            "deploy_pnl": deploy_pnl,
            "deploy_pnl_pct": (deploy_pnl / dep_eq * 100.0) if dep_eq else 0.0,
        }

    # ── NAV baselines ───────────────────────────────────────────────────
    def _update_nav(self) -> None:
        ai = mt5.account_info()
        if ai is None:
            return
        equity = float(ai.equity)
        # daily boundary = broker/server account day (calibrated server clock)
        if self.env.server_offset_s is None:
            try:
                self.env.calibrate()
            except Exception:
                pass
        day, _ = self._server_day()
        if self.rdb.daily_nav(day) is None:
            self.rdb.freeze_daily_nav(day, equity)
            log.info("DAILY NAV frozen (server day %s): equity=%.2f", day, equity)
        if not self.rdb.get_status("deployment_generation"):
            self.rdb.set_status("deployment_generation", self.generation)
            self.rdb.set_status("deployment_start_timestamp", _now_iso())
            self.rdb.set_status("deployment_start_epoch", str(time.time()))
            self.rdb.set_status("deployment_start_equity", str(equity))
            self.rdb.freeze_deployment_nav(self.generation, equity,
                                           note="TB-R6.1 local_windows deploy")
            log.info("DEPLOYMENT NAV frozen: %s equity=%.2f", self.generation, equity)

    # ── strategy cycle ──────────────────────────────────────────────────
    def cycle(self) -> None:
        self.env.calibrate()
        ref = self.env.adapter.server_reference(datetime.now(timezone.utc))
        snap = self.feed.get_synchronized_closed_triangle(reference_time=ref)
        if not snap.signal_snapshot_valid:
            code = snap.failure_code.value if snap.failure_code else "NO_SNAPSHOT"
            if code == "NO_NEW_SIGNAL_BAR":
                return                       # same bar; nothing new
            if code in ("STALE_SIGNAL_BAR", "NO_COMMON_CLOSED_BAR",
                        "MISSING_LEG"):
                self.market_open = False
                self.state = "ONLINE_MARKET_CLOSED"
            else:
                self.state = "DEGRADED"
            return
        self.market_open = True
        self.bars_processed += 1
        key = str(snap.signal_bar_close_time)
        self.last_bar_key = key

        # PRIMARY — SHADOW ONLY (never reaches execution)
        p = self.primary.process_snapshot(snap)
        if p.decision == BasketDecision.OPEN_BASKET:
            self.primary_open_signals += 1
            self.last_signal_time = _now_iso()
            _log_event(self.ledger, EventType.SIGNAL_OBSERVED, "",
                       PRIMARY_STRATEGY_ID, f"R6.1|PRI|{key}",
                       payload={"z": float(p.zscore),
                                "decision": "OPEN_BASKET",
                                "note": "PRIMARY SHADOW ONLY"})
            log.info("PRIMARY signal (shadow): z=%.4f", p.zscore)

        # CONTROL — executable on approved DEMO
        c = self.control.process_snapshot(snap)
        if c.decision == BasketDecision.OPEN_BASKET:
            self.control_open_signals += 1
            self.last_signal_time = _now_iso()
            _log_event(self.ledger, EventType.SIGNAL_OBSERVED, "",
                       CONTROL_STRATEGY_ID, f"R6.1|CTL|{key}",
                       payload={"z": float(c.zscore), "decision": "OPEN_BASKET"})
            log.info("CONTROL signal: z=%.4f", c.zscore)
            if self.open_basket_id is None:
                self._try_open_control(c, key)
            else:
                _log_event(self.ledger, EventType.ENGINE_BLOCKED,
                           self.open_basket_id, CONTROL_STRATEGY_ID,
                           f"BLK|{self.open_basket_id}",
                           payload={"reason": "basket already open"})
        if c.decision == BasketDecision.CLOSE_BASKET and self.open_basket_id:
            self._close_control(key)

    def _try_open_control(self, intent, key: str) -> None:
        if not self.account_gate:
            self.last_error = "control signal but account gate failed; no order"
            self.rdb.record_error("worker", self.last_error)
            return
        if not self.disk_ok:
            self.last_error = "control signal but disk guard failed; no order"
            return
        qh = wait_for_quote_health(self.env, timeout_s=25.0)
        if not qh["ok"]:
            _log_event(self.ledger, EventType.SIGNAL_REJECTED, intent.basket_id,
                       CONTROL_STRATEGY_ID, f"REJ|{intent.basket_id}",
                       payload={"reason": qh["reason"]})
            log.warning("preflight rejected: %s", qh["reason"])
            return
        _log_event(self.ledger, EventType.BASKET_INTENT_CREATED,
                   intent.basket_id, CONTROL_STRATEGY_ID,
                   f"INTENT|{intent.basket_id}",
                   payload={"z": float(intent.zscore)},
                   prior_state="SIGNAL_DETECTED", new_state="INTENT_CREATED")
        _attribution("control")
        res = self.layer.open_basket(translate_intent(
            intent, BASKET_NOTIONAL_USD))
        _attribution("unknown")
        if res.state == BasketState.OPEN:
            self.open_basket_id = intent.basket_id
            truth = broker_truth(self.env, CONTROL_MAGIC)
            _log_event(self.ledger, EventType.BASKET_OPEN_VERIFIED,
                       self.open_basket_id, CONTROL_STRATEGY_ID,
                       f"OPEN|{self.open_basket_id}",
                       payload={"positions": truth["positions"]},
                       prior_state="ENTRY_SUBMITTING", new_state="OPEN_VERIFIED")
            # R6.4: confirm open back to the engine so INTENT -> OPEN
            # (enables engine-side close logic and prevents ghost INTENT
            # from blocking future entries)
            self.control.on_basket_open_confirmed(intent.basket_id)
            log.info("CONTROL basket OPEN: %s (3 legs verified)",
                     self.open_basket_id)
        else:
            _log_event(self.ledger, EventType.SIGNAL_REJECTED,
                       intent.basket_id, CONTROL_STRATEGY_ID,
                       f"REJ|{intent.basket_id}",
                       payload={"reason": res.error_message})
            # R6.4: revert ghost INTENT so future entries are not blocked
            self.control.on_basket_open_failed(intent.basket_id)
            log.warning("control open failed: %s", res.error_message)

    def _close_control(self, key: str) -> None:
        bid = self.open_basket_id
        _log_event(self.ledger, EventType.EXIT_SIGNAL_OBSERVED, bid,
                   CONTROL_STRATEGY_ID, f"EXITSIG|{bid}",
                   prior_state="OPEN_VERIFIED", new_state="CLOSE_REQUESTED")
        _log_event(self.ledger, EventType.EXIT_ATTEMPT_STARTED, bid,
                   CONTROL_STRATEGY_ID, f"CLOSE|{bid}",
                   prior_state="CLOSE_REQUESTED", new_state="CLOSE_SUBMITTING")
        _attribution("control")
        res = self.layer.close_basket(bid)
        _attribution("unknown")
        truth_after = broker_truth(self.env, CONTROL_MAGIC)
        flat = len(truth_after["positions"]) == 0
        st = "CLOSED_VERIFIED" if flat else "RECONCILIATION_REQUIRED"
        _log_event(self.ledger, EventType.BASKET_CLOSED_VERIFIED, bid,
                   CONTROL_STRATEGY_ID, f"CLOSEDV|{bid}",
                   payload={"flat": flat},
                   prior_state="CLOSE_SUBMITTING", new_state=st)
        if flat:
            # R6.4: confirm close back to the engine so it removes the
            # basket from _active_baskets (enables future entries)
            self.control.on_basket_close_confirmed(bid)
            self.control_baskets_completed += 1
            self.open_basket_id = None
            log.info("CONTROL basket CLOSED + flat verified: %s", bid)
        else:
            self.state = "RECONCILIATION_REQUIRED"
            self.last_error = f"close of {bid} not verified flat"
            self.rdb.record_error("worker", self.last_error)

    # ── state refresh ──────────────────────────────────────────────────
    def _refresh_state(self) -> None:
        """Recompute the operational state each cycle.

        The market can recover, so ONLINE_MARKET_CLOSED must NOT latch
        forever (it used to be excluded here, leaving the state stuck
        after a transient stale feed). DEGRADED_DISK is intentionally
        sticky until the disk condition clears elsewhere.
        """
        if self.open_basket_id:
            self.state = "OPEN"
        elif self.state != "DEGRADED_DISK":
            self.state = "FLAT" if self.market_open else "ONLINE_MARKET_CLOSED"

    # ── heartbeat / disk ────────────────────────────────────────────────
    def _check_disk(self) -> None:
        try:
            free = shutil.disk_usage(STATE_DIR).free / (1024 ** 3)
            if free < MIN_FREE_DISK_GB:
                self.disk_ok = False
                self.last_error = f"disk critically low ({free:.2f} GB free)"
                self.state = "DEGRADED_DISK"
                self.rdb.record_error("worker", self.last_error)
        except Exception:
            pass

    def heartbeat(self) -> None:
        self._check_disk()
        pnl = self._pnl()
        ai = mt5.account_info() if self.mt5_ok else None
        try:
            free_gb = shutil.disk_usage(STATE_DIR).free / (1024 ** 3)
        except Exception:
            free_gb = 0.0
        self.rdb.record_heartbeat({
            "ts": _now_iso(), "pid": os.getpid(),
            "generation": self.generation, "state": self.state,
            "mt5_connected": self.mt5_ok, "account_gate": self.account_gate,
            "market_open": self.market_open,
            "last_closed_bar": self.last_bar_key,
            "last_signal_time": self.last_signal_time,
            "open_basket_id": self.open_basket_id or "",
            "today_pnl": pnl["today_pnl"],
            "today_pnl_pct": pnl["today_pnl_pct"],
            "open_pnl": pnl["open_pnl"],
            "deploy_pnl": pnl["deploy_pnl"],
            "deploy_pnl_pct": pnl["deploy_pnl_pct"],
            "account_equity": float(ai.equity) if ai else 0.0,
            "disk_free_gb": free_gb, "last_error": self.last_error,
        })

    # ── main loop ───────────────────────────────────────────────────────
    def run(self) -> int:
        _install_order_send_accounting()
        self.rdb.set_status("worker_start_ts", _now_iso())
        log.info("worker start generation=%s profile=%s", self.generation,
                 DEPLOYMENT_PROFILE)
        try:
            while True:
                if not self._ensure_mt5():
                    self.state = "WAITING_FOR_MT5"
                    self.last_error = "MT5 unavailable; bounded retry"
                    log.info("WAITING_FOR_MT5 (retry %ds)", MT5_RETRY_INTERVAL_S)
                    self.heartbeat()
                    time.sleep(MT5_RETRY_INTERVAL_S)
                    continue
                if not self.reconciled:
                    self._post_connect_setup()
                    if not self.reconciled:      # BLOCKED_* -> stay online, no trades
                        self.heartbeat()
                        time.sleep(HEARTBEAT_INTERVAL_S)
                        continue
                self._update_nav()
                self.cycles += 1
                self.cycle()
                self._refresh_state()
                self.last_error = ""
                self.heartbeat()
                time.sleep(HEARTBEAT_INTERVAL_S)
        except KeyboardInterrupt:
            log.info("worker interrupted; exiting")
        except Exception as e:  # pragma: no cover
            log.exception("worker fatal")
            self.last_error = f"fatal: {e}"[:300]
            self.rdb.record_error("worker", self.last_error)
        finally:
            if self.ledger:
                self.ledger.close()
            self.rdb.close()
        log.info("worker exit: primary_open=%d control_open=%d completed=%d "
                 "bars=%d order_send=%s",
                 self.primary_open_signals, self.control_open_signals,
                 self.control_baskets_completed, self.bars_processed,
                 dict(ORDER_SEND_COUNTS))
        return 0


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="TB persistent demo worker")
    ap.add_argument("--generation", default="")
    args = ap.parse_args()

    _setup_logging()
    lock = PidLock(WORKER_PID_FILE, "worker")
    got = lock.try_acquire()
    if not got["ok"]:
        log.error("SINGLETON BLOCKED: %s", got["reason"])
        print(f"SINGLETON_BLOCKED: {got['reason']}", flush=True)
        return 2
    generation = args.generation or datetime.now(
        timezone.utc).strftime("GEN-%Y%m%dT%H%M%S")
    try:
        return DemoWorker(generation).run()
    finally:
        lock.release()


if __name__ == "__main__":
    sys.exit(main())
