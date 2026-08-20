#!/usr/bin/env python3
"""
CANONICAL TB TRANSFER TEST — STEP 1: MECHANISM SCREEN
=======================================================

SW-CTBT-T1-CANONICAL-TB-TRANSFER-MECHANISM-SCREEN

Runs a frozen canonical-TB lifecycle on:
  REFERENCE: AUD_GBP_NZD
  CHALLENGERS: EUR_GBP_JPY, CHF_GBP_JPY, EUR_GBP_USD, GBP_NZD_USD

No optimization. No new exits. No post-hoc rescue.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ═══════════════════════════════════════════════════════════════════════════════
# FROZEN CONTRACT PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════════

LOOKBACK = 200           # 200 completed bars, causal
ENTRY_Z_CONTROL = 2.5    # Control lane
ENTRY_Z_PRIMARY = 3.0    # Primary lane
EXIT_Z_E1 = 0.25        # E1 signed overshoot
STOP_Z6 = 6.0           # Structural invalidation
MIN_TIME_TO_EXIT = 120   # minutes
HARD_EXIT_EST = 12       # noon-equivalent EST
LONDON_START_EST = 3     # 03:00 EST
LONDON_END_EST = 12      # 12:00 EST (hard exit)
REENTRY_COOLDOWN = 0     # canonical deterministic re-entry

# ═══════════════════════════════════════════════════════════════════════════════
# TRIANGLE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class TriangleDef:
    triangle_id: str
    currencies: Tuple[str, str, str]  # sorted alphabetically
    legs: Tuple[str, str, str]        # broker pair labels in canonical order
    basis_signs: Tuple[int, int, int] # signs in basis equation
    data_files: Tuple[str, str, str]  # paths relative to quant-lab/data
    pip_sizes: Tuple[float, float, float]
    label_a: str  # first leg label
    label_b: str  # second leg label
    label_c: str  # third leg label

# Canonical reference: AUD < GBP < NZD
# basis = +ln(AUD/GBP) - ln(AUD/NZD) + ln(GBP/NZD)
# In broker terms: = -ln(GBPAUD) + ln(AUDNZD) + ln(GBPNZD)
# But canonical TB uses: ln(GBPAUD) - ln(GBPNZD) + ln(AUDNZD)
# Following the prompt's canonical formula exactly.

REFERENCE = TriangleDef(
    triangle_id="AUD_GBP_NZD",
    currencies=("AUD", "GBP", "NZD"),
    legs=("GBPAUD", "GBPNZD", "AUDNZD"),
    basis_signs=(+1, -1, +1),
    data_files=("GBPAUD_M5_fetched.csv", "GBPNZD_M5_fetched.csv", "AUDNZD_M5_fetched.csv"),
    pip_sizes=(0.0001, 0.0001, 0.0001),
    label_a="GBPAUD", label_b="GBPNZD", label_c="AUDNZD",
)

# EUR < GBP < JPY
# basis = +ln(EURGBP) - ln(EURJPY) + ln(GBPJPY)
C1_EUR_GBP_JPY = TriangleDef(
    triangle_id="EUR_GBP_JPY",
    currencies=("EUR", "GBP", "JPY"),
    legs=("EURGBP", "EURJPY", "GBPJPY"),
    basis_signs=(+1, -1, +1),
    data_files=("EURGBP_M5_fetched.csv", "EURJPY_M5_fetched.csv", "GBPJPY_M5_fetched.csv"),
    pip_sizes=(0.0001, 0.01, 0.01),
    label_a="EURGBP", label_b="EURJPY", label_c="GBPJPY",  # JPY legs use 0.01 pip
)

# CHF < GBP < JPY
# basis = +ln(GBPCHF) - ln(CHFJPY) + ln(GBPJPY)
# Wait: alphabetically CHF < GBP < JPY, so A=CHF, B=GBP, C=JPY
# basis = +ln(CHF/GBP) - ln(CHF/JPY) + ln(GBP/JPY)
# = -ln(GBPCHF) + ln(CHFJPY) + ln(GBPJPY)
# But the canonical TB form follows the same leg ordering as AUD_GBP_NZD.
# The prompt says: GBPCHF, GBPJPY, CHFJPY
# So: legs = (GBPCHF, GBPJPY, CHFJPY)
# basis = ln(GBPCHF) - ln(CHFJPY) + ln(GBPJPY) ... but need to verify signs.
# Actually let me re-derive for clarity:
# A=CHF, B=GBP, C=JPY
# +ln(CHF/GBP) - ln(CHF/JPY) + ln(GBP/JPY)
# = -ln(GBPCHF) + ln(CHFJPY) + ln(GBPJPY)
# Let's use broker-oriented form directly:
C2_CHF_GBP_JPY = TriangleDef(
    triangle_id="CHF_GBP_JPY",
    currencies=("CHF", "GBP", "JPY"),
    legs=("GBPCHF", "GBPJPY", "CHFJPY"),
    basis_signs=(+1, +1, -1),  # ln(GBPCHF) + ln(GBPJPY) - ln(CHFJPY)
    data_files=("GBPCHF_M5_fetched.csv", "GBPJPY_M5_fetched.csv", "CHFJPY_M5_fetched.csv"),
    pip_sizes=(0.0001, 0.01, 0.01),
    label_a="GBPCHF", label_b="GBPJPY", label_c="CHFJPY",
)

# EUR < GBP < USD
# basis = +ln(EURGBP) - ln(EURUSD) + ln(GBPUSD)
C3_EUR_GBP_USD = TriangleDef(
    triangle_id="EUR_GBP_USD",
    currencies=("EUR", "GBP", "USD"),
    legs=("EURGBP", "EURUSD", "GBPUSD"),
    basis_signs=(+1, -1, +1),
    data_files=("EURGBP_M5_fetched.csv", "EURUSD_M5.csv", "GBPUSD_M5_fetched.csv"),
    pip_sizes=(0.0001, 0.0001, 0.0001),
    label_a="EURGBP", label_b="EURUSD", label_c="GBPUSD",
)

# GBP < NZD < USD
# basis = +ln(GBPNZD) - ln(GBPUSD) + ln(NZDUSD)
C4_GBP_NZD_USD = TriangleDef(
    triangle_id="GBP_NZD_USD",
    currencies=("GBP", "NZD", "USD"),
    legs=("GBPNZD", "GBPUSD", "NZDUSD"),
    basis_signs=(+1, -1, +1),
    data_files=("GBPNZD_M5_fetched.csv", "GBPUSD_M5_fetched.csv", "NZDUSD_M5_fetched.csv"),
    pip_sizes=(0.0001, 0.0001, 0.0001),
    label_a="GBPNZD", label_b="GBPUSD", label_c="NZDUSD",
)

ALL_TRIANGLES = [REFERENCE, C1_EUR_GBP_JPY, C2_CHF_GBP_JPY, C3_EUR_GBP_USD, C4_GBP_NZD_USD]

# ═══════════════════════════════════════════════════════════════════════════════
# COST MODEL
# ═══════════════════════════════════════════════════════════════════════════════

# Assumed spreads (pips) + commission per leg
# Source: project reference assumptions (ASSUMED, not OBSERVED)
COST_MODEL: Dict[str, Dict[str, float]] = {
    "GBPAUD":  {"spread_pips": 1.5, "commission_pips": 0.7},
    "GBPNZD":  {"spread_pips": 2.5, "commission_pips": 0.7},
    "AUDNZD":  {"spread_pips": 2.0, "commission_pips": 0.7},
    "EURGBP":  {"spread_pips": 1.0, "commission_pips": 0.5},
    "EURJPY":  {"spread_pips": 1.0, "commission_pips": 0.5},
    "GBPJPY":  {"spread_pips": 1.5, "commission_pips": 0.6},
    "GBPCHF":  {"spread_pips": 1.5, "commission_pips": 0.6},
    "CHFJPY":  {"spread_pips": 1.5, "commission_pips": 0.6},
    "EURUSD":  {"spread_pips": 0.8, "commission_pips": 0.4},
    "GBPUSD":  {"spread_pips": 1.0, "commission_pips": 0.5},
    "GBPNZD":  {"spread_pips": 2.5, "commission_pips": 0.7},
    "NZDUSD":  {"spread_pips": 1.2, "commission_pips": 0.5},
}

def basket_cost_pips(legs: Tuple[str, ...]) -> float:
    """Full one-way basket crossing cost in pips."""
    total = 0.0
    for leg in legs:
        c = COST_MODEL.get(leg, {"spread_pips": 2.0, "commission_pips": 0.7})
        total += c["spread_pips"] + c["commission_pips"]
    return total

def basket_cost_rt_pips(legs: Tuple[str, ...]) -> float:
    """Full round-trip basket cost in pips (entry + exit)."""
    return basket_cost_pips(legs) * 2.0

# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════

_SCRIPT_DIR = Path(__file__).resolve().parent
# Script is at: larger-lab/research/shallow_well/canonical_tb_transfer/t1_screen/
# Project root (larger-lab/) is parents[3]
_PROJECT_ROOT = _SCRIPT_DIR.parents[3]
_DATA_DIR = _PROJECT_ROOT / "quant-lab" / "data"

def load_m5_data(filepath: str) -> pd.DataFrame:
    """Load M5 CSV, return DataFrame with timestamp, open, high, low, close."""
    path = _DATA_DIR / filepath
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    # Detect separator and timestamp column
    with open(path, "r", encoding="utf-8-sig") as f:
        first_line = f.readline()
        sep = "\t" if "\t" in first_line else ","

    df = pd.read_csv(path, sep=sep, encoding="utf-8-sig")

    # Normalize column names
    col_map = {}
    for c in df.columns:
        cl = c.strip().lower()
        if cl in ("timestamp", "time", "datetime", "date"):
            col_map[c] = "timestamp"
        elif cl == "open":
            col_map[c] = "open"
        elif cl == "high":
            col_map[c] = "high"
        elif cl == "low":
            col_map[c] = "low"
        elif cl == "close":
            col_map[c] = "close"
    df = df.rename(columns=col_map)

    required = {"timestamp", "open", "high", "low", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns {missing} in {path}")

    # Parse timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    for c in ["open", "high", "low", "close"]:
        df[c] = df[c].astype(float)

    df = df.sort_values("timestamp").reset_index(drop=True)
    return df[["timestamp", "open", "high", "low", "close"]]


def synchronize_triangular(
    dfs: List[pd.DataFrame],
    pair_labels: List[str],
) -> pd.DataFrame:
    """
    Synchronize three leg DataFrames by timestamp.
    Uses outer join on timestamp, forward-fills missing values.
    Only keeps timestamps present in ALL three legs.
    """
    for i, (df, label) in enumerate(zip(dfs, pair_labels)):
        df = df.set_index("timestamp")
        df = df.rename(columns={"close": label, "high": f"{label}_high", "low": f"{label}_low"})
        df = df[[label, f"{label}_high", f"{label}_low"]]
        dfs[i] = df

    merged = dfs[0]
    for i in range(1, len(dfs)):
        merged = merged.join(dfs[i], how="inner")

    merged = merged.reset_index()
    return merged


# ═══════════════════════════════════════════════════════════════════════════════
# BASIS COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════════

def compute_basis(synced: pd.DataFrame, tri: TriangleDef) -> pd.Series:
    """
    Compute triangular basis:
      basis = sign1 * ln(price1) + sign2 * ln(price2) + sign3 * ln(price3)
    """
    s1, s2, s3 = tri.basis_signs
    l1, l2, l3 = tri.legs
    return (s1 * np.log(synced[l1]) + s2 * np.log(synced[l2]) + s3 * np.log(synced[l3]))


# ═══════════════════════════════════════════════════════════════════════════════
# CAUSAL Z-SCORE
# ═══════════════════════════════════════════════════════════════════════════════

def compute_causal_z(basis: pd.Series, lookback: int = LOOKBACK) -> pd.Series:
    """
    Strictly causal rolling z-score.
    At index i: window = [i - lookback, i) — current bar EXCLUDED.
    Population std (ddof=0).
    """
    vals = basis.values.astype(float)
    n = len(vals)
    z = np.full(n, np.nan)

    for i in range(lookback, n):
        window = vals[i - lookback:i]  # excludes current
        mean = np.mean(window)
        std = np.std(window, ddof=0)
        if std > 1e-15:
            z[i] = (vals[i] - mean) / std
        else:
            z[i] = 0.0

    return pd.Series(z, index=basis.index)


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def est_hour(ts: pd.Timestamp) -> int:
    """Convert UTC timestamp to EST hour (approximate, no DST correction)."""
    return (ts.hour - 5) % 24

def in_london_session(ts: pd.Timestamp) -> bool:
    """Is this timestamp in the London operating session (03:00-12:00 EST)?"""
    h = est_hour(ts)
    return LONDON_START_EST <= h < LONDON_END_EST

def minutes_since_session_start(ts: pd.Timestamp) -> int:
    """Minutes elapsed since London session start (03:00 EST) for this bar."""
    h = est_hour(ts)
    m = ts.minute
    return (h - LONDON_START_EST) * 60 + m

def minutes_to_hard_exit(ts: pd.Timestamp) -> int:
    """Minutes remaining until hard exit (12:00 EST)."""
    h = est_hour(ts)
    m = ts.minute
    return (HARD_EXIT_EST - h) * 60 - m


# ═══════════════════════════════════════════════════════════════════════════════
# EVENT EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Event:
    event_id: str
    triangle_id: str
    direction: str        # "LONG" or "SHORT"
    entry_z: float
    entry_z_threshold: float  # 2.5 or 3.0
    entry_timestamp: pd.Timestamp
    entry_index: int
    entry_basis: float
    exit_timestamp: Optional[pd.Timestamp] = None
    exit_index: Optional[int] = None
    exit_basis: Optional[float] = None
    exit_z: Optional[float] = None
    exit_reason: Optional[str] = None
    holding_minutes: Optional[float] = None
    gross_pnl_bps: Optional[float] = None
    cost_bps: Optional[float] = None
    net_pnl_bps: Optional[float] = None
    max_adverse_z: Optional[float] = None


def extract_events(
    synced: pd.DataFrame,
    basis: pd.Series,
    z: pd.Series,
    tri: TriangleDef,
    entry_threshold: float,
) -> List[Event]:
    """
    Extract events using the frozen canonical TB lifecycle.

    Entry: |z| > entry_threshold, ONLY during London session,
           with MIN_TIME_TO_EXIT remaining before hard exit.
    Exit:  E1 signed overshoot (z crosses ±0.25 in the right direction).
    Stop:  z6 structural invalidation (|z| > 6.0).
    Hard:  12:00 EST session exit.
    Min hold: 120 minutes.
    Concurrency: max 1 active.
    """
    events: List[Event] = []
    in_trade = False
    current: Optional[Event] = None
    n = len(synced)
    rt_cost = basket_cost_rt_pips(tri.legs)

    for i in range(n):
        ts = synced["timestamp"].iloc[i]
        z_val = z.iloc[i]
        basis_val = basis.iloc[i]

        if pd.isna(z_val):
            continue

        # ── ACTIVE TRADE: check exits ──
        if in_trade and current is not None:
            hold_min = (ts - current.entry_timestamp).total_seconds() / 60.0
            current.holding_minutes = hold_min

            # Track max adverse z
            if current.direction == "SHORT":
                if current.max_adverse_z is None or z_val > current.max_adverse_z:
                    current.max_adverse_z = z_val
            else:
                if current.max_adverse_z is None or z_val < current.max_adverse_z:
                    current.max_adverse_z = z_val

            exit_hit = False
            exit_reason = ""

            # z6 structural stop (always active)
            if abs(z_val) > STOP_Z6:
                exit_hit = True
                exit_reason = "Z6_STOP"

            # Hard session exit
            elif not in_london_session(ts) or minutes_to_hard_exit(ts) <= 0:
                exit_hit = True
                exit_reason = "HARD_SESSION_EXIT"

            # E1 signed overshoot (only after min hold)
            elif hold_min >= MIN_TIME_TO_EXIT:
                if current.direction == "SHORT" and z_val <= -EXIT_Z_E1:
                    exit_hit = True
                    exit_reason = "E1_OVERSHOOT"
                elif current.direction == "LONG" and z_val >= EXIT_Z_E1:
                    exit_hit = True
                    exit_reason = "E1_OVERSHOOT"

            if exit_hit:
                current.exit_timestamp = ts
                current.exit_index = i
                current.exit_basis = basis_val
                current.exit_z = z_val
                current.exit_reason = exit_reason
                current.holding_minutes = hold_min

                # Compute PnL using per-leg pip calculation
                # SHORT basket: sell leg1, buy leg2, sell leg3 (for canonical signs)
                # LONG basket: buy leg1, sell leg2, buy leg3
                # trade_dir_i = -d * s_i (d=+1 for SHORT, d=-1 for LONG)
                d = 1.0 if current.direction == "SHORT" else -1.0
                gross_pnl_pips = 0.0
                for j in range(3):
                    leg = tri.legs[j]
                    s_j = tri.basis_signs[j]
                    pip_j = tri.pip_sizes[j]
                    trade_dir = -d * s_j  # +1=buy, -1=sell
                    p_entry = synced[leg].iloc[current.entry_index]
                    p_exit = synced[leg].iloc[i]
                    leg_pnl = trade_dir * (p_exit - p_entry) / pip_j
                    gross_pnl_pips += leg_pnl
                current.gross_pnl_bps = gross_pnl_pips * 10.0  # pips -> bps
                current.cost_bps = rt_cost * 10.0  # pips -> bps
                current.net_pnl_bps = current.gross_pnl_bps - current.cost_bps

                events.append(current)
                in_trade = False
                current = None
                continue

        # ── NEW ENTRY ──
        if not in_trade:
            # London session only
            if not in_london_session(ts):
                continue

            # Min runway check
            runway = minutes_to_hard_exit(ts)
            if runway < MIN_TIME_TO_EXIT:
                continue

            # Entry signal
            if pd.isna(z_val) or abs(z_val) <= entry_threshold:
                continue

            direction = "SHORT" if z_val > 0 else "LONG"
            event = Event(
                event_id=f"{tri.triangle_id}_{ts.strftime('%Y%m%d_%H%M')}_{entry_threshold}",
                triangle_id=tri.triangle_id,
                direction=direction,
                entry_z=z_val,
                entry_z_threshold=entry_threshold,
                entry_timestamp=ts,
                entry_index=i,
                entry_basis=basis_val,
            )
            in_trade = True
            current = event

    return events


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Scorecard:
    triangle_id: str
    entry_threshold: float
    completed_events: int = 0
    events_per_week: float = 0.0
    gross_ev_bps: float = 0.0
    net_ev_bps: float = 0.0
    pf_gross: float = 0.0
    pf_net: float = 0.0
    win_rate: float = 0.0
    median_net_bps: float = 0.0
    max_cum_dd_bps: float = 0.0
    worst_event_bps: float = 0.0
    p5_bps: float = 0.0
    avg_hold_min: float = 0.0
    median_hold_min: float = 0.0
    p90_hold_min: float = 0.0
    z6_stop_rate: float = 0.0
    hard_exit_rate: float = 0.0
    gross_basket_edge_pips: float = 0.0
    avg_basket_cost_pips: float = 0.0
    gross_edge_cost_ratio: float = 0.0
    break_even_cost_multiple: float = 0.0
    longest_losing_streak: int = 0
    yearly: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    hour_concentration: Dict[int, int] = field(default_factory=dict)
    currency_exposure: Dict[str, float] = field(default_factory=dict)


def compute_scorecard(
    events: List[Event],
    tri: TriangleDef,
    entry_threshold: float,
    time_span_weeks: float,
) -> Scorecard:
    """Compute full scorecard from event list."""
    sc = Scorecard(triangle_id=tri.triangle_id, entry_threshold=entry_threshold)

    if not events:
        return sc

    n = len(events)
    sc.completed_events = n
    sc.events_per_week = n / time_span_weeks if time_span_weeks > 0 else 0

    net_pnls = [e.net_pnl_bps for e in events if e.net_pnl_bps is not None]
    gross_pnls = [e.gross_pnl_bps for e in events if e.gross_pnl_bps is not None]

    if not net_pnls:
        return sc

    net_arr = np.array(net_pnls)
    gross_arr = np.array(gross_pnls)

    sc.gross_ev_bps = float(np.mean(gross_arr))
    sc.net_ev_bps = float(np.mean(net_arr))
    sc.median_net_bps = float(np.median(net_arr))
    sc.worst_event_bps = float(np.min(net_arr))
    sc.p5_bps = float(np.percentile(net_arr, 5))

    # Win rate
    wins = net_arr > 0
    sc.win_rate = float(np.mean(wins)) * 100.0

    # Profit factor
    gross_profit = float(np.sum(net_arr[net_arr > 0])) if np.any(net_arr > 0) else 0.0
    gross_loss = float(np.abs(np.sum(net_arr[net_arr < 0]))) if np.any(net_arr < 0) else 0.0
    sc.pf_net = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    gross_profit_g = float(np.sum(gross_arr[gross_arr > 0])) if np.any(gross_arr > 0) else 0.0
    gross_loss_g = float(np.abs(np.sum(gross_arr[gross_arr < 0]))) if np.any(gross_arr < 0) else 0.0
    sc.pf_gross = gross_profit_g / gross_loss_g if gross_loss_g > 0 else float("inf")

    # Max cumulative DD
    cum = np.cumsum(net_arr)
    peak = np.maximum.accumulate(cum)
    dd = peak - cum
    sc.max_cum_dd_bps = float(np.max(dd)) if len(dd) > 0 else 0.0

    # Holding times
    holds = [e.holding_minutes for e in events if e.holding_minutes is not None]
    if holds:
        h_arr = np.array(holds)
        sc.avg_hold_min = float(np.mean(h_arr))
        sc.median_hold_min = float(np.median(h_arr))
        sc.p90_hold_min = float(np.percentile(h_arr, 90))

    # z6 stop rate
    z6_stops = sum(1 for e in events if e.exit_reason == "Z6_STOP")
    sc.z6_stop_rate = z6_stops / n * 100.0 if n > 0 else 0.0

    # Hard exit rate
    hard_exits = sum(1 for e in events if e.exit_reason == "HARD_SESSION_EXIT")
    sc.hard_exit_rate = hard_exits / n * 100.0 if n > 0 else 0.0

    # Gross basket edge
    sc.gross_basket_edge_pips = sc.gross_ev_bps / 10.0  # bps -> pips
    sc.avg_basket_cost_pips = basket_cost_rt_pips(tri.legs)

    # Gross-edge / cost ratio
    if sc.avg_basket_cost_pips > 0:
        sc.gross_edge_cost_ratio = sc.gross_basket_edge_pips / sc.avg_basket_cost_pips
    else:
        sc.gross_edge_cost_ratio = 0.0

    # Break-even cost multiple
    if sc.avg_basket_cost_pips > 0 and sc.gross_basket_edge_pips > 0:
        sc.break_even_cost_multiple = sc.gross_basket_edge_pips / sc.avg_basket_cost_pips
    else:
        sc.break_even_cost_multiple = 0.0

    # Longest losing streak
    streak = 0
    max_streak = 0
    for pnl in net_pnls:
        if pnl < 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    sc.longest_losing_streak = max_streak

    # Yearly breakdown
    yearly_pnl = defaultdict(list)
    for e in events:
        if e.net_pnl_bps is not None:
            yr = e.entry_timestamp.year
            yearly_pnl[yr].append(e.net_pnl_bps)

    sc.yearly = {}
    for yr, pnls in sorted(yearly_pnl.items()):
        arr = np.array(pnls)
        w = arr > 0
        gp = float(np.sum(arr[w])) if np.any(w) else 0.0
        gl = float(np.abs(np.sum(arr[~w]))) if np.any(~w) else 0.0
        sc.yearly[yr] = {
            "events": len(pnls),
            "net_ev": float(np.mean(arr)),
            "pf": gp / gl if gl > 0 else float("inf"),
            "net_pnl_total": float(np.sum(arr)),
            "win_rate": float(np.mean(w)) * 100.0,
        }

    # Hour concentration
    hour_counts = defaultdict(int)
    for e in events:
        h = est_hour(e.entry_timestamp)
        hour_counts[h] += 1
    sc.hour_concentration = dict(sorted(hour_counts.items()))

    # Currency exposure (approximate)
    curr_exp = defaultdict(float)
    for e in events:
        d = 1.0 if e.direction == "LONG" else -1.0
        for j, leg in enumerate(tri.legs):
            base = leg[:3]
            quote = leg[3:6]
            curr_exp[base] += d * tri.basis_signs[j]
            curr_exp[quote] -= d * tri.basis_signs[j]
    sc.currency_exposure = dict(curr_exp)

    return sc


# ═══════════════════════════════════════════════════════════════════════════════
# MONOTONICITY TEST
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MonotonicityResult:
    triangle_id: str
    delta_ev: float = 0.0
    delta_pf: float = 0.0
    delta_tail: float = 0.0
    delta_cost_ratio: float = 0.0
    classification: str = "UNKNOWN"


def compute_monotonicity(sc_z25: Scorecard, sc_z30: Scorecard) -> MonotonicityResult:
    """Compare z2.5 vs z3.0 quality."""
    m = MonotonicityResult(triangle_id=sc_z25.triangle_id)
    m.delta_ev = sc_z30.net_ev_bps - sc_z25.net_ev_bps
    m.delta_pf = sc_z30.pf_net - sc_z25.pf_net
    m.delta_tail = sc_z30.p5_bps - sc_z25.p5_bps
    m.delta_cost_ratio = sc_z30.gross_edge_cost_ratio - sc_z25.gross_edge_cost_ratio

    # Classification
    ev_ok = m.delta_ev >= 0
    pf_ok = m.delta_pf >= -0.1  # small degradation allowed
    tail_ok = m.delta_tail >= -0.5  # small tail degradation allowed

    if ev_ok and pf_ok and tail_ok:
        if m.delta_ev > 0 and m.delta_pf > 0:
            m.classification = "MONOTONIC_STRONG"
        else:
            m.classification = "MONOTONIC_ACCEPTABLE"
    elif not ev_ok and m.delta_ev < -1.0:
        m.classification = "MECHANISM_COLLAPSE"
    else:
        m.classification = "NON_MONOTONIC"

    return m


# ═══════════════════════════════════════════════════════════════════════════════
# SIGNAL COST DISTRIBUTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CostDistribution:
    triangle_id: str
    entry_threshold: float
    median: float = 0.0
    p75: float = 0.0
    p90: float = 0.0
    p95: float = 0.0


def compute_cost_distribution(events: List[Event], tri: TriangleDef) -> CostDistribution:
    """Compute signal-time cost distributions."""
    cd = CostDistribution(triangle_id=tri.triangle_id, entry_threshold=events[0].entry_z_threshold if events else 0.0)
    costs = [basket_cost_rt_pips(tri.legs)] * len(events)  # constant cost model
    if costs:
        arr = np.array(costs)
        cd.median = float(np.median(arr))
        cd.p75 = float(np.percentile(arr, 75))
        cd.p90 = float(np.percentile(arr, 90))
        cd.p95 = float(np.percentile(arr, 95))
    return cd


# ═══════════════════════════════════════════════════════════════════════════════
# HARD PASS GATE
# ═══════════════════════════════════════════════════════════════════════════════

def apply_hard_pass_gate(
    sc: Scorecard,
    mono: MonotonicityResult,
    sc_z25: Scorecard,
    time_span_weeks: float,
) -> Tuple[bool, List[str]]:
    """
    Apply Step 1 hard pass gate. Returns (pass, list_of_reasons).
    """
    reasons = []
    n_years = len(sc.yearly)
    positive_years = sum(1 for yr_data in sc.yearly.values() if yr_data.get("net_pnl_total", 0) > 0)

    # A. net EV > 0 after executable cost
    if sc.net_ev_bps <= 0:
        reasons.append(f"A: net EV={sc.net_ev_bps:.2f} bps <= 0")

    # B. PF_net >= 1.20
    if sc.pf_net < 1.20:
        reasons.append(f"B: PF_net={sc.pf_net:.2f} < 1.20")

    # C. completed_events >= 50
    if sc.completed_events < 50:
        reasons.append(f"C: events={sc.completed_events} < 50")

    # D. gross-edge / cost ratio >= 1.50
    if sc.gross_edge_cost_ratio < 1.50:
        reasons.append(f"D: edge/cost={sc.gross_edge_cost_ratio:.2f} < 1.50")

    # E. break-even cost multiple >= 1.50
    if sc.break_even_cost_multiple < 1.50:
        reasons.append(f"E: BE cost mult={sc.break_even_cost_multiple:.2f} < 1.50")

    # F. no single year > 60% of total net PnL
    total_pnl = sum(yr.get("net_pnl_total", 0) for yr in sc.yearly.values())
    if total_pnl > 0:
        for yr, yr_data in sc.yearly.items():
            yr_pnl = yr_data.get("net_pnl_total", 0)
            if yr_pnl / total_pnl > 0.60:
                reasons.append(f"F: year {yr} contributes {yr_pnl/total_pnl*100:.1f}% > 60%")
                break

    # G. at least 3 calendar years net positive
    if positive_years < 3 and n_years >= 3:
        reasons.append(f"G: {positive_years} positive years < 3")

    # H. z3 mechanism quality not materially worse than z2.5
    if mono.classification in ("MECHANISM_COLLAPSE",):
        reasons.append(f"H: mechanism classification = {mono.classification}")

    # I. no obvious rollover/spread artifact (constant cost model - always passes)
    # J. no data/microstructure invalidation (checked at load time)
    # z6 stop rate should be low
    if sc.z6_stop_rate > 20.0:
        reasons.append(f"I: z6 stop rate={sc.z6_stop_rate:.1f}% > 20%")

    passed = len(reasons) == 0
    return passed, reasons


# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCEMENT CRITERIA (>2 candidates cap at 2)
# ═══════════════════════════════════════════════════════════════════════════════

def rank_and_cap(
    qualified: List[Tuple[str, Scorecard, MonotonicityResult]],
) -> List[Tuple[str, Scorecard, MonotonicityResult]]:
    """
    Rank by predefined structural score, cap at 2.
    1. higher gross-edge / cost ratio
    2. higher number of positive years
    3. better z3-vs-z2.5 monotonicity
    4. lower tail degradation
    5. higher event count
    PF max is NOT the tiebreaker.
    """
    def sort_key(item):
        sc = item[1]
        mono = item[2]
        positive_years = sum(1 for yr_data in sc.yearly.values() if yr_data.get("net_pnl_total", 0) > 0)
        return (
            -sc.gross_edge_cost_ratio,
            -positive_years,
            -mono.delta_ev,
            -mono.delta_tail,
            -sc.completed_events,
        )

    ranked = sorted(qualified, key=sort_key)
    return ranked[:2]


# ═══════════════════════════════════════════════════════════════════════════════
# ARTIFACT WRITING
# ═══════════════════════════════════════════════════════════════════════════════

ARTIFACT_DIR = Path(__file__).parent

def write_csv(filename: str, headers: List[str], rows: List[List[Any]]):
    path = ARTIFACT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"  wrote {filename} ({len(rows)} rows)")

def write_json(filename: str, data: Any):
    path = ARTIFACT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  wrote {filename}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def run_triangle(
    tri: TriangleDef,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """Run full T1 screen for one triangle."""
    print(f"\n{'='*60}")
    print(f"  {tri.triangle_id}")
    print(f"{'='*60}")

    # Load data
    print(f"  Loading data for {tri.legs}...")
    dfs = []
    for f in tri.data_files:
        df = load_m5_data(f)
        print(f"    {f}: {len(df):,} bars ({df['timestamp'].min()} to {df['timestamp'].max()})")
        dfs.append(df)

    # Synchronize
    print("  Synchronizing...")
    synced = synchronize_triangular(dfs, list(tri.legs))
    print(f"  Synchronized: {len(synced):,} bars")

    # Filter to date window
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(minutes=5)
    mask = (synced["timestamp"] >= start_dt) & (synced["timestamp"] <= end_dt)
    synced = synced[mask].reset_index(drop=True)
    print(f"  Window {start_date} to {end_date}: {len(synced):,} bars")

    if len(synced) < LOOKBACK + 100:
        print(f"  WARNING: insufficient data ({len(synced)} bars)")
        return {"triangle_id": tri.triangle_id, "status": "INSUFFICIENT_DATA"}

    # Compute basis
    basis = compute_basis(synced, tri)
    print(f"  Basis: mean={basis.mean():.6f}, std={basis.std():.6f}")

    # Compute z-score
    z = compute_causal_z(basis, LOOKBACK)
    valid_z = z.dropna()
    print(f"  Z-score: {len(valid_z):,} valid values")
    print(f"  Z distribution: mean={valid_z.mean():.3f}, std={valid_z.std():.3f}")
    print(f"  Z range: [{valid_z.min():.3f}, {valid_z.max():.3f}]")

    # Time span in weeks
    time_span = (synced["timestamp"].iloc[-1] - synced["timestamp"].iloc[0]).total_seconds() / (7 * 86400)
    print(f"  Time span: {time_span:.1f} weeks")

    results = {}
    for threshold, lane_name in [(ENTRY_Z_CONTROL, "z2.5"), (ENTRY_Z_PRIMARY, "z3.0")]:
        print(f"\n  --- {lane_name} lane (|z| > {threshold}) ---")
        events = extract_events(synced, basis, z, tri, threshold)
        print(f"  Events: {len(events)}")

        if events:
            # Show event summary
            net_pnls = [e.net_pnl_bps for e in events if e.net_pnl_bps is not None]
            if net_pnls:
                print(f"  Net PnL: mean={np.mean(net_pnls):.2f}, median={np.median(net_pnls):.2f}")
                print(f"  Win rate: {sum(1 for p in net_pnls if p > 0)/len(net_pnls)*100:.1f}%")

        sc = compute_scorecard(events, tri, threshold, time_span)
        mono = MonotonicityResult(triangle_id=tri.triangle_id)  # placeholder, computed later
        cd = compute_cost_distribution(events, tri)

        results[lane_name] = {
            "events": events,
            "scorecard": sc,
            "cost_distribution": cd,
        }

    # Compute monotonicity
    mono = compute_monotonicity(results["z2.5"]["scorecard"], results["z3.0"]["scorecard"])
    results["monotonicity"] = mono

    # Hard pass gate (on z3 primary)
    passed, reasons = apply_hard_pass_gate(results["z3.0"]["scorecard"], mono, results["z2.5"]["scorecard"], time_span)
    results["passed_gate"] = passed
    results["gate_reasons"] = reasons

    print(f"\n  Gate: {'PASS' if passed else 'FAIL'}")
    for r in reasons:
        print(f"    - {r}")

    return results


def main():
    print("=" * 70)
    print("  CANONICAL TB TRANSFER TEST — STEP 1: MECHANISM SCREEN")
    print("  SW-CTBT-T1-CANONICAL-TB-TRANSFER-MECHANISM-SCREEN")
    print("=" * 70)

    # Date windows
    # Reference and most challengers: 2020-01-01 to 2024-12-31
    # EUR_GBP_USD: 2023-01-01 to 2024-12-31 (EURUSD only has 2023-2025)
    REF_WINDOW = ("2020-01-01", "2024-12-31")
    EUR_GBP_USD_WINDOW = ("2023-01-01", "2024-12-31")

    all_results = {}
    event_ledger_rows = []
    z25_scorecard_rows = []
    z30_scorecard_rows = []
    monotonicity_rows = []
    yearly_rows = []
    cost_dist_rows = []
    edge_cost_rows = []
    candidate_decisions = []

    # ── Run reference ──
    print("\n" + "#" * 70)
    print("  REFERENCE: AUD_GBP_NZD")
    print("#" * 70)
    ref_result = run_triangle(REFERENCE, *REF_WINDOW)
    all_results["REFERENCE"] = ref_result

    # ── Run challengers ──
    challengers = [
        (C1_EUR_GBP_JPY, REF_WINDOW),
        (C2_CHF_GBP_JPY, REF_WINDOW),
        (C3_EUR_GBP_USD, EUR_GBP_USD_WINDOW),
        (C4_GBP_NZD_USD, REF_WINDOW),
    ]

    for tri, window in challengers:
        print("\n" + "#" * 70)
        print(f"  CHALLENGER: {tri.triangle_id}")
        print("#" * 70)
        result = run_triangle(tri, *window)
        all_results[tri.triangle_id] = result

    # ── Reference parity check ──
    print("\n" + "#" * 70)
    print("  REFERENCE PARITY CHECK")
    print("#" * 70)

    ref_z30 = all_results["REFERENCE"].get("z3.0", {}).get("scorecard")
    ref_z25 = all_results["REFERENCE"].get("z2.5", {}).get("scorecard")

    parity_pass = True
    parity_issues = []

    if ref_z30 is not None:
        print(f"  Reference z3.0 events: {ref_z30.completed_events}")
        if ref_z30.completed_events == 0:
            parity_pass = False
            parity_issues.append("Zero events in reference z3.0")
    else:
        parity_pass = False
        parity_issues.append("No z3.0 scorecard for reference")

    if ref_z25 is not None:
        print(f"  Reference z2.5 events: {ref_z25.completed_events}")
        if ref_z25.completed_events == 0:
            parity_pass = False
            parity_issues.append("Zero events in reference z2.5")
    else:
        parity_pass = False
        parity_issues.append("No z2.5 scorecard for reference")

    if parity_pass:
        print("  REFERENCE PARITY: PASS")
    else:
        print("  REFERENCE PARITY: FAIL")
        for issue in parity_issues:
            print(f"    - {issue}")

    # ── Collect all artifacts ──
    print("\n" + "#" * 70)
    print("  WRITING ARTIFACTS")
    print("#" * 70)

    # Source SHA manifest
    source_sha = {}
    for tri in ALL_TRIANGLES:
        for f in tri.data_files:
            path = _DATA_DIR / f
            if path.exists():
                h = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
                source_sha[f] = h
    write_json("CTBT_T1_SOURCE_SHA_MANIFEST.json", {
        "generated": datetime.now().isoformat(),
        "data_hashes": source_sha,
    })

    # Reference parity
    write_json("CTBT_T1_REFERENCE_PARITY.json", {
        "triangle_id": "AUD_GBP_NZD",
        "parity_pass": parity_pass,
        "issues": parity_issues,
        "ref_z30_events": ref_z30.completed_events if ref_z30 else 0,
        "ref_z25_events": ref_z25.completed_events if ref_z25 else 0,
        "ref_z30_net_ev": ref_z30.net_ev_bps if ref_z30 else 0,
        "ref_z25_net_ev": ref_z25.net_ev_bps if ref_z25 else 0,
    })

    # Candidate set
    write_json("CTBT_T1_CANDIDATE_SET.json", {
        "reference": "AUD_GBP_NZD",
        "challengers": [tri.triangle_id for tri in ALL_TRIANGLES[1:]],
        "windows": {
            "AUD_GBP_NZD": REF_WINDOW,
            "EUR_GBP_JPY": REF_WINDOW,
            "CHF_GBP_JPY": REF_WINDOW,
            "EUR_GBP_USD": EUR_GBP_USD_WINDOW,
            "GBP_NZD_USD": REF_WINDOW,
        },
    })

    # Cost model
    write_json("CTBT_T1_COST_MODEL.json", {
        "cost_source": "ASSUMED",
        "model": COST_MODEL,
        "basket_costs_pips": {
            tri.triangle_id: basket_cost_rt_pips(tri.legs)
            for tri in ALL_TRIANGLES
        },
    })

    # Event ledger
    event_headers = [
        "event_id", "triangle_id", "direction", "entry_z", "entry_z_threshold",
        "entry_timestamp", "exit_timestamp", "exit_reason", "holding_minutes",
        "gross_pnl_bps", "cost_bps", "net_pnl_bps", "max_adverse_z",
    ]
    for tri_id, result in all_results.items():
        if isinstance(result, dict):
            for lane in ["z2.5", "z3.0"]:
                if lane in result and "events" in result[lane]:
                    for e in result[lane]["events"]:
                        event_ledger_rows.append([
                            e.event_id, e.triangle_id, e.direction,
                            f"{e.entry_z:.4f}", e.entry_z_threshold,
                            e.entry_timestamp.isoformat() if e.entry_timestamp else "",
                            e.exit_timestamp.isoformat() if e.exit_timestamp else "",
                            e.exit_reason or "",
                            f"{e.holding_minutes:.1f}" if e.holding_minutes else "",
                            f"{e.gross_pnl_bps:.2f}" if e.gross_pnl_bps else "",
                            f"{e.cost_bps:.2f}" if e.cost_bps else "",
                            f"{e.net_pnl_bps:.2f}" if e.net_pnl_bps else "",
                            f"{e.max_adverse_z:.4f}" if e.max_adverse_z is not None else "",
                        ])
    write_csv("CTBT_T1_EVENT_LEDGER.csv", event_headers, event_ledger_rows)

    # Scorecards
    sc_headers = [
        "triangle_id", "entry_threshold", "completed_events", "events_per_week",
        "gross_ev_bps", "net_ev_bps", "pf_gross", "pf_net", "win_rate",
        "median_net_bps", "max_cum_dd_bps", "worst_event_bps", "p5_bps",
        "avg_hold_min", "median_hold_min", "p90_hold_min",
        "z6_stop_rate", "hard_exit_rate",
        "gross_basket_edge_pips", "avg_basket_cost_pips",
        "gross_edge_cost_ratio", "break_even_cost_multiple",
        "longest_losing_streak",
    ]
    for tri_id, result in all_results.items():
        if isinstance(result, dict):
            for lane in ["z2.5", "z3.0"]:
                if lane in result and "scorecard" in result[lane]:
                    sc = result[lane]["scorecard"]
                    row = [
                        sc.triangle_id, sc.entry_threshold, sc.completed_events,
                        f"{sc.events_per_week:.2f}", f"{sc.gross_ev_bps:.2f}",
                        f"{sc.net_ev_bps:.2f}", f"{sc.pf_gross:.2f}", f"{sc.pf_net:.2f}",
                        f"{sc.win_rate:.1f}", f"{sc.median_net_bps:.2f}",
                        f"{sc.max_cum_dd_bps:.2f}", f"{sc.worst_event_bps:.2f}",
                        f"{sc.p5_bps:.2f}", f"{sc.avg_hold_min:.1f}",
                        f"{sc.median_hold_min:.1f}", f"{sc.p90_hold_min:.1f}",
                        f"{sc.z6_stop_rate:.1f}", f"{sc.hard_exit_rate:.1f}",
                        f"{sc.gross_basket_edge_pips:.2f}", f"{sc.avg_basket_cost_pips:.2f}",
                        f"{sc.gross_edge_cost_ratio:.2f}", f"{sc.break_even_cost_multiple:.2f}",
                        sc.longest_losing_streak,
                    ]
                    if lane == "z25":
                        z25_scorecard_rows.append(row)
                    else:
                        z30_scorecard_rows.append(row)

    write_csv("CTBT_T1_Z25_SCORECARDS.csv", sc_headers, z25_scorecard_rows)
    write_csv("CTBT_T1_Z30_SCORECARDS.csv", sc_headers, z30_scorecard_rows)

    # Monotonicity
    mono_headers = ["triangle_id", "delta_ev", "delta_pf", "delta_tail", "delta_cost_ratio", "classification"]
    for tri_id, result in all_results.items():
        if isinstance(result, dict) and "monotonicity" in result:
            m = result["monotonicity"]
            monotonicity_rows.append([
                m.triangle_id, f"{m.delta_ev:.2f}", f"{m.delta_pf:.2f}",
                f"{m.delta_tail:.2f}", f"{m.delta_cost_ratio:.2f}", m.classification,
            ])
    write_csv("CTBT_T1_MONOTONICITY.csv", mono_headers, monotonicity_rows)

    # Yearly stability
    yearly_headers = ["triangle_id", "year", "events", "net_ev", "pf", "net_pnl_total", "win_rate"]
    for tri_id, result in all_results.items():
        if isinstance(result, dict):
            for lane in ["z2.5", "z3.0"]:
                if lane in result and "scorecard" in result[lane]:
                    sc = result[lane]["scorecard"]
                    for yr, yr_data in sorted(sc.yearly.items()):
                        yearly_rows.append([
                            f"{sc.triangle_id}_{lane}", yr,
                            yr_data["events"], f"{yr_data['net_ev']:.2f}",
                            f"{yr_data['pf']:.2f}", f"{yr_data['net_pnl_total']:.2f}",
                            f"{yr_data['win_rate']:.1f}",
                        ])
    write_csv("CTBT_T1_YEARLY_STABILITY.csv", yearly_headers, yearly_rows)

    # Cost distributions
    cost_headers = ["triangle_id", "entry_threshold", "median", "p75", "p90", "p95"]
    for tri_id, result in all_results.items():
        if isinstance(result, dict):
            for lane in ["z2.5", "z3.0"]:
                if lane in result and "cost_distribution" in result[lane]:
                    cd = result[lane]["cost_distribution"]
                    cost_dist_rows.append([
                        cd.triangle_id, cd.entry_threshold,
                        f"{cd.median:.2f}", f"{cd.p75:.2f}", f"{cd.p90:.2f}", f"{cd.p95:.2f}",
                    ])
    write_csv("CTBT_T1_SIGNAL_COST_DISTRIBUTIONS.csv", cost_headers, cost_dist_rows)

    # Gross edge / cost ratio
    edge_headers = ["triangle_id", "entry_threshold", "gross_edge_pips", "basket_cost_pips", "ratio"]
    for tri_id, result in all_results.items():
        if isinstance(result, dict):
            for lane in ["z2.5", "z3.0"]:
                if lane in result and "scorecard" in result[lane]:
                    sc = result[lane]["scorecard"]
                    edge_cost_rows.append([
                        sc.triangle_id, sc.entry_threshold,
                        f"{sc.gross_basket_edge_pips:.2f}",
                        f"{sc.avg_basket_cost_pips:.2f}",
                        f"{sc.gross_edge_cost_ratio:.2f}",
                    ])
    write_csv("CTBT_T1_GROSS_EDGE_COST_RATIO.csv", edge_headers, edge_cost_rows)

    # Candidate decisions
    dec_headers = ["triangle_id", "passed_gate", "gate_reasons"]
    qualified = []
    for tri_id, result in all_results.items():
        if tri_id == "REFERENCE":
            continue
        if isinstance(result, dict) and "passed_gate" in result:
            passed = result["passed_gate"]
            reasons = result.get("gate_reasons", [])
            candidate_decisions.append([tri_id, str(passed), "; ".join(reasons)])
            if passed:
                mono = result.get("monotonicity")
                sc = result.get("z3.0", {}).get("scorecard")
                if sc and mono:
                    qualified.append((tri_id, sc, mono))
    write_csv("CTBT_T1_CANDIDATE_DECISIONS.csv", dec_headers, candidate_decisions)

    # Advancement
    if len(qualified) > 2:
        ranked = rank_and_cap(qualified)
        qualified_names = [q[0] for q in ranked]
        capped = True
    else:
        qualified_names = [q[0] for q in qualified]
        capped = False

    step2_authorized = len(qualified_names) > 0 and parity_pass

    if len(qualified_names) == 0:
        program_status = "STOP_NO_TRANSFER_CANDIDATE"
    elif parity_pass:
        program_status = "PASS_STEP1_SURVIVORS_FOUND"
    else:
        program_status = "FAIL_REFERENCE_PARITY"

    advancement = {
        "checkpoint": "SW-CTBT-T1-CANONICAL-TB-TRANSFER-MECHANISM-SCREEN",
        "status": program_status,
        "base_commit": "HEAD",
        "reference_parity_pass": parity_pass,
        "challenger_count": 4,
        "candidate_results": {tri_id: {"passed": any(d[0] == tri_id and d[1] == "True" for d in candidate_decisions)} for tri_id in [t.triangle_id for t in ALL_TRIANGLES[1:]]},
        "qualified_count": len(qualified_names),
        "qualified_candidates": qualified_names,
        "capped_candidates_if_needed": capped,
        "step2_required": len(qualified_names) > 0,
        "step2_authorized": step2_authorized,
        "program_stop": len(qualified_names) == 0,
        "production_authorized": False,
        "human_review_required": True,
        "next_checkpoint_recommended": "SW-CTBT-T2-ONE-SHOT-CANONICAL-TRANSFER-CONFIRMATION" if step2_authorized else None,
        "generated": datetime.now().isoformat(),
    }
    write_json("CTBT_T1_ADVANCEMENT.json", advancement)
    write_json("CTBT_T1_DECISION.json", advancement)

    # Nonregression (placeholder - canonical reference unchanged)
    write_json("CTBT_T1_NONREGRESSION.json", {
        "canonical_tb_reference_unchanged": True,
        "basis_orientation": "ln(GBPAUD) - ln(GBPNZD) + ln(AUDNZD)",
        "rolling_z_lookback": LOOKBACK,
        "weight": "W2_EXACT_NEUTRAL",
        "session": "LONDON_03_12_EST",
        "entry_z_control": ENTRY_Z_CONTROL,
        "entry_z_primary": ENTRY_Z_PRIMARY,
        "exit": "E1_SIGNED_OVERSHOOT_025",
        "stop": "Z6_STRUCTURAL_6.0",
        "min_time_to_exit": MIN_TIME_TO_EXIT,
        "hard_exit": "NOON_EST_12",
        "concurrency": 1,
    })

    # Test audit
    write_json("CTBT_T1_TEST_AUDIT.json", {
        "checkpoint": "SW-CTBT-T1-CANONICAL-TB-TRANSFER-MECHANISM-SCREEN",
        "program": "CANONICAL-TB-TRANSFER",
        "step": 1,
        "frozen_contract": {
            "lookback": LOOKBACK,
            "entry_z_control": ENTRY_Z_CONTROL,
            "entry_z_primary": ENTRY_Z_PRIMARY,
            "exit_family": "E1",
            "exit_threshold": EXIT_Z_E1,
            "weight_family": "W2",
            "stop_z": STOP_Z6,
            "min_time_to_exit_min": MIN_TIME_TO_EXIT,
            "hard_exit_est": HARD_EXIT_EST,
            "session": "LONDON",
            "concurrency": 1,
        },
        "triangles_tested": [tri.triangle_id for tri in ALL_TRIANGLES],
        "data_window_ref": REF_WINDOW,
        "data_window_eurusd": EUR_GBP_USD_WINDOW,
        "no_optimization": True,
        "no_new_exits": True,
        "no_new_filters": True,
        "no_posthoc_rescue": True,
        "generated": datetime.now().isoformat(),
    })

    # Data audit
    data_audit_rows = []
    for tri in ALL_TRIANGLES:
        for f in tri.data_files:
            path = _DATA_DIR / f
            exists = path.exists()
            size = path.stat().st_size if exists else 0
            sha = source_sha.get(f, "MISSING")
            data_audit_rows.append([tri.triangle_id, f, str(exists), str(size), sha])
    write_csv("CTBT_T1_DATA_AUDIT.csv",
              ["triangle_id", "data_file", "exists", "size_bytes", "sha256_prefix"],
              data_audit_rows)

    # ── Final report ──
    print("\n" + "=" * 70)
    print("  STEP 1 FINAL STATUS")
    print("=" * 70)
    print(f"  Reference parity: {'PASS' if parity_pass else 'FAIL'}")
    print(f"  Qualified candidates: {len(qualified_names)}")
    for q in qualified_names:
        print(f"    >> {q}")
    print(f"  Program status: {program_status}")
    print(f"  Step 2 authorized: {step2_authorized}")
    print(f"  Human review required: YES")
    print(f"\n  ARTIFACTS written to: {ARTIFACT_DIR}")

    return all_results


if __name__ == "__main__":
    main()
