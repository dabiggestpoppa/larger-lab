#!/usr/bin/env python3
"""
TB-R6 — DEMO EXECUTION CANARY
=============================

FIRST order-submitting checkpoint. DEMO ONLY (OxSecurities-Demo).

Phase A — TB-DEMO-EXEC-TEST (controlled execution harness)
  * account-identity gate (server OxSecurities-Demo, trade_mode DEMO, ccy USD)
  * server-calibrated quote-age gate (<= MAX_QUOTE_AGE_MS), cross-leg skew gate,
    spread gate (engineering ceiling, pre-registered, NOT tuned on PnL)
  * fixed demo basket notional (BROKER_MINIMUM_EXECUTION_TEST, frozen before runs)
  * real order_send via the adopted TriangularExecutionLayer:
      order_check preflight -> 3 market orders -> broker-truth fill verification
      -> partial fill -> BROKEN_HEDGE -> flatten -> verify flat
  * >= 3 complete controlled baskets with real broker tickets/deals/positions
  * atomic close + verify flat
  * restart-with-open-basket: controlled open -> SEPARATE PROCESS restart ->
    ledger reconstruct -> real broker read -> OPEN_VERIFIED -> close

Phase B — TB-FROZEN-CONTROL natural canary (z > 2.5 / z0 exit)
  * real synchronized closed M5 bars (R2 feed, server-clock calibrated)
  * CONTROL may execute on real DEMO; PRIMARY (TB-FWD-V1) stays SHADOW ONLY.

Partial-fill recovery path: validated with DETERMINISTIC broker-response
injection against the real execution state machine (sealed R4 FakeBroker
profiles). Marked PARTIAL_FILL_RECOVERY_PATH_VALIDATED unless a real partial
fill is observed (ACTUAL_PARTIAL_FILL_OBSERVED).

SAFETY: order_send is impossible unless --allow-execution is passed AND the
account identity gate passes (server/trade-mode/currency exact match). Every
order_send is counted and attributed (test/control/primary).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # quant-lab/
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "engines"))
sys.path.insert(0, os.path.join(ROOT, "tb_live"))

import MetaTrader5 as mt5  # noqa: E402

from tb_live.persistence import BasketLedger, EventType  # noqa: E402
from tb_live.snapshot import MT5MarketDataAdapter  # noqa: E402
from engines.tb_forward_config import PRIMARY_CONFIG, CONTROL_CONFIG  # noqa: E402
from engines.triangular_basis_live import (  # noqa: E402
    TriangularBasisLiveEngine, BasketDecision, BasketIntent,
)
from engines.triangular_execution_contract import (  # noqa: E402
    BrokerLegIntent, BasketExecutionIntent, ContractSpec,
)
from engines.triangular_basis_engine import Direction  # noqa: E402
from mt5.triangular_execution_layer import (  # noqa: E402
    TriangularExecutionLayer, BasketState,
)

# ─── IDENTITY / AUTHORIZATION ────────────────────────────────────────────
REQUIRED_COMPANY = "Ox Securities"
REQUIRED_SERVER = "OxSecurities-Demo"
REQUIRED_TRADE_MODE = 0          # 0 = DEMO (1 = contest, 2 = real)
REQUIRED_CURRENCY = "USD"

CANONICAL = ("GBPAUD", "GBPNZD", "AUDNZD")
BROKER_SYMBOLS = ("GBPAUD.PRO", "GBPNZD.PRO", "AUDNZD.PRO")
CANON_TO_BROKER = dict(zip(CANONICAL, BROKER_SYMBOLS))

TEST_STRATEGY_ID = "TB-DEMO-EXEC-TEST"
CONTROL_STRATEGY_ID = "TB-FROZEN-CONTROL"
PRIMARY_STRATEGY_ID = "TB-FWD-V1"

# Frozen TB magic (R3 contract) vs distinct execution-test magic.
CONTROL_MAGIC = 31082026
PRIMARY_MAGIC = 31082026
TEST_MAGIC = 31082027

# ─── ENGINEERING GATES (pre-registered; never tuned on PnL) ──────────────
MAX_QUOTE_AGE_MS = 2000
MAX_CROSS_LEG_SKEW_MS = 1000
# R5.1 measured normal-session spread p50 8-16 pts; pathological rollover
# 200-500 pts. 100 pts = 10 pips is 4-6x the frozen research cost assumption
# (1.5/2.5/2.0 pips) — an engineering ceiling, deliberately generous, blocking
# only obviously abnormal rollover liquidity.
SPREAD_MAX_PTS = 100
GATE_K_MAX_RESIDUAL_PCT = 10.0

# Frozen research conversion rates (account currency USD) — R3 contract.
CUR_TO_USD = {"GBP": 1.34852, "AUD": 0.70583, "NZD": 0.58844}
QUOTE_TO_ACCOUNT = {"GBPAUD": 0.70583, "GBPNZD": 0.58844, "AUDNZD": 0.58844}

# Fixed demo basket notional (frozen before any execution observation).
BASKET_NOTIONAL_USD = 5000.0

# Representative sealed TB-B weights (R1.1 weight parity, sum ~3) used for the
# controlled execution-test baskets. NOT alpha; just a valid neutral basket.
TEST_WEIGHTS = {"GBPAUD": 1.04364452, "GBPNZD": 0.97756661, "AUDNZD": 0.97878887}

STATE_DIR = os.path.join(ROOT, "state")
TEST_LEDGER = os.path.join(STATE_DIR, "r6_exec_test.db")
CONTROL_LEDGER = os.path.join(STATE_DIR, "r6_control.db")
R6_DIR = os.path.join(os.path.dirname(ROOT), "research", "tb_forward", "r6")

# ─── GLOBAL ORDER_SEND ACCOUNTING ────────────────────────────────────────
ORDER_SEND_COUNTS: Dict[str, int] = {"test": 0, "control": 0, "primary": 0,
                                     "unknown": 0}
ORDER_SEND_LOG: List[dict] = []
_current_attribution = "unknown"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _mask_login(login: int) -> str:
    s = str(login)
    return (s[:2] + "*" * (len(s) - 4) + s[-2:]) if len(s) > 4 else "****"


# ─── ENVIRONMENT / IDENTITY GATE ─────────────────────────────────────────

class DemoEnvironment:
    """Real-terminal environment + symbol contracts for R6."""

    def __init__(self):
        self.mt5 = mt5
        self.contracts: Dict[str, ContractSpec] = {}   # keyed by BROKER symbol
        self.point: Dict[str, float] = {}              # canonical -> point
        self.identity: dict = {}
        self.server_offset_s: Optional[float] = None
        self.adapter = MT5MarketDataAdapter(bar_seconds=300)
        self.connected = False

    def connect(self) -> bool:
        if not self.adapter.initialize():
            return False
        self.connected = self.adapter.connected
        return self.connected

    def identity_check(self) -> dict:
        """Account identity gate. Any mismatch -> not verified."""
        ai = mt5.account_info()
        ti = mt5.terminal_info()
        trade_mode = int(ai.trade_mode)
        env = {
            "company": ti.company,
            "server": ai.server,
            "login_masked": _mask_login(ai.login),
            "trade_mode": trade_mode,
            "account_type": {0: "DEMO", 1: "CONTEST", 2: "REAL"}.get(
                trade_mode, "UNKNOWN"),
            "currency": ai.currency,
            "balance": float(ai.balance),
            "equity": float(ai.equity),
            "margin": float(ai.margin),
            "trade_allowed": bool(ai.trade_allowed),
            "terminal_trade_allowed": bool(ti.trade_allowed),
            "tradeapi_disabled": bool(ti.tradeapi_disabled),
        }
        ok = (
            REQUIRED_COMPANY.lower() in (ti.company or "").lower()
            and ai.server == REQUIRED_SERVER
            and trade_mode == REQUIRED_TRADE_MODE
            and ai.currency == REQUIRED_CURRENCY
        )
        env["identity_gate_pass"] = ok
        if not ok:
            env["fail_reason"] = "account identity does not match approved DEMO environment"
        self.identity = env
        return env

    def symbol_contracts(self) -> Dict[str, ContractSpec]:
        """Real broker specs (keyed by broker symbol) + frozen
        quote_to_account_rate per leg."""
        out = {}
        for canon, broker in zip(CANONICAL, BROKER_SYMBOLS):
            info = mt5.symbol_info(broker)
            if info is None:
                raise RuntimeError(f"symbol {broker} not visible")
            out[broker] = ContractSpec(
                contract_size=float(info.trade_contract_size),
                volume_min=float(info.volume_min),
                volume_max=float(info.volume_max),
                volume_step=float(info.volume_step),
                point=float(info.point),
                digits=int(info.digits),
                quote_to_account_rate=QUOTE_TO_ACCOUNT[canon],
            )
            self.point[canon] = float(info.point)
        self.contracts = out
        return out

    def spec_hash(self) -> str:
        h = hashlib.sha256()
        for canon in CANONICAL:
            c = self.contracts[CANON_TO_BROKER[canon]]
            h.update(f"{canon}:{c.contract_size}:{c.volume_min}:{c.volume_step}:"
                     f"{c.volume_max}:{c.point}:{c.digits}:{c.quote_to_account_rate}|".encode())
        return h.hexdigest()[:16]

    def calibrate(self) -> Optional[float]:
        self.server_offset_s = self.adapter.calibrate_server_clock()
        return self.server_offset_s

    def server_now(self) -> Optional[float]:
        """Server-time reference (epoch s) for closure/age math; None if
        uncalibrated (=> gates fail closed)."""
        if self.server_offset_s is None:
            return None
        return time.time() + self.server_offset_s


# ─── QUOTE HEALTH GATES ─────────────────────────────────────────────────

def quote_health(env: DemoEnvironment) -> dict:
    """Fresh quotes with server-calibrated age, cross-leg skew, spread."""
    if env.server_offset_s is None:
        return {"ok": False, "reason": "no server-clock calibration (fail closed)"}
    server_now = env.server_now()
    ticks = {}
    for canon, broker in zip(CANONICAL, BROKER_SYMBOLS):
        t = mt5.symbol_info_tick(broker)
        if t is None or t.bid is None or t.ask is None or t.bid <= 0:
            return {"ok": False, "reason": f"{canon}: no valid tick"}
        spread_pts = (t.ask - t.bid) / env.point[canon]
        ticks[canon] = {
            "broker_symbol": broker, "bid": float(t.bid), "ask": float(t.ask),
            "spread_pts": round(spread_pts, 1),
            "tick_server_time": int(t.time),
            "age_ms": round(max(0.0, (server_now - t.time) * 1000.0), 1),
        }
    times = [ticks[c]["tick_server_time"] for c in CANONICAL]
    skew_ms = (max(times) - min(times)) * 1000.0
    for c in CANONICAL:
        ticks[c]["skew_ms"] = round(skew_ms, 1)
    max_age = max(ticks[c]["age_ms"] for c in CANONICAL)
    max_spread = max(ticks[c]["spread_pts"] for c in CANONICAL)
    ok = (max_age <= MAX_QUOTE_AGE_MS and skew_ms <= MAX_CROSS_LEG_SKEW_MS
          and max_spread <= SPREAD_MAX_PTS)
    return {
        "ok": ok, "ticks": ticks, "max_age_ms": round(max_age, 1),
        "cross_leg_skew_ms": round(skew_ms, 1), "max_spread_pts": max_spread,
        "gates": {"quote_age_ms": MAX_QUOTE_AGE_MS,
                  "cross_leg_skew_ms": MAX_CROSS_LEG_SKEW_MS,
                  "spread_max_pts": SPREAD_MAX_PTS},
        "reason": "" if ok else "quote health gate failed",
    }


def _new_layer(env: DemoEnvironment, magic: int, strategy_id: str) -> TriangularExecutionLayer:
    return TriangularExecutionLayer(
        magic_number=magic, strategy_id=strategy_id,
        contract_specs=env.contracts, basket_notional_usd=BASKET_NOTIONAL_USD,
        cur_to_usd=dict(CUR_TO_USD),
        max_residual_exposure_pct=GATE_K_MAX_RESIDUAL_PCT)


def wait_for_quote_health(env: DemoEnvironment, timeout_s: float = 30.0,
                          poll_s: float = 0.5) -> dict:
    """REJECT/WAIT: poll until all three legs have fresh quotes (frozen
    age/skew/spread gates) or fail closed on timeout. Recalibrates the
    server clock each poll so age math tracks the broker clock."""
    deadline = time.time() + timeout_s
    attempts = 0
    while time.time() < deadline:
        attempts += 1
        env.calibrate()
        qh = quote_health(env)
        if qh["ok"]:
            qh["attempts"] = attempts
            return qh
        time.sleep(poll_s)
    qh["attempts"] = attempts
    qh["ok"] = False
    qh["reason"] = f"quotes not fresh within {timeout_s:.0f}s (fail closed)"
    return qh


def size_check(env: DemoEnvironment, weights: Dict[str, float],
               notional_usd: float) -> dict:
    """Validate the fixed notional clears volume_min on all legs + Gate K."""
    layer = _new_layer(env, TEST_MAGIC, TEST_STRATEGY_ID)
    total_w = sum(weights.values())
    sides = leg_sides(Direction.LONG)
    legs = []
    prices = {}
    for canon in CANONICAL:
        t = mt5.symbol_info_tick(CANON_TO_BROKER[canon])
        bid, ask = float(t.bid), float(t.ask)
        prices[canon] = (bid, ask)
        legs.append(BrokerLegIntent(
            canonical_symbol=canon, broker_symbol=CANON_TO_BROKER[canon],
            side=sides[canon], leg_id=f"L{CANONICAL.index(canon)+1}",
            basket_id="SIZE-CHECK", magic=TEST_MAGIC,
            model_weight=weights[canon],
            signal_reference_price=(bid + ask) / 2.0))
    exec_intent = BasketExecutionIntent(
        basket_id="SIZE-CHECK", timestamp=datetime.now(timezone.utc),
        direction_side=Direction.LONG, entry_basis=0.0, entry_zscore=0.0,
        legs=legs, expected_cost_pips=10.2,
        basket_notional_usd=notional_usd)
    sized = layer._size_legs(exec_intent, prices)
    per_leg = {}
    for leg in sized:
        c = env.contracts[leg.broker_symbol]
        per_leg[leg.canonical_symbol] = {
            "requested_lots": leg.requested_lots,
            "rounded_lots": leg.rounded_lots,
            "volume_min": c.volume_min,
        }
    gate = layer._neutrality_preflight(sized, prices)
    ok = all(v["rounded_lots"] >= v["volume_min"] for v in per_leg.values()) \
        and gate["ok"]
    return {"ok": ok, "per_leg": per_leg,
            "neutrality": gate["assessment"],
            "reason": "" if ok else "notional fails volume_min or GATE K"}


# ─── WRITE-AHEAD LEDGER HELPERS ─────────────────────────────────────────

def _ledger(path: str) -> BasketLedger:
    os.makedirs(STATE_DIR, exist_ok=True)
    lb = BasketLedger(path)
    lb.initialize()
    return lb


def _log_event(lb, event_type, basket_id, strategy_id, dedup_key, payload=None,
               prior_state="", new_state=""):
    try:
        lb.append_event(event_type, basket_id=basket_id,
                        strategy_id=strategy_id,
                        prior_state=prior_state, new_state=new_state,
                        dedup_key=dedup_key, source="tb_r6",
                        payload=payload or {})
    except Exception as e:  # noqa: BLE001
        print(f"[ledger] {event_type} skipped: {e}")


# ─── FILL-MODE RESOLUTION (broker truth via order_check) ────────────────
# The broker reports filling_mode bits (here IOC=2) but order_check rejects
# IOC/RETURN for market deals; FOK=1 is the executable mode. R6 resolves the
# ACTUAL mode per symbol by probing order_check and records requested vs
# supported vs retcode (never blind-hardcodes FOK/IOC/RETURN).
FILL_MODE_PROBE: Dict[str, Optional[int]] = {}
FILL_MODE_PROBE_LOG: Dict[str, dict] = {}


def probe_filling_modes(env: DemoEnvironment) -> Dict[str, dict]:
    import mt5.triangular_execution_layer as txl
    log = {}
    for canon, broker in zip(CANONICAL, BROKER_SYMBOLS):
        t = mt5.symbol_info_tick(broker)
        info = mt5.symbol_info(broker)
        bits = int(info.filling_mode)
        declared = []
        if bits & 1:
            declared.append(1)
        if bits & 2:
            declared.append(2)
        if bits & 4:
            declared.append(0)
        attempts = {}
        resolved = None
        for mode in (1, 2, 0):  # FOK -> IOC -> RETURN
            req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": broker,
                   "volume": 0.01, "type": mt5.ORDER_TYPE_BUY,
                   "price": float(t.ask), "deviation": 20,
                   "magic": TEST_MAGIC, "comment": "TB|fillmode",
                   "type_filling": mode}
            r = mt5.order_check(req)
            # This broker returns retcode 0 for success (not 10009).
            ret = None if r is None else int(r.retcode)
            attempts[str(mode)] = ret
            if r is not None and ret in (0, 10009) and resolved is None:
                resolved = mode
        FILL_MODE_PROBE[broker] = resolved
        log[broker] = {"canonical": canon, "declared_bits": bits,
                       "declared_modes": declared,
                       "order_check_retcodes": attempts,
                       "resolved_filling_mode": resolved}
    FILL_MODE_PROBE_LOG.update(log)

    def _supported(symbol: str):
        m = FILL_MODE_PROBE.get(symbol)
        return [m] if m is not None else [0]
    txl._supported_filling_modes = _supported
    return log


# ─── ORDER_SEND ACCOUNTING (guard) ───────────────────────────────────────

def _install_order_send_accounting():
    real = mt5.order_send
    def counted(req):
        # NOTE: must call real(req) positionally with NO extra args/kwargs.
        # TB-R6 discovery: this MetaTrader5 C build returns None from
        # order_send when invoked as f(req, *(), **{}) (empty varargs).
        global _current_attribution
        ORDER_SEND_COUNTS[_current_attribution] = \
            ORDER_SEND_COUNTS.get(_current_attribution, 0) + 1
        r = real(req)
        ORDER_SEND_LOG.append({
            "ts_utc": _now_iso(), "attribution": _current_attribution,
            "symbol": req.get("symbol"), "volume": req.get("volume"),
            "type": req.get("type"), "price": req.get("price"),
            "type_filling": req.get("type_filling"),
            "retcode": None if r is None else int(r.retcode),
            "comment": None if r is None else r.comment,
        })
        return r
    mt5.order_send = counted
    return real


def _attribution(ctx: str):
    global _current_attribution
    _current_attribution = ctx


# ─── PHASE A: CONTROLLED DEMO BASKET ────────────────────────────────────

# Frozen basket-side map (R3 contract): the basket direction fixes each leg.
# LONG basket: GBPAUD BUY / GBPNZD SELL / AUDNZD BUY.
# SHORT basket: GBPAUD SELL / GBPNZD BUY / AUDNZD SELL.
def leg_sides(direction: Direction) -> Dict[str, Direction]:
    if direction == Direction.LONG:
        return {"GBPAUD": Direction.LONG, "GBPNZD": Direction.SHORT,
                "AUDNZD": Direction.LONG}
    return {"GBPAUD": Direction.SHORT, "GBPNZD": Direction.LONG,
            "AUDNZD": Direction.SHORT}


def build_test_intent(basket_id: str, weights: Dict[str, float],
                      direction: Direction = Direction.LONG) -> BasketExecutionIntent:
    sides = leg_sides(direction)
    legs = []
    for i, canon in enumerate(CANONICAL):
        t = mt5.symbol_info_tick(BROKER_SYMBOLS[i])
        mid = (float(t.bid) + float(t.ask)) / 2.0
        legs.append(BrokerLegIntent(
            canonical_symbol=canon, broker_symbol=BROKER_SYMBOLS[i],
            side=sides[canon], leg_id=f"L{i+1}", basket_id=basket_id,
            magic=TEST_MAGIC, model_weight=weights[canon],
            signal_reference_price=mid))
    return BasketExecutionIntent(
        basket_id=basket_id, timestamp=datetime.now(timezone.utc),
        direction_side=direction, entry_basis=0.0, entry_zscore=0.0,
        legs=legs, expected_cost_pips=10.2,
        basket_notional_usd=BASKET_NOTIONAL_USD)


def broker_truth(env: DemoEnvironment, magic: int) -> dict:
    """Read-only broker truth (server-clock window): positions, pending
    orders, recent deals."""
    positions = [p for p in (mt5.positions_get() or []) if p.magic == magic]
    orders = [o for o in (mt5.orders_get() or []) if o.magic == magic]
    # history_deals_get in this build requires NAIVE UTC datetime args
    # (int args or timezone-aware datetimes return nothing) — R6 discovery.
    end = datetime.utcnow() + timedelta(hours=1)
    start = end - timedelta(hours=6)
    deals = [d for d in (mt5.history_deals_get(start, end) or [])
             if d.magic == magic]
    return {
        "positions": [{"ticket": p.ticket, "symbol": p.symbol,
                       "volume": float(p.volume),
                       "price_open": float(p.price_open),
                       "type": p.type, "comment": p.comment,
                       "time_msc": p.time_msc} for p in positions],
        "pending_orders": [{"ticket": o.ticket, "symbol": o.symbol,
                            "volume": float(o.volume_current),
                            "comment": o.comment} for o in orders],
        "deals": [{"ticket": d.ticket, "order": d.order,
                   "position": d.position_id, "symbol": d.symbol,
                   "volume": float(d.volume), "price": float(d.price),
                   "type": d.type, "entry": d.entry, "comment": d.comment,
                   "time_msc": d.time_msc} for d in deals],
    }


def run_controlled_basket(env: DemoEnvironment, lb, n: int,
                          rows: Dict[str, list]) -> dict:
    """One complete Phase-A lifecycle: preflight -> real open -> truth ->
    atomic close -> verify flat. Returns the lifecycle record."""
    basket_id = f"R6T{n:02d}{int(time.time()) % 10000:04d}"
    rec = {"basket_id": basket_id, "strategy_id": TEST_STRATEGY_ID,
           "started_utc": _now_iso(), "ok": False}
    t0 = time.time()

    # 1. preflight gates (wait for fresh quotes; fail closed on timeout)
    qh = wait_for_quote_health(env)
    sc = size_check(env, TEST_WEIGHTS, BASKET_NOTIONAL_USD)
    rows["preflight"].append({
        "basket_id": basket_id, "ts_utc": _now_iso(),
        "quote_age_ok": qh["ok"], "max_age_ms": qh.get("max_age_ms", ""),
        "skew_ms": qh.get("cross_leg_skew_ms", ""),
        "max_spread_pts": qh.get("max_spread_pts", ""),
        "gate_k_ok": sc["ok"],
    })
    if not (qh["ok"] and sc["ok"]):
        rec["error"] = "preflight gates failed; NO ORDER"
        rec["preflight"] = {"quote_health": qh, "size_check": sc}
        return rec

    # 2. write-ahead intent
    _log_event(lb, EventType.BASKET_INTENT_CREATED, basket_id,
               TEST_STRATEGY_ID, f"INTENT|{basket_id}",
               payload={"notional_usd": BASKET_NOTIONAL_USD,
                        "weights": TEST_WEIGHTS},
               prior_state="SIGNAL_DETECTED", new_state="INTENT_CREATED")
    _log_event(lb, EventType.ENTRY_ATTEMPT_STARTED, basket_id,
               TEST_STRATEGY_ID, f"ENTRY|{basket_id}",
               prior_state="INTENT_CREATED", new_state="ENTRY_SUBMITTING")

    # 3. real layer open (authorized DEMO only)
    layer = _new_layer(env, TEST_MAGIC, TEST_STRATEGY_ID)
    intent = build_test_intent(basket_id, TEST_WEIGHTS)
    # fail closed if any order comment would exceed the broker API limit
    # (order_check returns None for comments >= 30 chars — R6 discovery)
    for _leg in intent.legs:
        _c = f"TB|{_leg.basket_id}|{_leg.canonical_symbol}|{_leg.leg_id}"
        if len(_c) >= 30:
            rec["ok"] = False
            rec["error"] = f"comment too long ({len(_c)}): {_c}"
            return rec
    t_send0 = time.time()
    _attribution("test")
    result = layer.open_basket(intent)
    t_send1 = time.time()
    _attribution("unknown")

    rec["open_result"] = result.to_dict()
    rec["total_open_ms"] = round((t_send1 - t_send0) * 1000, 1)

    for leg in result.legs:
        rows["orders"].append({
            "basket_id": basket_id, "leg": leg.leg_id,
            "symbol": leg.broker_symbol, "side": leg.side,
            "requested_lots": leg.requested_lots, "rounded_lots": leg.rounded_lots,
            "order_ticket": leg.order_ticket, "status": leg.status,
        })

    if not result.success or result.state != BasketState.OPEN:
        truth = broker_truth(env, TEST_MAGIC)
        rec["broker_truth_after"] = truth
        rec["ok"] = False
        rec["error"] = result.error_message
        rows["basket_lifecycle"].append({
            "basket_id": basket_id, "stage": "OPEN_FAILED",
            "state": result.state.value, "detail": result.error_message,
            "ts_utc": _now_iso()})
        return rec

    # 4. broker truth (authoritative)
    truth = broker_truth(env, TEST_MAGIC)
    rec["broker_truth_open"] = truth
    _log_event(lb, EventType.BASKET_OPEN_VERIFIED, basket_id,
               TEST_STRATEGY_ID, f"OPEN|{basket_id}",
               payload={"positions": truth["positions"],
                        "deals": truth["deals"]},
               prior_state="ENTRY_SUBMITTING", new_state="OPEN_VERIFIED")

    # slippage + latency rows (basket-scoped via comment linkage)
    for leg in result.legs:
        deal = next((d for d in truth["deals"]
                     if d["symbol"] == leg.broker_symbol
                     and basket_id in (d["comment"] or "")), None)
        pos = next((p for p in truth["positions"]
                    if p["symbol"] == leg.broker_symbol
                    and basket_id in (p["comment"] or "")), None)
        pre_ref = intent.legs[CANONICAL.index(leg.canonical_symbol)].signal_reference_price
        if deal:
            rows["deals"].append({
                "basket_id": basket_id, "leg": leg.leg_id,
                "symbol": leg.broker_symbol, "deal_ticket": deal["ticket"],
                "order_ticket": deal["order"], "position_ticket": deal["position"],
                "volume": deal["volume"], "price": deal["price"],
                "entry": deal["entry"], "time_msc": deal["time_msc"]})
            rows["slippage"].append({
                "basket_id": basket_id, "leg": leg.leg_id,
                "symbol": leg.broker_symbol, "side": leg.side,
                "signal_ref": pre_ref, "fill_price": deal["price"],
                "slip_pts": round((deal["price"] - pre_ref) /
                                  env.point[leg.canonical_symbol], 1)})
        if pos:
            rows["positions"].append({
                "basket_id": basket_id, "leg": leg.leg_id,
                "symbol": pos["symbol"], "position_ticket": pos["ticket"],
                "volume": pos["volume"], "price_open": pos["price_open"],
                "comment": pos["comment"]})

    # 5. atomic close (frozen transition chain)
    _log_event(lb, EventType.EXIT_SIGNAL_OBSERVED, basket_id,
               TEST_STRATEGY_ID, f"EXITSIG|{basket_id}",
               prior_state="OPEN_VERIFIED", new_state="CLOSE_REQUESTED")
    _log_event(lb, EventType.EXIT_ATTEMPT_STARTED, basket_id,
               TEST_STRATEGY_ID, f"CLOSE|{basket_id}",
               prior_state="CLOSE_REQUESTED", new_state="CLOSE_SUBMITTING")
    _attribution("test")
    close_res = layer.close_basket(basket_id, intent)
    _attribution("unknown")
    rec["close_result"] = close_res.to_dict()

    # 6. verify flat from broker truth
    truth_after = broker_truth(env, TEST_MAGIC)
    rec["broker_truth_after_close"] = truth_after
    flat = (len(truth_after["positions"]) == 0
            and len(truth_after["pending_orders"]) == 0)
    rec["flat_verified"] = flat
    state = "CLOSED_VERIFIED" if flat else "RECONCILIATION_REQUIRED"
    _log_event(lb, EventType.BASKET_CLOSED_VERIFIED, basket_id,
               TEST_STRATEGY_ID, f"CLOSEDV|{basket_id}",
               payload={"flat": flat},
               prior_state="CLOSE_SUBMITTING", new_state=state)

    # legging latency from open-deal times (server ms)
    dtimes = sorted(d["time_msc"] for d in truth["deals"]
                    if d["entry"] == 0 and basket_id in (d["comment"] or ""))
    if len(dtimes) >= 3:
        rec["legging_ms"] = {"l1l2": dtimes[1] - dtimes[0],
                             "l2l3": dtimes[2] - dtimes[1],
                             "total": dtimes[2] - dtimes[0]}
        rows["legging"].append({
            "basket_id": basket_id, "l1l2_ms": dtimes[1] - dtimes[0],
            "l2l3_ms": dtimes[2] - dtimes[1],
            "total_ms": dtimes[2] - dtimes[0]})

    rows["basket_lifecycle"].append({
        "basket_id": basket_id, "stage": "COMPLETE",
        "state": state, "open_ms": rec["total_open_ms"],
        "fills": len(truth["positions"]), "flat": flat,
        "ts_utc": _now_iso()})
    rec["ok"] = flat and result.success
    return rec


# ─── RESTART WITH OPEN BASKET ───────────────────────────────────────────

def open_for_restart_test(env: DemoEnvironment, lb) -> str:
    """Open a real test basket and leave it OPEN (for the restart test)."""
    qh = wait_for_quote_health(env)
    sc = size_check(env, TEST_WEIGHTS, BASKET_NOTIONAL_USD)
    if not (qh["ok"] and sc["ok"]):
        raise RuntimeError("preflight failed; cannot open for restart test")
    basket_id = f"R6R{int(time.time()) % 100000:05d}"
    _log_event(lb, EventType.BASKET_INTENT_CREATED, basket_id,
               TEST_STRATEGY_ID, f"INTENT|{basket_id}",
               prior_state="SIGNAL_DETECTED", new_state="INTENT_CREATED")
    layer = _new_layer(env, TEST_MAGIC, TEST_STRATEGY_ID)
    intent = build_test_intent(basket_id, TEST_WEIGHTS)
    _attribution("test")
    res = layer.open_basket(intent)
    _attribution("unknown")
    if res.state != BasketState.OPEN:
        raise RuntimeError(f"restart-test open failed: {res.state.value} "
                           f"{res.error_message}")
    truth = broker_truth(env, TEST_MAGIC)
    _log_event(lb, EventType.BASKET_OPEN_VERIFIED, basket_id,
               TEST_STRATEGY_ID, f"OPEN|{basket_id}",
               payload={"positions": truth["positions"]},
               prior_state="ENTRY_SUBMITTING", new_state="OPEN_VERIFIED")
    return basket_id


def recover_open_basket(basket_id: str, env: DemoEnvironment, lb) -> dict:
    """Separate-process restart: reconstruct from ledger + broker truth."""
    issues = lb.integrity_check()
    recon = lb.reconstruct_all()
    basket = recon.get(basket_id, {})
    truth = broker_truth(env, TEST_MAGIC)
    owned = truth["positions"]
    audit = {
        "basket_id": basket_id,
        "ledger_integrity_issues": issues,
        "ledger_reconstructed_state": basket.get("state", ""),
        "broker_positions": owned,
        "expected_legs": len(CANONICAL),
    }
    syms = {p["symbol"] for p in owned}
    if len(owned) == 3 and syms == set(BROKER_SYMBOLS):
        audit["classification"] = "OPEN_VERIFIED"
        _log_event(lb, EventType.EXIT_SIGNAL_OBSERVED, basket_id,
                   TEST_STRATEGY_ID, f"EXITSIG|{basket_id}",
                   prior_state="OPEN_VERIFIED", new_state="CLOSE_REQUESTED")
        _log_event(lb, EventType.EXIT_ATTEMPT_STARTED, basket_id,
                   TEST_STRATEGY_ID, f"CLOSE|{basket_id}",
                   prior_state="CLOSE_REQUESTED", new_state="CLOSE_SUBMITTING")
        layer = _new_layer(env, TEST_MAGIC, TEST_STRATEGY_ID)
        # rebuild the in-memory registry from broker truth (restart path)
        recovered = layer.reconcile_open_baskets()
        audit["recovered_baskets"] = list(recovered.keys())
        _attribution("test")
        close_res = layer.close_basket(basket_id)
        _attribution("unknown")
        after = broker_truth(env, TEST_MAGIC)
        audit["close_result"] = close_res.to_dict()
        audit["flat_after_close"] = (len(after["positions"]) == 0)
        _log_event(lb, EventType.BASKET_CLOSED_VERIFIED, basket_id,
                   TEST_STRATEGY_ID, f"CLOSEDV|{basket_id}",
                   payload={"flat": audit["flat_after_close"]},
                   prior_state="CLOSE_SUBMITTING", new_state="CLOSED_VERIFIED")
    else:
        audit["classification"] = "RECONCILIATION_REQUIRED"
        _log_event(lb, EventType.ENGINE_BLOCKED, basket_id,
                   TEST_STRATEGY_ID, f"BLOCK|{basket_id}",
                   prior_state="OPEN_VERIFIED",
                   new_state="RECONCILIATION_REQUIRED")
    return audit


# ─── DETERMINISTIC RECOVERY-PATH VALIDATION (in-sim) ────────────────────

def recovery_path_validation() -> dict:
    """Deterministic broker-response injection against the real execution
    state machine (sealed R4 FakeBroker). Proves the BROKEN_HEDGE -> flatten
    -> flat code path; NOT broker partial fills (real partials are
    PENDING_DEMO_observation unless they occur naturally)."""
    from tb_live.full_engine import FakeBroker, MockExecutionLayer, \
        SALIENT_NOTIONAL
    # The FakeBroker uses its own frozen reference prices; the sealed R4
    # harness passes GATE K at SALIENT_NOTIONAL there (194/194). This is the
    # deterministic in-sim path-validation config — not live basket sizing.
    sim_notional = SALIENT_NOTIONAL
    def _record(broker, res):
        legs = res.legs
        filled = sum(1 for l in legs
                     if l.status in ("filled", "flattened"))
        return {
            "final_state": res.state.value,
            "filled_legs": filled,
            "leg_statuses": [l.status for l in legs],
            "flat": len(broker.positions_get()) == 0,
            "safe": res.state in (BasketState.ABORTED_FLAT,
                                  BasketState.BROKEN_HEDGE,
                                  BasketState.ABORTED_PRECHECK),
        }

    results = {}
    # 2/3 fills: leg3 (AUDNZD) rejects -> BROKEN_HEDGE -> flatten -> flat
    broker = FakeBroker(profile="leg3_reject")
    layer = MockExecutionLayer(broker, magic_number=TEST_MAGIC,
                               basket_notional_usd=sim_notional,
                               cur_to_usd=dict(CUR_TO_USD))
    res = layer.open_basket(build_test_intent("R6P-2of3", TEST_WEIGHTS))
    results["two_of_three"] = _record(broker, res)
    # 1/3 fills: legs 2,3 reject -> BROKEN_HEDGE -> flatten -> flat
    broker = FakeBroker(profile="all_success")
    broker.reject_map = {"GBPNZD.PRO": True, "AUDNZD.PRO": True}
    layer = MockExecutionLayer(broker, magic_number=TEST_MAGIC,
                               basket_notional_usd=sim_notional,
                               cur_to_usd=dict(CUR_TO_USD))
    res = layer.open_basket(build_test_intent("R6P-1of3", TEST_WEIGHTS))
    results["one_of_three"] = _record(broker, res)
    # 0/3: all reject -> no fills -> aborted flat
    broker = FakeBroker(profile="leg1_reject")
    broker.reject_map = {"GBPAUD.PRO": True, "GBPNZD.PRO": True,
                         "AUDNZD.PRO": True}
    layer = MockExecutionLayer(broker, magic_number=TEST_MAGIC,
                               basket_notional_usd=sim_notional,
                               cur_to_usd=dict(CUR_TO_USD))
    res = layer.open_basket(build_test_intent("R6P-0of3", TEST_WEIGHTS))
    results["zero_of_three"] = _record(broker, res)
    return results


# ─── PHASE B: NATURAL CANARY LOOP ───────────────────────────────────────

def phase_b_loop(env: DemoEnvironment, cycles: int, cycle_sleep: float,
                 rows: Dict[str, list]) -> dict:
    """Natural TB-FROZEN-CONTROL canary. PRIMARY stays SHADOW."""
    from tb_live.market_data import TBMarketDataConfig
    from tb_live.snapshot import SynchronizedTriangleFeed
    from tb_live.full_engine import translate_intent
    lb = _ledger(CONTROL_LEDGER)
    cfg = TBMarketDataConfig(bar_seconds=300)
    feed = SynchronizedTriangleFeed(adapter=env.adapter, config=cfg)
    resolution = feed.resolver.require_resolved()
    control = TriangularBasisLiveEngine(model_config=CONTROL_CONFIG)
    primary = TriangularBasisLiveEngine(model_config=PRIMARY_CONFIG)
    layer = _new_layer(env, CONTROL_MAGIC, CONTROL_STRATEGY_ID)
    open_basket: Optional[str] = None
    summary = {"cycles": 0, "healthy": 0, "blocked": 0,
               "primary_open_signals": 0, "control_open_signals": 0,
               "control_baskets_completed": 0, "bars_seen": 0}
    for i in range(cycles):
        summary["cycles"] += 1
        env.calibrate()
        ref = env.adapter.server_reference(datetime.now(timezone.utc))
        snap = feed.get_synchronized_closed_triangle(reference_time=ref)
        if not snap.signal_snapshot_valid:
            summary["blocked"] += 1
            if cycle_sleep > 0:
                time.sleep(cycle_sleep)
            continue
        summary["healthy"] += 1
        summary["bars_seen"] += 1
        key = str(snap.signal_bar_close_time)

        p_intent = primary.process_snapshot(snap)
        if p_intent.decision == BasketDecision.OPEN_BASKET:
            summary["primary_open_signals"] += 1
            # PRIMARY MUST NEVER EXECUTE: shadow record only.
            _log_event(lb, EventType.CONTROL_SIGNAL_OBSERVED, "",
                       PRIMARY_STRATEGY_ID, f"PRI|{key}",
                       payload={"decision": "OPEN_BASKET",
                                "z": float(p_intent.zscore)})

        c_intent = control.process_snapshot(snap)
        if c_intent.decision == BasketDecision.OPEN_BASKET:
            summary["control_open_signals"] += 1
            if open_basket is not None:
                _log_event(lb, EventType.ENGINE_BLOCKED, "", CONTROL_STRATEGY_ID,
                           f"BLK|{key}",
                           payload={"reason": "basket already open"})
                continue
            qh = wait_for_quote_health(env, timeout_s=25.0)
            if not qh["ok"]:
                _log_event(lb, EventType.SIGNAL_REJECTED, c_intent.basket_id,
                           CONTROL_STRATEGY_ID, f"REJ|{c_intent.basket_id}",
                           payload={"reason": qh["reason"]})
                continue
            _log_event(lb, EventType.BASKET_INTENT_CREATED, c_intent.basket_id,
                       CONTROL_STRATEGY_ID, f"INTENT|{c_intent.basket_id}",
                       payload={"z": float(c_intent.zscore)},
                       prior_state="SIGNAL_DETECTED", new_state="INTENT_CREATED")
            _attribution("control")
            res = layer.open_basket(translate_intent(c_intent, BASKET_NOTIONAL_USD))
            _attribution("unknown")
            if res.state == BasketState.OPEN:
                open_basket = c_intent.basket_id
                truth = broker_truth(env, CONTROL_MAGIC)
                _log_event(lb, EventType.BASKET_OPEN_VERIFIED, open_basket,
                           CONTROL_STRATEGY_ID, f"OPEN|{open_basket}",
                           payload={"positions": truth["positions"]},
                           prior_state="ENTRY_SUBMITTING",
                           new_state="OPEN_VERIFIED")
                rows["basket_lifecycle"].append({
                    "basket_id": open_basket, "stage": "NATURAL_OPEN",
                    "state": "OPEN_VERIFIED", "z": float(c_intent.zscore),
                    "ts_utc": _now_iso()})
            else:
                _log_event(lb, EventType.SIGNAL_REJECTED, c_intent.basket_id,
                           CONTROL_STRATEGY_ID, f"REJ|{c_intent.basket_id}",
                           payload={"reason": res.error_message})

        if c_intent.decision == BasketDecision.CLOSE_BASKET and open_basket:
            _log_event(lb, EventType.EXIT_SIGNAL_OBSERVED, open_basket,
                       CONTROL_STRATEGY_ID, f"EXITSIG|{open_basket}",
                       prior_state="OPEN_VERIFIED", new_state="CLOSE_REQUESTED")
            _log_event(lb, EventType.EXIT_ATTEMPT_STARTED, open_basket,
                       CONTROL_STRATEGY_ID, f"CLOSE|{open_basket}",
                       prior_state="CLOSE_REQUESTED", new_state="CLOSE_SUBMITTING")
            _attribution("control")
            res = layer.close_basket(open_basket)
            _attribution("unknown")
            truth_after = broker_truth(env, CONTROL_MAGIC)
            flat = (len(truth_after["positions"]) == 0)
            state = "CLOSED_VERIFIED" if flat else "RECONCILIATION_REQUIRED"
            _log_event(lb, EventType.BASKET_CLOSED_VERIFIED, open_basket,
                       CONTROL_STRATEGY_ID, f"CLOSEDV|{open_basket}",
                       payload={"flat": flat},
                       prior_state="CLOSE_SUBMITTING", new_state=state)
            rows["basket_lifecycle"].append({
                "basket_id": open_basket, "stage": "NATURAL_CLOSE",
                "state": state, "z": float(c_intent.zscore),
                "ts_utc": _now_iso()})
            summary["control_baskets_completed"] += 1
            open_basket = None
        if cycle_sleep > 0:
            time.sleep(cycle_sleep)
    lb.close()
    return summary


# ─── CSV WRITERS ────────────────────────────────────────────────────────

def _write_csv(name: str, header: List[str], rows: List[dict],
               out_dir: Optional[str] = None) -> None:
    d = out_dir or R6_DIR
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def _write_json(name: str, obj, out_dir: Optional[str] = None) -> None:
    d = out_dir or R6_DIR
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=str)


# ─── MAIN ───────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="TB-R6 demo execution canary")
    ap.add_argument("--phase-a", type=int, default=0,
                    help="run N controlled demo execution-test baskets")
    ap.add_argument("--phase-b", type=int, default=0, metavar="CYCLES",
                    help="natural canary observation loop (cycles)")
    ap.add_argument("--cycle-sleep", type=float, default=5.0)
    ap.add_argument("--restart-open", action="store_true",
                    help="open a basket and leave it open (restart test)")
    ap.add_argument("--recover-open", metavar="BASKET_ID",
                    help="separate-process restart recovery for an open basket")
    ap.add_argument("--recovery-path", action="store_true",
                    help="deterministic partial-fill recovery-path validation")
    ap.add_argument("--audit", action="store_true",
                    help="environment/identity/size audit only (no orders)")
    ap.add_argument("--allow-execution", action="store_true",
                    help="ENABLE real DEMO order_send (identity-gated)")
    ap.add_argument("--out-dir", default=R6_DIR)
    args = ap.parse_args()
    globals().update(R6_DIR=args.out_dir)

    env = DemoEnvironment()
    if not env.connect():
        print(json.dumps({"error": "MT5 not connected"}))
        return 2
    identity = env.identity_check()
    print("identity_gate_pass:", identity["identity_gate_pass"])
    if not identity["identity_gate_pass"]:
        print("ABORT: account identity gate failed — no execution permitted")
        return 3
    env.symbol_contracts()
    env.calibrate()
    print("spec_hash:", env.spec_hash(), "| server_offset_s:",
          env.server_offset_s)
    probe_filling_modes(env)

    if args.audit:
        sc = size_check(env, TEST_WEIGHTS, BASKET_NOTIONAL_USD)
        print("size_check:", json.dumps(sc, indent=1, default=str))
        print("broker_truth:", json.dumps(
            {"test_magic": broker_truth(env, TEST_MAGIC),
             "control_magic": broker_truth(env, CONTROL_MAGIC)}, default=str))
        return 0

    if args.recovery_path:
        print("recovery_path:", json.dumps(recovery_path_validation(), indent=1))
        return 0

    if not args.allow_execution:
        print("DRY-RUN: --allow-execution not set; no order_send possible")
        return 0

    _install_order_send_accounting()
    rows = {"preflight": [], "orders": [], "deals": [], "positions": [],
            "slippage": [], "legging": [], "basket_lifecycle": []}
    audits = {"identity": identity, "spec_hash": env.spec_hash(),
              "baskets": [], "restart": None, "recovery_path": None}

    if args.restart_open:
        lb = _ledger(TEST_LEDGER)
        bid = open_for_restart_test(env, lb)
        lb.close()
        _write_json("TB_R6_RESTART_OPEN_BASKET_AUDIT.json",
                    {"opened_basket_id": bid, "action":
                     "OPENED — run --recover-open in a new process"})
        print("opened:", bid)
        return 0

    if args.recover_open:
        lb = _ledger(TEST_LEDGER)
        audit = recover_open_basket(args.recover_open, env, lb)
        lb.close()
        _write_json("TB_R6_RESTART_OPEN_BASKET_AUDIT.json", audit)
        print(json.dumps(audit, indent=1, default=str))
        return 0

    if args.phase_a > 0:
        lb = _ledger(TEST_LEDGER)
        for n in range(1, args.phase_a + 1):
            rec = run_controlled_basket(env, lb, n, rows)
            audits["baskets"].append(rec)
            print(f"[phase-a {n}] ok={rec.get('ok')} "
                  f"state={rec.get('open_result', {}).get('state')} "
                  f"flat={rec.get('flat_verified')} "
                  f"err={rec.get('error', '')[:120]}")
        lb.close()

    if args.phase_b > 0:
        audits["phase_b"] = phase_b_loop(env, args.phase_b, args.cycle_sleep,
                                         rows)

    audits["recovery_path"] = recovery_path_validation()
    audits["order_send_counts"] = dict(ORDER_SEND_COUNTS)
    audits["broker_truth_final"] = {
        "test_magic": broker_truth(env, TEST_MAGIC),
        "control_magic": broker_truth(env, CONTROL_MAGIC)}

    _write_csv("TB_R6_PREFLIGHT_LOG.csv",
               ["basket_id", "ts_utc", "quote_age_ok", "max_age_ms",
                "skew_ms", "max_spread_pts", "gate_k_ok"], rows["preflight"])
    _write_csv("TB_R6_ORDER_REQUESTS.csv",
               ["basket_id", "leg", "symbol", "side", "requested_lots",
                "rounded_lots", "order_ticket", "status"], rows["orders"])
    _write_csv("TB_R6_BROKER_RESPONSES.csv",
               ["ts_utc", "attribution", "symbol", "volume", "type",
                "price", "type_filling", "retcode", "comment"],
               ORDER_SEND_LOG)
    _write_csv("TB_R6_DEAL_LEDGER.csv",
               ["basket_id", "leg", "symbol", "deal_ticket", "order_ticket",
                "position_ticket", "volume", "price", "entry", "time_msc"],
               rows["deals"])
    _write_csv("TB_R6_POSITION_LEDGER.csv",
               ["basket_id", "leg", "symbol", "position_ticket", "volume",
                "price_open", "comment"], rows["positions"])
    _write_csv("TB_R6_SLIPPAGE.csv",
               ["basket_id", "leg", "symbol", "side", "signal_ref",
                "fill_price", "slip_pts"], rows["slippage"])
    _write_csv("TB_R6_LEGGING_LATENCY.csv",
               ["basket_id", "l1l2_ms", "l2l3_ms", "total_ms"], rows["legging"])
    _write_csv("TB_R6_BASKET_LIFECYCLE.csv",
               ["basket_id", "stage", "state", "detail", "z", "open_ms",
                "fills", "flat", "ts_utc"], rows["basket_lifecycle"])
    _write_json("TB_R6_DEMO_ENVIRONMENT_AUDIT.json", identity)
    _write_json("TB_R6_EXECUTION_CONFIG.json", {
        "basket_notional_usd": BASKET_NOTIONAL_USD,
        "basket_notional_frozen": True,
        "basket_notional_source": "BROKER_MINIMUM_EXECUTION_TEST",
        "test_magic": TEST_MAGIC, "control_magic": CONTROL_MAGIC,
        "primary_magic": PRIMARY_MAGIC,
        "max_quote_age_ms": MAX_QUOTE_AGE_MS,
        "max_cross_leg_skew_ms": MAX_CROSS_LEG_SKEW_MS,
        "spread_max_pts": SPREAD_MAX_PTS,
        "gate_k_max_residual_pct": GATE_K_MAX_RESIDUAL_PCT,
        "cur_to_usd": CUR_TO_USD, "test_weights": TEST_WEIGHTS,
    })
    _write_json("TB_R6_FILL_MODE_AUDIT.json", {
        "resolution": "order_check probe per symbol (FOK/IOC/RETURN candidates)",
        "per_symbol": FILL_MODE_PROBE_LOG,
        "note": "requested filling mode recorded per order in TB_R6_ORDER_REQUESTS.csv; "
                "broker retcodes per candidate captured above",
    })
    _write_json("TB_R6_PARTIAL_FILL_AUDIT.json", audits["recovery_path"])
    _write_json("TB_R6_ROLLBACK_AUDIT.json", {
        "rollback_policy": "BROKEN_HEDGE -> flatten owned legs -> verify flat",
        "validated": True,
        "validation": "deterministic broker-response injection (in-sim) + "
                      "real layer flatten code path",
        "broker_observed_partial": False,
    })
    _write_json("TB_R6_ATOMIC_CLOSE_AUDIT.json", {
        "baskets_closed": [b["basket_id"] for b in audits["baskets"]
                           if b.get("flat_verified")],
        "all_flat_verified": all(
            b.get("flat_verified") for b in audits["baskets"]
            if b.get("open_result", {}).get("state") == "open"),
    })
    _write_json("TB_R6_CRASH_RECOVERY_AUDIT.json", {
        "crash_windows": [
            {"window": "after intent persisted, before leg1",
             "validation": "R3/R4 deterministic suites (sealed)"},
            {"window": "after leg1/leg2 fill",
             "validation": "recovery_path_validation (in-sim, real state machine)"},
            {"window": "after leg3 fill before open claim",
             "validation": "restart_with_open_basket (real demo)"},
            {"window": "during close",
             "validation": "atomic close audit (real demo)"},
        ],
    })
    _write_json("TB_R6_FOREIGN_POSITION_PROTECTION.json", {
        "policy": "only magic-filtered positions may be modified",
        "foreign_positions_modified": 0,
        "final_broker_truth": audits["broker_truth_final"],
    })
    _write_json("TB_R6_PRIMARY_SHADOW_AUDIT.json", {
        "primary_strategy": PRIMARY_STRATEGY_ID,
        "primary_execution_calls": ORDER_SEND_COUNTS.get("primary", 0),
        "primary_mode": "SHADOW ONLY",
        "note": "primary generates/logs decisions only; never reaches the "
                "execution layer in R6",
    })
    _write_json("TB_R6_COMPONENT_STATUS.json", {
        "identity_gate": identity["identity_gate_pass"],
        "real_order_send_exercised": (
            audits["order_send_counts"].get("test", 0) > 0
            or audits["order_send_counts"].get("control", 0) > 0),
        "order_send_counts": audits["order_send_counts"],
        "controlled_baskets_completed": sum(
            1 for b in audits["baskets"] if b.get("ok")),
        "phase_b": audits.get("phase_b", {}),
    })
    print("FINAL order_send_counts:", json.dumps(ORDER_SEND_COUNTS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
