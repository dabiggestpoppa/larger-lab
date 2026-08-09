#!/usr/bin/env python3
"""
CEREBUS — Triangular GBP/AUD/NZD Strategy Engine
=================================================

Implements three setups from the triangular brainstorm:

1. TRIANGULAR BASIS MEAN REVERSION
   Basis = ln(GBPAUD) - ln(GBPNZD) + ln(AUDNZD)
   Trade when z-score of basis exceeds threshold

2. GBPAUD/GBPNZD RATIO TRADE (Synthetic AUDNZD)
   Ratio = GBPAUD / GBPNZD = 1 / AUDNZD
   Trade AUD/NZD view via GBP crosses

3. LEAD-LAG CATCH-UP TRADE
   GBPAUD leads, GBPNZD lags, AUDNZD as filter
   Residual = r_GBPNZD - r_GBPAUD - r_AUDNZD
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

ASIAN_START_H_EST = 19
ASIAN_END_H_EST = 3
LONDON_START_H_EST = 3
LONDON_END_H_EST = 12
HARD_EXIT_H_EST = 12

# Strategy parameters
BASIS_LOOKBACK = 100
BASIS_ENTRY_Z = 2.0
BASIS_EXIT_Z = 0.0
BASIS_STOP_Z = 4.0

RATIO_LOOKBACK = 100
RATIO_ENTRY_Z = 2.0
RATIO_EXIT_Z = 0.0
RATIO_STOP_Z = 4.0

LEADLAG_LOOKBACK = 20
LEADLAG_THRESHOLD = 0.0005  # 5 pips residual threshold

# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class Direction(Enum):
    LONG = 1
    SHORT = -1
    FLAT = 0


class TradeResult(Enum):
    TP_HIT = "TP_HIT"
    SL_HIT = "SL_HIT"
    TIMEOUT = "TIMEOUT"
    NO_ENTRY = "NO_ENTRY"


class StrategyType(Enum):
    TRIANGULAR_BASIS = "triangular_basis"
    RATIO_TRADE = "ratio_trade"
    LEAD_LAG = "lead_lag"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass
class TriangularBar:
    """Synchronized bar across all three pairs"""
    timestamp: datetime
    gbp_aud: float
    gbp_nzd: float
    aud_nzd: float
    gbp_aud_high: float
    gbp_aud_low: float
    gbp_nzd_high: float
    gbp_nzd_low: float
    aud_nzd_high: float
    aud_nzd_low: float


@dataclass
class Trade:
    strategy: StrategyType
    direction: Direction
    entry_price: float  # reference price (GBPAUD)
    entry_gbp_aud: float = 0.0
    entry_gbp_nzd: float = 0.0
    entry_aud_nzd: float = 0.0
    sl_price: float = 0.0
    tp_price: float = 0.0
    entry_time: datetime = None
    size_gbp_aud: float = 1.0
    size_gbp_nzd: float = 1.0
    size_aud_nzd: float = 1.0
    result: Optional[TradeResult] = None
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl_pips: float = 0.0
    pnl_gbp_aud: float = 0.0
    pnl_gbp_nzd: float = 0.0
    pnl_aud_nzd: float = 0.0


@dataclass
class SessionData:
    date: datetime.date
    asian_high_gbp_aud: float
    asian_low_gbp_aud: float
    asian_high_gbp_nzd: float
    asian_low_gbp_nzd: float
    asian_high_aud_nzd: float
    asian_low_aud_nzd: float
    london_close_gbp_aud: Optional[float] = None
    london_close_gbp_nzd: Optional[float] = None
    london_close_aud_nzd: Optional[float] = None


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

_TIMESTAMP_FORMATS = [
    "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M", "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M",
    "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M",
    "%Y%m%d %H:%M:%S",
]


def compute_atr(bars: List[TriangularBar], pair: str, period: int = 20) -> List[float]:
    """Compute ATR for a specific pair."""
    atr = [0.0] * len(bars)
    for i in range(period, len(bars)):
        tr_sum = 0.0
        for j in range(i - period + 1, i + 1):
            if pair == 'gbp_aud':
                high = bars[j].gbp_aud_high
                low = bars[j].gbp_aud_low
                prev_close = bars[j-1].gbp_aud if j > 0 else bars[j].gbp_aud
            elif pair == 'gbp_nzd':
                high = bars[j].gbp_nzd_high
                low = bars[j].gbp_nzd_low
                prev_close = bars[j-1].gbp_nzd if j > 0 else bars[j].gbp_nzd
            else:  # aud_nzd
                high = bars[j].aud_nzd_high
                low = bars[j].aud_nzd_low
                prev_close = bars[j-1].aud_nzd if j > 0 else bars[j].aud_nzd
            
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_sum += tr
        atr[i] = tr_sum / period
    return atr


def parse_timestamp(raw: str) -> datetime:
    raw = raw.strip()
    for fmt in _TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse timestamp '{raw}'")


def get_pip_size(symbol: str) -> float:
    sym = symbol.upper()
    if "JPY" in sym:
        return 0.01
    if sym in ("BTCUSD", "ETHUSD", "BNBUSD", "SOLUSD", "LTCUSD", "BCHUSD"):
        return 1.0
    if sym == "XAUUSD":
        return 0.1
    if sym == "XAGUSD":
        return 0.01
    if sym in ("US500", "NAS100", "DE30", "FR40", "HK50"):
        return 1.0
    return 0.0001


def _est_hour(dt: datetime) -> int:
    return (dt.hour - 5) % 24


def _session_date(dt: datetime):
    h = _est_hour(dt)
    if h >= ASIAN_START_H_EST:
        return (dt + timedelta(days=1)).date()
    return dt.date()


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_bars_csv(csv_path: str) -> List[Bar]:
    bars: List[Bar] = []
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with open(path, newline="", encoding="utf-8-sig") as f:
        first_line = f.readline()
        f.seek(0)
        delimiter = "\t" if "\t" in first_line else ","
        reader = csv.DictReader(f, delimiter=delimiter)
        for row_num, row in enumerate(reader, start=2):
            clean_row = {k.strip().strip("<").strip(">"): v for k, v in row.items()}
            ts_raw = (clean_row.get("timestamp") or clean_row.get("Timestamp")
                      or clean_row.get("TIMESTAMP") or clean_row.get("datetime")
                      or clean_row.get("Datetime") or clean_row.get("DATETIME")
                      or clean_row.get("time") or clean_row.get("Time") or clean_row.get("TIME"))
            if ts_raw is None:
                date_val = (clean_row.get("date") or clean_row.get("Date") or clean_row.get("DATE"))
                time_val = (clean_row.get("time") or clean_row.get("Time") or clean_row.get("TIME"))
                if date_val and time_val:
                    ts_raw = f"{date_val.strip()} {time_val.strip()}"
            if ts_raw is None or not ts_raw.strip():
                raise ValueError(f"Row {row_num}: no timestamp. Columns: {list(row.keys())}")
            o = clean_row.get("OPEN") or clean_row.get("open")
            h = clean_row.get("HIGH") or clean_row.get("high")
            l = clean_row.get("LOW") or clean_row.get("low")
            c = clean_row.get("CLOSE") or clean_row.get("close")
            v = clean_row.get("VOLUME") or clean_row.get("volume") or clean_row.get("Volume") or "0"
            if any(v is None for v in (o, h, l, c)):
                raise ValueError(f"Row {row_num}: missing OHLC. Columns: {list(row.keys())}")
            bars.append(Bar(
                timestamp=parse_timestamp(ts_raw),
                open=float(o), high=float(h), low=float(l), close=float(c), volume=float(v)
            ))

    bars.sort(key=lambda b: b.timestamp)
    return bars


def synchronize_bars(
    gbp_aud_bars: List[Bar],
    gbp_nzd_bars: List[Bar],
    aud_nzd_bars: List[Bar]
) -> List[TriangularBar]:
    """Synchronize three bar series by timestamp (nearest match within 1 minute)."""
    # Build timestamp -> bar maps
    gbp_aud_map = {b.timestamp: b for b in gbp_aud_bars}
    gbp_nzd_map = {b.timestamp: b for b in gbp_nzd_bars}
    aud_nzd_map = {b.timestamp: b for b in aud_nzd_bars}

    # Get all unique timestamps
    all_timestamps = set(gbp_aud_map.keys()) | set(gbp_nzd_map.keys()) | set(aud_nzd_map.keys())
    all_timestamps = sorted(all_timestamps)

    synced = []
    for ts in all_timestamps:
        # Find nearest bar for each pair (within 1 minute tolerance)
        gbp_aud_bar = gbp_aud_map.get(ts)
        gbp_nzd_bar = gbp_nzd_map.get(ts)
        aud_nzd_bar = aud_nzd_map.get(ts)

        if gbp_aud_bar and gbp_nzd_bar and aud_nzd_bar:
            synced.append(TriangularBar(
                timestamp=ts,
                gbp_aud=gbp_aud_bar.close,
                gbp_nzd=gbp_nzd_bar.close,
                aud_nzd=aud_nzd_bar.close,
                gbp_aud_high=gbp_aud_bar.high,
                gbp_aud_low=gbp_aud_bar.low,
                gbp_nzd_high=gbp_nzd_bar.high,
                gbp_nzd_low=gbp_nzd_bar.low,
                aud_nzd_high=aud_nzd_bar.high,
                aud_nzd_low=aud_nzd_bar.low,
            ))

    return synced


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

def compute_sessions(bars: List[TriangularBar]) -> List[SessionData]:
    """Group bars into sessions and compute Asian ranges for all three pairs."""
    sessions: Dict[datetime.date, Dict] = defaultdict(lambda: {
        "asian_gbp_aud": [], "london_gbp_aud": [],
        "asian_gbp_nzd": [], "london_gbp_nzd": [],
        "asian_aud_nzd": [], "london_aud_nzd": [],
    })

    for bar in bars:
        sdate = _session_date(bar.timestamp)
        est_h = _est_hour(bar.timestamp)

        if est_h >= ASIAN_START_H_EST or est_h < ASIAN_END_H_EST:
            sessions[sdate]["asian_gbp_aud"].append(bar)
            sessions[sdate]["asian_gbp_nzd"].append(bar)
            sessions[sdate]["asian_aud_nzd"].append(bar)
        elif LONDON_START_H_EST <= est_h < LONDON_END_H_EST:
            sessions[sdate]["london_gbp_aud"].append(bar)
            sessions[sdate]["london_gbp_nzd"].append(bar)
            sessions[sdate]["london_aud_nzd"].append(bar)

    result = []
    for sdate in sorted(sessions.keys()):
        data = sessions[sdate]

        # Need data for all three pairs in both sessions
        if not all([
            data["asian_gbp_aud"], data["london_gbp_aud"],
            data["asian_gbp_nzd"], data["london_gbp_nzd"],
            data["asian_aud_nzd"], data["london_aud_nzd"],
        ]):
            continue

        asian_high_gbp_aud = max(b.gbp_aud_high for b in data["asian_gbp_aud"])
        asian_low_gbp_aud = min(b.gbp_aud_low for b in data["asian_gbp_aud"])
        asian_high_gbp_nzd = max(b.gbp_nzd_high for b in data["asian_gbp_nzd"])
        asian_low_gbp_nzd = min(b.gbp_nzd_low for b in data["asian_gbp_nzd"])
        asian_high_aud_nzd = max(b.aud_nzd_high for b in data["asian_aud_nzd"])
        asian_low_aud_nzd = min(b.aud_nzd_low for b in data["asian_aud_nzd"])

        london_close_gbp_aud = data["london_gbp_aud"][-1].gbp_aud
        london_close_gbp_nzd = data["london_gbp_nzd"][-1].gbp_nzd
        london_close_aud_nzd = data["london_aud_nzd"][-1].aud_nzd

        result.append(SessionData(
            date=sdate,
            asian_high_gbp_aud=asian_high_gbp_aud,
            asian_low_gbp_aud=asian_low_gbp_aud,
            asian_high_gbp_nzd=asian_high_gbp_nzd,
            asian_low_gbp_nzd=asian_low_gbp_nzd,
            asian_high_aud_nzd=asian_high_aud_nzd,
            asian_low_aud_nzd=asian_low_aud_nzd,
            london_close_gbp_aud=london_close_gbp_aud,
            london_close_gbp_nzd=london_close_gbp_nzd,
            london_close_aud_nzd=london_close_aud_nzd,
        ))

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 1: TRIANGULAR BASIS MEAN REVERSION
# ═══════════════════════════════════════════════════════════════════════════════

def compute_basis(bars: List[TriangularBar]) -> List[float]:
    """Compute triangular basis: ln(GBPAUD) - ln(GBPNZD) + ln(AUDNZD)"""
    basis = []
    for bar in bars:
        b = np.log(bar.gbp_aud) - np.log(bar.gbp_nzd) + np.log(bar.aud_nzd)
        basis.append(b)
    return basis


def compute_basis_zscore(basis: List[float], lookback: int = BASIS_LOOKBACK) -> List[float]:
    """Compute rolling z-score of basis."""
    z_scores = []
    for i in range(len(basis)):
        if i < lookback:
            z_scores.append(0.0)
        else:
            window = basis[i-lookback:i]
            mean = np.mean(window)
            std = np.std(window)
            if std > 0:
                z = (basis[i] - mean) / std
            else:
                z = 0.0
            z_scores.append(z)
    return z_scores


def run_triangular_basis_backtest(
    bars: List[TriangularBar],
    sessions: List[SessionData],
    pip_size_gbp_aud: float,
    pip_size_gbp_nzd: float,
    pip_size_aud_nzd: float
) -> List[Trade]:
    """Run triangular basis mean reversion backtest.
    
    Triangular basis: ln(GBPAUD) - ln(GBPNZD) + ln(AUDNZD)
    
    When basis is HIGH (z > entry): GBPAUD is expensive vs synthetic
    -> Short GBPAUD, Long GBPNZD, Short AUDNZD
    
    When basis is LOW (z < -entry): GBPAUD is cheap vs synthetic  
    -> Long GBPAUD, Short GBPNZD, Long AUDNZD
    
    Position sizing: volatility-weighted so GBP/AUD/NZD exposures cancel
    """
    basis = compute_basis(bars)
    z_scores = compute_basis_zscore(basis)

    # Compute ATR for position sizing
    atr_period = 20
    atr_gbp_aud = compute_atr(bars, 'gbp_aud', atr_period)
    atr_gbp_nzd = compute_atr(bars, 'gbp_nzd', atr_period)
    atr_aud_nzd = compute_atr(bars, 'aud_nzd', atr_period)

    trades = []
    in_trade = False
    current_trade = None

    for i, bar in enumerate(bars):
        z = z_scores[i]
        est_h = _est_hour(bar.timestamp)

        # Hard exit at 12 PM EST
        if est_h >= HARD_EXIT_H_EST and in_trade:
            current_trade.result = TradeResult.TIMEOUT
            current_trade.exit_time = bar.timestamp
            # Calculate PnL for each leg using stored entry prices
            if current_trade.direction == Direction.SHORT:
                # Short GBPAUD, Long GBPNZD, Short AUDNZD
                current_trade.pnl_gbp_aud = (current_trade.entry_gbp_aud - bar.gbp_aud) / pip_size_gbp_aud * current_trade.size_gbp_aud
                current_trade.pnl_gbp_nzd = (bar.gbp_nzd - current_trade.entry_gbp_nzd) / pip_size_gbp_nzd * current_trade.size_gbp_nzd
                current_trade.pnl_aud_nzd = (current_trade.entry_aud_nzd - bar.aud_nzd) / pip_size_aud_nzd * current_trade.size_aud_nzd
            else:  # LONG
                # Long GBPAUD, Short GBPNZD, Long AUDNZD
                current_trade.pnl_gbp_aud = (bar.gbp_aud - current_trade.entry_gbp_aud) / pip_size_gbp_aud * current_trade.size_gbp_aud
                current_trade.pnl_gbp_nzd = (current_trade.entry_gbp_nzd - bar.gbp_nzd) / pip_size_gbp_nzd * current_trade.size_gbp_nzd
                current_trade.pnl_aud_nzd = (bar.aud_nzd - current_trade.entry_aud_nzd) / pip_size_aud_nzd * current_trade.size_aud_nzd
            current_trade.pnl_pips = current_trade.pnl_gbp_aud + current_trade.pnl_gbp_nzd + current_trade.pnl_aud_nzd
            trades.append(current_trade)
            in_trade = False
            current_trade = None
            continue

        # Entry logic
        if not in_trade:
            if z > BASIS_ENTRY_Z:
                # Basis high: GBPAUD expensive vs synthetic
                # Short GBPAUD, Long GBPNZD, Short AUDNZD
                # Size by inverse ATR for volatility parity
                size_gbp_aud = 1.0 / atr_gbp_aud[i] if atr_gbp_aud[i] > 0 else 1.0
                size_gbp_nzd = 1.0 / atr_gbp_nzd[i] if atr_gbp_nzd[i] > 0 else 1.0
                size_aud_nzd = 1.0 / atr_aud_nzd[i] if atr_aud_nzd[i] > 0 else 1.0
                
                # Normalize so total risk is balanced
                total_size = size_gbp_aud + size_gbp_nzd + size_aud_nzd
                size_gbp_aud = size_gbp_aud / total_size * 3.0
                size_gbp_nzd = size_gbp_nzd / total_size * 3.0
                size_aud_nzd = size_aud_nzd / total_size * 3.0
                
                current_trade = Trade(
                    strategy=StrategyType.TRIANGULAR_BASIS,
                    direction=Direction.SHORT,
                    entry_price=bar.gbp_aud,  # reference
                    entry_gbp_aud=bar.gbp_aud,
                    entry_gbp_nzd=bar.gbp_nzd,
                    entry_aud_nzd=bar.aud_nzd,
                    sl_price=0,
                    tp_price=0,
                    entry_time=bar.timestamp,
                    size_gbp_aud=size_gbp_aud,
                    size_gbp_nzd=size_gbp_nzd,
                    size_aud_nzd=size_aud_nzd,
                )
                in_trade = True
            elif z < -BASIS_ENTRY_Z:
                # Basis low: GBPAUD cheap vs synthetic
                # Long GBPAUD, Short GBPNZD, Long AUDNZD
                size_gbp_aud = 1.0 / atr_gbp_aud[i] if atr_gbp_aud[i] > 0 else 1.0
                size_gbp_nzd = 1.0 / atr_gbp_nzd[i] if atr_gbp_nzd[i] > 0 else 1.0
                size_aud_nzd = 1.0 / atr_aud_nzd[i] if atr_aud_nzd[i] > 0 else 1.0
                
                total_size = size_gbp_aud + size_gbp_nzd + size_aud_nzd
                size_gbp_aud = size_gbp_aud / total_size * 3.0
                size_gbp_nzd = size_gbp_nzd / total_size * 3.0
                size_aud_nzd = size_aud_nzd / total_size * 3.0
                
                current_trade = Trade(
                    strategy=StrategyType.TRIANGULAR_BASIS,
                    direction=Direction.LONG,
                    entry_price=bar.gbp_aud,
                    entry_gbp_aud=bar.gbp_aud,
                    entry_gbp_nzd=bar.gbp_nzd,
                    entry_aud_nzd=bar.aud_nzd,
                    sl_price=0,
                    tp_price=0,
                    entry_time=bar.timestamp,
                    size_gbp_aud=size_gbp_aud,
                    size_gbp_nzd=size_gbp_nzd,
                    size_aud_nzd=size_aud_nzd,
                )
                in_trade = True

        # Exit logic
        if in_trade:
            if current_trade.direction == Direction.SHORT:
                # Exit when z returns to 0 or hits stop
                if z <= BASIS_EXIT_Z:
                    current_trade.result = TradeResult.TP_HIT
                    current_trade.exit_time = bar.timestamp
                    current_trade.pnl_gbp_aud = (current_trade.entry_gbp_aud - bar.gbp_aud) / pip_size_gbp_aud * current_trade.size_gbp_aud
                    current_trade.pnl_gbp_nzd = (bar.gbp_nzd - current_trade.entry_gbp_nzd) / pip_size_gbp_nzd * current_trade.size_gbp_nzd
                    current_trade.pnl_aud_nzd = (current_trade.entry_aud_nzd - bar.aud_nzd) / pip_size_aud_nzd * current_trade.size_aud_nzd
                    current_trade.pnl_pips = current_trade.pnl_gbp_aud + current_trade.pnl_gbp_nzd + current_trade.pnl_aud_nzd
                    trades.append(current_trade)
                    in_trade = False
                    current_trade = None
                elif z >= BASIS_STOP_Z:
                    current_trade.result = TradeResult.SL_HIT
                    current_trade.exit_time = bar.timestamp
                    current_trade.pnl_gbp_aud = (current_trade.entry_gbp_aud - bar.gbp_aud) / pip_size_gbp_aud * current_trade.size_gbp_aud
                    current_trade.pnl_gbp_nzd = (bar.gbp_nzd - current_trade.entry_gbp_nzd) / pip_size_gbp_nzd * current_trade.size_gbp_nzd
                    current_trade.pnl_aud_nzd = (current_trade.entry_aud_nzd - bar.aud_nzd) / pip_size_aud_nzd * current_trade.size_aud_nzd
                    current_trade.pnl_pips = current_trade.pnl_gbp_aud + current_trade.pnl_gbp_nzd + current_trade.pnl_aud_nzd
                    trades.append(current_trade)
                    in_trade = False
                    current_trade = None
            else:  # LONG
                if z >= BASIS_EXIT_Z:
                    current_trade.result = TradeResult.TP_HIT
                    current_trade.exit_time = bar.timestamp
                    current_trade.pnl_gbp_aud = (bar.gbp_aud - current_trade.entry_gbp_aud) / pip_size_gbp_aud * current_trade.size_gbp_aud
                    current_trade.pnl_gbp_nzd = (current_trade.entry_gbp_nzd - bar.gbp_nzd) / pip_size_gbp_nzd * current_trade.size_gbp_nzd
                    current_trade.pnl_aud_nzd = (bar.aud_nzd - current_trade.entry_aud_nzd) / pip_size_aud_nzd * current_trade.size_aud_nzd
                    current_trade.pnl_pips = current_trade.pnl_gbp_aud + current_trade.pnl_gbp_nzd + current_trade.pnl_aud_nzd
                    trades.append(current_trade)
                    in_trade = False
                    current_trade = None
                elif z <= -BASIS_STOP_Z:
                    current_trade.result = TradeResult.SL_HIT
                    current_trade.exit_time = bar.timestamp
                    current_trade.pnl_gbp_aud = (bar.gbp_aud - current_trade.entry_gbp_aud) / pip_size_gbp_aud * current_trade.size_gbp_aud
                    current_trade.pnl_gbp_nzd = (current_trade.entry_gbp_nzd - bar.gbp_nzd) / pip_size_gbp_nzd * current_trade.size_gbp_nzd
                    current_trade.pnl_aud_nzd = (bar.aud_nzd - current_trade.entry_aud_nzd) / pip_size_aud_nzd * current_trade.size_aud_nzd
                    current_trade.pnl_pips = current_trade.pnl_gbp_aud + current_trade.pnl_gbp_nzd + current_trade.pnl_aud_nzd
                    trades.append(current_trade)
                    in_trade = False
                    current_trade = None

    return trades


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 2: GBPAUD/GBPNZD RATIO TRADE (Synthetic AUDNZD)
# ════════════════════════════════════════════════════════════════════════════════

def compute_ratio(bars: List[TriangularBar]) -> List[float]:
    """Compute GBPAUD / GBPNZD ratio (should equal 1/AUDNZD)"""
    ratio = []
    for bar in bars:
        r = bar.gbp_aud / bar.gbp_nzd
        ratio.append(r)
    return ratio


def compute_ratio_zscore(ratio: List[float], lookback: int = RATIO_LOOKBACK) -> List[float]:
    """Compute rolling z-score of ratio."""
    z_scores = []
    for i in range(len(ratio)):
        if i < lookback:
            z_scores.append(0.0)
        else:
            window = ratio[i-lookback:i]
            mean = np.mean(window)
            std = np.std(window)
            if std > 0:
                z = (ratio[i] - mean) / std
            else:
                z = 0.0
            z_scores.append(z)
    return z_scores


def run_ratio_backtest(
    bars: List[TriangularBar],
    sessions: List[SessionData],
    pip_size_gbp_aud: float,
    pip_size_gbp_nzd: float,
    pip_size_aud_nzd: float
) -> List[Trade]:
    """Run GBPAUD/GBPNZD ratio trade backtest.
    
    Ratio = GBPAUD / GBPNZD = 1 / AUDNZD
    
    When ratio is HIGH (z > entry): GBPAUD expensive vs GBPNZD
    -> Short GBPAUD, Long GBPNZD (synthetic Long AUDNZD)
    
    When ratio is LOW (z < -entry): GBPAUD cheap vs GBPNZD
    -> Long GBPAUD, Short GBPNZD (synthetic Short AUDNZD)
    """
    ratio = compute_ratio(bars)
    z_scores = compute_ratio_zscore(ratio)

    # Compute ATR for position sizing
    atr_period = 20
    atr_gbp_aud = compute_atr(bars, 'gbp_aud', atr_period)
    atr_gbp_nzd = compute_atr(bars, 'gbp_nzd', atr_period)

    trades = []
    in_trade = False
    current_trade = None

    for i, bar in enumerate(bars):
        z = z_scores[i]
        est_h = _est_hour(bar.timestamp)

        # Hard exit at 12 PM EST
        if est_h >= HARD_EXIT_H_EST and in_trade:
            current_trade.result = TradeResult.TIMEOUT
            current_trade.exit_time = bar.timestamp
            if current_trade.direction == Direction.SHORT:
                # Short GBPAUD, Long GBPNZD
                current_trade.pnl_gbp_aud = (current_trade.entry_gbp_aud - bar.gbp_aud) / pip_size_gbp_aud * current_trade.size_gbp_aud
                current_trade.pnl_gbp_nzd = (bar.gbp_nzd - current_trade.entry_gbp_nzd) / pip_size_gbp_nzd * current_trade.size_gbp_nzd
            else:  # LONG
                # Long GBPAUD, Short GBPNZD
                current_trade.pnl_gbp_aud = (bar.gbp_aud - current_trade.entry_gbp_aud) / pip_size_gbp_aud * current_trade.size_gbp_aud
                current_trade.pnl_gbp_nzd = (current_trade.entry_gbp_nzd - bar.gbp_nzd) / pip_size_gbp_nzd * current_trade.size_gbp_nzd
            current_trade.pnl_pips = current_trade.pnl_gbp_aud + current_trade.pnl_gbp_nzd
            trades.append(current_trade)
            in_trade = False
            current_trade = None
            continue

        # Entry logic
        if not in_trade:
            if z > RATIO_ENTRY_Z:
                # Ratio high: GBPAUD expensive vs GBPNZD -> Short GBPAUD, Long GBPNZD (Long AUDNZD)
                size_gbp_aud = 1.0 / atr_gbp_aud[i] if atr_gbp_aud[i] > 0 else 1.0
                size_gbp_nzd = 1.0 / atr_gbp_nzd[i] if atr_gbp_nzd[i] > 0 else 1.0
                total_size = size_gbp_aud + size_gbp_nzd
                size_gbp_aud = size_gbp_aud / total_size * 2.0
                size_gbp_nzd = size_gbp_nzd / total_size * 2.0
                
                current_trade = Trade(
                    strategy=StrategyType.RATIO_TRADE,
                    direction=Direction.SHORT,  # Short the ratio = Long AUDNZD
                    entry_price=bar.gbp_aud,
                    entry_gbp_aud=bar.gbp_aud,
                    entry_gbp_nzd=bar.gbp_nzd,
                    sl_price=0,
                    tp_price=0,
                    entry_time=bar.timestamp,
                    size_gbp_aud=size_gbp_aud,
                    size_gbp_nzd=size_gbp_nzd,
                )
                in_trade = True
            elif z < -RATIO_ENTRY_Z:
                # Ratio low: GBPAUD cheap vs GBPNZD -> Long GBPAUD, Short GBPNZD (Short AUDNZD)
                size_gbp_aud = 1.0 / atr_gbp_aud[i] if atr_gbp_aud[i] > 0 else 1.0
                size_gbp_nzd = 1.0 / atr_gbp_nzd[i] if atr_gbp_nzd[i] > 0 else 1.0
                total_size = size_gbp_aud + size_gbp_nzd
                size_gbp_aud = size_gbp_aud / total_size * 2.0
                size_gbp_nzd = size_gbp_nzd / total_size * 2.0
                
                current_trade = Trade(
                    strategy=StrategyType.RATIO_TRADE,
                    direction=Direction.LONG,  # Long the ratio = Short AUDNZD
                    entry_price=bar.gbp_aud,
                    entry_gbp_aud=bar.gbp_aud,
                    entry_gbp_nzd=bar.gbp_nzd,
                    sl_price=0,
                    tp_price=0,
                    entry_time=bar.timestamp,
                    size_gbp_aud=size_gbp_aud,
                    size_gbp_nzd=size_gbp_nzd,
                )
                in_trade = True

        # Exit logic
        if in_trade:
            if current_trade.direction == Direction.SHORT:
                if z <= RATIO_EXIT_Z:
                    current_trade.result = TradeResult.TP_HIT
                    current_trade.exit_time = bar.timestamp
                    current_trade.pnl_gbp_aud = (current_trade.entry_gbp_aud - bar.gbp_aud) / pip_size_gbp_aud * current_trade.size_gbp_aud
                    current_trade.pnl_gbp_nzd = (bar.gbp_nzd - current_trade.entry_gbp_nzd) / pip_size_gbp_nzd * current_trade.size_gbp_nzd
                    current_trade.pnl_pips = current_trade.pnl_gbp_aud + current_trade.pnl_gbp_nzd
                    trades.append(current_trade)
                    in_trade = False
                    current_trade = None
                elif z >= RATIO_STOP_Z:
                    current_trade.result = TradeResult.SL_HIT
                    current_trade.exit_time = bar.timestamp
                    current_trade.pnl_gbp_aud = (current_trade.entry_gbp_aud - bar.gbp_aud) / pip_size_gbp_aud * current_trade.size_gbp_aud
                    current_trade.pnl_gbp_nzd = (bar.gbp_nzd - current_trade.entry_gbp_nzd) / pip_size_gbp_nzd * current_trade.size_gbp_nzd
                    current_trade.pnl_pips = current_trade.pnl_gbp_aud + current_trade.pnl_gbp_nzd
                    trades.append(current_trade)
                    in_trade = False
                    current_trade = None
            else:  # LONG
                if z >= RATIO_EXIT_Z:
                    current_trade.result = TradeResult.TP_HIT
                    current_trade.exit_time = bar.timestamp
                    current_trade.pnl_gbp_aud = (bar.gbp_aud - current_trade.entry_gbp_aud) / pip_size_gbp_aud * current_trade.size_gbp_aud
                    current_trade.pnl_gbp_nzd = (current_trade.entry_gbp_nzd - bar.gbp_nzd) / pip_size_gbp_nzd * current_trade.size_gbp_nzd
                    current_trade.pnl_pips = current_trade.pnl_gbp_aud + current_trade.pnl_gbp_nzd
                    trades.append(current_trade)
                    in_trade = False
                    current_trade = None
                elif z <= -RATIO_STOP_Z:
                    current_trade.result = TradeResult.SL_HIT
                    current_trade.exit_time = bar.timestamp
                    current_trade.pnl_gbp_aud = (bar.gbp_aud - current_trade.entry_gbp_aud) / pip_size_gbp_aud * current_trade.size_gbp_aud
                    current_trade.pnl_gbp_nzd = (current_trade.entry_gbp_nzd - bar.gbp_nzd) / pip_size_gbp_nzd * current_trade.size_gbp_nzd
                    current_trade.pnl_pips = current_trade.pnl_gbp_aud + current_trade.pnl_gbp_nzd
                    trades.append(current_trade)
                    in_trade = False
                    current_trade = None

    return trades

    return trades


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 3: LEAD-LAG CATCH-UP TRADE
# ════════════════════════════════════════════════════════════════════════════════

def compute_returns(bars: List[TriangularBar], period: int = 5) -> Tuple[List[float], List[float], List[float]]:
    """Compute returns for all three pairs over period bars."""
    gbp_aud_ret = [0.0] * len(bars)
    gbp_nzd_ret = [0.0] * len(bars)
    aud_nzd_ret = [0.0] * len(bars)

    for i in range(period, len(bars)):
        gbp_aud_ret[i] = np.log(bars[i].gbp_aud / bars[i-period].gbp_aud)
        gbp_nzd_ret[i] = np.log(bars[i].gbp_nzd / bars[i-period].gbp_nzd)
        aud_nzd_ret[i] = np.log(bars[i].aud_nzd / bars[i-period].aud_nzd)

    return gbp_aud_ret, gbp_nzd_ret, aud_nzd_ret


def compute_leadlag_residual(
    gbp_aud_ret: List[float],
    gbp_nzd_ret: List[float],
    aud_nzd_ret: List[float]
) -> List[float]:
    """Compute residual: r_GBPNZD - r_GBPAUD - r_AUDNZD"""
    residual = []
    for i in range(len(gbp_aud_ret)):
        res = gbp_nzd_ret[i] - gbp_aud_ret[i] - aud_nzd_ret[i]
        residual.append(res)
    return residual


def run_leadlag_backtest(
    bars: List[TriangularBar],
    sessions: List[SessionData],
    pip_size_gbp_aud: float,
    pip_size_gbp_nzd: float,
    pip_size_aud_nzd: float
) -> List[Trade]:
    """Run lead-lag catch-up backtest."""
    gbp_aud_ret, gbp_nzd_ret, aud_nzd_ret = compute_returns(bars, 5)
    residual = compute_leadlag_residual(gbp_aud_ret, gbp_nzd_ret, aud_nzd_ret)

    # Rolling stats on residual
    residual_mean = []
    residual_std = []
    for i in range(len(residual)):
        if i < LEADLAG_LOOKBACK:
            residual_mean.append(0.0)
            residual_std.append(1.0)
        else:
            window = residual[i-LEADLAG_LOOKBACK:i]
            residual_mean.append(np.mean(window))
            residual_std.append(np.std(window) if np.std(window) > 0 else 1.0)

    trades = []
    in_trade = False
    current_trade = None

    for i, bar in enumerate(bars):
        est_h = _est_hour(bar.timestamp)

        # Hard exit at 12 PM EST
        if est_h >= HARD_EXIT_H_EST and in_trade:
            current_trade.result = TradeResult.TIMEOUT
            current_trade.exit_price = bar.gbp_nzd
            current_trade.exit_time = bar.timestamp
            if current_trade.direction == Direction.LONG:
                current_trade.pnl_gbp_nzd = (bar.gbp_nzd - current_trade.entry_price) / pip_size_gbp_nzd
            else:
                current_trade.pnl_gbp_nzd = (current_trade.entry_price - bar.gbp_nzd) / pip_size_gbp_nzd
            current_trade.pnl_pips = current_trade.pnl_gbp_nzd
            trades.append(current_trade)
            in_trade = False
            current_trade = None
            continue

        # Entry logic: GBPAUD moved, AUDNZD stable, GBPNZD lagging
        if not in_trade and i >= LEADLAG_LOOKBACK:
            gbp_move = gbp_aud_ret[i]
            aud_nzd_move = aud_nzd_ret[i]
            gbp_nzd_actual = gbp_nzd_ret[i]
            gbp_nzd_expected = gbp_move + aud_nzd_move
            lag_residual = gbp_nzd_actual - gbp_nzd_expected

            # Normalize by rolling std
            z_residual = (residual[i] - residual_mean[i]) / residual_std[i] if residual_std[i] > 0 else 0

            # Long GBPNZD catch-up: GBPAUD up, AUDNZD stable, GBPNZD lagging
            if gbp_move > LEADLAG_THRESHOLD and abs(aud_nzd_move) < LEADLAG_THRESHOLD and lag_residual < -LEADLAG_THRESHOLD:
                current_trade = Trade(
                    strategy=StrategyType.LEAD_LAG,
                    direction=Direction.LONG,
                    entry_price=bar.gbp_nzd,
                    sl_price=bar.gbp_nzd - 20 * pip_size_gbp_nzd,  # 20 pip SL
                    tp_price=bar.gbp_nzd + 20 * pip_size_gbp_nzd,  # 20 pip TP
                    entry_time=bar.timestamp,
                    size_gbp_nzd=1.0,
                )
                in_trade = True

            # Short GBPNZD catch-up: GBPAUD down, AUDNZD stable, GBPNZD not down enough
            elif gbp_move < -LEADLAG_THRESHOLD and abs(aud_nzd_move) < LEADLAG_THRESHOLD and lag_residual > LEADLAG_THRESHOLD:
                current_trade = Trade(
                    strategy=StrategyType.LEAD_LAG,
                    direction=Direction.SHORT,
                    entry_price=bar.gbp_nzd,
                    sl_price=bar.gbp_nzd + 20 * pip_size_gbp_nzd,
                    tp_price=bar.gbp_nzd - 20 * pip_size_gbp_nzd,
                    entry_time=bar.timestamp,
                    size_gbp_nzd=1.0,
                )
                in_trade = True

        # Exit logic
        if in_trade:
            if current_trade.direction == Direction.LONG:
                if bar.gbp_nzd_high >= current_trade.tp_price:
                    current_trade.result = TradeResult.TP_HIT
                    current_trade.exit_price = current_trade.tp_price
                    current_trade.exit_time = bar.timestamp
                    current_trade.pnl_gbp_nzd = (current_trade.tp_price - current_trade.entry_price) / pip_size_gbp_nzd
                    current_trade.pnl_pips = current_trade.pnl_gbp_nzd
                    trades.append(current_trade)
                    in_trade = False
                    current_trade = None
                elif bar.gbp_nzd_low <= current_trade.sl_price:
                    current_trade.result = TradeResult.SL_HIT
                    current_trade.exit_price = current_trade.sl_price
                    current_trade.exit_time = bar.timestamp
                    current_trade.pnl_gbp_nzd = (current_trade.sl_price - current_trade.entry_price) / pip_size_gbp_nzd
                    current_trade.pnl_pips = current_trade.pnl_gbp_nzd
                    trades.append(current_trade)
                    in_trade = False
                    current_trade = None
            else:  # SHORT
                if bar.gbp_nzd_low <= current_trade.tp_price:
                    current_trade.result = TradeResult.TP_HIT
                    current_trade.exit_price = current_trade.tp_price
                    current_trade.exit_time = bar.timestamp
                    current_trade.pnl_gbp_nzd = (current_trade.entry_price - current_trade.tp_price) / pip_size_gbp_nzd
                    current_trade.pnl_pips = current_trade.pnl_gbp_nzd
                    trades.append(current_trade)
                    in_trade = False
                    current_trade = None
                elif bar.gbp_nzd_high >= current_trade.sl_price:
                    current_trade.result = TradeResult.SL_HIT
                    current_trade.exit_price = current_trade.sl_price
                    current_trade.exit_time = bar.timestamp
                    current_trade.pnl_gbp_nzd = (current_trade.entry_price - current_trade.sl_price) / pip_size_gbp_nzd
                    current_trade.pnl_pips = current_trade.pnl_gbp_nzd
                    trades.append(current_trade)
                    in_trade = False
                    current_trade = None

    return trades


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICS & REPORTING
# ═══════════════════════════════════════════════════════════════════════════════

def compute_stats(trades: List[Trade], strategy_name: str) -> Dict:
    if not trades:
        return {"strategy": strategy_name, "total_trades": 0}

    wins = [t for t in trades if t.pnl_pips > 0]
    losses = [t for t in trades if t.pnl_pips < 0]
    total = len(trades)
    win_rate = len(wins) / total * 100 if total > 0 else 0.0

    gross_profit = sum(t.pnl_pips for t in wins) if wins else 0.0
    gross_loss = abs(sum(t.pnl_pips for t in losses)) if losses else 0.0
    net_pnl = gross_profit - gross_loss
    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    avg_trade = net_pnl / total if total > 0 else 0.0

    # Max drawdown
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trades:
        cumulative += t.pnl_pips
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    tp_hits = len([t for t in trades if t.result == TradeResult.TP_HIT])
    sl_hits = len([t for t in trades if t.result == TradeResult.SL_HIT])
    timeouts = len([t for t in trades if t.result == TradeResult.TIMEOUT])

    return {
        "strategy": strategy_name,
        "total_trades": total,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "gross_profit_pips": round(gross_profit, 1),
        "gross_loss_pips": round(-gross_loss, 1),
        "net_pnl_pips": round(net_pnl, 1),
        "profit_factor": round(pf, 2),
        "avg_trade_pips": round(avg_trade, 2),
        "max_drawdown_pips": round(max_dd, 1),
        "tp_hits": tp_hits,
        "sl_hits": sl_hits,
        "timeouts": timeouts,
    }


def print_report(stats: Dict):
    print()
    print("=" * 70)
    print(f"  {stats['strategy'].upper()} -- BACKTEST REPORT")
    print("=" * 70)

    if stats['total_trades'] == 0:
        print("\n  No trades executed.\n")
        return

    print(f"\n  -- RESULTS ----------------------------------------")
    print(f"  Total Trades:    {stats['total_trades']}")
    print(f"  Wins:            {stats['wins']}")
    print(f"  Losses:          {stats['losses']}")
    print(f"  Win Rate:        {stats['win_rate']}%")
    print(f"  TP Hits:         {stats['tp_hits']}")
    print(f"  SL Hits:         {stats['sl_hits']}")
    print(f"  Timeouts:        {stats['timeouts']}")
    print(f"\n  -- PnL -------------------------------------------")
    print(f"  Gross Profit:    +{stats['gross_profit_pips']:.1f} pips")
    print(f"  Gross Loss:      {stats['gross_loss_pips']:.1f} pips")
    print(f"  Net PnL:         {stats['net_pnl_pips']:.1f} pips")
    print(f"  Profit Factor:   {stats['profit_factor']:.2f}")
    print(f"  Avg Trade:       {stats['avg_trade_pips']:.2f} pips")
    print(f"  Max Drawdown:    {stats['max_drawdown_pips']:.1f} pips")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Triangular GBP/AUD/NZD Strategy Backtest")
    parser.add_argument("--gbpaud", default="quant-lab/data/GBPAUD_M5.csv", help="GBPAUD data file")
    parser.add_argument("--gbpnzd", default="quant-lab/data/GBPNZD_M5.csv", help="GBPNZD data file")
    parser.add_argument("--audnzd", default="quant-lab/data/AUDNZD_PRO_M5.csv", help="AUDNZD data file")
    parser.add_argument("--strategy", choices=["basis", "ratio", "leadlag", "all"], default="all", help="Strategy to run")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    print("Loading data...")
    gbp_aud_bars = load_bars_csv(args.gbpaud)
    gbp_nzd_bars = load_bars_csv(args.gbpnzd)
    aud_nzd_bars = load_bars_csv(args.audnzd)

    print(f"  GBPAUD: {len(gbp_aud_bars):,} bars")
    print(f"  GBPNZD: {len(gbp_nzd_bars):,} bars")
    print(f"  AUDNZD: {len(aud_nzd_bars):,} bars")

    print("Synchronizing bars...")
    synced_bars = synchronize_bars(gbp_aud_bars, gbp_nzd_bars, aud_nzd_bars)
    print(f"  Synchronized: {len(synced_bars):,} bars")

    if len(synced_bars) < 1000:
        print("ERROR: Not enough synchronized data")
        return

    print("Computing sessions...")
    sessions = compute_sessions(synced_bars)
    print(f"  Sessions: {len(sessions)}")

    pip_gbp_aud = get_pip_size("GBPAUD")
    pip_gbp_nzd = get_pip_size("GBPNZD")
    pip_aud_nzd = get_pip_size("AUDNZD")

    all_stats = []

    if args.strategy in ("basis", "all"):
        print("\n" + "="*70)
        print("RUNNING STRATEGY 1: TRIANGULAR BASIS MEAN REVERSION")
        print("="*70)
        trades = run_triangular_basis_backtest(synced_bars, sessions, pip_gbp_aud, pip_gbp_nzd, pip_aud_nzd)
        stats = compute_stats(trades, "Triangular Basis Mean Reversion")
        print_report(stats)
        all_stats.append(stats)

    if args.strategy in ("ratio", "all"):
        print("\n" + "="*70)
        print("RUNNING STRATEGY 2: GBPAUD/GBPNZD RATIO TRADE")
        print("="*70)
        trades = run_ratio_backtest(synced_bars, sessions, pip_gbp_aud, pip_gbp_nzd, pip_aud_nzd)
        stats = compute_stats(trades, "GBPAUD/GBPNZD Ratio Trade")
        print_report(stats)
        all_stats.append(stats)

    if args.strategy in ("leadlag", "all"):
        print("\n" + "="*70)
        print("RUNNING STRATEGY 3: LEAD-LAG CATCH-UP TRADE")
        print("="*70)
        trades = run_leadlag_backtest(synced_bars, sessions, pip_gbp_aud, pip_gbp_nzd, pip_aud_nzd)
        stats = compute_stats(trades, "Lead-Lag Catch-Up Trade")
        print_report(stats)
        all_stats.append(stats)

    # Summary
    if len(all_stats) > 1:
        print("\n" + "="*70)
        print("SUMMARY COMPARISON")
        print("="*70)
        print(f"{'Strategy':<35} {'Trades':>8} {'WR%':>6} {'Net Pips':>10} {'PF':>6} {'MaxDD':>8}")
        print("-"*70)
        for s in all_stats:
            print(f"{s['strategy']:<35} {s['total_trades']:>8} {s['win_rate']:>6.1f} {s['net_pnl_pips']:>10.1f} {s['profit_factor']:>6.2f} {s['max_drawdown_pips']:>8.1f}")


if __name__ == "__main__":
    main()