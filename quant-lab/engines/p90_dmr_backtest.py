"""
P90 + DMR Engine - Backtest Harness
=====================================

Loads M5 bar data from CSV, feeds bars through P90Engine (with DMR
nested sub-routine active), and computes performance stats including
DMR-specific metrics.

DMR is NOT a separate strategy — it is a nested sub-routine inside the
P90 IN_TRADE state. All DMR signals are tracked separately in stats.

Usage:
    $env:PYTHONPATH="quant-lab"; python -m engines.p90_dmr_backtest --csv path/to/m5_bars.csv --symbol EURUSD
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from collections import defaultdict
from datetime import datetime, timedelta, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from p90_engine_dmr import (
    P90Engine,
    P90Variant,
    P90Signal,
    Bar,
    TradeDirection,
)

# ─── TIMESTAMP PARSING ────────────────────────────────────────────────────

_TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y %H:%M",
    "%Y%m%d %H:%M:%S",
]


def parse_timestamp(raw: str) -> datetime:
    raw = raw.strip()
    for fmt in _TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse timestamp '{raw}'. Tried: {_TIMESTAMP_FORMATS}")


# ─── CSV LOADING ──────────────────────────────────────────────────────────

def load_bars_csv(csv_path: str) -> List[Bar]:
    bars: List[Bar] = []
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            ts_raw = (row.get("timestamp") or row.get("Timestamp")
                      or row.get("time") or row.get("Time")
                      or row.get("date") or row.get("Date")
                      or row.get("datetime") or row.get("Datetime"))
            if ts_raw is None:
                raise ValueError(f"Row {row_num}: no timestamp column. Columns: {list(row.keys())}")

            o = row.get("open") or row.get("Open") or row.get("OPEN")
            h = row.get("high") or row.get("High") or row.get("HIGH")
            l = row.get("low") or row.get("Low") or row.get("LOW")
            c = row.get("close") or row.get("Close") or row.get("CLOSE")

            if any(v is None for v in (o, h, l, c)):
                raise ValueError(f"Row {row_num}: missing OHLC. Columns: {list(row.keys())}")

            bars.append(Bar(timestamp=parse_timestamp(ts_raw), open=float(o),
                            high=float(h), low=float(l), close=float(c)))

    bars.sort(key=lambda b: b.timestamp)
    return bars


# ─── SESSION GROUPING ─────────────────────────────────────────────────────

ASIAN_START_H = 19
ASIAN_END_H = 3
TRADING_START_H = 3
TRADING_END_H = 12


def _est_hour(dt: datetime) -> int:
    return (dt.hour - 5) % 24


def _session_date(dt: datetime):
    h = _est_hour(dt)
    if h >= ASIAN_START_H:
        return (dt + timedelta(days=1)).date()
    return dt.date()


def group_by_session(bars: List[Bar]):
    sessions = defaultdict(lambda: {"asian": [], "trading": []})
    for bar in bars:
        sdate = _session_date(bar.timestamp)
        h = _est_hour(bar.timestamp)
        if h >= ASIAN_START_H or h < ASIAN_END_H:
            sessions[sdate]["asian"].append(bar)
        elif TRADING_START_H <= h < TRADING_END_H:
            sessions[sdate]["trading"].append(bar)
    for sdate in sessions:
        sessions[sdate]["asian"].sort(key=lambda b: b.timestamp)
        sessions[sdate]["trading"].sort(key=lambda b: b.timestamp)
    return dict(sorted(sessions.items()))


# ─── ASIAN RANGE ──────────────────────────────────────────────────────────

def calc_asian_range(asian_bars):
    if not asian_bars:
        return 0.0, 0.0
    return max(b.high for b in asian_bars), min(b.low for b in asian_bars)


# ─── STATISTICS ───────────────────────────────────────────────────────────

def _pnl_pips(sig: P90Signal, pip_size: float) -> Optional[float]:
    """Calculate PnL in pips for a completed trade signal."""
    if sig.entry_price is None:
        return None

    if sig.event == "TP_HIT":
        exit_price = sig.tp_price
    elif sig.event == "SL_HIT":
        exit_price = sig.sl_price
    elif sig.event == "EWS_EXIT":
        exit_price = sig.tp_price
    elif sig.event == "DMR_TP_HIT":
        exit_price = sig.tp_price
    elif sig.event == "DMR_SL_HIT":
        # DMR_SL_HIT reports P90 entry; estimate DMR PnL separately
        exit_price = sig.sl_price
    else:
        return None

    if exit_price is None:
        return None

    if sig.direction.name == "LONG":
        return (exit_price - sig.entry_price) / pip_size
    else:
        return (sig.entry_price - exit_price) / pip_size


def _calc_stats_block(pnls: List[float]) -> Dict:
    """Compute stats block for a list of PnL values."""
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    total = len(pnls)
    win_rate = len(wins) / total * 100 if total > 0 else 0.0
    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0
    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    avg_trade = sum(pnls) / total if total > 0 else 0.0

    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = abs(sum(losses) / len(losses)) if losses else 0.0
    r_multiple = avg_win / avg_loss if avg_loss > 0 else float("inf")

    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for pnl in pnls:
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    return {
        "trades": total,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "gross_profit_pips": round(gross_profit, 1),
        "gross_loss_pips": round(-gross_loss, 1),
        "profit_factor": round(pf, 2) if pf != float("inf") else "inf",
        "avg_trade_pips": round(avg_trade, 2),
        "avg_r_multiple": round(r_multiple, 2) if r_multiple != float("inf") else "inf",
        "max_drawdown_pips": round(max_dd, 1),
    }


def compute_stats(
    signals: List[P90Signal],
    pip_size: float,
) -> Dict:
    """
    Compute backtest statistics, splitting P90 and DMR trades.
    """
    # ── P90 completed trades (TP_HIT, SL_HIT, EWS_EXIT) ───────────────
    p90_completed = [s for s in signals if s.event in ("TP_HIT", "SL_HIT", "EWS_EXIT")]
    p90_pnls = []
    for sig in p90_completed:
        pnl = _pnl_pips(sig, pip_size)
        if pnl is not None:
            p90_pnls.append(pnl)

    overall = _calc_stats_block(p90_pnls)

    # ── Per-variant breakdown ─────────────────────────────────────────
    per_variant = {}
    for variant in [P90Variant.INITIAL, P90Variant.CASCADE]:
        v_completed = [s for s in p90_completed if s.variant == variant]
        v_pnls = []
        for sig in v_completed:
            pnl = _pnl_pips(sig, pip_size)
            if pnl is not None:
                v_pnls.append(pnl)
        per_variant[variant.value] = _calc_stats_block(v_pnls)

    # ── DMR-specific stats ────────────────────────────────────────────
    dmr_triggered = [s for s in signals if s.event == "DMR_TRIGGERED"]
    dmr_tp_hits = [s for s in signals if s.event == "DMR_TP_HIT"]
    dmr_sl_hits = [s for s in signals if s.event == "DMR_SL_HIT"]
    dmr_cancelled = [s for s in signals if s.event == "DMR_CANCELLED"]

    dmr_completed = dmr_tp_hits + dmr_sl_hits
    dmr_pnls = []
    for sig in dmr_completed:
        pnl = _pnl_pips(sig, pip_size)
        if pnl is not None:
            dmr_pnls.append(pnl)

    dmr_stats = _calc_stats_block(dmr_pnls)

    # Shared SL breach count (DMR_SL_HIT means both DMR and P90 lost)
    shared_sl_count = len(dmr_sl_hits)

    result = {
        "total_trades": overall["trades"],
        "wins": overall["wins"],
        "losses": overall["losses"],
        "win_rate": overall["win_rate"],
        "gross_profit_pips": overall["gross_profit_pips"],
        "gross_loss_pips": overall["gross_loss_pips"],
        "profit_factor": overall["profit_factor"],
        "max_drawdown_pips": overall["max_drawdown_pips"],
        "avg_trade_pips": overall["avg_trade_pips"],
        "avg_r_multiple": overall["avg_r_multiple"],
        "per_variant": per_variant,
        "dmr": {
            "limits_placed": len(dmr_triggered) + len(dmr_cancelled) + len([
                s for s in signals
                if s.event == "DMR_TRIGGERED"
            ]),
            "triggered": len(dmr_triggered),
            "tp_hits": len(dmr_tp_hits),
            "sl_hits": len(dmr_sl_hits),
            "cancelled": len(dmr_cancelled),
            "completed_trades": len(dmr_completed),
            "stats": dmr_stats,
            "shared_sl_breaches": shared_sl_count,
        },
    }

    return result


# ─── REPORT ───────────────────────────────────────────────────────────────

def print_report(stats: Dict, symbol: str, total_sessions: int, total_bars: int) -> None:
    print()
    print("=" * 70)
    print(f"  P90 KINETIC ENGINE + DMR (NESTED SUB-ROUTINE)")
    print(f"  Symbol: {symbol}")
    print(f"  Sessions: {total_sessions} | Bars processed: {total_bars}")
    print("=" * 70)

    if stats["total_trades"] == 0:
        print("\n  No completed trades.\n")
        return

    print(f"\n  -- P90 OVERALL ----------------------------------------")
    print(f"  Total Trades:    {stats['total_trades']}")
    print(f"  Wins:            {stats['wins']}")
    print(f"  Losses:          {stats['losses']}")
    print(f"  Win Rate:        {stats['win_rate']}%")
    print(f"  Gross Profit:    +{stats['gross_profit_pips']:.1f} pips")
    print(f"  Gross Loss:      {stats['gross_loss_pips']:.1f} pips")
    print(f"  Profit Factor:   {stats['profit_factor']}")
    print(f"  Avg R-Multiple:  {stats['avg_r_multiple']}R")
    print(f"  Avg Trade:       {stats['avg_trade_pips']:+.2f} pips")
    print(f"  Max Drawdown:    {stats['max_drawdown_pips']:.1f} pips")

    print(f"\n  -- P90 PER-VARIANT BREAKDOWN ---------------------------")
    for v_name, v_stats in stats["per_variant"].items():
        if v_stats["trades"] == 0:
            print(f"  {v_name:18s}  No trades")
        else:
            print(
                f"  {v_name:18s}  Trades: {v_stats['trades']:3d} | "
                f"W: {v_stats['wins']:3d} L: {v_stats['losses']:3d} | "
                f"WR: {v_stats['win_rate']:5.1f}% | "
                f"PnL: {v_stats['gross_profit_pips'] + v_stats['gross_loss_pips']:+7.1f}p | "
                f"AvgR: {v_stats['avg_r_multiple']}R"
            )

    # ── DMR Section ───────────────────────────────────────────────────
    dmr = stats.get("dmr")
    if dmr:
        print(f"\n  {'='*54}")
        print(f"  -- DMR SUB-ROUTINE STATS -------------------------------")
        print(f"  {'='*54}")

        print(f"\n  DMR Limits Placed:    {dmr['limits_placed']}")
        print(f"  DMR Triggered (fill): {dmr['triggered']}")
        print(f"  DMR Cancelled:        {dmr['cancelled']}")

        if dmr["completed_trades"] > 0:
            ds = dmr["stats"]
            print(f"\n  -- DMR COMPLETED TRADES --------------------------------")
            print(f"  Trades:          {ds['trades']}")
            print(f"  Wins (TP Hit):   {ds['wins']}  ({dmr['tp_hits']})")
            print(f"  Losses (SL Hit): {ds['losses']}  ({dmr['sl_hits']})")
            print(f"  Win Rate:        {ds['win_rate']}%")
            print(f"  Gross Profit:    +{ds['gross_profit_pips']:.1f} pips")
            print(f"  Gross Loss:      {ds['gross_loss_pips']:.1f} pips")
            print(f"  Profit Factor:   {ds['profit_factor']}")
            print(f"  Avg R-Multiple:  {ds['avg_r_multiple']}R")
            print(f"  Avg Trade:       {ds['avg_trade_pips']:+.2f} pips")
            print(f"  Max Drawdown:    {ds['max_drawdown_pips']:.1f} pips")

            print(f"\n  -- SHARED SL BREACH EVENTS -----------------------------")
            print(f"  Events: {dmr['shared_sl_breaches']}")
            print(f"  (Both DMR and P90 closed on same boundary hit)")
        else:
            print(f"\n  No DMR trades completed (no limits were triggered).")

    print()
    print("=" * 70)


# ─── MAIN BACKTEST ─────────────────────────────────────────────────────────

def run_backtest(
    csv_path: str,
    symbol: str,
    pip_size: float = 0.0001,
) -> Dict:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    print(f"[P90+DMR BT] Loading bars from: {csv_path}")
    bars = load_bars_csv(csv_path)
    print(f"[P90+DMR BT] Loaded {len(bars):,} bars")

    if not bars:
        print("[P90+DMR BT] ERROR: No bars loaded.")
        return {}

    sessions = group_by_session(bars)
    print(f"[P90+DMR BT] Found {len(sessions)} sessions")

    engine = P90Engine(pip_size=pip_size, symbol=symbol)
    total_bars_processed = 0

    for sdate, session_bars in sessions.items():
        asian_bars = session_bars["asian"]
        trading_bars = session_bars["trading"]

        if not asian_bars or not trading_bars:
            continue

        asian_high, asian_low = calc_asian_range(asian_bars)
        if asian_high <= asian_low:
            continue

        engine.initialize_session(asian_high, asian_low)

        if not engine.session_active:
            continue

        for bar in trading_bars:
            engine.process_bar(bar)
            total_bars_processed += 1

    all_signals = engine.signal_log
    entry_count = sum(1 for s in all_signals if s.event == "ENTRY")
    dmr_trig = sum(1 for s in all_signals if s.event == "DMR_TRIGGERED")
    print(f"[P90+DMR BT] Signals: {len(all_signals)} ({entry_count} entries, {dmr_trig} DMR triggers)")

    stats = compute_stats(all_signals, pip_size)
    print_report(stats, symbol, len(sessions), total_bars_processed)
    return stats


# ─── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="P90 + DMR Backtest Harness"
    )
    parser.add_argument("--csv", required=True, help="Path to M5 bar CSV file")
    parser.add_argument("--symbol", default="EURUSD", help="Symbol (default: EURUSD)")
    parser.add_argument("--pip-size", type=float, default=0.0001,
                        help="Pip size (default: 0.0001 for EURUSD)")
    args = parser.parse_args()

    run_backtest(
        csv_path=args.csv,
        symbol=args.symbol,
        pip_size=args.pip_size,
    )


if __name__ == "__main__":
    main()
