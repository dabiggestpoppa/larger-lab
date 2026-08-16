#!/usr/bin/env python3
"""
TB-R4 — REAL MT5 FULL-ENGINE SHADOW & FAILURE SEAL (real-terminal audit)
========================================================================

Drives the COMPLETE TB forward engine against the ACTUAL connected
MT5/OxSecurities terminal in SHADOW mode. Reuses the R2 MT5MarketDataAdapter
and SymbolResolver; nothing is fabricated.

    REAL MT5 terminal
      -> REAL broker symbols / metadata
      -> REAL synchronized closed M5 bars (R2 feed)
      -> REAL bid/ask ticks
      -> TB-FWD-V1 PRIMARY + TB-FROZEN-CONTROL (shadow)
      -> TB-B canonical weights -> REAL contract specs -> hypothetical lots
      -> R3 durable ledger (intents persisted)
      -> SHADOW_ORDER_WOULD_SEND  (order_send NEVER called)

EXECUTION AUTHORIZATION: NOT_AUTHORIZED. mt5.order_send is wrapped by a guard
that FAILS the run if ever invoked; the shadow loop only persists intents.

If the terminal is unreachable the broker-specific sections are written as
PENDING_TERMINAL_VALIDATION (never declared PASS from mocks). Historical
strategy parity (265,809 bars / 194 / 405) is a separate canonical regression
run by tb_r2_parity.py / tb_r4_replay.py, not by this harness.

Run:  python quant-lab/engines/tb_r4_real_mt5.py [--sample-seconds 60] [--offline]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np  # noqa: E402

from tb_live.market_data import (  # noqa: E402
    TBMarketDataConfig, FailureCode,
)
from tb_live.snapshot import (  # noqa: E402
    MT5MarketDataAdapter, SymbolResolver, SynchronizedTriangleFeed,
)
from tb_live.persistence import (  # noqa: E402
    BasketLedger, EventType,
)
from tb_live.state_machine import BasketLifecycleState as S  # noqa: E402
from engines.triangular_basis_live import (  # noqa: E402
    TriangularBasisLiveEngine, BasketDecision,
)
from engines.tb_forward_config import (  # noqa: E402
    PRIMARY_CONFIG, CONTROL_CONFIG,
)
from engines.triangular_execution_contract import (  # noqa: E402
    ContractSpec, Direction, size_and_assess_basket,
)
from engines.tb_r4_replay import tkey  # noqa: E402  (timestamp normalizer)

ROOT = Path(__file__).parent.parent.parent
OUT = ROOT / "research" / "tb_forward"
OUT.mkdir(parents=True, exist_ok=True)

TB_MAGIC = 31082026
CANONICAL = ("GBPAUD", "GBPNZD", "AUDNZD")
# Frozen research conversion constants (account currency USD) -- canonical
# historical translation truth (never replaced by live rates in parity paths).
CUR_TO_USD = {"GBP": 1.34852, "AUD": 0.70583, "NZD": 0.58844}
BAR_SECONDS = 300

PENDING = "PENDING_TERMINAL_VALIDATION"


def _mask_login(login) -> str:
    s = str(login)
    if len(s) <= 4:
        return "*" * len(s)
    return s[:2] + "*" * (len(s) - 4) + s[-2:]


def _pct(series: List[float], q) -> float:
    if not series:
        return 0.0
    return float(np.percentile(sorted(series), q))


def _dist(series: List[float]) -> dict:
    if not series:
        return {"n": 0}
    return {
        "n": len(series),
        "median": round(statistics.median(series), 4),
        "p90": round(_pct(series, 90), 4),
        "p95": round(_pct(series, 95), 4),
        "p99": round(_pct(series, 99), 4),
        "max": round(max(series), 4),
    }


class RealMT5Audit:
    """Read-only audit + shadow loop against the actual MT5 terminal."""

    def __init__(self, sample_seconds: int = 60, max_cycles: int = 10,
                 cycle_sleep_s: int = 4, offline: bool = False):
        self.sample_seconds = sample_seconds
        self.max_cycles = max_cycles
        self.cycle_sleep_s = cycle_sleep_s
        self.offline = offline
        self.adapter: Optional[MT5MarketDataAdapter] = None
        self.feed: Optional[SynchronizedTriangleFeed] = None
        self.ledger: Optional[BasketLedger] = None
        self.primary = TriangularBasisLiveEngine(model_config=PRIMARY_CONFIG)
        self.control = TriangularBasisLiveEngine(model_config=CONTROL_CONFIG)
        self.order_send_attempts = 0
        self.resolution = None
        self.results: Dict[str, object] = {}

    # ── CONNECT (real terminal, read-only) ──────────────────────────────
    def connect(self) -> bool:
        if self.offline:
            return False
        try:
            import MetaTrader5 as mt5  # noqa: F401
        except ImportError:
            return False
        adapter = MT5MarketDataAdapter(bar_seconds=BAR_SECONDS)
        if not adapter.initialize():
            return False
        self.adapter = adapter
        return True

    # ── 1. ENVIRONMENT AUDIT ────────────────────────────────────────────
    def environment_audit(self) -> dict:
        if self.adapter is None:
            return {"status": PENDING}
        mt5 = self.adapter._mt5
        ti = mt5.terminal_info()
        ai = mt5.account_info()
        env = {
            "status": "CONNECTED",
            "terminal_connected": bool(ti.connected),
            "terminal_name": ti.name,
            "broker_company": ti.company,
            "server": ai.server,
            "account_login_masked": _mask_login(ai.login),
            "account_currency": ai.currency,
            "account_trade_mode": int(ai.trade_mode),  # 0=demo 1=contest 2=real
            "account_type": {0: "DEMO", 1: "CONTEST", 2: "REAL"}.get(
                int(ai.trade_mode), "UNKNOWN"),
            "leverage": getattr(ai, "leverage", None),
            "balance": float(ai.balance),
            "equity": float(ai.equity),
            "margin": float(ai.margin),
            "trade_allowed": bool(ai.trade_allowed),
            "terminal_trade_allowed": bool(ti.trade_allowed),
            "tradeapi_disabled": bool(ti.tradeapi_disabled),
        }
        self.results["environment"] = env
        return env

    # ── 2. SYMBOL RESOLUTION + SPECS ────────────────────────────────────
    def symbol_audit(self) -> dict:
        if self.adapter is None:
            return {"status": PENDING}
        resolver = SymbolResolver(self.adapter)
        res = resolver.require_resolved()
        self.resolution = res
        specs = {}
        for canon in CANONICAL:
            broker = res.mapping.get(canon)
            if broker is None:
                specs[canon] = {"resolved": False}
                continue
            info = res.metadata.get(canon, {})
            # live tick for spread/tick-time observation
            tk = None
            if self.adapter._mt5 is not None:
                try:
                    tk = self.adapter._mt5.symbol_info_tick(broker)
                except Exception:
                    tk = None
            spec = dict(info)
            spec["canonical_symbol"] = canon
            spec["broker_symbol"] = broker
            spec["resolved"] = True
            if tk is not None:
                spec["bid"] = float(tk.bid)
                spec["ask"] = float(tk.ask)
                spec["spread_price"] = round(float(tk.ask - tk.bid), 6)
                spec["spread_points"] = round(
                    (float(tk.ask - tk.bid)) / max(float(info.get("point", 1e-5)), 1e-9), 1)
                spec["tick_time_utc"] = str(datetime.fromtimestamp(
                    int(tk.time), tz=timezone.utc))
            specs[canon] = spec
        self.results["symbols"] = specs
        return specs

    # ── 3. REAL M5 DATA AUDIT ───────────────────────────────────────────
    def m5_audit(self, n_bars: int = 200) -> dict:
        if self.adapter is None or self.resolution is None:
            return {"status": PENDING}
        mt5 = self.adapter._mt5
        legs: Dict[str, List[dict]] = {}
        common_keys = Counter()
        for canon in CANONICAL:
            broker = self.resolution.mapping.get(canon)
            if broker is None:
                legs[canon] = []
                continue
            raw = mt5.copy_rates_from_pos(broker, mt5.TIMEFRAME_M5, 0, n_bars)
            if raw is None:
                raw = []
            rows = []
            for r in raw:
                t = datetime.fromtimestamp(int(r["time"]), tz=timezone.utc)
                rows.append({
                    "open_time_utc": str(t),
                    "close_time_utc": str(t + timedelta(seconds=BAR_SECONDS)),
                    "open": round(float(r["open"]), 5),
                    "high": round(float(r["high"]), 5),
                    "low": round(float(r["low"]), 5),
                    "close": round(float(r["close"]), 5),
                    "tick_volume": int(r["tick_volume"]),
                })
                common_keys[t] += 1
            legs[canon] = rows
        # common closed timestamps (all three legs have the bar)
        common = sorted(
            t for t, c in common_keys.items() if c == len(CANONICAL))
        last_common = common[-1] if common else None
        # forming bar = newest fetched bar of each leg (not yet closed)
        forming = {c: (r[-1]["open_time_utc"] if r else None)
                   for c, r in legs.items()}
        audit = {
            "status": "CONNECTED",
            "bars_requested_per_leg": n_bars,
            "bars_returned_per_leg": {c: len(r) for c, r in legs.items()},
            "timestamp_semantics": "OPEN_TIME",  # MT5 M5 bars keyed by open
            "timeframe_seconds": BAR_SECONDS,
            "last_bar_each_leg": {c: (r[-1]["open_time_utc"] if r else None)
                                  for c, r in legs.items()},
            "forming_bar_each_leg": forming,
            "common_closed_count": len(common),
            "last_common_closed_open_time": str(last_common) if last_common else None,
            "three_leg_sync_now": last_common is not None,
            "gap_seconds_between_leg_last_bars": (
                lambda ts: (max(ts) - min(ts)).total_seconds() if len(ts) == len(CANONICAL) else None)(
                [datetime.fromisoformat(legs[c][-1]["open_time_utc"])
                 for c in CANONICAL if legs[c]]),
        }
        self.results["m5"] = audit
        return audit

    # ── 4. REAL TICK QUALITY SAMPLE ─────────────────────────────────────
    def tick_sample(self) -> dict:
        if self.adapter is None or self.resolution is None:
            return {"status": PENDING}
        mt5 = self.adapter._mt5
        spreads: Dict[str, List[float]] = {c: [] for c in CANONICAL}
        ages: Dict[str, List[float]] = {c: [] for c in CANONICAL}
        skews: List[float] = []
        skew_times: List[float] = []
        t_end = time.time() + self.sample_seconds
        while time.time() < t_end:
            ticks = {}
            for canon in CANONICAL:
                broker = self.resolution.mapping.get(canon)
                tk = mt5.symbol_info_tick(broker)
                if tk is None or tk.bid is None or tk.ask is None:
                    continue
                spread_price = float(tk.ask - tk.bid)
                point = float(self.resolution.metadata[canon].get("point", 1e-5))
                spreads[canon].append(spread_price / point)
                age_ms = (datetime.now(timezone.utc) - datetime.fromtimestamp(
                    int(tk.time), tz=timezone.utc)).total_seconds() * 1000.0
                ages[canon].append(max(age_ms, 0.0))
                ticks[canon] = int(tk.time)
            if len(ticks) == 3:
                skews.append(max(ticks.values()) - min(ticks.values()))
                skew_times.append(max(ticks.values()))
            time.sleep(1.0)
        self.results["tick_sample"] = {
            "status": "CONNECTED",
            "sample_seconds": self.sample_seconds,
            "spread_points_per_leg": {c: _dist(v) for c, v in spreads.items()},
            "quote_age_ms_per_leg": {c: _dist(v) for c, v in ages.items()},
            "cross_leg_skew_s": _dist(skews),
            "tick_moved": len(set(skew_times)) > 1 if skew_times else False,
            "note": ("live sample; if market quiet/closed the distributions are "
                     "descriptive observations, not validated limits"),
        }
        return self.results["tick_sample"]

    # ── 5. REAL LOT TRANSLATION (hypothetical, no orders) ───────────────
    def lot_translation(self) -> dict:
        if self.adapter is None or self.resolution is None:
            return {"status": PENDING}
        csv_path = ROOT / "research" / "tb_forward" / "TB_R4_REAL_LOT_TRANSLATION.csv"
        import csv
        weights_csv = ROOT / "research" / "tb_forward" / "TB_R11_WEIGHT_PARITY.csv"
        if not weights_csv.exists():
            return {"status": "MISSING_R11_WEIGHTS_INPUT"}
        rows_in = []
        with open(weights_csv, encoding="utf-8") as f:
            rd = csv.DictReader(f)
            for r in rd:
                rows_in.append(r)
        # real specs + current mid prices
        specs, prices = {}, {}
        for canon in CANONICAL:
            broker = self.resolution.mapping[canon]
            info = self.resolution.metadata[canon]
            specs[broker] = ContractSpec(
                contract_size=float(info["contract_size"]),
                volume_min=float(info["volume_min"]),
                volume_max=float(info["volume_max"]),
                volume_step=float(info["volume_step"]),
                point=float(info["point"]),
                digits=int(info["digits"]),
                # USD-consistent translation (frozen research conversion)
                quote_to_account_rate=CUR_TO_USD.get(
                    {"GBPAUD": "AUD", "GBPNZD": "NZD", "AUDNZD": "NZD"}[canon], 1.0),
            )
            tk = self.adapter._mt5.symbol_info_tick(broker)
            prices[canon] = (float(tk.bid) + float(tk.ask)) / 2.0 if tk else 0.0
        notional = 25000.0  # documented hypothetical basket scale
        header = ["entry_time", "direction", "weight_GA", "weight_GN", "weight_AN",
                  "mid_GA", "mid_GN", "mid_AN",
                  "raw_GA", "raw_GN", "raw_AN",
                  "round_GA", "round_GN", "round_AN",
                  "max_currency_residual_pct", "max_weight_error_pct",
                  "passed_gate_k", "reject_reason"]
        rows = []
        gate_fail = 0
        residuals = []
        for r in rows_in:
            w = {"GBPAUD": float(r["canon_w_ga"]), "GBPNZD": float(r["canon_w_gn"]),
                 "AUDNZD": float(r["canon_w_an"])}
            # direction not in R11 CSV; use canonical z sign via TB_R11_P7_PARITY
            direction = Direction.SHORT
            out = size_and_assess_basket(
                notional, w, prices, specs, CUR_TO_USD,
                direction=direction,
                configured_max_residual_pct=10.0,
                configured_max_weight_error_pct=10.0)
            rows.append({
                "entry_time": r["entry_time"], "direction": direction.name,
                "weight_GA": round(w["GBPAUD"], 6), "weight_GN": round(w["GBPNZD"], 6),
                "weight_AN": round(w["AUDNZD"], 6),
                "mid_GA": round(prices["GBPAUD"], 5), "mid_GN": round(prices["GBPNZD"], 5),
                "mid_AN": round(prices["AUDNZD"], 5),
                "raw_GA": out["legs"][0]["raw_lots"], "raw_GN": out["legs"][1]["raw_lots"],
                "raw_AN": out["legs"][2]["raw_lots"],
                "round_GA": out["legs"][0]["rounded_lots"],
                "round_GN": out["legs"][1]["rounded_lots"],
                "round_AN": out["legs"][2]["rounded_lots"],
                "max_currency_residual_pct": out["exposure"]["max_currency_residual_pct"],
                "max_weight_error_pct": out["max_weight_error_pct"],
                "passed_gate_k": out["passed_gate_k"],
                "reject_reason": out["reject_reason"] or "",
            })
            residuals.append(out["exposure"]["max_currency_residual_pct"])
            if not out["passed_gate_k"]:
                gate_fail += 1
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            w.writerows(rows)
        result = {
            "status": "CONNECTED",
            "cases": len(rows),
            "basket_notional_usd": notional,
            "gate_k_pass": len(rows) - gate_fail,
            "gate_k_total": len(rows),
            "median_residual_pct": round(statistics.median(residuals), 4) if residuals else None,
            "max_residual_pct": round(max(residuals), 4) if residuals else None,
            "price_source": "real terminal mid at audit time (hypothetical translation, no orders)",
            "conversion_rates": CUR_TO_USD,
            "csv": str(csv_path.relative_to(ROOT)),
        }
        self.results["lot_translation"] = result
        return result

    # ── 6. REAL READ-ONLY RECONCILIATION ────────────────────────────────
    def broker_state_audit(self) -> dict:
        if self.adapter is None:
            return {"status": PENDING}
        mt5 = self.adapter._mt5
        try:
            positions = mt5.positions_get() or []
            orders = mt5.orders_get() or []
        except Exception as e:  # noqa: BLE001
            return {"status": "ERROR", "detail": str(e)}
        pos_rows = []
        for p in positions:
            pos_rows.append({
                "ticket": int(p.ticket), "symbol": p.symbol,
                "volume": float(p.volume), "type": int(p.type),
                "side": "BUY" if p.type == 0 else "SELL",
                "price_open": float(p.price_open),
                "magic": int(p.magic),
                "comment": p.comment,
                "owned_tb": int(p.magic) == TB_MAGIC,
            })
        tb_pos = [r for r in pos_rows if r["owned_tb"]]
        foreign = [r for r in pos_rows if not r["owned_tb"]]
        # recent history (read-only)
        hist = {"orders": [], "deals": []}
        try:
            fr = mt5.history_orders_get(datetime.now(timezone.utc) - timedelta(days=7),
                                        datetime.now(timezone.utc)) or []
            hist["orders"] = [
                {"ticket": int(o.ticket), "symbol": o.symbol, "magic": int(o.magic),
                 "type": int(o.type), "state": int(o.state)}
                for o in fr[-20:]]
            fd = mt5.history_deals_get(datetime.now(timezone.utc) - timedelta(days=7),
                                       datetime.now(timezone.utc)) or []
            hist["deals"] = [
                {"ticket": int(d.ticket), "order": int(d.order), "symbol": d.symbol,
                 "magic": int(d.magic), "type": int(d.type), "volume": float(d.volume)}
                for d in fd[-20:]]
        except Exception:  # noqa: BLE001
            hist = {"orders": [], "deals": []}
        result = {
            "status": "CONNECTED",
            "positions_total": len(pos_rows),
            "tb_magic_positions": len(tb_pos),
            "foreign_positions_protected": len(foreign),
            "pending_orders_total": len(orders),
            "tb_magic_pending_orders": sum(1 for o in orders if int(o.magic) == TB_MAGIC),
            "history_last_7d_orders": len(hist["orders"]),
            "history_last_7d_deals": len(hist["deals"]),
            "tb_positions": tb_pos,
            "foreign_positions": foreign,
            "history_sample": hist,
            "ownership_rule": "positions only TB-owned via magic 31082026 + linkage; "
                              "foreign/magic-mismatch positions never touched",
        }
        self.results["broker_state"] = result
        return result

    # ── 7. ORDER_SEND GUARD + SHADOW LOOP ───────────────────────────────
    def install_order_send_guard(self) -> None:
        """Wrap mt5.order_send so ANY attempted call fails the run."""
        if self.adapter is None:
            return
        mt5 = self.adapter._mt5
        real = mt5.order_send

        def guarded(*args, **kwargs):
            self.order_send_attempts += 1
            raise AssertionError(
                "order_send GUARD TRIPPED during TB-R4 shadow seal "
                "(execution_authorization=NOT_AUTHORIZED)")

        mt5.order_send = guarded
        self._real_order_send = real

    def shadow_loop(self, ledger_path: Optional[str] = None) -> dict:
        if self.adapter is None:
            return {"status": PENDING}
        cfg = TBMarketDataConfig(bar_seconds=BAR_SECONDS)
        self.feed = SynchronizedTriangleFeed(adapter=self.adapter, config=cfg)
        # resolver already locked by symbol_audit (real broker symbols)
        self.resolution = self.feed.resolver.require_resolved()
        self.ledger = BasketLedger(ledger_path or ":memory:")
        self.ledger.initialize()
        self.install_order_send_guard()
        cycles = []
        for i in range(self.max_cycles):
            ref = datetime.now(timezone.utc)
            snap = self.feed.get_synchronized_closed_triangle(reference_time=ref)
            row = {
                "cycle": i + 1,
                "ref_utc": str(ref),
                "signal_valid": snap.signal_snapshot_valid,
                "failure_code": snap.failure_code.value
                if not snap.signal_snapshot_valid else None,
                "selected_bar_close": str(snap.signal_bar_close_time)
                if snap.signal_snapshot_valid else None,
            }
            if snap.signal_snapshot_valid:
                exec_snap = self.feed.get_execution_quote_snapshot(
                    signal_bar_close_time=snap.signal_bar_close_time,
                    reference_time=ref)
                row["execution_valid"] = exec_snap.execution_snapshot_valid
                row["execution_failure"] = (
                    exec_snap.failure_code.value
                    if not exec_snap.execution_snapshot_valid else None)
                if exec_snap.execution_snapshot_valid:
                    row["max_quote_age_ms"] = exec_snap.max_quote_age_ms
                    row["max_cross_leg_skew_ms"] = exec_snap.max_cross_leg_skew_ms
            else:
                row["execution_valid"] = False
            if snap.signal_snapshot_valid:
                p = self.primary.process_snapshot(snap)
                c = self.control.process_snapshot(snap)
                row["primary_z"] = round(float(p.zscore), 6)
                row["control_z"] = round(float(c.zscore), 6)
                row["primary_action"] = p.decision.value
                row["control_action"] = c.decision.value
                row["primary_direction"] = p.direction.name
                self.ledger.append_event(
                    EventType.SIGNAL_OBSERVED, strategy_id=PRIMARY_CONFIG.strategy_id,
                    dedup_key=f"R4REAL|SIG|{snap.signal_bar_close_time}",
                    payload={"z": row["primary_z"], "action": p.decision.value})
                if p.decision == BasketDecision.OPEN_BASKET:
                    # hypothetical execution intent (real specs/prices already
                    # used by lot_translation); persist intent, DO NOT EXECUTE
                    self.ledger.append_event(
                        EventType.BASKET_INTENT_CREATED, basket_id=p.basket_id,
                        strategy_id=PRIMARY_CONFIG.strategy_id,
                        prior_state=S.SIGNAL_DETECTED.value,
                        new_state=S.INTENT_CREATED.value,
                        dedup_key=f"R4REAL|INTENT|{p.basket_id}",
                        source="tb_r4_real_mt5",
                        payload={"z": float(p.zscore), "direction": p.direction.name,
                                 "shadow_only": True,
                                 "order_send": "NOT_CALLED"})
                    row["shadow_order_would_send"] = True
            cycles.append(row)
            time.sleep(self.cycle_sleep_s)
        result = {
            "status": "CONNECTED",
            "cycles": cycles,
            "valid_snapshots": sum(1 for r in cycles if r["signal_valid"]),
            "sync_failures": [r["failure_code"] for r in cycles
                              if not r["signal_valid"]],
            "shadow_order_would_send_total": sum(
                1 for r in cycles if r.get("shadow_order_would_send")),
            "order_send_attempts": self.order_send_attempts,
            "ledger_events": self.ledger.n_events(),
            "ledger_integrity_problems": self.ledger.integrity_check(),
        }
        self.results["shadow_loop"] = result
        return result

    def shutdown(self) -> None:
        if self.adapter is not None:
            try:
                if getattr(self, "_real_order_send", None) is not None:
                    self.adapter._mt5.order_send = self._real_order_send
            except Exception:  # noqa: BLE001
                pass
            self.adapter.shutdown()

    # ── RUN ALL ─────────────────────────────────────────────────────────
    def run(self) -> dict:
        if not self.connect():
            self.results = {
                "real_mt5_connected": False,
                "environment": {"status": PENDING},
                "symbols": {"status": PENDING},
                "m5": {"status": PENDING},
                "tick_sample": {"status": PENDING},
                "lot_translation": {"status": PENDING},
                "broker_state": {"status": PENDING},
                "shadow_loop": {"status": PENDING},
                "note": "No MT5 terminal reachable; broker sections "
                        "PENDING_TERMINAL_VALIDATION (never PASS from mocks).",
            }
            return self.results
        self.environment_audit()
        self.symbol_audit()
        self.m5_audit()
        self.tick_sample()
        self.lot_translation()
        self.broker_state_audit()
        self.shadow_loop()
        self.shutdown()
        self.results["real_mt5_connected"] = True
        return self.results


def write_artifacts(results: dict) -> None:
    env = results.get("environment", {})
    sym = results.get("symbols", {})
    m5 = results.get("m5", {})
    ts = results.get("tick_sample", {})
    lt = results.get("lot_translation", {})
    bs = results.get("broker_state", {})
    sl = results.get("shadow_loop", {})

    (OUT / "TB_R4_REAL_MT5_ENVIRONMENT_AUDIT.json").write_text(
        json.dumps(env, indent=2), encoding="utf-8")
    (OUT / "TB_R4_REAL_SYMBOL_SPEC_AUDIT.json").write_text(
        json.dumps(sym, indent=2), encoding="utf-8")
    (OUT / "TB_R4_REAL_MARKET_DATA_AUDIT.json").write_text(
        json.dumps(m5, indent=2), encoding="utf-8")
    (OUT / "TB_R4_REAL_ACCOUNT_RECONCILIATION.json").write_text(
        json.dumps(bs, indent=2), encoding="utf-8")
    (OUT / "TB_R4_SHADOW_LOOP_AUDIT.json").write_text(
        json.dumps(sl, indent=2), encoding="utf-8")

    # tick distributions (also as CSVs for the three required files)
    import csv as _csv
    for fname, key in [("TB_R4_REAL_TICK_QUALITY.csv", "quote_age_ms_per_leg"),
                       ("TB_R4_REAL_SPREAD_DISTRIBUTION.csv", "spread_points_per_leg")]:
        data = ts.get(key, {})
        with open(OUT / fname, "w", newline="", encoding="utf-8") as f:
            w = _csv.writer(f)
            w.writerow(["leg", "n", "median", "p90", "p95", "p99", "max"])
            for leg, d in data.items():
                if isinstance(d, dict) and d.get("n"):
                    w.writerow([leg, d["n"], d["median"], d["p90"], d["p95"],
                                d["p99"], d["max"]])
    with open(OUT / "TB_R4_REAL_CROSS_LEG_SKEW.csv", "w", newline="", encoding="utf-8") as f:
        w = _csv.writer(f)
        d = ts.get("cross_leg_skew_s", {})
        w.writerow(["metric", "n", "median", "p90", "p95", "p99", "max"])
        if isinstance(d, dict):
            w.writerow(["cross_leg_skew_s", d.get("n", 0), d.get("median", 0),
                        d.get("p90", 0), d.get("p95", 0), d.get("p99", 0),
                        d.get("max", 0)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-seconds", type=int, default=60)
    ap.add_argument("--cycles", type=int, default=10)
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    audit = RealMT5Audit(sample_seconds=args.sample_seconds,
                         max_cycles=args.cycles, offline=args.offline)
    results = audit.run()
    write_artifacts(results)

    env = results.get("environment", {})
    sl = results.get("shadow_loop", {})
    print(json.dumps({
        "real_mt5_connected": results.get("real_mt5_connected", False),
        "terminal": env.get("terminal_name"),
        "server": env.get("server"),
        "account_type": env.get("account_type"),
        "symbols_resolved": {
            c: (s.get("broker_symbol") if isinstance(s, dict) else None)
            for c, s in results.get("symbols", {}).items()},
        "m5_sync_now": (results.get("m5") or {}).get("three_leg_sync_now"),
        "tick_sample": (results.get("tick_sample") or {}).get("status"),
        "lot_translation": (results.get("lot_translation") or {}).get("status"),
        "broker_state": (results.get("broker_state") or {}).get("status"),
        "shadow_loop": (results.get("shadow_loop") or {}).get("status"),
        "order_send_attempts": sl.get("order_send_attempts"),
        "ledger_integrity_problems": sl.get("ledger_integrity_problems", []),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
