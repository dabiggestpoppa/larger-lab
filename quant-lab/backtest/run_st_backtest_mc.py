"""
ST BACKTEST + MC — EURUSD, USDCHF
==================================
Runs Symmetry Trap backtest with LIVE configs, extracts per-trade PnL,
then runs 10K MC simulations. Outputs in same format as P90 per-asset results.
"""
import json
import csv
import random
import pytz
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "engines"))

from symmetry_trap import SymmetryTrapEngine, TradeSignal, Bar, TradeDirection

DATA_DIR = Path(__file__).parent.parent / "data"
REPORTS_DIR = Path(__file__).parent.parent / "reports" / "per-asset"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

EST = pytz.timezone("US/Eastern")


def load_bars(csv_path: Path) -> list:
    bars = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                t_str = row.get("time", row.get("timestamp", row.get("date", "")))
                t = datetime.fromisoformat(t_str)
                if t.tzinfo is None:
                    t = EST.localize(t)
                else:
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


def get_asian_range(bars: list, est: pytz.timezone) -> tuple:
    """Get Asian Range high/low from 19:00-03:00 EST."""
    asian_bars = []
    for b in bars:
        h = b.timestamp.hour
        # Asian session: 19:00-03:00 EST
        if h >= 19 or h < 3:
            asian_bars.append(b)
    if not asian_bars:
        return None, None
    ah = max(b.high for b in asian_bars)
    al = min(b.low for b in asian_bars)
    return ah, al


def run_backtest(symbol: str, bars: list, config: dict) -> dict:
    """Run ST backtest, return trade results."""
    engine = SymmetryTrapEngine(config=config)

    trades = []
    current_date = None
    asian_high = None
    asian_low = None

    for i, bar in enumerate(bars):
        bar_date = bar.timestamp.date()

        # New day detection (03:00 EST = session init)
        if bar.timestamp.hour == 3 and bar.timestamp.minute == 0 and bar_date != current_date:
            current_date = bar_date
            # Find yesterday's Asian range
            prev_date = bar_date
            asian_bars = []
            for j in range(i, -1, -1):
                if bars[j].timestamp.date() != prev_date and bars[j].timestamp.date() != bar_date:
                    break
                h = bars[j].timestamp.hour
                if h >= 19 or h < 3:
                    asian_bars.append(bars[j])

            if asian_bars:
                asian_high = max(b.high for b in asian_bars)
                asian_low = min(b.low for b in asian_bars)
                engine.initialize_session(asian_high, asian_low)
            else:
                continue

        # 12 PM hard exit
        if bar.timestamp.hour == 12 and bar.timestamp.minute == 0:
            engine.hard_exit()

        if not engine.session_active:
            continue

        signal = engine.process_bar(bar)

        if signal and signal.event == "ENTRY":
            # Simulate the trade
            direction = signal.direction
            entry_px = signal.entry_price
            sl_px = signal.sl_price
            tp_px = signal.tp_price
            entry_time = signal.timestamp

            # Find bars after entry
            trade_bars = bars[i+1:]
            pnl_pips = None
            exit_type = "END"

            for tb in trade_bars:
                # Check new day (12 PM cutoff)
                if tb.timestamp.hour >= 12 and tb.timestamp.hour > entry_time.hour:
                    # End of session — close at last known
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
                else:
                    if tb.high >= sl_px:
                        pnl_pips = (entry_px - sl_px) / engine.pip_size
                        exit_type = "SL"
                        break
                    if tb.low <= tp_px:
                        pnl_pips = (entry_px - tp_px) / engine.pip_size
                        exit_type = "TP"
                        break

            if pnl_pips is None:
                # Ran out of bars — last bar close
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
            })

        elif signal and signal.event in ("TP_HIT", "SL_HIT"):
            # Already captured in ENTRY simulation — skip
            pass

    return trades


