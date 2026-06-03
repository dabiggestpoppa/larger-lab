"""
LIVE CONFIG BACKTEST — Exact configs deployed on MT5
=====================================================
Runs backtest + MC on the EXACT engine+asset combos running live.

P90 LIVE: GBPJPY, CHFJPY, GBPNZD, GBPAUD (with OCC_PLUS buffer SL)
ST LIVE:  EURUSD, USDCHF, NZDUSD (ST engine only)

Per MAD directive 2026-06-02 21:57: Backtest what we actually run.
"""
import json
import sys
import os
import random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "engines"))

import csv
import pytz
from collections import defaultdict

from p90_engine import P90Engine, P90Signal, Bar, TradeDirection
from symmetry_trap import SymmetryTrapEngine, TradeSignal as STSignal, Bar as STBar, TradeDirection as STDir

DATA_DIR = Path(__file__).parent.parent / "data"
REPORTS_DIR = Path(__file__).parent.parent / "reports" / "live_config_mc"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

EST = pytz.timezone("US/Eastern")


def load_bars_csv(path: str, max_rows: int = None) -> list:
    """Load M5 bars from CSV. Expects columns: time,open,high,low,close,volume"""
    bars = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if max_rows and i >= max_rows:
                break
            try:
                t = datetime.fromisoformat(row.get("time", row.get("timestamp", row.get("date", ""))))
                if t.tzinfo is None:
                    t = EST.localize(t)
                else:
                    t = t.astimezone(EST)
                bars.append(Bar(
                    time=t,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=int(float(row.get("volume", 0))),
                ))
            except (KeyError, ValueError) as e:
                continue
    bars.sort(key=lambda b: b.time)
    return bars


def classify_tier(ar_pips: float, tiers: dict) -> str:
    """Classify AR into T1/T2/T3."""
    if ar_pips <= tiers["T1"]["ar_max"]:
        return "T1"
    elif ar_pips <= tiers["T2"]["ar_max"]:
        return "T2"
    else:
        return "T3"


def run_p90_backtest(symbol: str, bars: list, config: dict) -> dict:
    """Run P90 engine backtest with live config."""
    engine = P90Engine(
        k_factor=config["k_factor"],
        tiers=config["tiers"],
        p90_threshold=config["p90_threshold"],
    )
    
    trades = []
    for bar in bars:
        signal = engine.process_bar(bar)
        if signal:
            # Simulate trade outcome
            trade = simulate_trade(signal, bars, bar, config, "P90")
            if trade:
                trades.append(trade)
    
    return compute_stats(trades, symbol, "P90")


def run_st_backtest(symbol: str, bars: list, config: dict) -> dict:
    """Run Symmetry Trap engine backtest with live config."""
    engine = SymmetryTrapEngine(
        tiers=config["tiers"],
        gear_shifts=config.get("gear_shifts", {}),
    )
    
    trades = []
    for bar in bars:
        signal = engine.process_bar(bar)
        if signal:
            trade = simulate_trade_st(signal, bars, bar, config, "ST")
            if trade:
                trades.append(trade)
    
    return compute_stats(trades, symbol, "ST")


