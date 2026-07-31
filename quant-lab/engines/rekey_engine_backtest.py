#!/usr/bin/env python3
"""
CEREBUS FX v4.0 — Rekey Engine Backtest
=========================================

Implements the 132% Kill Switch Rekey Protocol from the Holy Grail (§6.3, p.44):
  1. MLR (Monday London Range) defines structural anchor
  2. 132% breach = pattern invalidation → EXIT ALL immediately
  3. Wait for 78.6% retest (92% prob, 4-12hrs)
  4. Enter at 50% consolidation level (85% prob)
  5. Target -50% extension (78% prob)
  6. Compound edge: 61% full sequence success, 100% rekey occurrence

STATE MACHINE:
  NORMAL → APPROACHING → CRITICAL → BREACHED → REKEY_SEQUENCE

REKEY SEQUENCES (from fib_sequence_scanner_v2.py):
  Full:           132% → 78.6% → 50% → -50%   [45% freq, 85% success, 24-36hrs]
  Partial to 50%: 132% → 78.6% → 50%          [30% freq, 70% success, 18-28hrs]
  Early Reversal: 132% → 78.6%                [15% freq, 50% success, 12-20hrs]
  Direct Ext:     132% → -50%                 [10% freq, 90% success, 8-16hrs]

Usage:
    python rekey_engine_backtest.py --csv ../data/EURUSDPRO_M5_2023_2026.csv --symbol EURUSD
    python rekey_engine_backtest.py --all-pairs
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

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Session boundaries (EST)
ASIAN_START_H = 19
ASIAN_END_H = 3
LONDON_START_H = 3
LONDON_END_H = 12

# Rekey Fibonacci levels
FIB_REKEY = 1.32
FIB_RETRACE = 0.786
FIB_CONSOL = 0.50
FIB_TARGET = 0.50

# State machine thresholds (pips from kill switch)
THRESHOLD_APPROACHING = 30
THRESHOLD_CRITICAL = 15


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class RekeyState(Enum):
    NORMAL = "NORMAL"
    APPROACHING = "APPROACHING"
    CRITICAL = "CRITICAL"
    BREACHED = "BREACHED"
    REKEY_SEQUENCE = "REKEY_SEQUENCE"


class TradeDirection(Enum):
    LONG = 1
    SHORT = -1
    FLAT = 0


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

    @property
    def body(self) -> float:
        return self.close - self.open

    @property
    def body_abs(self) -> float:
        return abs(self.close - self.open)


@dataclass
class RekeySignal:
    event: str
    direction: Optional[TradeDirection]
    entry_price: Optional[float]
    sl_price: Optional[float]
    tp_price: Optional[float]
    kill_switch: Optional[float]
    seq_type: Optional[str] = None
    mlr_range_pips: float = 0.0
    timestamp: Optional[datetime] = None
    reason: str = ""


@dataclass
class MLRData:
    monday_date: datetime.date
    high: float
    low: float
    range_pips: float
    kill_switch_long: float
    kill_switch_short: float
    bias: str


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _est_hour(dt: datetime) -> int:
    return (dt.hour - 5) % 24


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


# ═══════════════════════════════════════════════════════════════════════════════
# CSV LOADING
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
                      or clean_row.get("Datetime") or clean_row.get("DATETIME"))
            if ts_raw is None:
                time_val = (clean_row.get("time") or clean_row.get("Time") or clean_row.get("TIME")
                           or clean_row.get("<TIME>"))
                if time_val and len(time_val.strip()) > 10:
                    ts_raw = time_val.strip()
            if ts_raw is None:
                date_val = (clean_row.get("date") or clean_row.get("Date") or clean_row.get("DATE")
                           or clean_row.get("<DATE>"))
                time_val = (clean_row.get("time") or clean_row.get("Time") or clean_row.get("TIME")
                           or clean_row.get("<TIME>"))
                if date_val and time_val:
                    ts_raw = f"{date_val.strip()} {time_val.strip()}"
            if ts_raw is None or not ts_raw.strip():
                raise ValueError(f"Row {row_num}: no timestamp. Columns: {list(row.keys())}")
            o = clean_row.get("OPEN") or clean_row.get("open")
            h = clean_row.get("HIGH") or clean_row.get("high")
            l = clean_row.get("LOW") or clean_row.get("low")
            c = clean_row.get("CLOSE") or clean_row.get("close")
            if any(v is None for v in (o, h, l, c)):
                raise ValueError(f"Row {row_num}: missing OHLC. Columns: {list(row.keys())}")
            bars.append(Bar(timestamp=parse_timestamp(ts_raw), open=float(o),
                            high=float(h), low=float(l), close=float(c)))

    bars.sort(key=lambda b: b.timestamp)
    return bars


# ═══════════════════════════════════════════════════════════════════════════════
# MLR CALCULATION
# ═══════════════════════════════════════════════════════════════════════════════

def compute_mlr(bars: List[Bar], pip_size: float) -> Dict[datetime.date, MLRData]:
    """Compute Monday London Range for each week."""
    mlr_data: Dict[datetime.date, MLRData] = {}
    daily_bars: Dict[datetime.date, List[Bar]] = defaultdict(list)
    for bar in bars:
        daily_bars[bar.timestamp.date()].append(bar)

    for date, day_bars in sorted(daily_bars.items()):
        monday = date - timedelta(days=date.weekday())
        if monday.weekday() != 0:
            continue

        monday_bars = daily_bars.get(monday, [])
        london_bars = [
            b for b in monday_bars
            if 8 <= b.timestamp.hour < 16
        ]

        if len(london_bars) < 10:
            continue

        high = max(b.high for b in london_bars)
        low = min(b.low for b in london_bars)
        range_pips = (high - low) / pip_size

        if range_pips <= 0:
            continue

        kill_switch_long = low - (FIB_REKEY * (high - low))
        kill_switch_short = high + (FIB_REKEY * (high - low))

        london_close = london_bars[-1].close
        mid = low + (high - low) / 2
        bias = "BULLISH" if london_close > mid else "BEARISH"

        mlr_data[monday] = MLRData(
            monday_date=monday,
            high=high,
            low=low,
            range_pips=range_pips,
            kill_switch_long=kill_switch_long,
            kill_switch_short=kill_switch_short,
            bias=bias,
        )

    return mlr_data


# ═══════════════════════════════════════════════════════════════════════════════
# REKEY ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class RekeyEngine:
    def __init__(self, pip_size: float = 0.0001, symbol: str = "EURUSD"):
        self.pip_size = pip_size
        self.symbol = symbol
        self.logger = logging.getLogger(f"cerebus.rekey.{symbol}")

        self.state = RekeyState.NORMAL
        self.direction = TradeDirection.FLAT
        self.mlr: Optional[MLRData] = None

        self.entry_price: Optional[float] = None
        self.sl_price: Optional[float] = None
        self.tp_price: Optional[float] = None
        self.kill_switch: Optional[float] = None

        self.retest_786_hit: bool = False
        self.consolidation_50_hit: bool = False
        self.breach_timestamp: Optional[datetime] = None
        self.entry_timestamp: Optional[datetime] = None

        self.signal_log: List[RekeySignal] = []

    def initialize_week(self, mlr: MLRData) -> None:
        self.mlr = mlr
        self.state = RekeyState.NORMAL
        self.direction = TradeDirection.FLAT
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None
        self.kill_switch = None
        self.retest_786_hit = False
        self.consolidation_50_hit = False
        self.breach_timestamp = None
        self.entry_timestamp = None

    def process_bar(self, bar: Bar) -> Optional[RekeySignal]:
        if self.mlr is None:
            return None

        if self.mlr.bias == "BULLISH":
            ks = self.mlr.kill_switch_long
        else:
            ks = self.mlr.kill_switch_short

        self.kill_switch = ks

        if self.state == RekeyState.NORMAL:
            dist_pips = abs(bar.close - ks) / self.pip_size
            if dist_pips <= THRESHOLD_CRITICAL:
                self.state = RekeyState.CRITICAL
            elif dist_pips <= THRESHOLD_APPROACHING:
                self.state = RekeyState.APPROACHING
            if self._check_breach(bar, ks):
                return self._handle_breach(bar, ks)

        elif self.state == RekeyState.APPROACHING:
            dist_pips = abs(bar.close - ks) / self.pip_size
            if dist_pips <= THRESHOLD_CRITICAL:
                self.state = RekeyState.CRITICAL
            elif dist_pips > THRESHOLD_APPROACHING:
                self.state = RekeyState.NORMAL
            if self._check_breach(bar, ks):
                return self._handle_breach(bar, ks)

        elif self.state == RekeyState.CRITICAL:
            if self._check_breach(bar, ks):
                return self._handle_breach(bar, ks)

        elif self.state == RekeyState.REKEY_SEQUENCE:
            return self._process_rekey_sequence(bar)

        return None

    def _check_breach(self, bar: Bar, ks: float) -> bool:
        if self.mlr.bias == "BULLISH":
            return bar.low <= ks
        else:
            return bar.high >= ks

    def _handle_breach(self, bar: Bar, ks: float) -> RekeySignal:
        self.state = RekeyState.BREACHED
        self.breach_timestamp = bar.timestamp

        if self.mlr.bias == "BULLISH":
            breach_dir = TradeDirection.SHORT
        else:
            breach_dir = TradeDirection.LONG

        self.direction = breach_dir
        self.state = RekeyState.REKEY_SEQUENCE

        sig = RekeySignal(
            event="BREACH",
            direction=breach_dir,
            entry_price=None,
            sl_price=None,
            tp_price=None,
            kill_switch=ks,
            mlr_range_pips=self.mlr.range_pips,
            timestamp=bar.timestamp,
            reason=f"132% kill switch breached. MLR={self.mlr.range_pips:.1f}p, bias={self.mlr.bias}",
        )
        self.signal_log.append(sig)
        return sig

    def _process_rekey_sequence(self, bar: Bar) -> Optional[RekeySignal]:
        if self.mlr is None or self.breach_timestamp is None:
            return None

        mlr_high = self.mlr.high
        mlr_low = self.mlr.low
        mlr_range = mlr_high - mlr_low

        # Rekey levels: entry at 50% consolidation, target -50% from entry
        if self.direction == TradeDirection.SHORT:
            # Price breached below KS (bearish), retest up to 78.6%, enter at 50%
            retest_786 = mlr_low + (mlr_range * FIB_RETRACE)
            consolidation_50 = mlr_low + (mlr_range * FIB_CONSOL)
            # Target: -50% of MLR below the consolidation entry
            target_neg50 = consolidation_50 - (mlr_range * FIB_TARGET)
        else:
            # Price breached above KS (bullish), retest down to 78.6%, enter at 50%
            retest_786 = mlr_high - (mlr_range * FIB_RETRACE)
            consolidation_50 = mlr_high - (mlr_range * FIB_CONSOL)
            # Target: -50% of MLR above the consolidation entry
            target_neg50 = consolidation_50 + (mlr_range * FIB_TARGET)

        # Step 2: Check for 78.6% retest
        if not self.retest_786_hit:
            if self.direction == TradeDirection.SHORT:
                if bar.high >= retest_786:
                    self.retest_786_hit = True
            else:
                if bar.low <= retest_786:
                    self.retest_786_hit = True

        # Step 3: Check for 50% consolidation (entry trigger)
        elif not self.consolidation_50_hit:
            if self.direction == TradeDirection.SHORT:
                if bar.low <= consolidation_50:
                    self.consolidation_50_hit = True
                    return self._enter_rekey_trade(bar, consolidation_50, target_neg50)
            else:
                if bar.high >= consolidation_50:
                    self.consolidation_50_hit = True
                    return self._enter_rekey_trade(bar, consolidation_50, target_neg50)

        # Step 4: In trade — check TP/SL
        elif self.entry_price is not None:
            if self.direction == TradeDirection.SHORT:
                # SL above MLR high + buffer (168% from low)
                sl = mlr_high + (mlr_range * 0.32)
                if bar.high >= sl:
                    return self._exit_trade(bar, sl, "SL_HIT")
                if bar.low <= self.tp_price:
                    return self._exit_trade(bar, self.tp_price, "TP_HIT")
            else:
                # SL below MLR low - buffer
                sl = mlr_low - (mlr_range * 0.32)
                if bar.low <= sl:
                    return self._exit_trade(bar, sl, "SL_HIT")
                if bar.high >= self.tp_price:
                    return self._exit_trade(bar, self.tp_price, "TP_HIT")

        # Timeout: 72 hours
        if bar.timestamp - self.breach_timestamp > timedelta(hours=72):
            self._reset_state()
            sig = RekeySignal(
                event="TIMEOUT",
                direction=self.direction,
                entry_price=None,
                sl_price=None,
                tp_price=None,
                kill_switch=self.kill_switch,
                mlr_range_pips=self.mlr.range_pips,
                timestamp=bar.timestamp,
                reason="Rekey sequence timeout (72h)",
            )
            self.signal_log.append(sig)
            return sig

        return None

    def _enter_rekey_trade(self, bar: Bar, entry: float, target: float) -> RekeySignal:
        self.entry_price = entry
        self.entry_timestamp = bar.timestamp
        self.tp_price = target

        if self.mlr is not None:
            mlr_range = self.mlr.high - self.mlr.low
            if self.direction == TradeDirection.SHORT:
                # SL above MLR high + 32% buffer
                self.sl_price = self.mlr.high + (mlr_range * 0.32)
            else:
                # SL below MLR low - 32% buffer
                self.sl_price = self.mlr.low - (mlr_range * 0.32)

        sig = RekeySignal(
            event="REKEY_ENTRY",
            direction=self.direction,
            entry_price=entry,
            sl_price=self.sl_price,
            tp_price=target,
            kill_switch=self.kill_switch,
            mlr_range_pips=self.mlr.range_pips if self.mlr else 0,
            timestamp=bar.timestamp,
            reason=f"Rekey entry at 50% consolidation. Target -50% extension.",
        )
        self.signal_log.append(sig)
        return sig

    def _exit_trade(self, bar: Bar, exit_price: float, event: str) -> RekeySignal:
        sig = RekeySignal(
            event=event,
            direction=self.direction,
            entry_price=self.entry_price,
            sl_price=self.sl_price,
            tp_price=self.tp_price,
            kill_switch=self.kill_switch,
            mlr_range_pips=self.mlr.range_pips if self.mlr else 0,
            timestamp=bar.timestamp,
            reason=f"Rekey exit: {event} @ {exit_price:.5f}",
        )
        self.signal_log.append(sig)
        self._reset_state()
        return sig

    def _reset_state(self) -> None:
        self.state = RekeyState.NORMAL
        self.direction = TradeDirection.FLAT
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None
        self.retest_786_hit = False
        self.consolidation_50_hit = False
        self.breach_timestamp = None
        self.entry_timestamp = None


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICS
# ═══════════════════════════════════════════════════════════════════════════════

def compute_stats(signals: List[RekeySignal], pip_size: float) -> Dict:
    completed = [s for s in signals if s.event in ("TP_HIT", "SL_HIT")]
    breaches = [s for s in signals if s.event == "BREACH"]
    entries = [s for s in signals if s.event == "REKEY_ENTRY"]
    timeouts = [s for s in signals if s.event == "TIMEOUT"]

    pnls_pips: List[float] = []
    for sig in completed:
        if sig.entry_price is None or sig.tp_price is None or sig.sl_price is None:
            continue
        if sig.event == "TP_HIT":
            exit_price = sig.tp_price
        elif sig.event == "SL_HIT":
            exit_price = sig.sl_price
        else:
            continue

        if sig.direction == TradeDirection.LONG:
            pnl = (exit_price - sig.entry_price) / pip_size
        else:
            pnl = (sig.entry_price - exit_price) / pip_size
        pnls_pips.append(pnl)

    if not pnls_pips:
        return {
            "total_breaches": len(breaches),
            "total_entries": len(entries),
            "total_trades": 0,
            "total_timeouts": len(timeouts),
            "wins": 0, "losses": 0, "win_rate": 0.0,
            "gross_profit_pips": 0.0, "gross_loss_pips": 0.0,
            "profit_factor": 0.0, "max_drawdown_pips": 0.0,
            "avg_trade_pips": 0.0, "avg_mlr_range_pips": 0.0,
        }

    wins = [p for p in pnls_pips if p > 0]
    losses = [p for p in pnls_pips if p < 0]
    total = len(pnls_pips)
    win_rate = len(wins) / total * 100 if total > 0 else 0.0
    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0
    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    avg_trade = sum(pnls_pips) / total if total > 0 else 0.0

    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for pnl in pnls_pips:
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    mlr_ranges = [s.mlr_range_pips for s in completed if s.mlr_range_pips > 0]
    avg_mlr = sum(mlr_ranges) / len(mlr_ranges) if mlr_ranges else 0.0

    return {
        "total_breaches": len(breaches),
        "total_entries": len(entries),
        "total_trades": total,
        "total_timeouts": len(timeouts),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "gross_profit_pips": round(gross_profit, 1),
        "gross_loss_pips": round(-gross_loss, 1),
        "profit_factor": round(pf, 2),
        "avg_trade_pips": round(avg_trade, 2),
        "max_drawdown_pips": round(max_dd, 1),
        "avg_mlr_range_pips": round(avg_mlr, 1),
        "net_pnl_pips": round(gross_profit - gross_loss, 1),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def print_report(stats: Dict, symbol: str, total_weeks: int, total_bars: int):
    print()
    print("=" * 70)
    print(f"  REKEY ENGINE -- BACKTEST REPORT")
    print(f"  Symbol: {symbol}")
    print(f"  Weeks analyzed: {total_weeks} | Bars processed: {total_bars:,}")
    print("=" * 70)

    print(f"\n  -- REKEY ACTIVITY ------------------------------------")
    print(f"  Total 132% Breaches:  {stats['total_breaches']}")
    print(f"  Rekey Entries:        {stats['total_entries']}")
    print(f"  Completed Trades:     {stats['total_trades']}")
    print(f"  Timeouts (72h):       {stats['total_timeouts']}")
    print(f"  Avg MLR Range:        {stats['avg_mlr_range_pips']:.1f} pips")

    if stats['total_trades'] == 0:
        print(f"\n  No completed rekey trades.\n")
        return

    print(f"\n  -- TRADE PERFORMANCE ---------------------------------")
    print(f"  Total Trades:    {stats['total_trades']}")
    print(f"  Wins:            {stats['wins']}")
    print(f"  Losses:          {stats['losses']}")
    print(f"  Win Rate:        {stats['win_rate']}%")
    print(f"  Gross Profit:    +{stats['gross_profit_pips']:.1f} pips")
    print(f"  Gross Loss:      {stats['gross_loss_pips']:.1f} pips")
    print(f"  Net PnL:         {stats['net_pnl_pips']:+.1f} pips")
    print(f"  Profit Factor:   {stats['profit_factor']}")
    print(f"  Avg Trade:       {stats['avg_trade_pips']:+.2f} pips")
    print(f"  Max Drawdown:    {stats['max_drawdown_pips']:.1f} pips")

    print()
    print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN BACKTEST
# ═══════════════════════════════════════════════════════════════════════════════

def run_backtest(csv_path: str, symbol: str, pip_size: float = None) -> Dict:
    if pip_size is None:
        pip_size = get_pip_size(symbol)

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    print(f"[REKEY] Loading bars from: {csv_path}")
    bars = load_bars_csv(csv_path)
    print(f"[REKEY] Loaded {len(bars):,} bars")

    if not bars:
        print("[REKEY] ERROR: No bars loaded.")
        return {}

    mlr_data = compute_mlr(bars, pip_size)
    print(f"[REKEY] Computed {len(mlr_data)} weekly MLR values")

    weekly_bars: Dict[datetime.date, List[Bar]] = defaultdict(list)
    for bar in bars:
        monday = bar.timestamp.date() - timedelta(days=bar.timestamp.weekday())
        weekly_bars[monday].append(bar)

    engine = RekeyEngine(pip_size=pip_size, symbol=symbol)
    total_bars_processed = 0

    for monday in sorted(mlr_data.keys()):
        mlr = mlr_data[monday]
        week_bars = weekly_bars.get(monday, [])

        if not week_bars:
            continue

        engine.initialize_week(mlr)

        for bar in sorted(week_bars, key=lambda b: b.timestamp):
            est_hour = _est_hour(bar.timestamp)
            if ASIAN_START_H <= est_hour or est_hour < ASIAN_END_H:
                continue
            engine.process_bar(bar)
            total_bars_processed += 1

    all_signals = engine.signal_log
    stats = compute_stats(all_signals, pip_size)
    print_report(stats, symbol, len(mlr_data), total_bars_processed)

    return stats


def run_all_pairs(data_dir: str):
    data_path = Path(data_dir)
    csv_files = sorted(data_path.glob("*_M5*.csv"))
    pro_files = [f for f in csv_files if "PRO" in f.name]
    if not pro_files:
        pro_files = csv_files

    all_results = {}

    for csv_file in pro_files[:20]:
        symbol = csv_file.stem.replace("_M5", "").replace("_PRO", "").replace("_2023_2026", "").replace("_2022_2026", "")
        pip_size = get_pip_size(symbol)

        print(f"\n{'='*70}")
        print(f"  Testing: {symbol} ({csv_file.name})")
        print(f"{'='*70}")

        try:
            stats = run_backtest(str(csv_file), symbol, pip_size)
            all_results[symbol] = stats
        except Exception as e:
            print(f"[REKEY] ERROR for {symbol}: {e}")
            continue

    print(f"\n\n{'='*70}")
    print(f"  REKEY ENGINE -- MULTI-PAIR SUMMARY")
    print(f"{'='*70}")
    print(f"\n  {'Pair':<12} {'Breaches':>10} {'Trades':>8} {'WR':>8} {'Net PnL':>12} {'PF':>8} {'MaxDD':>8}")
    print(f"  {'-'*66}")

    for symbol, stats in sorted(all_results.items(), key=lambda x: x[1].get('net_pnl_pips', 0), reverse=True):
        if stats.get('total_trades', 0) > 0:
            print(f"  {symbol:<12} {stats['total_breaches']:>10} {stats['total_trades']:>8} "
                  f"{stats['win_rate']:>7.1f}% {stats['net_pnl_pips']:>+11.1f}p "
                  f"{stats['profit_factor']:>7.2f} {stats['max_drawdown_pips']:>7.1f}p")

    return all_results


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="CEREBUS Rekey Engine Backtest -- 132% Kill Switch Protocol")
    parser.add_argument("--csv", type=str, help="Path to M5 bar CSV file")
    parser.add_argument("--symbol", type=str, default="EURUSD", help="Symbol (default: EURUSD)")
    parser.add_argument("--pip-size", type=float, default=None, help="Pip size (auto-detected if not specified)")
    parser.add_argument("--all-pairs", action="store_true", help="Test all pairs in quant-lab/data/")
    parser.add_argument("--data-dir", type=str, default=str(Path(__file__).parent.parent / "data"),
                        help="Data directory for --all-pairs mode")
    args = parser.parse_args()

    if args.all_pairs:
        run_all_pairs(args.data_dir)
    elif args.csv:
        run_backtest(args.csv, args.symbol, args.pip_size)
    else:
        default_csv = str(Path(__file__).parent.parent / "data" / "EURUSDPRO_M5_2023_2026.csv")
        run_backtest(default_csv, "EURUSD")


if __name__ == "__main__":
    main()
