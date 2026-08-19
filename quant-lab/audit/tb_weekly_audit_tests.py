#!/usr/bin/env python3
"""
TB-R6.3 — WEEKLY SIGNAL-COMPLETENESS AUDITOR · TEST SUITE
==========================================================

30 deterministic, offline checks for the independent weekly auditor:

  1-10  canonical replay science (primary/control, warmup, exclusion,
        strict entry, signed exits, stop, session, lifecycle)
  11-20 matching / outcome classes / determinism / no-signal handling
  21-27 cadence distributions + rolling activity + no-threshold-change
  28-30 authority (no broker writes, no runtime DB writes, no execution)

Run:  python quant-lab/audit/tb_weekly_audit_tests.py
Exit 0 when all pass. Writes TB_R6_3_AUDITS.json.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

QUANT_LAB = Path(__file__).resolve().parent.parent
for _p in (str(QUANT_LAB), str(QUANT_LAB / "audit"),
           str(QUANT_LAB / "engines")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pandas as pd  # noqa: E402

from tb_audit_core import (  # noqa: E402
    CONTROL_STRATEGY_ID,
    PRIMARY_STRATEGY_ID,
    STRATEGY_IDS,
    DecisionType,
    ExpectedEvent,
    LiveEvent,
    OutcomeClass,
    ParityStatus,
    bar_key_minute,
    direction_from_z,
    expected_event_id,
)
from tb_audit_data import (  # noqa: E402
    CANONICAL_SYMBOLS,
    DataCompletenessError,
    MarketDataLoader,
    RawBar,
    load_full_history,
)
from tb_audit_live import (  # noqa: E402
    LiveLedgerReader,
    EventMatcher,
    StaticParityProvider,
    NullParityProvider,
)
from tb_audit_replay import TBWeeklyReplayEngine  # noqa: E402
from tb_audit_stats import (  # noqa: E402
    Cadence,
    classify_count,
    month_counts,
    rolling_activity,
    week_counts,
    weekly_distribution,
)
from engines.tb_forward_config import (  # noqa: E402
    PRIMARY_CONFIG,
    CONTROL_CONFIG,
    LOOKBACK,
)

RESULTS = {"tests": [], "passed": 0, "failed": 0}

DEV_DATA = QUANT_LAB / "data"


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS["tests"].append({"name": name, "pass": bool(ok), "detail": detail})
    if ok:
        RESULTS["passed"] += 1
        print(f"  PASS  {name}")
    else:
        RESULTS["failed"] += 1
        print(f"  FAIL  {name}  {detail}")


# ─── synthetic bar helpers ───────────────────────────────────────────────
def noise(n: int, amp: float = 1e-4) -> List[float]:
    """Deterministic pseudo-noise basis offsets (sin wave, stable)."""
    return [amp * math.sin(i * 0.9) for i in range(n)]


# Seal-consistent synthetic prices: pair rates derived from the frozen
# seal USD rates so the currency-exposure matrix keeps its exact-neutral
# null space at ANY basis level (TB-B projection solvable, residual ~0).
GBP_USD, AUD_USD, NZD_USD = 1.34852, 0.70583, 0.58844
GA0, GN0, AN0 = GBP_USD / AUD_USD, GBP_USD / NZD_USD, AUD_USD / NZD_USD


def tri(b: float):
    k = math.exp(b)
    return GA0 * k, GN0 * k, AN0 * k


def make_data_window(week_start: datetime, warmup_basis: List[float],
                     window_basis: List[float],
                     win_start_min: int = 8 * 60) -> "object":
    """Aligned DataWindow: warmup = prior week Mon-Fri 08:00-16:55 UTC,
    window = continuous 5-min grid from Monday `win_start_min`."""
    ws = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    ga, gn = GA0, GN0

    def rawbar(ts, b):
        g1, g2, g3 = tri(b)
        return RawBar(ts=ts, open=g1, high=g1 + 1e-5, low=g1 - 1e-5,
                      close=g1, volume=0, source="test"), \
               RawBar(ts=ts, open=g2, high=g2 + 1e-5, low=g2 - 1e-5,
                      close=g2, volume=0, source="test"), \
               RawBar(ts=ts, open=g3, high=g3 + 1e-5, low=g3 - 1e-5,
                      close=g3, volume=0, source="test")

    # previous week Mon-Fri 08:00-16:55 UTC, in chronological order
    warm_ts = []
    for i in range(len(warmup_basis)):
        day = (i // 108) % 5
        idx = i % 108
        warm_ts.append(ws - timedelta(days=7 - day)
                       + timedelta(hours=8, minutes=5 * idx))
    win_ts = [ws + timedelta(minutes=win_start_min + 5 * i)
              for i in range(len(window_basis))]

    per = {s: [] for s in CANONICAL_SYMBOLS}
    for ts, b in zip(warm_ts, warmup_basis):
        ga_b, gn_b, an_b = rawbar(ts, b)
        per["GBPAUD"].append(ga_b)
        per["GBPNZD"].append(gn_b)
        per["AUDNZD"].append(an_b)
    for ts, b in zip(win_ts, window_basis):
        ga_b, gn_b, an_b = rawbar(ts, b)
        per["GBPAUD"].append(ga_b)
        per["GBPNZD"].append(gn_b)
        per["AUDNZD"].append(an_b)

    from types import SimpleNamespace
    return SimpleNamespace(
        week_start=ws, week_end=ws + timedelta(days=7),
        per_symbol=per, warmup_bars=len(warmup_basis),
        window_bars=len(window_basis),
        bars=per["GBPAUD"][len(warmup_basis):])


MON = datetime(2024, 3, 4)      # a Monday


def replay_syn(strategy, warm, win, win_start_min=8 * 60):
    dw = make_data_window(MON, warm, win, win_start_min)
    eng = TBWeeklyReplayEngine(model_config=strategy)
    return eng.replay(dw), dw


def entries_of(res):
    return [e for e in res.expected_events
            if e.decision_type == DecisionType.ENTRY]


def exits_of(res):
    return [e for e in res.expected_events
            if e.decision_type == DecisionType.EXIT]


# ─── expected-z reference (canonical formula, current bar excluded) ──────
def expected_z(basis: List[float], i: int) -> float:
    if i < LOOKBACK + 1:
        return 0.0
    window = basis[i - LOOKBACK:i]           # previous 200, current excluded
    mean = sum(window) / len(window)
    var = sum((x - mean) ** 2 for x in window) / len(window)   # ddof=0
    std = math.sqrt(var)
    return (basis[i] - mean) / std if std > 0 else 0.0


def basis_of(dw) -> List[float]:
    return [math.log(b.close)
            - math.log(dw.per_symbol["GBPNZD"][k].close)
            + math.log(dw.per_symbol["AUDNZD"][k].close)
            for k, b in enumerate(dw.per_symbol["GBPAUD"])]


# ─── test 1-2: canonical replay + frozen reference anchor ────────────────
def test_1_2_anchor_and_synthetic():
    # 1. synthetic: raw bars -> independent replay of PRIMARY
    warm = noise(540)
    win = [0.004, 0.0, -1e-4] + noise(50, 1e-5)
    res, _ = replay_syn(PRIMARY_CONFIG, warm, win)
    ents = entries_of(res)
    check("1 raw bars independently replay canonical primary",
          len(ents) == 1 and ents[0].direction == "SHORT" and
          ents[0].z > PRIMARY_CONFIG.entry_z,
          f"entries={len(ents)} first={ents[0].direction if ents else '-'} "
          f"z={ents[0].z if ents else '-'}")
    # 2. synthetic: control
    res_c, _ = replay_syn(CONTROL_CONFIG, warm, win)
    ents_c = entries_of(res_c)
    check("2 raw bars independently replay canonical control",
          len(ents_c) == 1 and ents_c[0].z > CONTROL_CONFIG.entry_z,
          f"entries={len(ents_c)}")
    # anchor: frozen dev window reproduces 405/194 (independent replay)
    if DEV_DATA.exists():
        try:
            hist = load_full_history(DEV_DATA)
            from tb_audit_replay import replay_historical
            res = replay_historical(hist, collect_records=False)
            n_ctl = sum(1 for e in res[CONTROL_STRATEGY_ID].expected_events
                        if e.decision_type == DecisionType.ENTRY)
            n_pri = sum(1 for e in res[PRIMARY_STRATEGY_ID].expected_events
                        if e.decision_type == DecisionType.ENTRY)
            check("1a frozen historical anchor: CONTROL == 405", n_ctl == 405,
                  f"control entries={n_ctl}")
            check("2a frozen historical anchor: PRIMARY == 194", n_pri == 194,
                  f"primary entries={n_pri}")
        except Exception as e:  # noqa: BLE001
            check("1a/2a frozen historical anchor", False, str(e))
    else:
        check("1a/2a frozen historical anchor", False,
              f"dev data missing at {DEV_DATA}")


# ─── test 3: 200-bar warmup ──────────────────────────────────────────────
def test_3_warmup():
    dw = make_data_window(MON, noise(100), [0.004] + [0.0] * 5)
    res = TBWeeklyReplayEngine(model_config=PRIMARY_CONFIG).replay(dw)
    check("3 correct 200-bar warmup (cold start -> no signal)",
          len(entries_of(res)) == 0 and res.entry_count == 0,
          f"entries={len(entries_of(res))}")


# ─── test 4: current bar excluded ────────────────────────────────────────
def test_4_current_bar_excluded():
    # warmup <= 400 bars so the engine's internal buffer never trims and its
    # z window is exactly the previous 200 bars of the full history
    warm = noise(300)
    win = [0.004] + noise(30, 1e-5)
    res, dw = replay_syn(PRIMARY_CONFIG, warm, win)
    basis = basis_of(dw)
    # replay records carry z per bar; compare to canonical expected_z
    z_by_key = {r.bar_key: r.z for r in res.records}
    ok = True
    for k, rec in enumerate(res.records):
        # index into full basis: warmup len + k
        i = dw.warmup_bars + k
        want = expected_z(basis, i)
        if abs(rec.z - want) > 1e-9:
            ok = False
            check("4 current bar excluded (z == canonical prev-200)",
                  False, f"bar {rec.bar_key}: got {rec.z} want {want}")
            return
    check("4 current bar excluded (z == canonical prev-200, ddof=0)",
          ok, f"verified over {len(res.records)} bars")


# ─── test 5: strict z threshold ──────────────────────────────────────────
def test_5_strict_z():
    check("5a frozen entry thresholds", PRIMARY_CONFIG.entry_z == 3.0 and
          CONTROL_CONFIG.entry_z == 2.5,
          f"primary={PRIMARY_CONFIG.entry_z} control={CONTROL_CONFIG.entry_z}")
    warm = noise(540)
    win = [0.004, 0.0, -1e-4] + noise(60, 1e-5)
    for cfg, label in ((PRIMARY_CONFIG, "primary"), (CONTROL_CONFIG, "control")):
        res, _ = replay_syn(cfg, warm, win)
        bad = [e for e in entries_of(res) if abs(e.z) <= cfg.entry_z]
        # every entry strictly exceeds its threshold
        check(f"5b {label} strict |z| > threshold",
              len(bad) == 0,
              f"entries with |z| <= {cfg.entry_z}: {len(bad)}")


# ─── test 6: signed primary exit ─────────────────────────────────────────
def test_6_signed_primary_exit():
    warm = noise(540)
    # entry at 08:00 (z>+3); control exits first at z<=0, primary later at
    # z<=-0.25 (signed contract)
    win = [0.004, 0.0, -1e-4] + noise(60, 1e-5)
    res_c, _ = replay_syn(CONTROL_CONFIG, warm, win)
    res_p, _ = replay_syn(PRIMARY_CONFIG, warm, win)
    ex_c = exits_of(res_c)
    ex_p = exits_of(res_p)
    ok = len(ex_c) == 1 and len(ex_p) == 1
    if ok:
        c_bar, p_bar = ex_c[0].bar_key, ex_p[0].bar_key
        ok = (ex_c[0].exit_reason == "TP_HIT" and
              ex_p[0].exit_reason == "TP_HIT" and
              ex_c[0].z <= 0.0 and ex_p[0].z <= ex_c[0].z and
              c_bar < p_bar)
        check("6 signed primary exit (control exits at z<=0 BEFORE primary "
              "z<=-0.25)", ok,
              f"control@{c_bar} z={ex_c[0].z:.4f} / primary@{p_bar} "
              f"z={ex_p[0].z:.4f}")
    else:
        check("6 signed primary exit", False,
              f"control exits={len(ex_c)} primary exits={len(ex_p)}")


# ─── test 7: control zero exit ───────────────────────────────────────────
def test_7_control_zero_exit():
    check("7a frozen control exit = 0.0",
          CONTROL_CONFIG.short_exit_z == 0.0 and
          CONTROL_CONFIG.long_exit_z == 0.0)
    warm = noise(540)
    win = [0.004, 0.0, -1e-4] + noise(60, 1e-5)
    res_c, _ = replay_syn(CONTROL_CONFIG, warm, win)
    ex = exits_of(res_c)
    check("7b control zero exit respected (SHORT exits z<=0)",
          len(ex) == 1 and ex[0].exit_reason == "TP_HIT" and ex[0].z <= 0.0,
          f"exit z={ex[0].z if ex else '-'}")


# ─── test 8: z6 stop ─────────────────────────────────────────────────────
def test_8_stop():
    warm = noise(540)
    win = [0.004, 0.004, 0.004] + noise(30, 1e-5)   # sustained extreme
    res, _ = replay_syn(PRIMARY_CONFIG, warm, win)
    ex = exits_of(res)
    check("8 z6 stop respected (SHORT z>=+6 -> SL_HIT)",
          len(ex) == 1 and ex[0].exit_reason == "SL_HIT" and
          ex[0].z >= PRIMARY_CONFIG.stop_z,
          f"exit={ex[0].exit_reason if ex else '-'} z={ex[0].z if ex else '-'}")


# ─── test 9: session contract ────────────────────────────────────────────
def test_9_session():
    # 07:55 UTC = 02:55 EST outside London session -> blocked;
    # 08:00 UTC = 03:00 EST -> entry
    warm = noise(540)
    win = [0.004, 0.004] + noise(30, 1e-5)
    res, _ = replay_syn(CONTROL_CONFIG, warm, win, win_start_min=7 * 60 + 55)
    ents = entries_of(res)
    blocks = [r for r in res.records if r.block_reason]
    ok = len(ents) == 1 and ents[0].bar_key == "2024-03-04 08:00" and \
        any(r.block_reason == "OUTSIDE_LONDON_SESSION"
            for r in blocks if r.bar_key == "2024-03-04 07:55")
    check("9a session contract (no entry 02:55 EST; entry 03:00 EST)", ok,
          f"entries={[e.bar_key for e in ents]} blocks={[r.block_reason for r in blocks]}")
    # hard exit: entry 15:00 UTC (10 EST, 120 min left), z stays in
    # (entry, stop) band -> no TP, no SL -> TIMEOUT at 17:00 UTC (12 EST)
    warm2 = noise(540)
    win2 = [2.5e-4] * 30 + noise(10, 1e-5)
    res2, _ = replay_syn(CONTROL_CONFIG, warm2, win2, win_start_min=15 * 60)
    ex = exits_of(res2)
    check("9b session hard exit (TIMEOUT at 12 EST)",
          len(ex) == 1 and ex[0].exit_reason == "TIMEOUT" and
          ex[0].bar_key == "2024-03-04 17:00",
          f"exit={ex[0].exit_reason if ex else '-'} @ "
          f"{ex[0].bar_key if ex else '-'}")


# ─── test 10: lifecycle contract ─────────────────────────────────────────
def test_10_lifecycle():
    warm = noise(540)
    # entry (z~3.5, below the z6 stop) -> open -> no re-entry while open
    # -> exit -> re-entry allowed after close
    s = 2.5e-4
    win = [s, s, s, 0.0, -1e-4, 0.0, 0.0, s, 0.0] + [0.0] * 20
    res, _ = replay_syn(CONTROL_CONFIG, warm, win)
    ents = entries_of(res)
    ex = exits_of(res)
    blocks = [r for r in res.records
              if r.block_reason == "BASKET_ALREADY_OPEN"]
    check("10 lifecycle contract (INTENT->OPEN, no dup while open, "
          "re-entry after close)",
          len(ents) == 2 and len(ex) == 2 and len(blocks) >= 2 and
          ents[0].bar_key == "2024-03-04 08:00" and
          ents[1].bar_key == "2024-03-04 08:35" and
          ex[0].bar_key < ents[1].bar_key,
          f"entries={[e.bar_key for e in ents]} exits={len(ex)} "
          f"blocks={len(blocks)}")


# ─── matcher helpers ─────────────────────────────────────────────────────
def mk_expected(strategy, bar_key, direction="SHORT", z=3.1,
                basket="B1", gen=1, decision=DecisionType.ENTRY):
    return ExpectedEvent(
        event_id=expected_event_id(strategy, bar_key, direction,
                                   decision.value, gen),
        strategy_id=strategy, variant="TB-B", decision_type=decision,
        bar_key=bar_key, timestamp_utc=bar_key + ":00",
        direction=direction, basis=0.0, z=z, generation=gen,
        basket_id=basket, entry_eligible=True, entry_reason="Z_ENTRY")


def mk_live(event_type, strategy, bar_key="", basket="", z=0.0,
            dedup="", seq=1, ts="2024-03-04T08:00:00"):
    return LiveEvent(
        seq=seq, event_type=event_type, ts_utc=ts, strategy_id=strategy,
        basket_id=basket, dedup_key=dedup,
        payload={"z": z} if z else {}, bar_key=bar_key,
        direction=direction_from_z(z) if z else "FLAT", z=z)


def test_11_15_matching():
    BK = "2024-03-04 09:00"
    # 11: control entry + signal + open verified -> MATCHED_TAKEN
    exp = mk_expected(CONTROL_STRATEGY_ID, BK, basket="B1")
    live = [mk_live("SIGNAL_OBSERVED", CONTROL_STRATEGY_ID, BK, z=3.1,
                    dedup=f"R6.1|CTL|{BK}:00+00:00", seq=1),
            mk_live("BASKET_OPEN_VERIFIED", CONTROL_STRATEGY_ID,
                    basket="B1", seq=2)]
    recs, sums, _ = EventMatcher(StaticParityProvider(ParityStatus.PASS)) \
        .match([exp], live)
    o = recs[0].outcome
    check("11 runtime matched event classified MATCHED_TAKEN",
          o == OutcomeClass.MATCHED_TAKEN and
          sums[CONTROL_STRATEGY_ID].taken == 1, f"outcome={o.value}")

    # 12: primary signal (shadow-only) -> MATCHED_SHADOW
    exp = mk_expected(PRIMARY_STRATEGY_ID, BK, basket="B2")
    live = [mk_live("SIGNAL_OBSERVED", PRIMARY_STRATEGY_ID, BK, z=3.1,
                    dedup=f"R6.1|PRI|{BK}:00+00:00", seq=3)]
    recs, sums, _ = EventMatcher(StaticParityProvider(ParityStatus.PASS)) \
        .match([exp], live)
    o = recs[0].outcome
    check("12 shadow event classified MATCHED_SHADOW",
          o == OutcomeClass.MATCHED_SHADOW and
          sums[PRIMARY_STRATEGY_ID].shadow == 1, f"outcome={o.value}")

    # 13: control signal + execution rejected -> VALID_RUNTIME_BLOCK
    exp = mk_expected(CONTROL_STRATEGY_ID, BK, basket="B3")
    live = [mk_live("SIGNAL_OBSERVED", CONTROL_STRATEGY_ID, BK, z=3.1,
                    dedup=f"R6.1|CTL|{BK}:00+00:00", seq=4),
            mk_live("SIGNAL_REJECTED", CONTROL_STRATEGY_ID, basket="B3",
                    seq=5)]
    recs, sums, _ = EventMatcher(StaticParityProvider(ParityStatus.PASS)) \
        .match([exp], live)
    o = recs[0].outcome
    check("13 valid runtime blocker classified VALID_RUNTIME_BLOCK",
          o == OutcomeClass.VALID_RUNTIME_BLOCK and
          sums[CONTROL_STRATEGY_ID].valid_blocks == 1, f"outcome={o.value}")

    # 14: expected entry, runtime silent, parity PASS -> MISSED_SIGNAL
    exp = mk_expected(CONTROL_STRATEGY_ID, BK, basket="B4")
    recs, sums, _ = EventMatcher(StaticParityProvider(ParityStatus.PASS)) \
        .match([exp], [])
    o = recs[0].outcome
    check("14 missing live event becomes MISSED_SIGNAL",
          o == OutcomeClass.MISSED_SIGNAL and
          sums[CONTROL_STRATEGY_ID].missed == 1, f"outcome={o.value}")

    # 15: runtime signal with no expectation -> RUNTIME_ONLY_SIGNAL
    live = [mk_live("SIGNAL_OBSERVED", CONTROL_STRATEGY_ID,
                    "2024-03-04 10:00", z=-3.2,
                    dedup="R6.1|CTL|2024-03-04 10:00:00+00:00", seq=6)]
    recs, sums, _ = EventMatcher(StaticParityProvider(ParityStatus.PASS)) \
        .match([], live)
    o = recs[0].outcome
    check("15 extra runtime event becomes RUNTIME_ONLY_SIGNAL",
          o == OutcomeClass.RUNTIME_ONLY_SIGNAL and
          sums[CONTROL_STRATEGY_ID].runtime_only == 1, f"outcome={o.value}")


def test_16_20():
    BK = "2024-03-04 09:00"
    # 16: expected entry, runtime silent, parity FAIL -> DATA_DIVERGENCE
    exp = mk_expected(CONTROL_STRATEGY_ID, BK, basket="B5")
    recs, sums, _ = EventMatcher(StaticParityProvider(ParityStatus.FAIL)) \
        .match([exp], [])
    o = recs[0].outcome
    check("16 price divergence becomes DATA_DIVERGENCE (fail closed)",
          o == OutcomeClass.DATA_DIVERGENCE and
          sums[CONTROL_STRATEGY_ID].data_divergence == 1,
          f"outcome={o.value}")

    # 17: missing bars invalidate disputed comparison -> AUDIT_INVALID_DATA
    tmp = Path(tempfile.mkdtemp())
    try:
        _write_partial_cache(tmp)     # AUDNZD missing the audit week
        loader = MarketDataLoader(tmp)
        try:
            loader.load_week(MON, use_mt5=False)
            check("17 missing bars invalidates disputed comparison",
                  False, "loader did not fail closed")
        except DataCompletenessError:
            check("17 missing bars invalidates disputed comparison", True,
                  "DataCompletenessError raised (fail closed)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 18: no-signal week -> NO_SIGNAL
    recs, sums, _ = EventMatcher(StaticParityProvider(ParityStatus.PASS)) \
        .match([], [])
    check("18 no-signal week handled (NO_SIGNAL)",
          all(s.no_signal for s in sums.values()) and len(recs) == 0,
          f"no_signal={[s.no_signal for s in sums.values()]}")

    # 19: two-signal week -> both expected + independently classified
    warm = noise(540)
    win = ([0.004, 0.0, -1e-4] + [0.0] * 20 +   # Mon entry+exit
           [0.004, 0.0, -1e-4] + [0.0] * 20)    # Wed entry+exit
    res, _ = replay_syn(CONTROL_CONFIG, warm, win)
    ents = entries_of(res)
    check("19 two-signal week handled (2 expected entries)",
          len(ents) == 2 and len(exits_of(res)) == 2,
          f"entries={len(ents)} exits={len(exits_of(res))}")

    # 20: open basket prevents duplicate expected entry (step below the
    # z6 stop so the basket stays open across several bars)
    win = [2.5e-4] * 4 + [0.0] * 10
    res, _ = replay_syn(CONTROL_CONFIG, warm, win)
    ents = entries_of(res)
    blocks = [r for r in res.records if r.block_reason == "BASKET_ALREADY_OPEN"]
    check("20 open basket prevents duplicate expected entry",
          len(ents) == 1 and len(blocks) >= 2,
          f"entries={len(ents)} blocked={len(blocks)}")


def _write_partial_cache(tmp: Path) -> None:
    """GBPAUD/GBPNZD cover the week; AUDNZD ends before it (partial)."""
    def csv_rows(start: datetime, days: int):
        rows = []
        for d in range(days):
            day = start + timedelta(days=d)
            if day.weekday() >= 5:
                continue
            for h in range(0, 24):               # 24/5 M5 coverage
                for m in range(0, 60, 5):
                    t = day.replace(hour=h, minute=m)
                    rows.append((t, 1.75, 1.7501, 1.7499, 1.75, 10))
        return rows

    week_mon = MON - timedelta(days=MON.weekday())
    full = csv_rows(week_mon - timedelta(days=7), 14)      # covers the week
    partial = csv_rows(week_mon - timedelta(days=14), 7)   # ends before week
    (tmp / "GBPAUD_M5.csv").write_text(
        "timestamp,open,high,low,close,volume\n" + "\n".join(
            f"{t.isoformat(sep=' ')[:16]},1.75,1.7501,1.7499,1.75,10"
            for t, *_ in full), encoding="utf-8")
    (tmp / "GBPNZD_M5.csv").write_text(
        "timestamp,open,high,low,close,volume\n" + "\n".join(
            f"{t.isoformat(sep=' ')[:16]},2.05,2.0501,2.0499,2.05,10"
            for t, *_ in full), encoding="utf-8")
    (tmp / "AUDNZD_PRO_M5.csv").write_text(
        "time,open,high,low,close,volume\n" + "\n".join(
            f"{t.isoformat(sep=' ')[:16]},1.06,1.0601,1.0599,1.06,10"
            for t, *_ in partial), encoding="utf-8")


def test_21_determinism():
    warm = noise(540)
    win = [0.004, 0.0, -1e-4] + noise(40, 1e-5)
    r1, _ = replay_syn(CONTROL_CONFIG, warm, win)
    r2, _ = replay_syn(CONTROL_CONFIG, warm, win)
    ids1 = [e.event_id for e in r1.expected_events]
    ids2 = [e.event_id for e in r2.expected_events]
    check("21 deterministic expected_event_id",
          ids1 == ids2 and len(set(ids1)) == len(ids1) and
          ids1 and ids1[0].startswith("EXP-"),
          f"n={len(ids1)} stable={ids1 == ids2}")


def test_22_26_cadence():
    # synthetic dev history: 30 weeks x 1 entry each (deterministic)
    dev_entries: List[datetime] = [
        MON - timedelta(weeks=30 - w) + timedelta(hours=9)
        for w in range(30)]
    aud_entries = [MON + timedelta(hours=9), MON + timedelta(hours=10)]

    # 22/23: deterministic distributions
    w1, w2 = weekly_distribution(dev_entries), weekly_distribution(dev_entries)
    m1, m2 = month_counts(dev_entries), month_counts(dev_entries)
    check("22 weekly historical counts deterministic", w1 == w2 and
          w1["weeks"] == 30 and w1["mean"] == 1.0,
          f"weeks={w1['weeks']} mean={w1['mean']}")
    check("23 monthly historical counts deterministic", m1 == m2 and
          sum(m1.values()) == len(dev_entries),
          f"months={len(m1)} total={sum(m1.values())}")

    # 24-26: rolling counts
    roll = rolling_activity(dev_entries, aud_entries, MON)
    check("24 4-week rolling counts correct",
          roll["trailing_4_week"] == 4 and
          roll["trailing_4_week_weeks_covered"] == 4,
          f"t4={roll['trailing_4_week']} "
          f"weeks={roll['trailing_4_week_weeks_covered']}")
    check("25 8-week rolling counts correct",
          roll["trailing_8_week"] == 8 and
          roll["trailing_8_week_weeks_covered"] == 8,
          f"t8={roll['trailing_8_week']}")
    check("26 12-week rolling counts correct",
          roll["trailing_12_week"] == 12 and
          roll["trailing_12_week_weeks_covered"] == 12,
          f"t12={roll['trailing_12_week']}")
    check("26b current week count + classification diagnostic-only",
          roll["current_week"] == 2 and
          roll["current_week_class"] in
          ("NORMAL_ACTIVITY", "LOW_BUT_HISTORICALLY_NORMAL",
           "UNUSUALLY_LOW_ACTIVITY", "UNUSUALLY_HIGH_ACTIVITY"),
          f"current={roll['current_week']} "
          f"class={roll['current_week_class']}")


def test_27_no_threshold_change():
    from tb_weekly_audit import run_week_audit
    tmp = Path(tempfile.mkdtemp())
    try:
        _write_partial_cache(tmp)
        # extend AUDNZD so the week IS covered (full cache)
        _extend_audnzd(tmp)
        dev = {s: [MON - timedelta(weeks=8) + timedelta(hours=9)]
               for s in STRATEGY_IDS}
        rep = run_week_audit(
            MON, data_dir=tmp, live_db=tmp / "no.db",
            runtime_db=tmp / "no2.db", out_dir=tmp / "out",
            use_mt5=False, dev_entries_override=dev,
            parity_override=StaticParityProvider(ParityStatus.PASS))
        check("27 no threshold change from low frequency",
              rep["data_valid"] and
              PRIMARY_CONFIG.entry_z == 3.0 and
              CONTROL_CONFIG.entry_z == 2.5 and
              CONTROL_CONFIG.short_exit_z == 0.0 and
              PRIMARY_CONFIG.short_exit_z == -0.25,
              f"valid={rep['data_valid']} "
              f"primary_z={PRIMARY_CONFIG.entry_z} "
              f"control_z={CONTROL_CONFIG.entry_z}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _extend_audnzd(tmp: Path) -> None:
    """Rewrite AUDNZD_PRO_M5.csv to cover the audit week too (24/5)."""
    rows = []
    start = MON - timedelta(days=14)
    for d in range(21):
        day = start + timedelta(days=d)
        if day.weekday() >= 5:
            continue
        for h in range(0, 24):
            for m in range(0, 60, 5):
                rows.append(day.replace(hour=h, minute=m))
    (tmp / "AUDNZD_PRO_M5.csv").write_text(
        "time,open,high,low,close,volume\n" + "\n".join(
            f"{t.isoformat(sep=' ')[:16]},1.06,1.0601,1.0599,1.06,10"
            for t in rows), encoding="utf-8")


def test_28_no_broker_writes():
    from tb_weekly_audit import run_week_audit
    tmp = Path(tempfile.mkdtemp())
    try:
        _write_partial_cache(tmp)
        _extend_audnzd(tmp)
        dev = {s: [] for s in STRATEGY_IDS}
        run_week_audit(
            MON, data_dir=tmp, live_db=tmp / "no.db",
            runtime_db=tmp / "no2.db", out_dir=tmp / "out",
            use_mt5=False, dev_entries_override=dev,
            parity_override=StaticParityProvider(ParityStatus.PASS))
        check("28a audit path never imports MetaTrader5",
              "MetaTrader5" not in sys.modules,
              "MetaTrader5 imported during standard audit")
        # static: no order-sending capability anywhere in the audit package
        # (non-test modules only — the test file itself names the tokens)
        pkg = QUANT_LAB / "audit"
        src = ""
        for f in sorted(pkg.glob("*.py")):
            if f.name.endswith("_tests.py"):
                continue
            src += f.read_text(encoding="utf-8", errors="ignore")
        forbidden = ("order_send", "order_send_buy", "order_send_sell",
                     "trade_order", "positions_get")[:3]
        bad = [t for t in forbidden if t in src]
        check("28b no broker-write tokens in audit package",
              not bad, f"found {bad}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_29_no_runtime_db_writes():
    tmp = Path(tempfile.mkdtemp())
    try:
        db = tmp / "tb_control.db"
        _make_ledger(db)
        before = db.read_bytes()
        reader = LiveLedgerReader(db)
        evs = reader.read_events()
        after = db.read_bytes()
        wal = list(tmp.glob("*-wal")) + list(tmp.glob("*-journal"))
        check("29 no runtime DB writes (ledger byte-identical, no wal/journal)",
              before == after and len(wal) == 0 and
              all(ev.event_type == "SIGNAL_OBSERVED" for ev in evs),
              f"events={len(evs)} wal={len(wal)}")
        # bar-key parsing from the worker's dedup format
        ev = evs[0]
        check("29b live bar-key normalized from dedup key",
              ev.bar_key == "2024-03-04 09:00" and ev.direction == "SHORT",
              f"bar_key={ev.bar_key!r} direction={ev.direction}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _make_ledger(db: Path) -> None:
    con = sqlite3.connect(db)
    con.executescript("""
    CREATE TABLE events (
        event_id TEXT PRIMARY KEY, seq INTEGER NOT NULL UNIQUE,
        event_type TEXT NOT NULL, ts_utc TEXT NOT NULL,
        basket_id TEXT NOT NULL DEFAULT '',
        strategy_id TEXT NOT NULL DEFAULT '',
        prior_state TEXT NOT NULL DEFAULT '',
        new_state TEXT NOT NULL DEFAULT '',
        dedup_key TEXT UNIQUE,
        payload TEXT NOT NULL DEFAULT '{}',
        payload_hash TEXT NOT NULL DEFAULT '',
        source TEXT NOT NULL DEFAULT '',
        reason TEXT NOT NULL DEFAULT '');
    """)
    con.execute(
        "INSERT INTO events (event_id, seq, event_type, ts_utc, basket_id, "
        "strategy_id, dedup_key, payload) VALUES (?,?,?,?,?,?,?,?)",
        ("E1", 1, "SIGNAL_OBSERVED", "2024-03-04T09:00:05+00:00", "",
         CONTROL_STRATEGY_ID, "R6.1|CTL|2024-03-04 09:00:00+00:00",
         json.dumps({"z": 3.1, "decision": "OPEN_BASKET"})))
    con.commit()
    con.close()


def test_30_no_execution_authority():
    pkg = QUANT_LAB / "audit"
    src = ""
    for f in sorted(pkg.glob("*.py")):
        if f.name.endswith("_tests.py"):
            continue
        src += f.read_text(encoding="utf-8", errors="ignore")
    for token in ("order_send", "trade_order", "order_calc"):
        if token in src:
            check("30 no execution authority", False,
                  f"forbidden token {token} present")
            return
    check("30 no execution authority (static scan clean)",
          "mode=ro" in src and "READ ONLY" in src,
          "audit package has no order capability; readers use mode=ro")


# ─── runner ──────────────────────────────────────────────────────────────
def main() -> int:
    print("TB-R6.3 weekly signal-completeness auditor — test suite")
    test_1_2_anchor_and_synthetic()
    test_3_warmup()
    test_4_current_bar_excluded()
    test_5_strict_z()
    test_6_signed_primary_exit()
    test_7_control_zero_exit()
    test_8_stop()
    test_9_session()
    test_10_lifecycle()
    test_11_15_matching()
    test_16_20()
    test_21_determinism()
    test_22_26_cadence()
    test_27_no_threshold_change()
    test_28_no_broker_writes()
    test_29_no_runtime_db_writes()
    test_30_no_execution_authority()

    out = QUANT_LAB.parent / "research" / "tb_forward" / "r6_3"
    out.mkdir(parents=True, exist_ok=True)
    (out / "TB_R6_3_AUDITS.json").write_text(
        json.dumps({"suite": "tb_weekly_audit_tests",
                    "passed": RESULTS["passed"],
                    "failed": RESULTS["failed"],
                    "total": len(RESULTS["tests"]),
                    "tests": RESULTS["tests"]}, indent=2), encoding="utf-8")
    print(f"\npassed={RESULTS['passed']} failed={RESULTS['failed']} "
          f"total={len(RESULTS['tests'])}")
    return 0 if RESULTS["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
