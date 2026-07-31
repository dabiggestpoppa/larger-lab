"""
CEREBUS PORTFOLIO MC BACKTEST — Exact live deployment
=====================================================
Simulates the EXACT live portfolio: all 7 assets, specific engine configs,
trading simultaneously. MC is run on the PORTFOLIO P&L, not individual assets.

LIVE PORTFOLIO:
  P90: GBPJPY (OCC+5P), CHFJPY (OCC_EXACT), GBPAUD (OCC+8P), GBPNZD (OCC+8P)
  ST:  EURUSD, USDCHF, NZDUSD

This captures:
  - Correlated loss days (GBPJPY + CHFJPY both losing same session)
  - Portfolio drawdown (not sum of individual max DDs)
  - Real daily loss count distribution
  - Real loss streak distribution
"""
import json
import csv
import random
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
REPORTS_DIR = REPO_ROOT / "reports" / "portfolio_mc"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "engines"))

from p90_engine import P90Engine, P90Signal, Bar, TradeDirection
from symmetry_trap import SymmetryTrapEngine, TradeSignal as STSignal, TradeDirection as STDir

# ── LIVE PORTFOLIO CONFIG ─────────────────────────────────────────────
PORTFOLIO = {
    "GBPJPY": {
        "engine": "P90",
        "csv": "GBPJPY_M5.csv",
        "pip_size": 0.01,
        "k_factor": 0.48,
        "sl_buffer": 5.0,  # OCC_PLUS_5P
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
        "pip_size": 0.01,
        "k_factor": 0.48,
        "sl_buffer": 0.0,  # OCC_EXACT
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
        "pip_size": 0.0001,
        "k_factor": 0.48,
        "sl_buffer": 8.0,  # OCC_PLUS_8P
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
        "pip_size": 0.0001,
        "k_factor": 0.48,
        "sl_buffer": 8.0,  # OCC_PLUS_8P
        "tiers": {
            "T1": {"ar_max": 48.0, "au": 24.0, "trigger": 29.0},
            "T2": {"ar_max": 72.0, "au": 36.0, "trigger": 43.0},
            "T3": {"ar_max": 118.0, "au": 59.0, "trigger": 71.0},
        },
        "p90_threshold": 11.52,
    },
    "EURUSD": {
        "engine": "ST",
        "csv": "EURUSD_M5.csv",
        "pip_size": 0.0001,
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
        "pip_size": 0.0001,
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
        "pip_size": 0.0001,
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


def load_bars(csv_path: str) -> list:
    """Load M5 bars from CSV."""
    bars = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                bars.append({
                    "timestamp": row["timestamp"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                })
            except (KeyError, ValueError):
                continue
    bars.sort(key=lambda b: b["timestamp"])
    return bars


def make_bar_obj(b: dict, pip_size: float):
    """Create engine Bar from raw dict."""
    return Bar(
        time=datetime.fromisoformat(b["timestamp"]),
        open=b["open"],
        high=b["high"],
        low=b["low"],
        close=b["close"],
        volume=0,
    )


def simulate_trade_p90(signal, bars_after, pip_size, sl_buffer):
    """Simulate P90 trade outcome. Returns pnl in pips."""
    direction = signal.direction
    entry = signal.entry_price
    sl = signal.sl_price
    tp = signal.tp_price
    
    for b in bars_after:
        if direction == TradeDirection.BUY:
            if b["low"] <= sl:
                return round((sl - entry) / pip_size, 1)
            if b["high"] >= tp:
                return round((tp - entry) / pip_size, 1)
        else:
            if b["high"] >= sl:
                return round((entry - sl) / pip_size, 1)
            if b["low"] <= tp:
                return round((entry - tp) / pip_size, 1)
    
    # Ran out of bars
    last = bars_after[-1]["close"] if bars_after else entry
    if direction == TradeDirection.BUY:
        return round((last - entry) / pip_size, 1)
    return round((entry - last) / pip_size, 1)


def simulate_trade_st(signal, bars_after, pip_size):
    """Simulate ST trade outcome. Returns pnl in pips."""
    direction = signal.direction
    entry = signal.entry_price
    sl = signal.sl_price
    tp = signal.tp_price
    
    for b in bars_after:
        if direction == STDir.BUY:
            if b["low"] <= sl:
                return round((sl - entry) / pip_size, 1)
            if b["high"] >= tp:
                return round((tp - entry) / pip_size, 1)
        else:
            if b["high"] >= sl:
                return round((entry - sl) / pip_size, 1)
            if b["low"] <= tp:
                return round((entry - tp) / pip_size, 1)
    
    last = bars_after[-1]["close"] if bars_after else entry
    if direction == STDir.BUY:
        return round((last - entry) / pip_size, 1)
    return round((entry - last) / pip_size, 1)


def run_portfolio_backtest() -> list:
    """
    Run portfolio backtest — all assets simultaneously.
    Returns list of all trades across all assets with timestamps.
    """
    all_trades = []
    
    for symbol, cfg in PORTFOLIO.items():
        csv_path = str(DATA_DIR / cfg["csv"])
        if not Path(csv_path).exists():
            csv_path = str(DATA_DIR / f"{symbol}PRO_M5.csv")
        if not Path(csv_path).exists():
            print(f"  SKIP {symbol}: no CSV")
            continue
        
        print(f"  Loading {symbol}...")
        bars = load_bars(csv_path)
        print(f"    {len(bars)} bars")
        
        if len(bars) < 100:
            continue
        
        pip_size = cfg["pip_size"]
        trades = []
        
        if cfg["engine"] == "P90":
            engine = P90Engine(
                k_factor=cfg["k_factor"],
                tiers=cfg["tiers"],
                p90_threshold=cfg["p90_threshold"],
            )
            for i, bar_raw in enumerate(bars):
                bar = make_bar_obj(bar_raw, pip_size)
                signal = engine.process_bar(bar)
                if signal:
                    # Apply SL buffer for OCC_PLUS configs
                    if cfg["sl_buffer"] > 0:
                        if signal.direction == TradeDirection.BUY:
                            signal.sl_price -= cfg["sl_buffer"] * pip_size
                        else:
                            signal.sl_price += cfg["sl_buffer"] * pip_size
                    
                    bars_after = bars[i+1:]
                    pnl = simulate_trade_p90(signal, bars_after, pip_size, cfg["sl_buffer"])
                    trades.append({
                        "symbol": symbol,
                        "engine": "P90",
                        "timestamp": bar_raw["timestamp"],
                        "pnl_pips": pnl,
                        "is_win": pnl > 0,
                        "direction": "BUY" if signal.direction == TradeDirection.BUY else "SELL",
                    })
        
        else:  # ST engine
            engine = SymmetryTrapEngine(
                tiers=cfg["tiers"],
                gear_shifts=cfg.get("gear_shifts", {}),
            )
            for i, bar_raw in enumerate(bars):
                bar = make_bar_obj(bar_raw, pip_size)
                signal = engine.process_bar(bar)
                if signal:
                    bars_after = bars[i+1:]
                    pnl = simulate_trade_st(signal, bars_after, pip_size)
                    trades.append({
                        "symbol": symbol,
                        "engine": "ST",
                        "timestamp": bar_raw["timestamp"],
                        "pnl_pips": pnl,
                        "is_win": pnl > 0,
                        "direction": "BUY" if signal.direction == STDir.BUY else "SELL",
                    })
        
        print(f"    {len(trades)} trades | WR: {sum(1 for t in trades if t['is_win'])/max(len(trades),1):.1%}")
        all_trades.extend(trades)
    
    # Sort all trades by timestamp
    all_trades.sort(key=lambda t: t["timestamp"])
    return all_trades


def run_monte_carlo(trades: list, n_simulations: int = 10000) -> dict:
    """Run MC simulation on portfolio trades."""
    pnls = [t["pnl_pips"] for t in trades]
    
    terminal_pnls = []
    max_dds = []
    daily_loss_counts = []
    daily_wrs = []
    max_loss_streaks = []
    
    for _ in range(n_simulations):
        shuffled = random.sample(pnls, len(pnls))
        
        # Terminal PnL
        terminal_pnls.append(sum(shuffled))
        
        # Max DD
        cumulative = 0
        peak = 0
        max_dd = 0
        for p in shuffled:
            cumulative += p
            peak = max(peak, cumulative)
            max_dd = max(max_dd, peak - cumulative)
        max_dds.append(max_dd)
        
        # Loss streak
        max_streak = 0
        current = 0
        for p in shuffled:
            if p <= 0:
                current += 1
                max_streak = max(max_streak, current)
            else:
                current = 0
        max_loss_streaks.append(max_streak)
    
    terminal_pnls.sort()
    max_dds.sort()
    max_loss_streaks.sort()
    n = len(terminal_pnls)
    
    return {
        "n_simulations": n_simulations,
        "n_trades_in_pool": len(trades),
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
        "max_loss_streak_median": max_loss_streaks[n // 2],
        "max_loss_streak_95th": max_loss_streaks[int(n * 0.95)],
        "max_loss_streak_99th": max_loss_streaks[int(n * 0.99)],
        "max_loss_streak_worst": max_loss_streaks[-1],
    }


def compute_daily_stats(trades: list) -> dict:
    """Compute per-day statistics from trade list."""
    daily = defaultdict(list)
    for t in trades:
        day = t["timestamp"][:10]
        daily[day].append(t)
    
    daily_losses = []
    daily_wrs = []
    daily_pnls = []
    
    for day, day_trades in daily.items():
        losses = sum(1 for t in day_trades if not t["is_win"])
        wins = sum(1 for t in day_trades if t["is_win"])
        total = len(day_trades)
        daily_losses.append(losses)
        daily_wrs.append(wins / total if total > 0 else 0)
        daily_pnls.append(sum(t["pnl_pips"] for t in day_trades))
    
    daily_losses.sort()
    daily_wrs.sort()
    daily_pnls.sort()
    n = len(daily_losses)
    
    return {
        "n_days": n,
        "avg_daily_trades": round(sum(len(v) for v in daily.values()) / max(n, 1), 1),
        "avg_daily_losses": round(sum(daily_losses) / max(n, 1), 1),
        "max_daily_losses": max(daily_losses) if daily_losses else 0,
        "p50_daily_losses": daily_losses[n // 2] if daily_losses else 0,
        "p75_daily_losses": daily_losses[int(n * 0.75)] if daily_losses else 0,
        "p90_daily_losses": daily_losses[int(n * 0.90)] if n > 10 else max(daily_losses) if daily_losses else 0,
        "p95_daily_losses": daily_losses[int(n * 0.95)] if n > 20 else max(daily_losses) if daily_losses else 0,
        "avg_daily_wr": round(sum(daily_wrs) / max(n, 1), 3),
        "min_daily_wr": round(min(daily_wrs), 3) if daily_wrs else 0,
        "p5_daily_wr": round(daily_wrs[int(n * 0.05)], 3) if n > 20 else min(daily_wrs) if daily_wrs else 0,
        "p25_daily_wr": round(daily_wrs[int(n * 0.25)], 3) if daily_wrs else 0,
        "avg_daily_pnl": round(sum(daily_pnls) / max(n, 1), 1),
        "worst_daily_pnl": round(min(daily_pnls), 1) if daily_pnls else 0,
        "p5_daily_pnl": round(daily_pnls[int(n * 0.05)], 1) if n > 20 else min(daily_pnls) if daily_pnls else 0,
    }


def main():
    print("="*60)
    print("CEREBUS PORTFOLIO BACKTEST — LIVE CONFIG")
    print("="*60)
    
    # Step 1: Run portfolio backtest
    print("\n[1] Running portfolio backtest...")
    trades = run_portfolio_backtest()
    
    if not trades:
        print("ERROR: No trades generated")
        return
    
    total = len(trades)
    wins = sum(1 for t in trades if t["is_win"])
    losses = total - wins
    wr = wins / total
    total_pnl = sum(t["pnl_pips"] for t in trades)
    
    print(f"\n  PORTFOLIO: {total} trades | W{wins} L{losses} | WR {wr:.1%} | P&L {total_pnl:.1f}p")
    
    # Per-asset breakdown
    print("\n  Per-asset:")
    for symbol in PORTFOLIO:
        sym_trades = [t for t in trades if t["symbol"] == symbol]
        if sym_trades:
            sw = sum(1 for t in sym_trades if t["is_win"])
            sl = len(sym_trades) - sw
            sp = sum(t["pnl_pips"] for t in sym_trades)
            print(f"    {symbol:10s}: {len(sym_trades):4d}tr | W{sw} L{sl} | WR {sw/max(len(sym_trades),1):.1%} | {sp:+.1f}p")
    
    # Step 2: Daily stats
    print("\n[2] Computing daily statistics...")
    daily_stats = compute_daily_stats(trades)
    print(f"  {daily_stats['n_days']} trading days")
    print(f"  Avg daily losses: {daily_stats['avg_daily_losses']}")
    print(f"  P95 daily losses: {daily_stats['p95_daily_losses']}")
    print(f"  Avg daily WR: {daily_stats['avg_daily_wr']:.1%}")
    print(f"  P5 daily WR: {daily_stats['p5_daily_wr']:.1%}")
    
    # Step 3: Monte Carlo
    print("\n[3] Running Monte Carlo (10,000 simulations)...")
    mc = run_monte_carlo(trades, n_simulations=10000)
    
    print(f"  Terminal PnL median: {mc['terminal_pnl_median']:.1f}p")
    print(f"  Terminal PnL 5th: {mc['terminal_pnl_5th']:.1f}p")
    print(f"  Max DD 95th: {mc['max_dd_95th']:.1f}p")
    print(f"  Max DD worst: {mc['max_dd_worst']:.1f}p")
    print(f"  Max loss streak 95th: {mc['max_loss_streak_95th']}")
    print(f"  Max loss streak worst: {mc['max_loss_streak_worst']}")
    
    # Step 4: Generate MC comparator thresholds
    print("\n[4] Generating MC comparator thresholds...")
    thresholds = {
        "portfolio": {
            "max_daily_losses": daily_stats["p95_daily_losses"],
            "max_daily_losses_hard": daily_stats["max_daily_losses"],
            "min_daily_wr": daily_stats["p5_daily_wr"],
            "min_daily_wr_hard": daily_stats["min_daily_wr"],
            "max_loss_streak": mc["max_loss_streak_95th"],
            "max_loss_streak_hard": mc["max_loss_streak_worst"],
            "max_dd_pips_95th": mc["max_dd_95th"],
            "max_dd_pips_worst": mc["max_dd_worst"],
            "worst_daily_pnl": daily_stats["worst_daily_pnl"],
            "p5_daily_pnl": daily_stats["p5_daily_pnl"],
        }
    }
    
    print(f"  Max daily losses (P95): {thresholds['portfolio']['max_daily_losses']}")
    print(f"  Max daily losses (hard): {thresholds['portfolio']['max_daily_losses_hard']}")
    print(f"  Min daily WR (P5): {thresholds['portfolio']['min_daily_wr']:.1%}")
    print(f"  Max loss streak (P95): {thresholds['portfolio']['max_loss_streak']}")
    print(f"  Max loss streak (hard): {thresholds['portfolio']['max_loss_streak_hard']}")
    
    # Save everything
    output = {
        "timestamp": datetime.now().isoformat(),
        "portfolio": list(PORTFOLIO.keys()),
        "backtest": {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wr, 4),
            "total_pnl_pips": round(total_pnl, 1),
        },
        "daily_stats": daily_stats,
        "monte_carlo": mc,
        "thresholds": thresholds,
    }
    
    out_path = REPORTS_DIR / "portfolio_mc_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to {out_path}")
    print("="*60)
    
    return output


if __name__ == "__main__":
    main()
