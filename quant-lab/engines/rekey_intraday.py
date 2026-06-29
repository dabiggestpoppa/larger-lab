#!/usr/bin/env python3
"""
CEREBUS — Rekey Intraday Engine (Holy Grail Phase 4 Exact Model)
================================================================

SESSION WINDOWS (EST):
  Asian Range:    7:00 PM - 3:00 AM  (00:00-08:00 UTC) — 8 hours
  London Open:    2:00 AM - 6:00 AM  (07:00-11:00 UTC) — 4 hours

DIRECTION (Bifurcation):
  Compare Asian Range vs London Open Range
  - If ranges ALIGN (same bias) → trade continuation
  - If ranges BIFURCATE (opposite bias) → trade rekey
  - Bifurcation rate: ~42% EURUSD, ~51% OILUSD

TRADE SETUP:
  Entry:  Limit at 132% of London Open Range from breached band
  SL:     5 pips beyond 168% level
  TP:     0 level (opposite band of London Open Range)
  Window: 3AM-12PM EST (intraday only)

HOLY GRAIL DATA:
  Total bifurcated days: 349 (51.5% of all days)
  132% violation rate:  98.0% (342/349 days)
"""

from __future__ import annotations

import argparse
import csv
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS (EST)
# ═══════════════════════════════════════════════════════════════════════════════

ASIAN_START_EST = 19   # 7 PM
ASIAN_END_EST = 3      # 3 AM
LONDON_START_EST = 2   # 2 AM
LONDON_END_EST = 6     # 6 AM
TRADE_END_EST = 12     # 12 PM (no new trades after this)

FIB_REKEY = 1.32
FIB_168 = 1.68
SL_PIPS = 5


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
# DATA
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass
class SessionData:
    date: datetime.date
    asian_high: float
    asian_low: float
    asian_mid: float
    asian_range: float
    london_high: float
    london_low: float
    london_mid: float
    london_range: float
    bias: Direction = Direction.FLAT
    bifurcated: bool = False


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
                time_val = (clean_row.get("time") or clean_row.get("Time") or clean_row.get("TIME"))
                if time_val and len(time_val.strip()) > 10:
                    ts_raw = time_val.strip()
            if ts_raw is None:
                date_val = (clean_row.get("date") or clean_row.get("Date") or clean_row.get("DATE"))
                time_val = (clean_row.get("time") or clean_row.get("Time") or clean_row.get("TIME"))
                if date_val and time_val:
                    ts_raw = f"{date_val.strip()} {time_val.strip()}"
            if ts_raw is None or not ts_raw.strip():
                raise ValueError(f"Row {row_num}: no timestamp")
            o = clean_row.get("OPEN") or clean_row.get("open")
            h = clean_row.get("HIGH") or clean_row.get("high")
            l = clean_row.get("LOW") or clean_row.get("low")
            c = clean_row.get("CLOSE") or clean_row.get("close")
            if any(v is None for v in (o, h, l, c)):
                raise ValueError(f"Row {row_num}: missing OHLC")
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
    if h >= ASIAN_START_EST:
        return (dt + timedelta(days=1)).date()
    return dt.date()