def simulate_trade(signal, all_bars, entry_bar, config, engine_type):
    """Simulate a P90 trade — check if TP or SL hits first."""
    entry_idx = None
    for i, b in enumerate(all_bars):
        if b.time >= entry_bar.time:
            entry_idx = i
            break
    if entry_idx is None:
        return None
    
    direction = signal.direction
    entry_price = signal.entry_price
    sl = signal.sl_price
    tp = signal.tp_price
    
    for j in range(entry_idx + 1, len(all_bars)):
        b = all_bars[j]
        
        if direction == TradeDirection.BUY:
            if b.low <= sl:
                pnl = sl - entry_price
                return {"result": "LOSS", "pnl_pips": pnl, "exit": "SL", "entry_time": entry_bar.time.isoformat()}
            if b.high >= tp:
                pnl = tp - entry_price
                return {"result": "WIN", "pnl_pips": pnl, "exit": "TP", "entry_time": entry_bar.time.isoformat()}
        else:  # SELL
            if b.high >= sl:
                pnl = entry_price - sl
                return {"result": "LOSS", "pnl_pips": -pnl, "exit": "SL", "entry_time": entry_bar.time.isoformat()}
            if b.low <= tp:
                pnl = entry_price - tp
                return {"result": "WIN", "pnl_pips": pnl, "exit": "TP", "entry_time": entry_bar.time.isoformat()}
    
    # Bar ran out — close at last bar close
    last_close = all_bars[-1].close
    if direction == TradeDirection.BUY:
        pnl = last_close - entry_price
    else:
        pnl = entry_price - last_close
    return {"result": "WIN" if pnl > 0 else "LOSS", "pnl_pips": pnl, "exit": "END", "entry_time": entry_bar.time.isoformat()}


def simulate_trade_st(signal, all_bars, entry_bar, config, engine_type):
    """Simulate an ST trade."""
    entry_idx = None
    for i, b in enumerate(all_bars):
        if b.time >= entry_bar.time:
            entry_idx = i
            break
    if entry_idx is None:
        return None
    
    direction = signal.direction
    entry_price = signal.entry_price
    sl = signal.sl_price
    tp = signal.tp_price
    
    for j in range(entry_idx + 1, len(all_bars)):
        b = all_bars[j]
        
        if direction == STDir.BUY:
            if b.low <= sl:
                return {"result": "LOSS", "pnl_pips": sl - entry_price, "exit": "SL", "entry_time": entry_bar.time.isoformat()}
            if b.high >= tp:
                return {"result": "WIN", "pnl_pips": tp - entry_price, "exit": "TP", "entry_time": entry_bar.time.isoformat()}
        else:
            if b.high >= sl:
                return {"result": "LOSS", "pnl_pips": entry_price - sl, "exit": "SL", "entry_time": entry_bar.time.isoformat()}
            if b.low <= tp:
                return {"result": "WIN", "pnl_pips": entry_price - tp, "exit": "TP", "entry_time": entry_bar.time.isoformat()}
    
    last_close = all_bars[-1].close
    if direction == STDir.BUY:
        pnl = last_close - entry_price
    else:
        pnl = entry_price - last_close
    return {"result": "WIN" if pnl > 0 else "LOSS", "pnl_pips": pnl, "exit": "END", "entry_time": entry_bar.time.isoformat()}


def compute_stats(trades, symbol, engine_type):
    """Compute backtest statistics."""
    if not trades:
        return {"symbol": symbol, "engine": engine_type, "trades": 0}
    
    wins = [t for t in trades if t["result"] == "WIN"]
    losses = [t for t in trades if t["result"] == "LOSS"]
    total = len(trades)
    wr = len(wins) / total if total > 0 else 0
    
    pnls = [t["pnl_pips"] for t in trades]
    total_pnl = sum(pnls)
    gross_profit = sum(t["pnl_pips"] for t in wins)
    gross_loss = abs(sum(t["pnl_pips"] for t in losses)) if losses else 0.01
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999
    
    # Daily grouping for MC
    daily = defaultdict(list)
    for t in trades:
        day = t["entry_time"][:10]
        daily[day].append(t["pnl_pips"])
    
    daily_pnl = [sum(v) for v in daily.values()]
    daily_wins = [sum(1 for p in v if p > 0) for v in daily.values()]
    daily_losses = [sum(1 for p in v if p <= 0) for v in daily.values()]
    daily_wr = [w/(w+l) if (w+l) > 0 else 0 for w,l in zip(daily_wins, daily_losses)]
    
    # Max drawdown
    cumulative = 0
    peak = 0
    max_dd = 0
    for p in pnls:
        cumulative += p
        peak = max(peak, cumulative)
        dd = peak - cumulative
        max_dd = max(max_dd, dd)
    
    # Max loss streak
    max_streak = 0
    current = 0
    for t in trades:
        if t["result"] == "LOSS":
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    
    return {
        "symbol": symbol,
        "engine": engine_type,
        "trades": total,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(wr, 4),
        "total_pnl_pips": round(total_pnl, 1),
        "profit_factor": round(profit_factor, 2),
        "max_dd_pips": round(max_dd, 1),
        "max_loss_streak": max_streak,
        "avg_daily_losses": round(sum(daily_losses) / len(daily_losses), 1) if daily_losses else 0,
        "max_daily_losses": max(daily_losses) if daily_losses else 0,
        "p95_daily_losses": sorted(daily_losses)[int(len(daily_losses) * 0.95)] if len(daily_losses) > 20 else max(daily_losses) if daily_losses else 0,
        "avg_daily_wr": round(sum(daily_wr) / len(daily_wr), 3) if daily_wr else 0,
        "min_daily_wr": round(min(daily_wr), 3) if daily_wr else 0,
        "p5_daily_wr": sorted(daily_wr)[int(len(daily_wr) * 0.05)] if len(daily_wr) > 20 else min(daily_wr) if daily_wr else 0,
        "n_days": len(daily),
    }


