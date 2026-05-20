#!/usr/bin/env python3
"""
DMR (Deep Mean Reversion) MT5 Backtest Engine
==============================================
Fetches historical EUR/USD M5 data from MT5 terminal and runs the DMR
strategy logic bar-by-bar, producing results comparable to the Python
optimizer output.

Strategy: Deep Mean Reversion (DMR) / Play 1 — BASE 80
Source: CEREBUS FX v4.0 Manual
Optimized parameters from: optimizer_v4b_20260517_193302.json

Author: MT5 Backtest Engineer
Date: 2026-05-19
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta, timezone
import json
import math
import sys
import os

# ===========================================================================
# CONFIGURATION
# ===========================================================================

SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_M5
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2026, 4, 30, 23, 59)

# DMR Strategy Parameters (from optimizer + CEREBUS manual)
PIP_SIZE = 0.0001          # 1 pip for EUR/USD
ASIAN_RANGE_MAX = 30.0     # pips — max Asian range to trade
ASIAN_SESSION_START_UTC = 0   # 00:00 UTC
ASIAN_SESSION_END_UTC = 8     # 08:00 UTC

# P90 body thresholds by time window (EST)
P90_THRESHOLDS_EST = {
    (2, 4): 4.1,    # 2:00-4:00 AM EST
    (4, 6): 4.6,    # 4:00-6:00 AM EST
    (6, 8): 4.6,    # 6:00-8:00 AM EST
    (8, 10): 5.9,   # 8:00-10:00 AM EST
    (10, 11): 6.2,  # 10:00-11:00 AM EST
}

ENTRY_WINDOW_START_EST = 2    # 2:00 AM EST
ENTRY_WINDOW_END_EST = 11     # 11:00 AM EST
HARD_EXIT_HOUR_EST = 12       # 12:00 PM EST hard exit

# Risk / Position sizing
INITIAL_EQUITY = 10000.0
RISK_PCT_PER_TRADE = 0.05     # 5% of equity per trade (as specified)
SL_PCT_OF_P90_BODY = 0.80     # SL at 80% of P90 body from entry
TP1_PCT_OF_ASIAN = 0.25       # TP1 at 25% of Asian Range extension
TP2_PCT_OF_ASIAN = 0.50       # TP2 at 50% of Asian Range extension
MAX_HOLD_BARS = 144           # Max 12 hours (144 M5 bars)

# Tier sizing
TIER_CONFIG = {
    "T1": {"max_range": 20.0, "size_mult": 1.0},
    "T2": {"max_range": 30.0, "size_mult": 0.75},
    "T3": {"max_range": 45.0, "size_mult": 0.50},
}

# ===========================================================================
# DATA FETCHING
# ===========================================================================

def fetch_mt5_data(symbol, timeframe, start_date, end_date):
    """Fetch historical bars from MT5 terminal."""
    if not mt5.initialize():
        raise ConnectionError(f"MT5 init failed: {mt5.last_error()}")

    print(f"[MT5] Connected: {mt5.terminal_info().company}")
    print(f"[MT5] Fetching {symbol} M5 from {start_date} to {end_date}...")

    rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
    mt5.shutdown()

    if rates is None:
        raise RuntimeError(f"Failed to fetch data: {mt5.last_error()}")

    bars = []
    for r in rates:
        bars.append({
            "time": datetime.utcfromtimestamp(r[0]),
            "open": r[1],
            "high": r[2],
            "low": r[3],
            "close": r[4],
            "volume": int(r[5]),
            "spread": int(r[6]),
        })

    print(f"[MT5] Fetched {len(bars)} bars")
    return bars


# ===========================================================================
# DMR STRATEGY LOGIC
# ===========================================================================

def utc_to_est(dt_utc):
    """Convert UTC datetime to EST (UTC-5, ignoring DST for simplicity)."""
    return dt_utc - timedelta(hours=5)


def get_p90_threshold(est_hour):
    """Get P90 body threshold for given EST hour."""
    for (start, end), threshold in P90_THRESHOLDS_EST.items():
        if start <= est_hour < end:
            return threshold
    return None


def classify_tier(asian_range_pips):
    """Classify Asian Range into Tier."""
    if asian_range_pips < 20.0:
        return "T1"
    elif asian_range_pips < 30.0:
        return "T2"
    elif asian_range_pips < 45.0:
        return "T3"
    else:
        return "NO_GO"


def compute_asian_range(bars, trading_date):
    """
    Compute Asian Range for a given trading date.
    Asian session: 00:00-08:00 UTC on the trading date.
    """
    asian_bars = []
    for b in bars:
        if b["time"].date() == trading_date:
            if ASIAN_SESSION_START_UTC <= b["time"].hour < ASIAN_SESSION_END_UTC:
                asian_bars.append(b)

    if not asian_bars:
        return None, None, None

    asian_high = max(b["high"] for b in asian_bars)
    asian_low = min(b["low"] for b in asian_bars)
    asian_range = (asian_high - asian_low) / PIP_SIZE

    return asian_high, asian_low, asian_range


def run_dmr_backtest(bars):
    """
    Run DMR strategy on historical bars.

    Logic (Play 1 — BASE 80):
    1. Each trading day: compute Asian Range (00:00-08:00 UTC)
    2. Classify Tier (T1/T2/T3/NO-GO)
    3. Scan 2:00-11:00 AM EST for P90 candle close outside Asian band
    4. Enter on P90 close, SL at 80% of P90 body, TP at Asian extensions
    5. Hard exit at 12:00 PM EST
    """

    trades = []
    equity = INITIAL_EQUITY
    equity_curve = [equity]
    daily_asian = {}

    # Group bars by trading date
    dates = sorted(set(b["time"].date() for b in bars))

    # Pre-compute Asian ranges for each date
    for d in dates:
        ah, al, ar = compute_asian_range(bars, d)
        if ah is not None:
            daily_asian[d] = {"high": ah, "low": al, "range": ar}

    # Track state
    position = None  # {direction, entry_price, sl, tp1, tp2, size, entry_bar_idx, ...}
    current_date = None
    p90_detected_today = False

    for i, bar in enumerate(bars):
        bar_time = bar["time"]
        bar_date = bar_time.date()
        est = utc_to_est(bar_time)
        est_hour = est.hour + est.minute / 60.0

        # Reset daily state on new date
        if bar_date != current_date:
            current_date = bar_date
            p90_detected_today = False

        # --- EXIT LOGIC: Check existing position ---
        if position is not None:
            exited = False
            exit_price = None
            exit_reason = None

            # Hard exit at 12:00 PM EST
            if est_hour >= HARD_EXIT_HOUR_EST:
                exit_price = bar["close"]
                exit_reason = "hard_exit"
                exited = True

            # Check SL hit
            if not exited:
                if position["direction"] == "LONG":
                    if bar["low"] <= position["sl"]:
                        exit_price = position["sl"]
                        exit_reason = "sl"
                        exited = True
                    elif bar["high"] >= position["tp2"]:
                        exit_price = position["tp2"]
                        exit_reason = "tp2"
                        exited = True
                    elif bar["high"] >= position["tp1"]:
                        # Partial close at TP1 — move SL to BE+2p
                        position["tp1_hit"] = True
                        position["sl"] = position["entry_price"] + 2 * PIP_SIZE
                elif position["direction"] == "SHORT":
                    if bar["high"] >= position["sl"]:
                        exit_price = position["sl"]
                        exit_reason = "sl"
                        exited = True
                    elif bar["low"] <= position["tp2"]:
                        exit_price = position["tp2"]
                        exit_reason = "tp2"
                        exited = True
                    elif bar["low"] <= position["tp1"]:
                        position["tp1_hit"] = True
                        position["sl"] = position["entry_price"] - 2 * PIP_SIZE

            # Max hold time
            if not exited and (i - position["entry_bar_idx"]) >= MAX_HOLD_BARS:
                exit_price = bar["close"]
                exit_reason = "max_hold"
                exited = True

            if exited:
                # Calculate P&L
                if position["direction"] == "LONG":
                    pnl_pips = (exit_price - position["entry_price"]) / PIP_SIZE
                else:
                    pnl_pips = (position["entry_price"] - exit_price) / PIP_SIZE

                pnl_dollars = pnl_pips * position["size"] * 10.0  # $10/pip per lot
                equity += pnl_dollars

                trades.append({
                    "entry_time": position["entry_time"].isoformat(),
                    "exit_time": bar_time.isoformat(),
                    "direction": position["direction"],
                    "entry_price": position["entry_price"],
                    "exit_price": exit_price,
                    "sl": position["sl"],
                    "tp1": position["tp1"],
                    "tp2": position["tp2"],
                    "size": position["size"],
                    "pnl_pips": round(pnl_pips, 2),
                    "pnl_dollars": round(pnl_dollars, 2),
                    "exit_reason": exit_reason,
                    "tier": position["tier"],
                    "asian_range": position["asian_range"],
                })
                equity_curve.append(equity)
                position = None

        # --- ENTRY LOGIC: Look for P90 signals ---
        if position is not None:
            continue
        if bar_date not in daily_asian:
            continue

        asian = daily_asian[bar_date]
        tier = classify_tier(asian["range"])

        if tier == "NO_GO":
            continue
        if p90_detected_today:
            continue  # One trade per day

        # Check entry window (2:00-11:00 AM EST)
        if not (ENTRY_WINDOW_START_EST <= est_hour < ENTRY_WINDOW_END_EST):
            continue

        # P90 body threshold
        threshold = get_p90_threshold(est_hour)
        if threshold is None:
            continue

        # Calculate candle body
        body = abs(bar["close"] - bar["open"])
        body_pips = body / PIP_SIZE

        if body_pips < threshold:
            continue

        # Check close outside Asian band
        direction = None
        if bar["close"] > asian["high"] and bar["close"] > bar["open"]:
            direction = "LONG"
        elif bar["close"] < asian["low"] and bar["close"] < bar["open"]:
            direction = "SHORT"

        if direction is None:
            continue

        # Regime confirmation: ratio of current bar body to average body
        # Simplified: use body >= threshold as regime confirmation
        # (already filtered by P90 threshold)

        # Calculate position parameters
        tier_mult = TIER_CONFIG.get(tier, {"size_mult": 0.5})["size_mult"]

        if direction == "LONG":
            entry_price = bar["close"]
            sl = entry_price - SL_PCT_OF_P90_BODY * body
            tp1 = entry_price + TP1_PCT_OF_ASIAN * asian["range"] * PIP_SIZE
            tp2 = entry_price + TP2_PCT_OF_ASIAN * asian["range"] * PIP_SIZE
        else:
            entry_price = bar["close"]
            sl = entry_price + SL_PCT_OF_P90_BODY * body
            tp1 = entry_price - TP1_PCT_OF_ASIAN * asian["range"] * PIP_SIZE
            tp2 = entry_price - TP2_PCT_OF_ASIAN * asian["range"] * PIP_SIZE

        # Position sizing: 5% of equity / (SL distance * $10/pip)
        sl_distance_pips = abs(entry_price - sl) / PIP_SIZE
        risk_amount = equity * RISK_PCT_PER_TRADE
        lot_size = risk_amount / (sl_distance_pips * 10.0)
        lot_size = round(min(lot_size, 0.50) * tier_mult, 2)  # Cap at 0.50 lots

        if lot_size < 0.01:
            lot_size = 0.01

        position = {
            "direction": direction,
            "entry_price": entry_price,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "size": lot_size,
            "entry_bar_idx": i,
            "entry_time": bar_time,
            "tier": tier,
            "asian_range": asian["range"],
            "tp1_hit": False,
        }
        p90_detected_today = True

    # Close any remaining position at end of data
    if position is not None:
        last_bar = bars[-1]
        if position["direction"] == "LONG":
            pnl_pips = (last_bar["close"] - position["entry_price"]) / PIP_SIZE
        else:
            pnl_pips = (position["entry_price"] - last_bar["close"]) / PIP_SIZE
        pnl_dollars = pnl_pips * position["size"] * 10.0
        equity += pnl_dollars
        trades.append({
            "entry_time": position["entry_time"].isoformat(),
            "exit_time": last_bar["time"].isoformat(),
            "direction": position["direction"],
            "entry_price": position["entry_price"],
            "exit_price": last_bar["close"],
            "sl": position["sl"],
            "tp1": position["tp1"],
            "tp2": position["tp2"],
            "size": position["size"],
            "pnl_pips": round(pnl_pips, 2),
            "pnl_dollars": round(pnl_dollars, 2),
            "exit_reason": "end_data",
            "tier": position["tier"],
            "asian_range": position["asian_range"],
        })
        equity_curve.append(equity)

    return trades, equity_curve


# ===========================================================================
# RESULTS ANALYSIS
# ===========================================================================

def analyze_results(trades, equity_curve):
    """Compute performance metrics from trade list."""
    if not trades:
        return {"error": "No trades executed"}

    wins = [t for t in trades if t["pnl_pips"] > 0]
    losses = [t for t in trades if t["pnl_pips"] <= 0]

    total_pnl = sum(t["pnl_dollars"] for t in trades)
    total_pips = sum(t["pnl_pips"] for t in trades)
    avg_win = sum(t["pnl_pips"] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t["pnl_pips"] for t in losses) / len(losses) if losses else 0

    gross_profit = sum(t["pnl_dollars"] for t in wins)
    gross_loss = abs(sum(t["pnl_dollars"] for t in losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Max drawdown
    peak = equity_curve[0]
    max_dd = 0
    max_dd_pct = 0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = peak - eq
        dd_pct = (dd / peak) * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
            max_dd_pct = dd_pct

    # By exit reason
    by_exit = {}
    for t in trades:
        reason = t["exit_reason"]
        if reason not in by_exit:
            by_exit[reason] = 0
        by_exit[reason] += 1

    # By tier
    by_tier = {}
    for t in trades:
        tier = t["tier"]
        if tier not in by_tier:
            by_tier[tier] = {"trades": 0, "wins": 0, "pnl": 0}
        by_tier[tier]["trades"] += 1
        if t["pnl_pips"] > 0:
            by_tier[tier]["wins"] += 1
        by_tier[tier]["pnl"] += t["pnl_dollars"]

    # Expectancy
    win_rate = len(wins) / len(trades) * 100
    expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)

    # Kelly fraction
    if avg_loss != 0:
        kelly = (win_rate / 100 * avg_win + (1 - win_rate / 100) * avg_loss) / avg_win
    else:
        kelly = 0

    # Trading days
    trading_days = len(set(t["entry_time"][:10] for t in trades))
    avg_trades_per_day = len(trades) / max(trading_days, 1)

    return {
        "strategy": "Deep_Mean_Reversion",
        "source": "MT5_Backtest",
        "symbol": SYMBOL,
        "timeframe": "M5",
        "period": f"{START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}",
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "total_pnl_dollars": round(total_pnl, 2),
        "total_pips": round(total_pips, 2),
        "avg_win_pips": round(avg_win, 2),
        "avg_loss_pips": round(avg_loss, 2),
        "max_dd_dollars": round(-max_dd, 2),
        "max_dd_pct": round(max_dd_pct, 2),
        "profit_factor": round(profit_factor, 2),
        "expectancy_pips": round(expectancy, 3),
        "kelly_fraction": round(kelly, 4),
        "initial_equity": INITIAL_EQUITY,
        "final_equity": round(equity_curve[-1], 2),
        "total_return_pct": round((equity_curve[-1] - INITIAL_EQUITY) / INITIAL_EQUITY * 100, 1),
        "avg_trades_per_day": round(avg_trades_per_day, 2),
        "by_exit": by_exit,
        "by_tier": by_tier,
    }


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    print("=" * 70)
    print("  DMR (Deep Mean Reversion) — MT5 Backtest Engine")
    print("=" * 70)
    print()

    # Step 1: Fetch data from MT5
    try:
        bars = fetch_mt5_data(SYMBOL, TIMEFRAME, START_DATE, END_DATE)
    except (ConnectionError, RuntimeError) as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    print(f"[INFO] Data range: {bars[0]['time']} to {bars[-1]['time']}")
    print(f"[INFO] Total bars: {len(bars)}")
    print()

    # Step 2: Run backtest
    print("[BACKTEST] Running DMR strategy...")
    trades, equity_curve = run_dmr_backtest(bars)
    print(f"[BACKTEST] Completed. {len(trades)} trades generated.")
    print()

    # Step 3: Analyze results
    results = analyze_results(trades, equity_curve)

    # Step 4: Print summary
    print("=" * 70)
    print("  RESULTS SUMMARY")
    print("=" * 70)
    for key, val in results.items():
        if key not in ("by_exit", "by_tier"):
            print(f"  {key:.<35} {val}")
    print()
    print("  By Exit Reason:")
    for reason, count in results.get("by_exit", {}).items():
        print(f"    {reason:.<30} {count}")
    print()
    print("  By Tier:")
    for tier, data in results.get("by_tier", {}).items():
        wr = round(data["wins"] / data["trades"] * 100, 1) if data["trades"] > 0 else 0
        print(f"    {tier}: {data['trades']} trades, {wr}% WR, ${round(data['pnl'], 2)} PnL")
    print()

    # Step 5: Save results
    output_dir = os.path.dirname(os.path.abspath(__file__))

    results_path = os.path.join(output_dir, "dmr_mt5_backtest_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[SAVE] Results saved to: {results_path}")

    trades_path = os.path.join(output_dir, "dmr_mt5_trades.json")
    with open(trades_path, "w") as f:
        json.dump(trades, f, indent=2, default=str)
    print(f"[SAVE] Trades saved to: {trades_path}")

    return results, trades


if __name__ == "__main__":
    results, trades = main()