def compute_sessions(bars: List[Bar]) -> List[SessionData]:
    """Compute Asian Range (7PM-3AM) and London Open Range (2AM-6AM)."""
    sessions: Dict[datetime.date, Dict] = defaultdict(
        lambda: {"asian": [], "london": [], "trading": []}
    )

    for bar in bars:
        sdate = _session_date(bar.timestamp)
        est_h = _est_hour(bar.timestamp)

        # Asian Range: 7PM-3AM EST
        if est_h >= ASIAN_START_EST or est_h < ASIAN_END_EST:
            sessions[sdate]["asian"].append(bar)
        # London Open Range: 2AM-6AM EST
        elif LONDON_START_EST <= est_h < LONDON_END_EST:
            sessions[sdate]["london"].append(bar)
        # Trading window: 6AM-12PM EST (for entry/exit)
        elif ASIAN_END_EST <= est_h < TRADE_END_EST:
            sessions[sdate]["trading"].append(bar)

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

        london_high = max(b.high for b in london_bars)
        london_low = min(b.low for b in london_bars)
        london_range = london_high - london_low

        if asian_range <= 0 or london_range <= 0:
            continue

        asian_mid = asian_low + (asian_range / 2)
        london_mid = london_low + (london_range / 2)

        # Directional bias from London Open close vs midpoint
        london_close = london_bars[-1].close
        if london_close > london_mid:
            bias = Direction.LONG
        elif london_close < london_mid:
            bias = Direction.SHORT
        else:
            bias = Direction.FLAT

        # Bifurcation: Asian bias != London bias
        asian_close = asian_bars[-1].close
        asian_bias_bullish = asian_close > asian_mid
        london_bias_bullish = london_close > london_mid
        bifurcated = (asian_bias_bullish != london_bias_bullish)

        result.append(SessionData(
            date=sdate,
            asian_high=asian_high,
            asian_low=asian_low,
            asian_mid=asian_mid,
            asian_range=asian_range,
            london_high=london_high,
            london_low=london_low,
            london_mid=london_mid,
            london_range=london_range,
            bias=bias,
            bifurcated=bifurcated,
        ))

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# REKEY ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def compute_rekey_levels(session: SessionData, pip_size: float) -> Optional[Dict]:
    """
    Compute entry, SL, TP based on Holy Grail Rekey Protocol:
    
    1. 132% = trigger/invalidation level (SL)
    2. Entry = 50% consolidation (between band edge and 132%)
    3. SL = 132% level (5 pips beyond)
    4. TP = -50% extension from rekey anchor (opposite band)
    """
    if session.bias == Direction.FLAT:
        return None

    lr = session.london_range
    sl_buffer = SL_PIPS * pip_size

    if session.bias == Direction.LONG:
        # Bullish rekey: price dropped below London low
        level_132 = session.london_low - (FIB_REKEY * lr)  # 132% breach point
        entry = session.london_low - (0.50 * lr)  # 50% consolidation
        sl = level_132 - sl_buffer  # SL below 132%
        tp = session.london_high  # TP = opposite band (0 level)
    else:
        # Bearish rekey: price rose above London high
        level_132 = session.london_high + (FIB_REKEY * lr)  # 132% breach point
        entry = session.london_high + (0.50 * lr)  # 50% consolidation
        sl = level_132 + sl_buffer  # SL above 132%
        tp = session.london_low  # TP = opposite band (0 level)

    return {
        "direction": session.bias,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "level_132": level_132,
    }