def run_mc(backtest_result: dict, n_simulations: int = 10000) -> dict:
    """Run Monte Carlo simulation on backtest trades."""
    trades = backtest_result.get("_trades", [])
    if not trades:
        return {}
    
    pnls = [t["pnl_pips"] for t in trades]
    terminal_pnls = []
    max_dds = []
    
    for _ in range(n_simulations):
        shuffled = random.sample(pnls, len(pnls))
        cumulative = 0
        peak = 0
        max_dd = 0
        for p in shuffled:
            cumulative += p
            peak = max(peak, cumulative)
            max_dd = max(max_dd, peak - cumulative)
        terminal_pnls.append(cumulative)
        max_dds.append(max_dd)
    
    terminal_pnls.sort()
    max_dds.sort()
    n = len(terminal_pnls)
    
    return {
        "n_simulations": n_simulations,
        "terminal_pnl_median": round(terminal_pnls[n // 2], 1),
        "terminal_pnl_mean": round(sum(terminal_pnls) / n, 1),
        "terminal_pnl_5th": round(terminal_pnls[int(n * 0.05)], 1),
        "terminal_pnl_95th": round(terminal_pnls[int(n * 0.95)], 1),
        "max_dd_median": round(max_dds[n // 2], 1),
        "max_dd_95th": round(max_dds[int(n * 0.95)], 1),
        "max_dd_99th": round(max_dds[int(n * 0.99)], 1),
        "max_dd_worst": round(max_dds[-1], 1),
    }


# ── LIVE CONFIGS ──────────────────────────────────────────────────────

LIVE_CONFIGS = {
    # P90 assets
    "GBPJPY": {
        "engine": "P90",
        "csv": "GBPJPY_M5.csv",
        "k_factor": 0.48,
        "sl_method": "OCC_PLUS_5P",
        "sl_buffer": 5.0,
        "tiers": {
            "T1": {"ar_max": 38.0, "au": 19.0, "trigger": 23.0},
            "T2": {"ar_max": 58.0, "au": 29.0, "trigger": 35.0},
            "T3": {"ar_max": 95.0, "au": 48.0, "trigger": 58.0},
        },
        "p90_threshold": 9.12,
    },
    "CHFJPY": {
        "engine": "P90",
        "csv": "CHFJPY_M5.csv",
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "sl_buffer": 0.0,
        "tiers": {
            "T1": {"ar_max": 28.0, "au": 14.0, "trigger": 17.0},
            "T2": {"ar_max": 48.0, "au": 24.0, "trigger": 29.0},
            "T3": {"ar_max": 85.0, "au": 42.0, "trigger": 50.0},
        },
        "p90_threshold": 6.72,
    },
    "GBPAUD": {
        "engine": "P90",
        "csv": "GBPAUD_M5.csv",
        "k_factor": 0.48,
        "sl_method": "OCC_PLUS_8P",
        "sl_buffer": 8.0,
        "tiers": {
            "T1": {"ar_max": 42.0, "au": 21.0, "trigger": 25.0},
            "T2": {"ar_max": 64.0, "au": 32.0, "trigger": 38.0},
            "T3": {"ar_max": 105.0, "au": 52.0, "trigger": 63.0},
        },
        "p90_threshold": 10.08,
    },
    "GBPNZD": {
        "engine": "P90",
        "csv": "GBPNZD_M5.csv",
        "k_factor": 0.48,
        "sl_method": "OCC_PLUS_8P",
        "sl_buffer": 8.0,
        "tiers": {
            "T1": {"ar_max": 48.0, "au": 24.0, "trigger": 29.0},
            "T2": {"ar_max": 72.0, "au": 36.0, "trigger": 43.0},
            "T3": {"ar_max": 118.0, "au": 59.0, "trigger": 71.0},
        },
        "p90_threshold": 11.52,
    },
    # ST assets
    "EURUSD": {
        "engine": "ST",
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
        "engine": "ST",
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
    "NZDUSD": {
        "engine": "ST",
        "csv": "NZDUSD_M5.csv",
        "tiers": {
            "T1": {"ar_max": 28.0, "au": 14.0, "trigger": 17.0},
            "T2": {"ar_max": 42.0, "au": 17.0, "trigger": 20.0},
            "T3": {"ar_max": 64.0, "au": 21.0, "trigger": 25.0},
        },
        "gear_shifts": {
            "T1": [(20.0, "T2"), (25.0, "T3")],
            "T2": [(25.0, "T3")],
        },
    },
}


def main():
    results = {}
    
    for symbol, cfg in LIVE_CONFIGS.items():
        csv_path = DATA_DIR / cfg["csv"]
        if not csv_path.exists():
            # Try PRO variant
            csv_path = DATA_DIR / f"{symbol}PRO_M5.csv"
        if not csv_path.exists():
            print(f"  SKIP {symbol}: no CSV found")
            continue
        
        print(f"  Loading {symbol} from {csv_path.name}...")
        bars = load_bars_csv(str(csv_path))
        print(f"    {len(bars)} bars loaded")
        
        if len(bars) < 100:
            print(f"  SKIP {symbol}: insufficient data")
            continue
        
        if cfg["engine"] == "P90":
            result = run_p90_backtest(symbol, bars, cfg)
        else:
            result = run_st_backtest(symbol, bars, cfg)
        
        results[symbol] = result
        print(f"    {result.get('trades', 0)} trades | WR: {result.get('win_rate', 0):.1%} | P&L: {result.get('total_pnl_pips', 0):.1f}p")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = REPORTS_DIR / f"live_config_backtest_{timestamp}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to {out_path}")
    
    # Print summary table
    print("\n" + "="*80)
    print("LIVE CONFIG BACKTEST SUMMARY")
    print("="*80)
    print(f"{'Asset':<10} {'Engine':<6} {'Trades':>6} {'WR':>7} {'P&L(p)':>9} {'MaxDD':>7} {'MaxStk':>7} {'P95Loss':>8}")
    print("-"*80)
    for sym, r in results.items():
        print(f"{sym:<10} {r.get('engine','?'):<6} {r.get('trades',0):>6} {r.get('win_rate',0):>6.1%} {r.get('total_pnl_pips',0):>9.1f} {r.get('max_dd_pips',0):>7.1f} {r.get('max_loss_streak',0):>7} {r.get('p95_daily_losses',0):>8}")
    print("="*80)
    
    return results


if __name__ == "__main__":
    main()
