#!/usr/bin/env python3
"""
CEREBUS — Triangular Basis Engine (Production Version)
=======================================================

Market-neutral statistical arbitrage on GBP/AUD/NZD triangle.

Strategy: Triangular Basis Mean Reversion
- Basis = ln(GBPAUD) - ln(GBPNZD) + ln(AUDNZD)
- Entry: |z-score| > 2.0 (100-bar rolling)
- Exit: z-score → 0
- Stop: |z-score| > 4.0
- Hard exit: 12 PM EST
- Position sizing: Volatility-weighted (inverse ATR)

This is a TRUE market-neutral strategy - GBP, AUD, NZD exposures cancel.
Zero correlation to directional CEREBUS strategies.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, date
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class Config:
    # Session times (EST)
    ASIAN_START_H_EST = 19
    ASIAN_END_H_EST = 3
    LONDON_START_H_EST = 3
    LONDON_END_H_EST = 12
    HARD_EXIT_H_EST = 12
    
    # Basis parameters
    BASIS_LOOKBACK = 100
    BASIS_ENTRY_Z = 3.0          # Increased from 2.0 - wait for larger dislocations
    BASIS_EXIT_Z = 0.0
    BASIS_STOP_Z = 5.0           # Wider stop
    
    # Session filter - ONLY trade London session
    TRADE_LONDON_ONLY = True
    MIN_MINUTES_TO_EXIT = 120    # Don't enter if less than 2 hours to hard exit
    
    # Position sizing
    ATR_PERIOD = 20
    TARGET_RISK_PER_LEG = 1.0
    MAX_TOTAL_LEVERAGE = 3.0
    
    # Risk management
    MAX_CONCURRENT_TRADES = 1
    MAX_DAILY_LOSS_PIPS = 500
    
    # Costs (pips per round trip per leg)
    SPREAD_GBPAUD = 1.5
    SPREAD_GBPNZD = 2.5
    SPREAD_AUDNZD = 2.0
    COMMISSION_PIPS_PER_100K = 1.4


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class Direction(Enum):
    LONG = 1      # Long GBPAUD, Short GBPNZD, Long AUDNZD (basis cheap)
    SHORT = -1    # Short GBPAUD, Long GBPNZD, Short AUDNZD (basis rich)
    FLAT = 0


class TradeResult(Enum):
    TP_HIT = "TP_HIT"
    SL_HIT = "SL_HIT"
    TIMEOUT = "TIMEOUT"
    NO_ENTRY = "NO_ENTRY"
    COST_FILTER = "COST_FILTER"


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
    """Complete trade record with all three legs"""
    # Identification
    trade_id: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    
    # Direction
    direction: Direction = Direction.FLAT
    
    # Entry prices (per leg)
    entry_gbp_aud: float = 0.0
    entry_gbp_nzd: float = 0.0
    entry_aud_nzd: float = 0.0
    
    # Exit prices (per leg)
    exit_gbp_aud: float = 0.0
    exit_gbp_nzd: float = 0.0
    exit_aud_nzd: float = 0.0
    
    # Position sizes (per leg, volatility-normalized)
    size_gbp_aud: float = 0.0
    size_gbp_nzd: float = 0.0
    size_aud_nzd: float = 0.0
    
    # PnL (per leg in pips)
    pnl_gbp_aud: float = 0.0
    pnl_gbp_nzd: float = 0.0
    pnl_aud_nzd: float = 0.0
    pnl_gross_pips: float = 0.0
    pnl_costs_pips: float = 0.0
    pnl_net_pips: float = 0.0
    
    # Result
    result: TradeResult = TradeResult.NO_ENTRY
    
    # Basis values
    entry_basis: float = 0.0
    entry_zscore: float = 0.0
    exit_basis: float = 0.0
    exit_zscore: float = 0.0
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['direction'] = self.direction.name
        d['result'] = self.result.name
        d['entry_time'] = self.entry_time.isoformat() if self.entry_time else None
        d['exit_time'] = self.exit_time.isoformat() if self.exit_time else None
        return d


@dataclass
class SessionData:
    date: date
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


def _session_date(dt: datetime) -> date:
    h = _est_hour(dt)
    if h >= Config.ASIAN_START_H_EST:
        return (dt + timedelta(days=1)).date()
    return dt.date()


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
                continue
            o = clean_row.get("OPEN") or clean_row.get("open")
            h = clean_row.get("HIGH") or clean_row.get("high")
            l = clean_row.get("LOW") or clean_row.get("low")
            c = clean_row.get("CLOSE") or clean_row.get("close")
            v = clean_row.get("VOLUME") or clean_row.get("volume") or clean_row.get("Volume") or "0"
            if any(v is None for v in (o, h, l, c)):
                continue
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
    """Synchronize three bar series by timestamp."""
    gbp_aud_map = {b.timestamp: b for b in gbp_aud_bars}
    gbp_nzd_map = {b.timestamp: b for b in gbp_nzd_bars}
    aud_nzd_map = {b.timestamp: b for b in aud_nzd_bars}

    all_timestamps = set(gbp_aud_map.keys()) | set(gbp_nzd_map.keys()) | set(aud_nzd_map.keys())
    all_timestamps = sorted(all_timestamps)

    synced = []
    for ts in all_timestamps:
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
    sessions: Dict[date, Dict] = defaultdict(lambda: {
        "asian_gbp_aud": [], "london_gbp_aud": [],
        "asian_gbp_nzd": [], "london_gbp_nzd": [],
        "asian_aud_nzd": [], "london_aud_nzd": [],
    })

    for bar in bars:
        sdate = _session_date(bar.timestamp)
        est_h = _est_hour(bar.timestamp)

        if est_h >= Config.ASIAN_START_H_EST or est_h < Config.ASIAN_END_H_EST:
            sessions[sdate]["asian_gbp_aud"].append(bar)
            sessions[sdate]["asian_gbp_nzd"].append(bar)
            sessions[sdate]["asian_aud_nzd"].append(bar)
        elif Config.LONDON_START_H_EST <= est_h < Config.LONDON_END_H_EST:
            sessions[sdate]["london_gbp_aud"].append(bar)
            sessions[sdate]["london_gbp_nzd"].append(bar)
            sessions[sdate]["london_aud_nzd"].append(bar)

    result = []
    for sdate in sorted(sessions.keys()):
        data = sessions[sdate]
        if not all([
            data["asian_gbp_aud"], data["london_gbp_aud"],
            data["asian_gbp_nzd"], data["london_gbp_nzd"],
            data["asian_aud_nzd"], data["london_aud_nzd"],
        ]):
            continue

        result.append(SessionData(
            date=sdate,
            asian_high_gbp_aud=max(b.gbp_aud_high for b in data["asian_gbp_aud"]),
            asian_low_gbp_aud=min(b.gbp_aud_low for b in data["asian_gbp_aud"]),
            asian_high_gbp_nzd=max(b.gbp_nzd_high for b in data["asian_gbp_nzd"]),
            asian_low_gbp_nzd=min(b.gbp_nzd_low for b in data["asian_gbp_nzd"]),
            asian_high_aud_nzd=max(b.aud_nzd_high for b in data["asian_aud_nzd"]),
            asian_low_aud_nzd=min(b.aud_nzd_low for b in data["asian_aud_nzd"]),
            london_close_gbp_aud=data["london_gbp_aud"][-1].gbp_aud,
            london_close_gbp_nzd=data["london_gbp_nzd"][-1].gbp_nzd,
            london_close_aud_nzd=data["london_aud_nzd"][-1].aud_nzd,
        ))

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# BASIS COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════════

def compute_basis(bars: List[TriangularBar]) -> List[float]:
    """Triangular basis: ln(GBPAUD) - ln(GBPNZD) + ln(AUDNZD)"""
    return [np.log(b.gbp_aud) - np.log(b.gbp_nzd) + np.log(b.aud_nzd) for b in bars]


def compute_basis_zscore(basis: List[float], lookback: int) -> List[float]:
    """Rolling z-score of basis."""
    z_scores = []
    for i in range(len(basis)):
        if i < lookback:
            z_scores.append(0.0)
        else:
            window = basis[i-lookback:i]
            mean = np.mean(window)
            std = np.std(window)
            z_scores.append((basis[i] - mean) / std if std > 0 else 0.0)
    return z_scores


# ═══════════════════════════════════════════════════════════════════════════════
# BACKTEST ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class TriangularBasisEngine:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.pip_gbp_aud = get_pip_size("GBPAUD")
        self.pip_gbp_nzd = get_pip_size("GBPNZD")
        self.pip_aud_nzd = get_pip_size("AUDNZD")
        self.trades: List[Trade] = []
        self.current_trade: Optional[Trade] = None
        self.in_trade = False
        self.daily_pnl = defaultdict(float)
        self.trade_counter = 0

    def run_backtest(self, bars: List[TriangularBar], sessions: List[SessionData]) -> List[Trade]:
        """Run complete backtest."""
        print(f"Computing basis and z-scores...")
        basis = compute_basis(bars)
        z_scores = compute_basis_zscore(basis, self.config.BASIS_LOOKBACK)
        
        print(f"Computing ATR for position sizing...")
        atr_gbp_aud = compute_atr(bars, 'gbp_aud', self.config.ATR_PERIOD)
        atr_gbp_nzd = compute_atr(bars, 'gbp_nzd', self.config.ATR_PERIOD)
        atr_aud_nzd = compute_atr(bars, 'aud_nzd', self.config.ATR_PERIOD)

        print(f"Running backtest on {len(bars):,} bars...")
        
        for i, bar in enumerate(bars):
            z = z_scores[i]
            b = basis[i]
            est_h = _est_hour(bar.timestamp)
            sdate = _session_date(bar.timestamp)

            # Check daily loss limit
            if self.daily_pnl[sdate] <= -self.config.MAX_DAILY_LOSS_PIPS:
                if self.in_trade:
                    self._exit_trade(bar, i, basis, z_scores, TradeResult.SL_HIT, "Daily loss limit")
                continue

            # Hard exit at 12 PM EST
            if est_h >= self.config.HARD_EXIT_H_EST and self.in_trade:
                self._exit_trade(bar, i, basis, z_scores, TradeResult.TIMEOUT, "Hard exit 12PM EST")
                continue

            # Entry logic
            if not self.in_trade:
                # Session filter: only trade London session (3AM-12PM EST)
                if self.config.TRADE_LONDON_ONLY:
                    if not (self.config.LONDON_START_H_EST <= est_h < self.config.LONDON_END_H_EST):
                        continue
                
                # Minimum time to hard exit filter
                minutes_to_exit = (self.config.HARD_EXIT_H_EST - est_h) * 60
                if minutes_to_exit < self.config.MIN_MINUTES_TO_EXIT:
                    continue
                
                if z > self.config.BASIS_ENTRY_Z:
                    self._enter_trade(bar, i, basis, z_scores, atr_gbp_aud, atr_gbp_nzd, atr_aud_nzd, Direction.SHORT)
                elif z < -self.config.BASIS_ENTRY_Z:
                    self._enter_trade(bar, i, basis, z_scores, atr_gbp_aud, atr_gbp_nzd, atr_aud_nzd, Direction.LONG)

            # Exit logic
            if self.in_trade:
                if self.current_trade.direction == Direction.SHORT:
                    if z <= self.config.BASIS_EXIT_Z:
                        self._exit_trade(bar, i, basis, z_scores, TradeResult.TP_HIT, "Mean reversion")
                    elif z >= self.config.BASIS_STOP_Z:
                        self._exit_trade(bar, i, basis, z_scores, TradeResult.SL_HIT, "Stop loss")
                else:  # LONG
                    if z >= self.config.BASIS_EXIT_Z:
                        self._exit_trade(bar, i, basis, z_scores, TradeResult.TP_HIT, "Mean reversion")
                    elif z <= -self.config.BASIS_STOP_Z:
                        self._exit_trade(bar, i, basis, z_scores, TradeResult.SL_HIT, "Stop loss")

        print(f"Backtest complete: {len(self.trades)} trades")
        return self.trades

    def _enter_trade(self, bar: TriangularBar, idx: int, basis: List[float], z_scores: List[float],
                     atr_gbp_aud: List[float], atr_gbp_nzd: List[float], atr_aud_nzd: List[float],
                     direction: Direction):
        """Enter a new triangular trade."""
        # Volatility-weighted position sizing
        size_gbp_aud = 1.0 / atr_gbp_aud[idx] if atr_gbp_aud[idx] > 0 else 1.0
        size_gbp_nzd = 1.0 / atr_gbp_nzd[idx] if atr_gbp_nzd[idx] > 0 else 1.0
        size_aud_nzd = 1.0 / atr_aud_nzd[idx] if atr_aud_nzd[idx] > 0 else 1.0
        
        # Normalize to target total leverage
        total_size = size_gbp_aud + size_gbp_nzd + size_aud_nzd
        scale = self.config.MAX_TOTAL_LEVERAGE / total_size
        size_gbp_aud *= scale
        size_gbp_nzd *= scale
        size_aud_nzd *= scale

        self.trade_counter += 1
        trade_id = f"TRI_{bar.timestamp.strftime('%Y%m%d_%H%M%S')}_{self.trade_counter}"
        
        self.current_trade = Trade(
            trade_id=trade_id,
            entry_time=bar.timestamp,
            direction=direction,
            entry_gbp_aud=bar.gbp_aud,
            entry_gbp_nzd=bar.gbp_nzd,
            entry_aud_nzd=bar.aud_nzd,
            size_gbp_aud=size_gbp_aud,
            size_gbp_nzd=size_gbp_nzd,
            size_aud_nzd=size_aud_nzd,
            entry_basis=basis[idx],
            entry_zscore=z_scores[idx],
        )
        self.in_trade = True

    def _exit_trade(self, bar: TriangularBar, idx: int, basis: List[float], z_scores: List[float],
                    result: TradeResult, reason: str):
        """Exit current trade and calculate PnL."""
        if not self.current_trade:
            return

        t = self.current_trade
        t.exit_time = bar.timestamp
        t.exit_gbp_aud = bar.gbp_aud
        t.exit_gbp_nzd = bar.gbp_nzd
        t.exit_aud_nzd = bar.aud_nzd
        t.exit_basis = basis[idx]
        t.exit_zscore = z_scores[idx]
        t.result = result

        # Calculate PnL per leg (in pips)
        if t.direction == Direction.SHORT:
            # Short GBPAUD, Long GBPNZD, Short AUDNZD
            t.pnl_gbp_aud = (t.entry_gbp_aud - bar.gbp_aud) / self.pip_gbp_aud * t.size_gbp_aud
            t.pnl_gbp_nzd = (bar.gbp_nzd - t.entry_gbp_nzd) / self.pip_gbp_nzd * t.size_gbp_nzd
            t.pnl_aud_nzd = (t.entry_aud_nzd - bar.aud_nzd) / self.pip_aud_nzd * t.size_aud_nzd
        else:  # LONG
            # Long GBPAUD, Short GBPNZD, Long AUDNZD
            t.pnl_gbp_aud = (bar.gbp_aud - t.entry_gbp_aud) / self.pip_gbp_aud * t.size_gbp_aud
            t.pnl_gbp_nzd = (t.entry_gbp_nzd - bar.gbp_nzd) / self.pip_gbp_nzd * t.size_gbp_nzd
            t.pnl_aud_nzd = (bar.aud_nzd - t.entry_aud_nzd) / self.pip_aud_nzd * t.size_aud_nzd

        t.pnl_gross_pips = t.pnl_gbp_aud + t.pnl_gbp_nzd + t.pnl_aud_nzd

        # Calculate costs (spread + commission for 3 legs, round trip)
        t.pnl_costs_pips = (
            self.config.SPREAD_GBPAUD + self.config.SPREAD_GBPNZD + self.config.SPREAD_AUDNZD +
            self.config.COMMISSION_PIPS_PER_100K * 3
        ) * (t.size_gbp_aud + t.size_gbp_nzd + t.size_aud_nzd) / 3.0

        t.pnl_net_pips = t.pnl_gross_pips - t.pnl_costs_pips

        # Update daily PnL
        sdate = _session_date(bar.timestamp)
        self.daily_pnl[sdate] += t.pnl_net_pips

        self.trades.append(t)
        self.in_trade = False
        self.current_trade = None


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICS & REPORTING
# ═══════════════════════════════════════════════════════════════════════════════

def compute_stats(trades: List[Trade]) -> Dict:
    if not trades:
        return {"total_trades": 0}

    wins = [t for t in trades if t.pnl_net_pips > 0]
    losses = [t for t in trades if t.pnl_net_pips < 0]
    total = len(trades)
    win_rate = len(wins) / total * 100 if total > 0 else 0.0

    gross_profit = sum(t.pnl_net_pips for t in wins) if wins else 0.0
    gross_loss = abs(sum(t.pnl_net_pips for t in losses)) if losses else 0.0
    net_pnl = gross_profit - gross_loss
    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    avg_trade = net_pnl / total if total > 0 else 0.0

    # Max drawdown
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trades:
        cumulative += t.pnl_net_pips
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    tp_hits = len([t for t in trades if t.result == TradeResult.TP_HIT])
    sl_hits = len([t for t in trades if t.result == TradeResult.SL_HIT])
    timeouts = len([t for t in trades if t.result == TradeResult.TIMEOUT])

    # By session
    session_pnl = defaultdict(float)
    for t in trades:
        session_pnl[t.entry_time.date()] += t.pnl_net_pips

    return {
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
        "avg_gross_pips": round(np.mean([t.pnl_gross_pips for t in trades]), 2),
        "avg_costs_pips": round(np.mean([t.pnl_costs_pips for t in trades]), 2),
        "avg_net_pips": round(np.mean([t.pnl_net_pips for t in trades]), 2),
        "profitable_days": len([d for d in session_pnl.values() if d > 0]),
        "losing_days": len([d for d in session_pnl.values() if d < 0]),
    }


def print_report(stats: Dict):
    print()
    print("=" * 70)
    print("  TRIANGULAR BASIS ENGINE -- BACKTEST REPORT")
    print("=" * 70)

    if stats['total_trades'] == 0:
        print("\n  No trades executed.\n")
        return

    print(f"\n  -- RESULTS ----------------------------------------")
    print(f"  Total Trades:       {stats['total_trades']}")
    print(f"  Wins:               {stats['wins']}")
    print(f"  Losses:             {stats['losses']}")
    print(f"  Win Rate:           {stats['win_rate']}%")
    print(f"  TP Hits:            {stats['tp_hits']}")
    print(f"  SL Hits:            {stats['sl_hits']}")
    print(f"  Timeouts:           {stats['timeouts']}")
    print(f"  Profitable Days:    {stats.get('profitable_days', 'N/A')}")
    print(f"  Losing Days:        {stats.get('losing_days', 'N/A')}")
    
    print(f"\n  -- PnL (NET, after costs) -------------------------")
    print(f"  Gross Profit:       +{stats['gross_profit_pips']:.1f} pips")
    print(f"  Gross Loss:         {stats['gross_loss_pips']:.1f} pips")
    print(f"  Net PnL:            {stats['net_pnl_pips']:.1f} pips")
    print(f"  Profit Factor:      {stats['profit_factor']:.2f}")
    print(f"  Avg Trade:          {stats['avg_trade_pips']:.2f} pips")
    print(f"  Max Drawdown:       {stats['max_drawdown_pips']:.1f} pips")
    
    print(f"\n  -- COST ANALYSIS ----------------------------------")
    print(f"  Avg Gross/Trade:    {stats.get('avg_gross_pips', 0):.2f} pips")
    print(f"  Avg Costs/Trade:    {stats.get('avg_costs_pips', 0):.2f} pips")
    print(f"  Avg Net/Trade:      {stats.get('avg_net_pips', 0):.2f} pips")
    print(f"  Cost Ratio:         {stats.get('avg_costs_pips', 0)/max(stats.get('avg_gross_pips', 1), 1)*100:.1f}%")
    print()


def save_trades_json(trades: List[Trade], filepath: str):
    """Save trades to JSON for analysis."""
    data = [t.to_dict() for t in trades]
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(trades)} trades to {filepath}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="CEREBUS Triangular Basis Engine")
    parser.add_argument("--gbpaud", default="quant-lab/data/GBPAUD_M5.csv")
    parser.add_argument("--gbpnzd", default="quant-lab/data/GBPNZD_M5.csv")
    parser.add_argument("--audnzd", default="quant-lab/data/AUDNZD_PRO_M5.csv")
    parser.add_argument("--output", default="quant-lab/reports/triangular_trades.json")
    parser.add_argument("--entry-z", type=float, default=2.0)
    parser.add_argument("--stop-z", type=float, default=4.0)
    parser.add_argument("--lookback", type=int, default=100)
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")

    # Override config from args
    Config.BASIS_ENTRY_Z = args.entry_z
    Config.BASIS_STOP_Z = args.stop_z
    Config.BASIS_LOOKBACK = args.lookback

    print("=" * 70)
    print("  CEREBUS TRIANGULAR BASIS ENGINE")
    print("  GBP/AUD/NZD Market-Neutral Statistical Arbitrage")
    print("=" * 70)
    print(f"  Entry Z: {Config.BASIS_ENTRY_Z} | Stop Z: {Config.BASIS_STOP_Z} | Lookback: {Config.BASIS_LOOKBACK}")
    print()

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

    # Run backtest
    engine = TriangularBasisEngine()
    trades = engine.run_backtest(synced_bars, sessions)

    # Statistics
    stats = compute_stats(trades)
    print_report(stats)

    # Save trades
    if trades:
        save_trades_json(trades, args.output)

    # Summary for parameter sweep
    print(f"\n  -- PARAMETER SUMMARY ------------------------------")
    print(f"  entry_z={Config.BASIS_ENTRY_Z}, stop_z={Config.BASIS_STOP_Z}, lookback={Config.BASIS_LOOKBACK}")
    print(f"  net_pnl={stats.get('net_pnl_pips', 0):.1f}, pf={stats.get('profit_factor', 0):.2f}, wr={stats.get('win_rate', 0):.1f}%")
    print(f"  max_dd={stats.get('max_drawdown_pips', 0):.1f}, trades={stats.get('total_trades', 0)}")


if __name__ == "__main__":
    main()