def run_backtest(csv_path: str, symbol: str, pip_size: float = None) -> Dict:
    """Run rekey intraday backtest."""
    if pip_size is None:
        pip_size = get_pip_size(symbol)

    logging.basicConfig(level=logging.WARNING,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    print(f"[REKEY] Loading: {csv_path}")
    bars = load_bars_csv(csv_path)
    print(f"[REKEY] Loaded {len(bars):,} bars")

    sessions = compute_sessions(bars)
    print(f"[REKEY] Sessions: {len(sessions)}")

    # Group bars by session date
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

        # Trading window: 3AM-12PM EST (after London range is set)
        session_bars = sorted(bars_by_date.get(session.date, []), key=lambda b: b.timestamp)
        trading_bars = [b for b in session_bars
                       if ASIAN_END_EST <= _est_hour(b.timestamp) < TRADE_END_EST]

        if not trading_bars:
            continue

        trade = Trade(
            direction=levels["direction"],
            entry_price=levels["entry"],
            sl_price=levels["sl"],
            tp_price=levels["tp"],
            entry_time=session.date,
        )

        entry_triggered = False
        for bar in trading_bars:
            est_h = _est_hour(bar.timestamp)

            # Check entry
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
            if est_h >= TRADE_END_EST:
                trade.result = TradeResult.TIMEOUT
                trade.exit_price = bar.close
                trade.exit_time = bar.timestamp
                break

        if not entry_triggered:
            skipped_no_entry += 1
            continue

        if trade.result is None:
            trade.result = TradeResult.TIMEOUT
            # Use last bar close as exit if no TP/SL hit
            last_bar = trading_bars[-1] if trading_bars else None
            if last_bar:
                trade.exit_price = last_bar.close
                trade.exit_time = last_bar.timestamp

        # PnL
        if trade.exit_price is not None:
            if trade.direction == Direction.LONG:
                trade.pnl_pips = (trade.exit_price - trade.entry_price) / pip_size
            else:
                trade.pnl_pips = (trade.entry_price - trade.exit_price) / pip_size
        else:
            continue  # Skip if no exit price

        trades.append(trade)

    return compute_stats(trades, symbol, len(sessions), skipped_no_bias, skipped_no_entry)


def get_pip_size(symbol: str) -> float:
    sym = symbol.upper()
    if "JPY" in sym: return 0.01
    if sym in ("BTCUSD", "ETHUSD", "BNBUSD", "SOLUSD", "LTCUSD", "BCHUSD"): return 1.0
    if sym == "XAUUSD": return 0.1
    if sym == "XAGUSD": return 0.01
    if sym in ("US500", "NAS100", "DE30", "FR40", "HK50"): return 1.0
    return 0.0001


def compute_stats(trades: List[Trade], symbol: str, total_sessions: int,
                  skipped_no_bias: int, skipped_no_entry: int) -> Dict:
    if not trades:
        return {"symbol": symbol, "total_sessions": total_sessions, "total_trades": 0,
                "skipped_no_bias": skipped_no_bias, "skipped_no_entry": skipped_no_entry}

    wins = [t for t in trades if t.pnl_pips > 0]
    losses = [t for t in trades if t.pnl_pips < 0]
    total = len(trades)
    win_rate = len(wins) / total * 100 if total > 0 else 0.0
    gross_profit = sum(t.pnl_pips for t in wins) if wins else 0.0
    gross_loss = abs(sum(t.pnl_pips for t in losses)) if losses else 0.0
    net_pnl = gross_profit - gross_loss
    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    avg_trade = net_pnl / total if total > 0 else 0.0

    cumulative = 0.0; peak = 0.0; max_dd = 0.0
    for t in trades:
        cumulative += t.pnl_pips
        if cumulative > peak: peak = cumulative
        dd = peak - cumulative
        if dd > max_dd: max_dd = dd

    tp_hits = len([t for t in trades if t.result == TradeResult.TP_HIT])
    sl_hits = len([t for t in trades if t.result == TradeResult.SL_HIT])
    timeouts = len([t for t in trades if t.result == TradeResult.TIMEOUT])

    stats = {
        "symbol": symbol, "total_sessions": total_sessions, "total_trades": total,
        "skipped_no_bias": skipped_no_bias, "skipped_no_entry": skipped_no_entry,
        "wins": len(wins), "losses": len(losses), "win_rate": round(win_rate, 1),
        "gross_profit_pips": round(gross_profit, 1), "gross_loss_pips": round(-gross_loss, 1),
        "net_pnl_pips": round(net_pnl, 1), "profit_factor": round(pf, 2),
        "avg_trade_pips": round(avg_trade, 2), "max_drawdown_pips": round(max_dd, 1),
        "tp_hits": tp_hits, "sl_hits": sl_hits, "timeouts": timeouts,
    }

    print_report(stats)
    return stats


def print_report(stats: Dict):
    print()
    print("=" * 70)
    print(f"  REKEY INTRADAY ENGINE -- BACKTEST REPORT")
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


def run_all_pairs(data_dir: str):
    data_path = Path(data_dir)
    csv_files = sorted(data_path.glob("*_M5*.csv"))
    pro_files = [f for f in csv_files if "PRO" in f.name]
    if not pro_files:
        pro_files = csv_files
    all_results = {}
    for csv_file in pro_files[:25]:
        symbol = csv_file.stem.replace("_M5", "").replace("_PRO", "").replace("_2023_2026", "").replace("_2022_2026", "").replace("_JUNE", "").replace("_dt", "").replace("_MAD", "")
        pip_size = get_pip_size(symbol)
        print(f"\n{'='*70}")
        print(f"  Testing: {symbol} ({csv_file.name})")
        print(f"{'='*70}")
        try:
            stats = run_backtest(str(csv_file), symbol, pip_size)
            all_results[symbol] = stats
        except Exception as e:
            print(f"[REKEY] ERROR for {symbol}: {e}")
            import traceback; traceback.print_exc()
            continue

    print(f"\n\n{'='*70}")
    print(f"  REKEY INTRADAY -- MULTI-PAIR SUMMARY")
    print(f"{'='*70}")
    print(f"\n  {'Pair':<12} {'Sessions':>10} {'Trades':>8} {'WR':>8} {'Net PnL':>12} {'PF':>8} {'MaxDD':>8}")
    print(f"  {'-'*68}")
    for symbol, stats in sorted(all_results.items(), key=lambda x: x[1].get('net_pnl_pips', 0), reverse=True):
        if stats.get('total_trades', 0) > 0:
            print(f"  {symbol:<12} {stats['total_sessions']:>10} {stats['total_trades']:>8} "
                  f"{stats['win_rate']:>7.1f}% {stats['net_pnl_pips']:>+11.1f}p "
                  f"{stats['profit_factor']:>7.2f} {stats['max_drawdown_pips']:>7.1f}p")
    return all_results


def main():
    parser = argparse.ArgumentParser(description="CEREBUS Rekey Intraday Engine")
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
