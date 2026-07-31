"""
Hyperliquid → Symmetry Trap Backtest
=====================================
Fetches Hyperliquid historical OHLCV data, runs through the CEREBUS
Symmetry Trap pure-Python engine (engines/symmetry_trap.py), outputs results.

This uses the SAME engine that all existing backtests use — just with
Hyperliquid data instead of MT5 data.

Usage:
    python quant-lab/backtest/run_hyperliquid_st.py --coins BTC ETH SOL --days 365
    python quant-lab/backtest/run_hyperliquid_st.py --coins BTC --days 730 --interval 1h
    python quant-lab/backtest/run_hyperliquid_st.py --all-major --days 180
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Path Setup ────────────────────────────────────────────────────────────
REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
QUANT_LAB = REPO_ROOT / "quant-lab"
DATA_DIR = QUANT_LAB / "data"
REPORTS_DIR = QUANT_LAB / "reports" / "hyperliquid"
CONFIGS_DIR = QUANT_LAB / "configs"
ENGINES_DIR = QUANT_LAB / "engines"

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(CONFIGS_DIR))
sys.path.insert(0, str(ENGINES_DIR))
sys.path.insert(0, str(QUANT_LAB / "data"))

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Imports ───────────────────────────────────────────────────────────────
from asset_configs import ASSET_CONFIGS
from hyperliquid_fetcher import fetch_candles, INTERVAL_MAP
from hyperliquid.info import Info
from hyperliquid.utils.constants import MAINNET_API_URL
from symmetry_trap import SymmetryTrapEngine, TradeSignal, Bar, TradeDirection

EST = timezone(timedelta(hours=-5))


def hl_candles_to_bars(candles: list[dict]) -> list[Bar]:
    """Convert Hyperliquid candles to engine Bar objects."""
    bars = []
    for c in candles:
        dt_utc = datetime.fromtimestamp(c["t"] / 1000, tz=timezone.utc)
        dt_est = dt_utc.astimezone(EST)
        bars.append(Bar(
            timestamp=dt_est,
            open=float(c["o"]),
            high=float(c["h"]),
            low=float(c["l"]),
            close=float(c["c"]),
        ))
    bars.sort(key=lambda b: b.timestamp)
    return bars


def load_bars_from_csv(csv_path: Path) -> list[Bar]:
    """Load bars from a Hyperliquid CSV file."""
    bars = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                t = datetime.fromisoformat(row["time"])
                if t.tzinfo is None:
                    t = t.replace(tzinfo=timezone.utc)
                t = t.astimezone(EST)
                bars.append(Bar(
                    timestamp=t,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                ))
            except (KeyError, ValueError):
                continue
    bars.sort(key=lambda b: b.timestamp)
    return bars


def run_st_backtest(
    symbol: str,
    bars: list[Bar],
    config: dict,
    verbose: bool = True,
) -> dict:
    """Run Symmetry Trap backtest using the pure-Python engine.

    Handles Asian session tracking, session initialization, and trade
    simulation — matching the logic in run_st_backtest_mc.py.
    """
    engine = SymmetryTrapEngine(config=config)

    trades = []  # List of dicts with pnl_pips, exit, direction, etc.
    current_date = None

    for i, bar in enumerate(bars):
        bar_date = bar.timestamp.date()

        # ── Session init at 3AM EST ──────────────────────────────────
        if bar.timestamp.hour == 3 and bar.timestamp.minute == 0 and bar_date != current_date:
            current_date = bar_date

            # Collect Asian session bars (19:00-03:00 EST)
            asian_bars = []
            for j in range(i, -1, -1):
                b = bars[j]
                if b.timestamp.date() != bar_date and b.timestamp.date() != current_date:
                    break
                h = b.timestamp.hour
                if h >= 19 or h < 3:
                    asian_bars.append(b)

            if asian_bars:
                asian_high = max(b.high for b in asian_bars)
                asian_low = min(b.low for b in asian_bars)
                engine.initialize_session(asian_high, asian_low)

        # ── 12PM EST: Hard exit ─────────────────────────────────────
        if bar.timestamp.hour == 12 and bar.timestamp.minute == 0:
            engine.hard_exit()

        # ── Skip if session not active ──────────────────────────────
        if not engine.session_active:
            continue

        signal = engine.process_bar(bar)

        # ── Simulate trade on ENTRY ─────────────────────────────────
        if signal and signal.event == "ENTRY":
            direction = signal.direction
            entry_px = signal.entry_price
            sl_px = signal.sl_price
            tp_px = signal.tp_price
            entry_time = signal.timestamp

            # Look at subsequent bars for TP/SL
            trade_bars = bars[i + 1:]
            pnl_pips = None
            exit_type = "END"

            for tb in trade_bars:
                # 12PM cutoff
                if tb.timestamp.hour >= 12 and tb.timestamp.hour > entry_time.hour:
                    if direction == TradeDirection.LONG:
                        pnl_pips = (tb.close - entry_px) / engine.pip_size
                    else:
                        pnl_pips = (entry_px - tb.close) / engine.pip_size
                    exit_type = "12PM"
                    break

                if direction == TradeDirection.LONG:
                    if tb.low <= sl_px:
                        pnl_pips = (sl_px - entry_px) / engine.pip_size
                        exit_type = "SL"
                        break
                    if tb.high >= tp_px:
                        pnl_pips = (tp_px - entry_px) / engine.pip_size
                        exit_type = "TP"
                        break
                else:  # SHORT
                    if tb.high >= sl_px:
                        pnl_pips = (entry_px - sl_px) / engine.pip_size
                        exit_type = "SL"
                        break
                    if tb.low <= tp_px:
                        pnl_pips = (entry_px - tp_px) / engine.pip_size
                        exit_type = "TP"
                        break

            if pnl_pips is None:
                # Ran out of bars
                last_close = bars[-1].close
                if direction == TradeDirection.LONG:
                    pnl_pips = (last_close - entry_px) / engine.pip_size
                else:
                    pnl_pips = (entry_px - last_close) / engine.pip_size
                exit_type = "END"

            trades.append({
                "pnl_pips": round(pnl_pips, 1),
                "exit": exit_type,
                "direction": "LONG" if direction == TradeDirection.LONG else "SHORT",
                "entry_time": entry_time.isoformat(),
                "au": engine.au_pips,
                "tier": engine.tier_name,
            })

    # ── Compute statistics ──────────────────────────────────────────
    total = len(trades)
    wins = sum(1 for t in trades if t["pnl_pips"] > 0)
    losses = sum(1 for t in trades if t["pnl_pips"] <= 0)
    total_pnl = sum(t["pnl_pips"] for t in trades)
    wr = (wins / total * 100.0) if total > 0 else 0.0

    gross_profit = sum(t["pnl_pips"] for t in trades if t["pnl_pips"] > 0)
    gross_loss = abs(sum(t["pnl_pips"] for t in trades if t["pnl_pips"] < 0))
    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Max drawdown
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trades:
        cumulative += t["pnl_pips"]
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    # Consecutive wins/losses
    max_consec_wins = 0
    max_consec_losses = 0
    consec_w = 0
    consec_l = 0
    for t in trades:
        if t["pnl_pips"] > 0:
            consec_w += 1
            consec_l = 0
            max_consec_wins = max(max_consec_wins, consec_w)
        else:
            consec_l += 1
            consec_w = 0
            max_consec_losses = max(max_consec_losses, consec_l)

    avg_win = (gross_profit / wins) if wins > 0 else 0.0
    avg_loss = (gross_loss / losses) if losses > 0 else 0.0
    expectancy = (total_pnl / total) if total > 0 else 0.0

    # Exit type distribution
    exit_counts = {}
    for t in trades:
        exit_counts[t["exit"]] = exit_counts.get(t["exit"], 0) + 1

    result = {
        "symbol": symbol,
        "engine": "SymmetryTrap",
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wr, 1),
        "profit_factor": round(pf, 2),
        "total_pnl_pips": round(total_pnl, 1),
        "max_drawdown_pips": round(max_dd, 1),
        "avg_win_pips": round(avg_win, 1),
        "avg_loss_pips": round(avg_loss, 1),
        "expectancy_pips": round(expectancy, 1),
        "max_consec_wins": max_consec_wins,
        "max_consec_losses": max_consec_losses,
        "gross_profit": round(gross_profit, 1),
        "gross_loss": round(gross_loss, 1),
        "exit_distribution": exit_counts,
        "bars_processed": len(bars),
        "date_range": {
            "start": bars[0].timestamp.isoformat() if bars else None,
            "end": bars[-1].timestamp.isoformat() if bars else None,
        },
    }

    if verbose:
        print("")
        print("=" * 60)
        print("  SYMMETRY TRAP BACKTEST — " + symbol + " (Hyperliquid)")
        print("=" * 60)
        print("  Period:    " + str(result['date_range']['start'][:10]) + " -> " + str(result['date_range']['end'][:10]))
        print("  Bars:      " + str(len(bars)))
        print("  Trades:    " + str(total))
        print("  Wins:      " + str(wins) + " | Losses: " + str(losses))
        print("  WR:        " + str(round(wr, 1)) + "%")
        print("  PF:        " + str(round(pf, 2)))
        print("  PnL:       " + str(round(total_pnl, 1)) + " pips")
        print("  MaxDD:     " + str(round(max_dd, 1)) + " pips")
        print("  Avg Win:   " + str(round(avg_win, 1)) + " pips")
        print("  Avg Loss:  " + str(round(avg_loss, 1)) + " pips")
        print("  Exp:       " + str(round(expectancy, 1)) + " pips/trade")
        print("  MaxConsec: W" + str(max_consec_wins) + " / L" + str(max_consec_losses))
        if exit_counts:
            print("  Exits:     " + str(exit_counts))
        print("=" * 60)

    return result


def main():
    parser = argparse.ArgumentParser(description="Hyperliquid Symmetry Trap Backtest")
    parser.add_argument("--coins", nargs="+", default=["BTC", "ETH"],
                        help="Coin symbols (default: BTC ETH)")
    parser.add_argument("--all-major", action="store_true",
                        help="Fetch BTC, ETH, SOL only")
    parser.add_argument("--interval", default="5m",
                        choices=list(INTERVAL_MAP.keys()),
                        help="Candle interval (default: 5m)")
    parser.add_argument("--days", type=int, default=365,
                        help="Days of history (default: 365)")
    parser.add_argument("--start-date", type=str, default=None,
                        help="Start date YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, default=None,
                        help="End date YYYY-MM-DD")
    parser.add_argument("--fetch-only", action="store_true",
                        help="Only fetch data, don't backtest")
    parser.add_argument("--use-csv", action="store_true",
                        help="Use existing CSV files")
    parser.add_argument("--verbose", action="store_true", default=True,
                        help="Verbose output")
    args = parser.parse_args()

    if args.all_major:
        coins = ["BTC", "ETH", "SOL"]
    else:
        coins = args.coins

    interval = INTERVAL_MAP[args.interval]
    info = Info(MAINNET_API_URL)

    # Time range
    now_ms = int(time.time() * 1000)
    if args.start_date:
        start_dt = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        start_ms = int(start_dt.timestamp() * 1000)
    else:
        start_ms = now_ms - args.days * 24 * 3600 * 1000

    if args.end_date:
        end_dt = datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_ms = int(end_dt.timestamp() * 1000)
    else:
        end_ms = now_ms

    print("Hyperliquid Symmetry Trap Backtest")
    print("  Coins:    " + ", ".join(coins))
    print("  Interval: " + interval)
    print("  Range:    " + datetime.fromtimestamp(start_ms/1000, tz=timezone.utc).strftime('%Y-%m-%d')
          + " -> " + datetime.fromtimestamp(end_ms/1000, tz=timezone.utc).strftime('%Y-%m-%d'))
    print("")

    all_results = {}

    for coin in coins:
        symbol = coin + "USD"
        config_key = symbol

        if config_key not in ASSET_CONFIGS:
            print("  [" + coin + "] WARNING: No config in ASSET_CONFIGS, using defaults")
            config = {
                "tiers": {
                    "T1": {"ar_max": 60.0, "au": 200.0, "trigger": 240.0},
                    "T2": {"ar_max": 60.0, "au": 500.0, "trigger": 600.0},
                    "T3": {"ar_max": 60.0, "au": 1000.0, "trigger": 1200.0},
                },
                "gear_shifts": {},
            }
        else:
            config = ASSET_CONFIGS[config_key]

        # ── Step 1: Get data ────────────────────────────────────────
        csv_path = DATA_DIR / (coin + "USD_M5.csv")
        if interval != "5m":
            csv_path = DATA_DIR / (coin + "USD_" + interval + ".csv")

        if args.use_csv and csv_path.exists():
            print("  [" + coin + "] Loading from CSV: " + str(csv_path))
            bars = load_bars_from_csv(csv_path)
        else:
            print("  [" + coin + "] Fetching from Hyperliquid API...")
            candles = fetch_candles(info, coin, interval, start_ms, end_ms)
            if not candles:
                print("  [" + coin + "] No data, skipping.")
                continue

            # Save CSV for reuse
            from hyperliquid_fetcher import candles_to_csv
            rows = candles_to_csv(candles, csv_path)
            print("  [" + coin + "] Saved " + str(rows) + " candles -> " + str(csv_path))

            bars = hl_candles_to_bars(candles)

        if not bars:
            print("  [" + coin + "] No bars loaded, skipping.")
            continue

        print("  [" + coin + "] Loaded " + str(len(bars)) + " bars")

        if args.fetch_only:
            continue

        # ── Step 2: Run backtest ────────────────────────────────────
        result = run_st_backtest(symbol, bars, config, verbose=args.verbose)
        all_results[symbol] = result

        # Save individual result
        result_path = REPORTS_DIR / (symbol + "_st_backtest.json")
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print("  [" + coin + "] Results -> " + str(result_path))

    # ── Summary ────────────────────────────────────────────────────
    if all_results and not args.fetch_only:
        summary_path = REPORTS_DIR / "hyperliquid_st_summary.json"
        with open(summary_path, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        print("")
        print("Summary -> " + str(summary_path))

        # Print comparison table
        print("")
        print("=" * 80)
        print("  HYPERLIQUID SYMMETRY TRAP — MULTI-ASSET SUMMARY")
        print("=" * 80)
        header = "  %-10s %8s %8s %8s %12s %10s %10s" % (
            "Symbol", "Trades", "WR%", "PF", "PnL(pips)", "MaxDD", "Exp")
        print(header)
        print("  " + "-" * 66)
        for sym, r in all_results.items():
            line = "  %-10s %8d %7.1f%% %7.2f %10.1f %9.1f %9.1f" % (
                sym, r['total_trades'], r['win_rate'], r['profit_factor'],
                r['total_pnl_pips'], r['max_drawdown_pips'], r['expectancy_pips'])
            print(line)
        print("=" * 80)


if __name__ == "__main__":
    main()
