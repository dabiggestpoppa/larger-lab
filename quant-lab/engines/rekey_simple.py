#!/usr/bin/env python3
"""
CEREBUS — Simple Rekey Engine (Intraday)
=========================================

DIRECTION (from Quant Bible §1.6):
  Bullish: London close > Asian midpoint
  Bearish: London close < Asian midpoint

TRADE SETUP:
  - Limit order at 132% of Asian Range from the breached band
  - SL = 5 pips below 168% level
  - TP = 0 level (opposite Asian band — full range retracement)
  - Intraday only (close by 12 PM EST)

FORMULAS:
  Asian Midpoint = Asian Low + (Asian Range / 2)
  132% Level (Bullish) = Asian Low - (1.32 × Asian Range)
  132% Level (Bearish) = Asian High + (1.32 × Asian Range)
  168% Level (Bullish) = Asian Low - (1.68 × Asian Range)
  168% Level (Bearish) = Asian High + (1.68 × Asian Range)
  SL (Bullish) = 168% Level - 5 pips
  SL (Bearish) = 168% Level + 5 pips
  TP (Bullish) = Asian High (0 level = opposite band)
  TP (Bearish) = Asian Low (0 level = opposite band)
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

ASIAN_START_H_EST = 19
ASIAN_END_H_EST = 3
LONDON_START_H_EST = 3
LONDON_END_H_EST = 12
HARD_EXIT_H_EST = 12

FIB_REKEY = 1.32
FIB_168 = 1.68
SL_BUFFER_PIPS = 5


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


@dataclass
class Trade:
    direction: Direction
    entry_price: float
    sl_price: float
    tp_price: float
    entry_time: datetime
    result: Optional[TradeResult] = None
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl_pips: float = 0.0


@dataclass
class SessionData:
    date: datetime.date
    asian_high: float
    asian_low: float
    asian_range: float
    asian_mid: float
    london_close: Optional[float] = None
    bias: Direction = Direction.FLAT


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
# SESSION PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

def _est_hour(dt: datetime) -> int:
    return (dt.hour - 5) % 24


def _session_date(dt: datetime):
    h = _est_hour(dt)
    if h >= ASIAN_START_H_EST:
        return (dt + timedelta(days=1)).date()
    return dt.date()


def compute_sessions(bars: List[Bar]) -> List[SessionData]:
    """Group bars into sessions and compute Asian range + London close."""
    sessions: Dict[datetime.date, Dict] = defaultdict(lambda: {"asian": [], "london": []})

    for bar in bars:
        sdate = _session_date(bar.timestamp)
        est_h = _est_hour(bar.timestamp)

        if est_h >= ASIAN_START_H_EST or est_h < ASIAN_END_H_EST:
            sessions[sdate]["asian"].append(bar)
        elif LONDON_START_H_EST <= est_h < LONDON_END_H_EST:
            sessions[sdate]["london"].append(bar)

    result = []
    for sdate in sorted(sessions.keys()):
        data = sessions[sdate]
        asian_bars = sorted(data["asian"], key=lambda b: b.timestamp)
        london_bars = sorted(data["london"], key=lambda b: b.timestamp)

        if not asian_bars or not london_bars:
            continue

        asian_high = max(b.high for b in asian_bars)
        asian_low = min(b.low for b in asian_bars)
        asian_range = asian_high - asian_low

        if asian_range <= 0:
            continue

        asian_mid = asian_low + (asian_range / 2)
        london_close = london_bars[-1].close if london_bars else asian_bars[-1].close

        # Directional bias: London close vs Asian midpoint (Quant Bible §1.6)
        # Bullish: London close > Asian midpoint
        # Bearish: London close < Asian midpoint
        if london_close > asian_mid:
            bias = Direction.LONG
        elif london_close < asian_mid:
            bias = Direction.SHORT
        else:
            bias = Direction.FLAT

        result.append(SessionData(
            date=sdate,
            asian_high=asian_high,
            asian_low=asian_low,
            asian_range=asian_range,
            asian_mid=asian_mid,
            bias=bias,
        ))

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# REKEY ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def compute_rekey_levels(session: SessionData, pip_size: float) -> Optional[Dict]:
    """Compute entry, SL, TP for rekey trade."""
    if session.bias == Direction.FLAT:
        return None

    ar = session.asian_range
    sl_buffer = SL_BUFFER_PIPS * pip_size

    if session.bias == Direction.LONG:
        # Bullish: price dropped below Asian low, rekey LONG
        entry = session.asian_low - (FIB_REKEY * ar)
        level_168 = session.asian_low - (FIB_168 * ar)
        sl = level_168 - sl_buffer  # 5 pips below 168%
        tp = session.asian_high  # 0 level = opposite band
    else:
        # Bearish: price rose above Asian high, rekey SHORT
        entry = session.asian_high + (FIB_REKEY * ar)
        level_168 = session.asian_high + (FIB_168 * ar)
        sl = level_168 + sl_buffer  # 5 pips above 168%
        tp = session.asian_low  # 0 level = opposite band

    return {
        "direction": session.bias,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "level_132": entry,
        "level_168": level_168,
    }


def run_backtest(csv_path: str, symbol: str, pip_size: float = None) -> Dict:
    """Run simple rekey backtest on intraday data."""
    if pip_size is None:
        pip_size = get_pip_size(symbol)

    logging.basicConfig(level=logging.WARNING,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    print(f"[REKEY] Loading bars from: {csv_path}")
    bars = load_bars_csv(csv_path)
    print(f"[REKEY] Loaded {len(bars):,} bars")

    if not bars:
        return {}

    sessions = compute_sessions(bars)
    print(f"[REKEY] Computed {len(sessions)} sessions")

    # Group bars by session date for intraday processing
    bars_by_date: Dict[datetime.date, List[Bar]] = defaultdict(list)
    for bar in bars:
        sdate = _session_date(bar.timestamp)
        bars_by_date[sdate].append(bar)

    trades: List[Trade] = []
    skipped_no_bias = 0
    skipped_no_entry = 0

    for session in sessions:
        if session.bias == Direction.FLAT:
            skipped_no_bias += 1
            continue

        levels = compute_rekey_levels(session, pip_size)
        if levels is None:
            continue

        # Process ALL intraday bars from 3 AM to 4 PM EST for entry trigger
        # 63% of 132% breaches happen during London (3AM-12PM), 35% during Asian (7PM-3AM)
        session_bars = sorted(bars_by_date.get(session.date, []), key=lambda b: b.timestamp)
        intraday_bars = [b for b in session_bars
                        if LONDON_START_H_EST <= _est_hour(b.timestamp) <= HARD_EXIT_H_EST]

        trade = Trade(
            direction=levels["direction"],
            entry_price=levels["entry"],
            sl_price=levels["sl"],
            tp_price=levels["tp"],
            entry_time=session.date,
        )

        entry_triggered = False
        for bar in intraday_bars:
            est_h = _est_hour(bar.timestamp)

            # Check if entry triggers
            if not entry_triggered:
                if levels["direction"] == Direction.LONG:
                    if bar.low <= levels["entry"]:
                        entry_triggered = True
                        trade.entry_time = bar.timestamp
                else:
                    if bar.high >= levels["entry"]:
                        entry_triggered = True
                        trade.entry_time = bar.timestamp

            # After entry, check TP/SL
            if entry_triggered:
                if levels["direction"] == Direction.LONG:
                    if bar.low <= levels["sl"]:
                        trade.result = TradeResult.SL_HIT
                        trade.exit_price = levels["sl"]
                        trade.exit_time = bar.timestamp
                        break
                    if bar.high >= levels["tp"]:
                        trade.result = TradeResult.TP_HIT
                        trade.exit_price = levels["tp"]
                        trade.exit_time = bar.timestamp
                        break
                else:
                    if bar.high >= levels["sl"]:
                        trade.result = TradeResult.SL_HIT
                        trade.exit_price = levels["sl"]
                        trade.exit_time = bar.timestamp
                        break
                    if bar.low <= levels["tp"]:
                        trade.result = TradeResult.TP_HIT
                        trade.exit_price = levels["tp"]
                        trade.exit_time = bar.timestamp
                        break

            # Hard exit at 12 PM EST
            if est_h >= HARD_EXIT_H_EST:
                trade.result = TradeResult.TIMEOUT
                trade.exit_price = bar.close
                trade.exit_time = bar.timestamp
                break

        if not entry_triggered:
            skipped_no_entry += 1
            continue

        if trade.result is None:
            trade.result = TradeResult.TIMEOUT

        # Calculate PnL
        if trade.direction == Direction.LONG:
            trade.pnl_pips = (trade.exit_price - trade.entry_price) / pip_size
        else:
            trade.pnl_pips = (trade.entry_price - trade.exit_price) / pip_size

        trades.append(trade)

    # Compute stats
    return compute_stats(trades, symbol, len(sessions), skipped_no_bias, skipped_no_entry)


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


def compute_stats(trades: List[Trade], symbol: str, total_sessions: int,
                  skipped_no_bias: int, skipped_no_entry: int) -> Dict:
    if not trades:
        return {
            "symbol": symbol,
            "total_sessions": total_sessions,
            "total_trades": 0,
            "skipped_no_bias": skipped_no_bias,
            "skipped_no_entry": skipped_no_entry,
        }

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

    stats = {
        "symbol": symbol,
        "total_sessions": total_sessions,
        "total_trades": total,
        "skipped_no_bias": skipped_no_bias,
        "skipped_no_entry": skipped_no_entry,
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

    print_report(stats)
    return stats


def print_report(stats: Dict):
    print()
    print("=" * 70)
    print(f"  SIMPLE REKEY ENGINE -- BACKTEST REPORT")
    print(f"  Symbol: {stats['symbol']}")
    print(f"  Sessions: {stats['total_sessions']} | Trades: {stats['total_trades']}")
    print(f"  Skipped (no bias): {stats['skipped_no_bias']} | Skipped (no entry): {stats['skipped_no_entry']}")
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
    print(f"  Net PnL:         {stats['net_pnl_pips']:+.1f} pips")
    print(f"  Profit Factor:   {stats['profit_factor']}")
    print(f"  Avg Trade:       {stats['avg_trade_pips']:+.2f} pips")
    print(f"  Max Drawdown:    {stats['max_drawdown_pips']:.1f} pips")
    print()
    print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════════
# MULTI-PAIR
# ═══════════════════════════════════════════════════════════════════════════════

def run_all_pairs(data_dir: str):
    data_path = Path(data_dir)
    csv_files = sorted(data_path.glob("*_M5*.csv"))
    pro_files = [f for f in csv_files if "PRO" in f.name]
    if not pro_files:
        pro_files = csv_files

    all_results = {}

    for csv_file in pro_files[:25]:
        symbol = csv_file.stem.replace("_M5", "").replace("_PRO", "").replace("_2023_2026", "").replace("_2022_2026", "").replace("_JUNE", "")
        pip_size = get_pip_size(symbol)

        print(f"\n{'='*70}")
        print(f"  Testing: {symbol} ({csv_file.name})")
        print(f"{'='*70}")

        try:
            stats = run_backtest(str(csv_file), symbol, pip_size)
            all_results[symbol] = stats
        except Exception as e:
            print(f"[REKEY] ERROR for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Summary
    print(f"\n\n{'='*70}")
    print(f"  REKEY ENGINE -- MULTI-PAIR SUMMARY")
    print(f"{'='*70}")
    print(f"\n  {'Pair':<12} {'Sessions':>10} {'Trades':>8} {'WR':>8} {'Net PnL':>12} {'PF':>8} {'MaxDD':>8}")
    print(f"  {'-'*68}")

    for symbol, stats in sorted(all_results.items(), key=lambda x: x[1].get('net_pnl_pips', 0), reverse=True):
        if stats.get('total_trades', 0) > 0:
            print(f"  {symbol:<12} {stats['total_sessions']:>10} {stats['total_trades']:>8} "
                  f"{stats['win_rate']:>7.1f}% {stats['net_pnl_pips']:>+11.1f}p "
                  f"{stats['profit_factor']:>7.2f} {stats['max_drawdown_pips']:>7.1f}p")

    return all_results


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="CEREBUS Simple Rekey Engine -- Intraday")
    parser.add_argument("--csv", type=str, help="Path to M5 bar CSV file")
    parser.add_argument("--symbol", type=str, default="EURUSD", help="Symbol")
    parser.add_argument("--pip-size", type=float, default=None, help="Pip size")
    parser.add_argument("--all-pairs", action="store_true", help="Test all pairs")
    parser.add_argument("--data-dir", type=str, default=str(Path(__file__).parent.parent / "data"))
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
