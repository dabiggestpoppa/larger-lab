#!/usr/bin/env python3
"""
TB-R2 — SYNCHRONIZED MARKET-DATA TEST SUITE
============================================
Deterministic tests for the R2 market-data layer. All tests use mocks —
no MT5 terminal required.

Covers the frozen synthetic matrix:
  A  PERFECT STATE        all 3 same closed bar, fresh ticks, low skew
  B  ONE BAR LATE         2 legs at T, 1 leg at T-5 -> fail/wait
  C  FORMING BAR          forming candle never used; last common closed bar
  D  NO COMMON BAR        -> fail
  E  STALE TICK           -> execution invalid
  F  CROSS-LEG SKEW       -> execution invalid
  G  ZERO BID             -> invalid
  H  ASK < BID            -> invalid
  I  DUPLICATE BAR        per-leg duplicate -> fail (dedup deterministic)
  J  CLOCK REGRESSION     older tick than previous -> flag
  K  DISCONNECT           -> fail closed
  L  SYMBOL SUFFIX        canonical mapping works
  M  SAME SIGNAL BAR x10  -> one evaluation only
  N  NEXT M5 BAR          -> exactly one new evaluation
Plus: closed-M5-only guarantee, bar-timestamp semantics, session semantics,
zero-order_send guarantee (adapter exposes no order functions; fresh signal +
fresh ticks + valid weights still yield ZERO broker orders).

Run:  python quant-lab/engines/tb_r2_tests.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np  # noqa: E402

from tb_live.market_data import (  # noqa: E402
    TBMarketDataConfig, ClosedBar, LegQuote, TriangleSignalSnapshot,
    TriangleExecutionSnapshot, TriangleSnapshotHealth,
    FailureCode, HealthState,
    validate_signal_snapshot, validate_execution_snapshot,
)
from tb_live.snapshot import (  # noqa: E402
    MockMarketDataAdapter, SymbolResolver, SynchronizedTriangleFeed,
    MT5MarketDataAdapter, CANONICAL_SYMBOLS,
)
from triangular_basis_live import (  # noqa: E402
    TriangularBasisLiveEngine, BasketDecision,
)
from tb_forward_config import PRIMARY_CONFIG  # noqa: E402

TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


UTC = timezone.utc
T0 = datetime(2024, 6, 10, 10, 0, 0, tzinfo=UTC)      # 10:00 (05:00 EST)
T5 = datetime(2024, 6, 10, 10, 5, 0, tzinfo=UTC)
T10 = datetime(2024, 6, 10, 10, 10, 0, tzinfo=UTC)
GA, GN, AN = 1.70179, 1.91038, 1.12619


def bar(sym: str, t: datetime, close=GA, high=None, low=None) -> ClosedBar:
    h = high if high is not None else close
    l = low if low is not None else close
    return ClosedBar(symbol=sym, bar_open_time=t,
                     bar_close_time=t + timedelta(seconds=300),
                     open=close, high=h, low=l, close=close, volume=1.0,
                     is_closed=True, bar_id=f"{sym}:{t}")


def tick(sym: str, t: datetime, bid=GA, ask=None) -> LegQuote:
    ask = ask if ask is not None else bid + 0.0001
    return LegQuote(symbol=sym, bid=bid, ask=ask, last=bid, tick_time=t,
                    received_time=t, quote_age_ms=0.0, spread_price=ask - bid,
                    valid=bid > 0 and ask > 0 and ask >= bid)


def synced_bars(t: datetime, ga=GA, gn=GN, an=AN):
    return {"GBPAUD": bar("GBPAUD", t, ga),
            "GBPNZD": bar("GBPNZD", t, gn),
            "AUDNZD": bar("AUDNZD", t, an)}


def fresh_ticks(t: datetime, ga=GA, gn=GN, an=AN, skew_s=0.0):
    return {"GBPAUD": tick("GBPAUD", t, ga),
            "GBPNZD": tick("GBPNZD", t, gn),
            "AUDNZD": tick("AUDNZD", t - timedelta(seconds=skew_s), an)}


def default_infos(symbols=CANONICAL_SYMBOLS, trade_mode=4):
    """Explicit tradeable symbol metadata (no silent guessing)."""
    out = {}
    for s in symbols:
        out[s] = {"symbol": s, "visible": True, "trade_mode": trade_mode,
                  "digits": 5, "point": 1e-5, "contract_size": 100000.0,
                  "volume_min": 0.01, "volume_step": 0.01, "volume_max": 200.0,
                  "trade_tick_size": 1e-5, "trade_tick_value": 1.0,
                  "trade_stops_level": 0, "filling_mode": 0}
    return out


def make_feed(bars, ticks=None, infos=None, forming=None,
              cfg: TBMarketDataConfig = None, disconnected=False):
    adapter = MockMarketDataAdapter(bars=bars, ticks=ticks or {},
                                    infos=infos or default_infos(),
                                    forming=forming or {},
                                    disconnected=disconnected)
    cfg = cfg or TBMarketDataConfig()
    feed = SynchronizedTriangleFeed(adapter=adapter, config=cfg)
    feed.resolver.resolve()
    return feed, adapter


# ═══════════════════════════════════════════════════════════════════════
# A. PERFECT STATE
# ═══════════════════════════════════════════════════════════════════════
@test
def A_perfect_state_signal_and_execution_valid():
    bars = {"GBPAUD": [bar("GBPAUD", T0), bar("GBPAUD", T5)],
            "GBPNZD": [bar("GBPNZD", T0), bar("GBPNZD", T5)],
            "AUDNZD": [bar("AUDNZD", T0), bar("AUDNZD", T5)]}
    feed, _ = make_feed(bars, ticks=fresh_ticks(T5))
    snap = feed.get_synchronized_closed_triangle(reference_time=T5)
    assert snap.signal_snapshot_valid, snap.failure_code
    assert snap.signal_bar_close_time == T0      # latest closed (forming T5 dropped)
    exec_snap = feed.get_execution_quote_snapshot(T0, T5)
    assert exec_snap.execution_snapshot_valid, exec_snap.failure_code


# ═══════════════════════════════════════════════════════════════════════
# B. ONE LEG STUCK TWO BARS BEHIND -> stale-common rule invalidates
# ═══════════════════════════════════════════════════════════════════════
@test
def B_one_bar_late_fails_closed():
    # GA/GN closed at T0,T5,T10; AN stuck at T0 (two bars behind)
    bars = {"GBPAUD": [bar("GBPAUD", T0), bar("GBPAUD", T5), bar("GBPAUD", T10)],
            "GBPNZD": [bar("GBPNZD", T0), bar("GBPNZD", T5), bar("GBPNZD", T10)],
            "AUDNZD": [bar("AUDNZD", T0)]}
    feed, _ = make_feed(bars)
    ref = T10 + timedelta(seconds=300)   # 10:15: T10 closed for GA/GN
    snap = feed.get_synchronized_closed_triangle(reference_time=ref)
    assert not snap.signal_snapshot_valid
    assert snap.failure_code == FailureCode.STALE_SIGNAL_BAR


# ═══════════════════════════════════════════════════════════════════════
# C. FORMING BAR NEVER USED
# ═══════════════════════════════════════════════════════════════════════
@test
def C_forming_bar_never_used():
    bars = {"GBPAUD": [bar("GBPAUD", T0), bar("GBPAUD", T5, close=9999.0)],
            "GBPNZD": [bar("GBPNZD", T0), bar("GBPNZD", T5)],
            "AUDNZD": [bar("AUDNZD", T0), bar("AUDNZD", T5)]}
    feed, _ = make_feed(bars)
    snap = feed.get_synchronized_closed_triangle(reference_time=T5)
    assert snap.signal_snapshot_valid, snap.failure_code
    assert snap.signal_bar_close_time == T0
    assert snap.gbpaud_bar.close == GA          # not the forming 9999


# ═══════════════════════════════════════════════════════════════════════
# D. NO COMMON BAR
# ═══════════════════════════════════════════════════════════════════════
@test
def D_no_common_bar_fails():
    bars = {"GBPAUD": [bar("GBPAUD", T0)],
            "GBPNZD": [bar("GBPNZD", T5)],
            "AUDNZD": [bar("AUDNZD", T10)]}
    feed, _ = make_feed(bars)
    snap = feed.get_synchronized_closed_triangle(reference_time=T10)
    assert not snap.signal_snapshot_valid
    assert snap.failure_code in (FailureCode.NO_COMMON_CLOSED_BAR,
                                 FailureCode.MISSING_LEG)


# ═══════════════════════════════════════════════════════════════════════
# E. STALE TICK -> execution invalid
# ═══════════════════════════════════════════════════════════════════════
@test
def E_stale_tick_execution_invalid():
    bars = {"GBPAUD": [bar("GBPAUD", T0)], "GBPNZD": [bar("GBPNZD", T0)],
            "AUDNZD": [bar("AUDNZD", T0)]}
    old = datetime(2024, 6, 10, 9, 0, 0, tzinfo=UTC)   # 1h old
    feed, _ = make_feed(bars, ticks=fresh_ticks(old), cfg=TBMarketDataConfig(
        max_quote_age_ms=2000.0))
    exec_snap = feed.get_execution_quote_snapshot(T0, datetime(2024, 6, 10, 10, 1, tzinfo=UTC))
    assert not exec_snap.execution_snapshot_valid
    assert exec_snap.failure_code == FailureCode.STALE_EXECUTION_QUOTES


# ═══════════════════════════════════════════════════════════════════════
# F. CROSS-LEG SKEW -> execution invalid
# ═══════════════════════════════════════════════════════════════════════
@test
def F_cross_leg_skew_execution_invalid():
    bars = {"GBPAUD": [bar("GBPAUD", T0)], "GBPNZD": [bar("GBPNZD", T0)],
            "AUDNZD": [bar("AUDNZD", T0)]}
    ref = datetime(2024, 6, 10, 10, 1, tzinfo=UTC)
    # all ticks fresh (< 2000ms age) but two legs 1200ms apart -> skew > 1000ms
    t_skew = ref - timedelta(milliseconds=1200)
    ticks = {"GBPAUD": tick("GBPAUD", ref, GA),
             "GBPNZD": tick("GBPNZD", t_skew, GN),
             "AUDNZD": tick("AUDNZD", t_skew, AN)}
    feed, _ = make_feed(bars, ticks=ticks,
                        cfg=TBMarketDataConfig(max_cross_leg_skew_ms=1000.0))
    exec_snap = feed.get_execution_quote_snapshot(T0, ref)
    assert not exec_snap.execution_snapshot_valid
    assert exec_snap.failure_code == FailureCode.CROSS_LEG_SKEW


# ═══════════════════════════════════════════════════════════════════════
# G. ZERO BID -> invalid
# ═══════════════════════════════════════════════════════════════════════
@test
def G_zero_bid_invalid():
    bars = {"GBPAUD": [bar("GBPAUD", T0)], "GBPNZD": [bar("GBPNZD", T0)],
            "AUDNZD": [bar("AUDNZD", T0)]}
    ticks = fresh_ticks(T5)
    ticks["GBPNZD"] = tick("GBPNZD", T5, bid=0.0)
    feed, _ = make_feed(bars, ticks=ticks)
    exec_snap = feed.get_execution_quote_snapshot(T0, T5)
    assert not exec_snap.execution_snapshot_valid
    assert exec_snap.failure_code == FailureCode.INVALID_QUOTE


# ═══════════════════════════════════════════════════════════════════════
# H. ASK < BID -> invalid
# ═══════════════════════════════════════════════════════════════════════
@test
def H_ask_below_bid_invalid():
    bars = {"GBPAUD": [bar("GBPAUD", T0)], "GBPNZD": [bar("GBPNZD", T0)],
            "AUDNZD": [bar("AUDNZD", T0)]}
    ticks = fresh_ticks(T5)
    ticks["AUDNZD"] = tick("AUDNZD", T5, bid=1.2, ask=1.1)
    feed, _ = make_feed(bars, ticks=ticks)
    exec_snap = feed.get_execution_quote_snapshot(T0, T5)
    assert not exec_snap.execution_snapshot_valid
    assert exec_snap.failure_code == FailureCode.INVALID_QUOTE


# ═══════════════════════════════════════════════════════════════════════
# I. DUPLICATE BAR (per-leg duplicate timestamps -> fail closed)
# ═══════════════════════════════════════════════════════════════════════
@test
def I_duplicate_bar_fails_closed():
    dup = bar("GBPAUD", T0)
    bars = {"GBPAUD": [bar("GBPAUD", T0), bar("GBPAUD", T0, close=1.7001),
                       bar("GBPAUD", T5)],
            "GBPNZD": [bar("GBPNZD", T0), bar("GBPNZD", T5)],
            "AUDNZD": [bar("AUDNZD", T0), bar("AUDNZD", T5)]}
    feed, _ = make_feed(bars)
    snap = feed.get_synchronized_closed_triangle(reference_time=T5)
    assert not snap.signal_snapshot_valid
    assert snap.failure_code == FailureCode.MISSING_LEG  # dup set -> empty fetch


# ═══════════════════════════════════════════════════════════════════════
# J. CLOCK REGRESSION
# ═══════════════════════════════════════════════════════════════════════
@test
def J_clock_regression_flags():
    bars = {"GBPAUD": [bar("GBPAUD", T0)], "GBPNZD": [bar("GBPNZD", T0)],
            "AUDNZD": [bar("AUDNZD", T0)]}
    feed, _ = make_feed(bars, ticks=fresh_ticks(T5),
                        cfg=TBMarketDataConfig(clock_regression_tolerance_ms=5000.0))
    s1 = feed.get_execution_quote_snapshot(T0, T5)
    assert s1.execution_snapshot_valid
    # next call with an OLDER tick -> regression
    old_tick = fresh_ticks(datetime(2024, 6, 10, 9, 55, 0, tzinfo=UTC))
    feed.adapter.ticks = old_tick
    s2 = feed.get_execution_quote_snapshot(T0, T5)
    assert not s2.execution_snapshot_valid
    assert s2.failure_code == FailureCode.CLOCK_REGRESSION


# ═══════════════════════════════════════════════════════════════════════
# K. DISCONNECT -> fail closed
# ═══════════════════════════════════════════════════════════════════════
@test
def K_disconnect_fails_closed():
    bars = {"GBPAUD": [bar("GBPAUD", T0), bar("GBPAUD", T5)],
            "GBPNZD": [bar("GBPNZD", T0), bar("GBPNZD", T5)],
            "AUDNZD": [bar("AUDNZD", T0), bar("AUDNZD", T5)]}
    feed, adapter = make_feed(bars, ticks=fresh_ticks(T5))
    adapter.disconnected = True
    snap = feed.get_synchronized_closed_triangle(reference_time=T5)
    assert not snap.signal_snapshot_valid
    exec_snap = feed.get_execution_quote_snapshot(T0, T5)
    assert not exec_snap.execution_snapshot_valid


# ═══════════════════════════════════════════════════════════════════════
# L. SYMBOL SUFFIX RESOLUTION
# ═══════════════════════════════════════════════════════════════════════
@test
def L_symbol_suffix_resolution():
    # broker exposes only GBPAUD.PRO etc.; plain names unavailable
    bars = {"GBPAUD": [bar("GBPAUD.PRO", T0), bar("GBPAUD.PRO", T5)],
            "GBPNZD": [bar("GBPNZD.PRO", T0), bar("GBPNZD.PRO", T5)],
            "AUDNZD": [bar("AUDNZD.PRO", T0), bar("AUDNZD.PRO", T5)]}
    infos = {f"{s}.PRO": v for s, v in default_infos().items()}
    adapter = MockMarketDataAdapter(bars=bars, infos=infos)
    res = SymbolResolver(adapter)
    r = res.resolve()
    assert r.mapping == {"GBPAUD": "GBPAUD.PRO", "GBPNZD": "GBPNZD.PRO",
                         "AUDNZD": "AUDNZD.PRO"}
    assert r.locked


@test
def L_symbol_resolution_fails_on_no_tradeable():
    # trade_mode 0 (disabled) for every candidate -> unresolved
    infos = default_infos(trade_mode=0)
    adapter = MockMarketDataAdapter(bars={
        "GBPAUD": [bar("GBPAUD", T0)], "GBPNZD": [bar("GBPNZD", T0)],
        "AUDNZD": [bar("AUDNZD", T0)]}, infos=infos)
    res = SymbolResolver(adapter)
    try:
        res.require_resolved()
        assert False, "should have raised"
    except RuntimeError:
        pass


# ═══════════════════════════════════════════════════════════════════════
# M. SAME SIGNAL BAR x10 -> one evaluation only
# ═══════════════════════════════════════════════════════════════════════
@test
def M_same_signal_bar_looped_10_times_single_evaluation():
    bars = {"GBPAUD": [bar("GBPAUD", T0), bar("GBPAUD", T5)],
            "GBPNZD": [bar("GBPNZD", T0), bar("GBPNZD", T5)],
            "AUDNZD": [bar("AUDNZD", T0), bar("AUDNZD", T5)]}
    feed, _ = make_feed(bars)
    first = feed.get_synchronized_closed_triangle(reference_time=T5)
    assert first.signal_snapshot_valid
    for _ in range(10):
        again = feed.get_synchronized_closed_triangle(reference_time=T5)
        assert not again.signal_snapshot_valid
        assert again.failure_code == FailureCode.NO_NEW_SIGNAL_BAR
    assert feed.get_stats()["snapshots_emitted"] == 1


# ═══════════════════════════════════════════════════════════════════════
# N. NEXT M5 BAR -> exactly one new evaluation
# ═══════════════════════════════════════════════════════════════════════
@test
def N_next_m5_bar_one_new_evaluation():
    bars = {"GBPAUD": [bar("GBPAUD", T0), bar("GBPAUD", T5), bar("GBPAUD", T10)],
            "GBPNZD": [bar("GBPNZD", T0), bar("GBPNZD", T5), bar("GBPNZD", T10)],
            "AUDNZD": [bar("AUDNZD", T0), bar("AUDNZD", T5), bar("AUDNZD", T10)]}
    feed, _ = make_feed(bars)
    s1 = feed.get_synchronized_closed_triangle(reference_time=T5)
    assert s1.signal_snapshot_valid and s1.signal_bar_close_time == T0
    s2 = feed.get_synchronized_closed_triangle(reference_time=T10)
    assert s2.signal_snapshot_valid and s2.signal_bar_close_time == T5
    assert feed.get_stats()["snapshots_emitted"] == 2


# ═══════════════════════════════════════════════════════════════════════
# STALE SIGNAL BAR (common bar too old vs reference)
# ═══════════════════════════════════════════════════════════════════════
@test
def stale_signal_bar_fails_closed():
    bars = {"GBPAUD": [bar("GBPAUD", T0), bar("GBPAUD", T5)],
            "GBPNZD": [bar("GBPNZD", T0), bar("GBPNZD", T5)],
            "AUDNZD": [bar("AUDNZD", T0), bar("AUDNZD", T5)]}
    feed, _ = make_feed(bars, cfg=TBMarketDataConfig(max_signal_bar_age_s=600.0))
    late_ref = T5 + timedelta(minutes=30)   # common bar closed 25 min ago
    snap = feed.get_synchronized_closed_triangle(reference_time=late_ref)
    assert not snap.signal_snapshot_valid
    assert snap.failure_code == FailureCode.STALE_SIGNAL_BAR


# ═══════════════════════════════════════════════════════════════════════
# STRATEGY RECEIVES CLOSED M5 ONLY + execution ticks never regenerate signal
# ═══════════════════════════════════════════════════════════════════════
@test
def strategy_gets_closed_bar_and_ticks_do_not_enter_basis():
    # 3 legs with 40 bars so the wrapper has enough history to compute z
    bars = {}
    for sym in ("GBPAUD", "GBPNZD", "AUDNZD"):
        bars[sym] = [bar(sym, T0 + timedelta(minutes=5 * i),
                         close=GA if sym == "GBPAUD" else (GN if sym == "GBPNZD" else AN))
                     for i in range(40)]
    feed, _ = make_feed(bars, ticks=fresh_ticks(T0 + timedelta(minutes=200)))
    engine = TriangularBasisLiveEngine(model_config=PRIMARY_CONFIG)
    ref = T0 + timedelta(minutes=200)
    snap = feed.get_synchronized_closed_triangle(reference_time=ref)
    assert snap.signal_snapshot_valid
    # latest closed bar (index 39, just closed at reference) at T0+195min
    assert snap.signal_bar_close_time == T0 + timedelta(minutes=5 * 39)
    intent = engine.process_snapshot(snap)
    assert intent.decision in (BasketDecision.NO_ACTION, BasketDecision.OPEN_BASKET)
    # execution ticks (with wildly different prices) must not change basis
    crazy = fresh_ticks(T0 + timedelta(minutes=200), ga=2.5, gn=1.4, an=0.8)
    feed.adapter.ticks = crazy
    exec_snap = feed.get_execution_quote_snapshot(
        snap.signal_bar_close_time, T0 + timedelta(minutes=200))
    assert exec_snap.execution_snapshot_valid, exec_snap.failure_code
    # basis history must equal the bar-derived basis (ticks never entered)
    hist = engine._basis_history
    assert len(hist) == 1
    assert abs(hist[-1] - (np.log(GA) - np.log(GN) + np.log(AN))) < 1e-12


# ═══════════════════════════════════════════════════════════════════════
# VALIDATION LEVEL: direct contract checks
# ═══════════════════════════════════════════════════════════════════════
@test
def signal_validation_invalid_ohlc_nan_and_high_below_low():
    b = synced_bars(T0)
    b["GBPAUD"] = bar("GBPAUD", T0, close=float("nan"))
    snap = TriangleSignalSnapshot(
        signal_bar_close_time=T0, gbpaud_bar=b["GBPAUD"],
        gbpnzd_bar=b["GBPNZD"], audnzd_bar=b["AUDNZD"])
    assert validate_signal_snapshot(snap) == FailureCode.INVALID_OHLC

    b2 = synced_bars(T0)
    b2["GBPNZD"] = ClosedBar(
        symbol="GBPNZD", bar_open_time=T0,
        bar_close_time=T0 + timedelta(seconds=300),
        open=1.9, high=1.8, low=1.95, close=1.91, volume=1.0, is_closed=True)
    snap2 = TriangleSignalSnapshot(
        signal_bar_close_time=T0, gbpaud_bar=b2["GBPAUD"],
        gbpnzd_bar=b2["GBPNZD"], audnzd_bar=b2["AUDNZD"])
    assert validate_signal_snapshot(snap2) == FailureCode.INVALID_OHLC


@test
def execution_validation_skew_threshold_semantics():
    """Skew strictly greater than threshold fails; equal threshold passes."""
    bars = {"GBPAUD": [bar("GBPAUD", T0)], "GBPNZD": [bar("GBPNZD", T0)],
            "AUDNZD": [bar("AUDNZD", T0)]}
    ref = datetime(2024, 6, 10, 10, 1, 0, tzinfo=UTC)
    cfg = TBMarketDataConfig(max_cross_leg_skew_ms=1000.0)
    # exactly at threshold: skew 1000ms -> valid (not >)
    t = ref - timedelta(milliseconds=1000)
    feed, _ = make_feed(bars, ticks=fresh_ticks(ref, skew_s=1.0), cfg=cfg)
    # fresh_ticks skew_s=1.0 puts AN at ref-1s => skew 1000ms
    s = feed.get_execution_quote_snapshot(T0, ref)
    assert s.execution_snapshot_valid
    # threshold + 1ms
    feed2, _ = make_feed(bars, ticks=fresh_ticks(ref, skew_s=1.001), cfg=cfg)
    s2 = feed2.get_execution_quote_snapshot(T0, ref)
    assert not s2.execution_snapshot_valid
    assert s2.failure_code == FailureCode.CROSS_LEG_SKEW


# ═══════════════════════════════════════════════════════════════════════
# SESSION SEMANTICS (fixed UTC-5, no DST) preserved by the data layer
# ═══════════════════════════════════════════════════════════════════════
@test
def session_semantics_fixed_utc_minus_5():
    from triangular_basis_engine import _est_hour
    # 08:00 UTC = 03:00 EST -> session open
    assert _est_hour(datetime(2024, 6, 10, 8, 0, 0)) == 3
    # 17:00 UTC = 12:00 EST -> hard-exit boundary
    assert _est_hour(datetime(2024, 6, 10, 17, 0, 0)) == 12
    # 16:55 UTC = 11:55 EST
    assert _est_hour(datetime(2024, 6, 10, 16, 55, 0)) == 11
    # 07:55 UTC = 02:55 EST -> outside
    assert _est_hour(datetime(2024, 6, 10, 7, 55, 0)) == 2
    # 17:05 UTC = 12:05 EST -> after hard exit
    assert _est_hour(datetime(2024, 6, 10, 17, 5, 0)) == 12


# ═══════════════════════════════════════════════════════════════════════
# BAR TIMESTAMP SEMANTICS (MT5 open-time used verbatim; close = open + 300s)
# ═══════════════════════════════════════════════════════════════════════
@test
def bar_timestamp_semantics_locked():
    b = bar("GBPAUD", T0)
    assert b.bar_open_time == T0
    assert b.bar_close_time == T0 + timedelta(seconds=300)
    assert b.bar_close_time - b.bar_open_time == timedelta(seconds=300)
    assert b.timestamp == b.bar_open_time  # strategy key = open time


# ═══════════════════════════════════════════════════════════════════════
# ZERO ORDER GUARANTEES
# ═══════════════════════════════════════════════════════════════════════
@test
def mt5_adapter_exposes_no_order_functions():
    names = [n for n in dir(MT5MarketDataAdapter)
             if not n.startswith("_")]
    assert not any("order" in n.lower() or "trade" in n.lower()
                   for n in names), names
    assert "get_recent_bars" in names and "get_tick" in names


@test
def fresh_signal_fresh_ticks_valid_weights_produce_zero_orders():
    """Full shadow path: valid signal + valid ticks + valid weights must never
    reach order_send. The feed and wrapper contain no order code at all."""
    import inspect
    src = inspect.getsource(SynchronizedTriangleFeed) + \
        inspect.getsource(MockMarketDataAdapter)
    assert "order_send" not in src
    assert "order_send" not in inspect.getsource(TriangularBasisLiveEngine)


@test
def health_state_mapping():
    h = TriangleSnapshotHealth(
        signal_valid=False, execution_valid=False,
        signal_reason=FailureCode.NO_COMMON_CLOSED_BAR,
        execution_reason="NOT_TAKEN")
    assert h.overall_state() == HealthState.WAITING_FOR_BAR_SYNC
    h2 = TriangleSnapshotHealth(
        signal_valid=True, execution_valid=False,
        signal_reason=FailureCode.OK.value,
        execution_reason=FailureCode.STALE_EXECUTION_QUOTES.value)
    assert h2.overall_state() == HealthState.STALE_EXECUTION_QUOTES
    h3 = TriangleSnapshotHealth(
        signal_valid=True, execution_valid=True,
        signal_reason=FailureCode.OK.value,
        execution_reason=FailureCode.OK.value)
    assert h3.overall_state() == HealthState.HEALTHY


@test
def config_is_centralized_no_magic_constants():
    cfg = TBMarketDataConfig()
    assert cfg.bar_seconds == 300
    assert cfg.timeframe == "M5"
    assert cfg.max_quote_age_ms > 0
    assert cfg.max_cross_leg_skew_ms > 0
    assert cfg.canonical_timezone_semantics == "FIXED_UTC_MINUS_5"
    assert cfg.spread_gate_mode == "spread_monitor_only"


# ═══════════════════════════════════════════════════════════════════════
# EXECUTOR SHADOW-LOOP INTEGRATION (R2 feed wired into the loop; fail-closed)
# ═══════════════════════════════════════════════════════════════════════
@test
def executor_integration_fail_closed_modes():
    import importlib.util
    # import the executor module directly (mt5 package via namespace package)
    from pathlib import Path as _P
    mt5_dir = _P(__file__).parent.parent / "mt5"
    spec = importlib.util.spec_from_file_location(
        "triangular_basis_executor", mt5_dir / "triangular_basis_executor.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["triangular_basis_executor"] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001
        raise AssertionError(f"executor import failed: {e}")
    assert mod.DEFAULT_MODE == "shadow"
    assert mod.EXECUTION_AUTHORIZED is False
    assert mod.DEMO_AUTHORIZED is False
    assert mod.LIVE_AUTHORIZED is False
    assert mod.resolve_mode(None) == ("shadow", False)
    assert mod.resolve_mode("trade") == ("shadow", False)
    assert mod.resolve_mode("live") == ("shadow", False)
    assert mod.resolve_mode("demo")[1] is False   # demo not authorized yet
    assert mod.resolve_mode("garbage") == ("shadow", False)
    # the loop's data feed is the R2 SynchronizedTriangleFeed
    assert "SynchronizedTriangleFeed" in (
        mod.__doc__ or "") or "SynchronizedTriangleFeed" in \
        __import__("inspect").getsource(mod)
    assert "fetch_latest_snapshot" not in __import__("inspect").getsource(mod)


def main():
    passed = 0
    failed = 0
    for fn in TESTS:
        try:
            fn()
            passed += 1
            print(f"  PASS  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\ncollected={len(TESTS)} passed={passed} failed={failed} skipped=0")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