def run_mc(trades: list, n_sims: int = 10000) -> dict:
    """Run MC on trade PnLs."""
    pnls = [t["pnl_pips"] for t in trades]
    n_trades = len(pnls)

    terminal_pnls = []
    max_dds = []
    max_streaks = []

    for _ in range(n_sims):
        shuffled = random.sample(pnls, n_trades)
        terminal_pnls.append(sum(shuffled))

        cumulative = 0; peak = 0; max_dd = 0
        for p in shuffled:
            cumulative += p
            peak = max(peak, cumulative)
            max_dd = max(max_dd, peak - cumulative)
        max_dds.append(max_dd)

        max_streak = current = 0
        for p in shuffled:
            if p <= 0:
                current += 1
                max_streak = max(max_streak, current)
            else:
                current = 0
        max_streaks.append(max_streak)

    terminal_pnls.sort()
    max_dds.sort()
    max_streaks.sort()
    n = len(terminal_pnls)

    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]

    return {
        "n_simulations": n_sims,
        "terminal_pnl_median": round(terminal_pnls[n // 2], 1),
        "terminal_pnl_mean": round(sum(terminal_pnls) / n, 1),
        "terminal_pnl_5th": round(terminal_pnls[int(n * 0.05)], 1),
        "terminal_pnl_25th": round(terminal_pnls[int(n * 0.25)], 1),
        "terminal_pnl_75th": round(terminal_pnls[int(n * 0.75)], 1),
        "terminal_pnl_95th": round(terminal_pnls[int(n * 0.95)], 1),
        "max_dd_median": round(max_dds[n // 2], 1),
        "max_dd_95th": round(max_dds[int(n * 0.95)], 1),
        "max_dd_99th": round(max_dds[int(n * 0.99)], 1),
        "max_dd_worst": round(max_dds[-1], 1),
        "max_loss_streak_median": max_streaks[n // 2],
        "max_loss_streak_95th": max_streaks[int(n * 0.95)],
        "max_loss_streak_99th": max_streaks[int(n * 0.99)],
        "max_loss_streak_worst": max_streaks[-1],
    }


# ST LIVE CONFIGS (exact from run_live_config_backtest.py)
ST_CONFIGS = {
    "EURUSD": {
        "csv": "EURUSD_M5.csv",
        "tiers": {
            "T1": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0},
            "T2": {"ar_max": 30.0, "au": 12.0, "trigger": 15.0},
            "T3": {"ar_max": 45.0, "au": 15.0, "trigger": 19.0},
        },
        "gear_shifts": {
            "T1": [(15.0, "T2"), (19.0, "T3")],
            "T2": [(19.0, "T3")],
        },
    },
    "USDCHF": {
        "csv": "USDCHF_M5.csv",
        "tiers": {
            "T1": {"ar_max": 19.0, "au": 11.0, "trigger": 11.0},
            "T2": {"ar_max": 29.0, "au": 15.0, "trigger": 15.0},
            "T3": {"ar_max": 50.0, "au": 20.0, "trigger": 20.0},
        },
        "gear_shifts": {
            "T1": [(15.0, "T2"), (20.0, "T3")],
            "T2": [(20.0, "T3")],
        },
    },
}


def main():
    print("=" * 60)
    print("ST BACKTEST + MC — EURUSD, USDCHF (LIVE CONFIG)")
    print("=" * 60)

    for symbol, cfg in ST_CONFIGS.items():
        csv_path = DATA_DIR / cfg["csv"]
        if not csv_path.exists():
            print(f"SKIP {symbol}: {csv_path.name} not found")
            continue

        print(f"\n{symbol}: Loading {csv_path.name}...")
        bars = load_bars(csv_path)
        print(f"  {len(bars)} bars")

        print(f"  Running backtest...")
        trades = run_backtest(symbol, bars, cfg)
        print(f"  {len(trades)} trades")

        if not trades:
            print(f"  SKIP {symbol}: 0 trades")
            continue

        wins = [t for t in trades if t["pnl_pips"] > 0]
        losses = [t for t in trades if t["pnl_pips"] <= 0]
        wr = len(wins) / len(trades) * 100
        total_pnl = sum(t["pnl_pips"] for t in trades)
        gp = sum(t["pnl_pips"] for t in wins)
        gl = abs(sum(t["pnl_pips"] for t in losses)) if losses else 0.01
        pf = gp / gl

        print(f"  WR: {wr:.1f}% | PnL: {total_pnl:.1f}p | PF: {pf:.1f}")

        # MC
        print(f"  Running MC...")
        mc = run_mc(trades)

        result = {
            "asset": symbol,
            "timestamp": datetime.now().isoformat(),
            "backtest": {
                "trades": len(trades),
                "wins": len(wins),
                "losses": len(losses),
                "win_rate": round(wr / 100, 4),
                "total_pnl": round(total_pnl, 1),
                "profit_factor": round(pf, 2),
            },
            "monte_carlo": mc,
            "per_trade_pnl": [t["pnl_pips"] for t in trades],
        }

        out_path = REPORTS_DIR / f"{symbol}_mc_results.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"  Saved: {out_path}")

    print(f"\nDone.")
    print("=" * 60)


if __name__ == "__main__":
    main()
