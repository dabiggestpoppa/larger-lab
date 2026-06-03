"""
CEREBUS PORTFOLIO MC — Combine individual asset MC into portfolio-level
========================================================================
Reads per-asset MC results (already extracted from full backtest),
pools all trade P&Ls, and runs MC on the PORTFOLIO.

LIVE PORTFOLIO: GBPJPY, CHFJPY, GBPAUD, GBPNZD (P90) + EURUSD, USDCHF, NZDUSD (ST)
"""
import json
import random
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
REPORTS_DIR = REPO_ROOT / "reports"
PORTFOLIO_MC_DIR = REPORTS_DIR / "portfolio_mc"
PORTFOLIO_MC_DIR.mkdir(parents=True, exist_ok=True)

# LIVE PORTFOLIO assets
LIVE_ASSETS = ["GBPJPY", "CHFJPY", "GBPAUD", "GBPNZD", "EURUSD", "USDCHF", "NZDUSD"]

# MC simulation parameters
N_SIMULATIONS = 10000
INITIAL_BALANCE = 10000.0
RISK_PER_TRADE_PCT = 0.01  # 1%


def load_asset_trades(symbol: str) -> list:
    """
    Load individual trade P&Ls from per-asset MC results.
    Returns list of per-trade PnL in pips.
    """
    mc_path = REPORTS_DIR / "per-asset" / f"{symbol}_mc_results.json"
    if not mc_path.exists():
        print(f"  SKIP {symbol}: no MC results")
        return []
    
    data = json.loads(mc_path.read_text())
    
    # The MC results contain the raw per-trade PnL list
    if "per_trade_pnl" in data:
        return data["per_trade_pnl"]
    
    # If not in MC, extract from backtest + MC reorder
    bt = data.get("backtest", {})
    mc = data.get("monte_carlo", {})
    
    total_trades = bt.get("trades", 0)
    wins = bt.get("wins", 0)
    losses = bt.get("losses", 0)
    
    if total_trades == 0:
        print(f"  SKIP {symbol}: 0 trades in backtest")
        return []
    
    # Reconstruct individual trade P&Ls from MC trade list
    if "trades" in mc and mc["trades"]:
        return mc["trades"]
    
    print(f"  SKIP {symbol}: no trade-level data in MC results")
    return []


def load_all_portfolio_trades() -> dict:
    """Load trade P&Ls for all live assets."""
    all_trades = {}
    total_pool = 0
    
    for sym in LIVE_ASSETS:
        trades = load_asset_trades(sym)
        if trades:
            all_trades[sym] = trades
            total_pool += len(trades)
            wins = sum(1 for t in trades if t > 0)
            wr = wins / len(trades) if trades else 0
            print(f"  {sym}: {len(trades)} trades | WR {wr:.1%} | sum={sum(trades):.1f}p")
    
    print(f"\n  Total trade pool: {total_pool}")
    return all_trades


def run_portfolio_mc(all_trades: dict, n_sims: int = N_SIMULATIONS) -> dict:
    """Run MC on the combined portfolio trade pool."""
    # Pool ALL trades across all assets
    pooled_pnls = []
    for sym, trades in all_trades.items():
        pooled_pnls.extend(trades)
    
    n_trades = len(pooled_pnls)
    print(f"\n  Pooled: {n_trades} trades across {len(all_trades)} assets")
    
    if n_trades == 0:
        return {}
    
    # Overall stats from pooled trades
    wins = [p for p in pooled_pnls if p > 0]
    losses = [p for p in pooled_pnls if p < 0]
    total_wr = len(wins) / n_trades * 100
    total_pnl = sum(pooled_pnls)
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses)) if losses else 0.01
    pf = gross_profit / gross_loss
    
    print(f"  Pooled WR: {total_wr:.1f}% | P&L: {total_pnl:.1f}p | PF: {pf:.1f}")
    
    # MC simulations
    terminal_pnls = []
    max_dds = []
    max_streaks = []
    daily_loss_dist = []  # Track loss count per "day" (chunk of trades)
    
    # Estimate trades per day from live data
    # Live runs ~5-15 trades/day across 7 assets
    trades_per_day = 8  # conservative estimate
    
    for _ in range(n_sims):
        shuffled = random.sample(pooled_pnls, n_trades)
        
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
        
        # Max loss streak
        max_streak = 0
        current = 0
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
    
    # Per-asset in portfolio
    per_asset = {}
    for sym in all_trades:
        trades = all_trades[sym]
        aw = sum(1 for t in trades if t > 0)
        al = len(trades) - aw
        per_asset[sym] = {
            "trades": len(trades),
            "wins": aw,
            "losses": al,
            "win_rate": round(aw / len(trades) * 100, 1) if trades else 0,
            "total_pnl": round(sum(trades), 1),
        }
    
    result = {
        "portfolio": [sym for sym in all_trades],
        "timestamp": datetime.now().isoformat(),
        "n_simulations": n_sims,
        "pooled_stats": {
            "total_trades": n_trades,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(total_wr, 1),
            "total_pnl_pips": round(total_pnl, 1),
            "profit_factor": round(pf, 2),
        },
        "per_asset": per_asset,
        "monte_carlo": {
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
        },
    }
    
    return result


def generate_thresholds(mc_result: dict) -> dict:
    """Generate MC comparator thresholds from portfolio MC results."""
    mc = mc_result["monte_carlo"]
    pool = mc_result["pooled_stats"]
    
    # Estimate daily loss count from pooled trades
    # Assume ~8 trades/day across portfolio (based on live observation)
    avg_daily_trades = 8
    total_pool = pool["total_trades"]
    total_losses = pool["losses"]
    loss_rate = total_losses / total_pool if total_pool > 0 else 0
    avg_daily_losses = avg_daily_trades * loss_rate
    
    # P95 daily loss count from MC shuffle
    # From MC: if we shuffle all trades and chunk into days, what's P95 daily loss count?
    # Use binomial approximation: n=8 trades, p=loss_rate, P95
    # More accurately: use MC max_dd_worst / avg_loss_size
    
    thresholds = {
        # Daily loss count thresholds
        "max_daily_losses": max(3, int(avg_daily_losses * 2.5)),  # ~P95
        "max_daily_losses_hard": max(5, int(avg_daily_losses * 4)),  # ~P99
        
        # Daily WR thresholds
        "min_daily_wr": round(pool["win_rate"] / 100 * 0.70, 2),  # 70% of backtest WR
        "min_daily_wr_hard": round(pool["win_rate"] / 100 * 0.55, 2),  # 55% of backtest WR
        
        # Loss streak thresholds
        "max_loss_streak": mc["max_loss_streak_95th"],
        "max_loss_streak_hard": mc["max_loss_streak_worst"],
        
        # Drawdown thresholds (pips)
        "max_dd_pips_95th": mc["max_dd_95th"],
        "max_dd_pips_worst": mc["max_dd_worst"],
        
        # Per-asset thresholds (from individual MC)
        "per_asset": {},
    }
    
    # Add per-asset thresholds
    for sym, stats in mc_result.get("per_asset", {}).items():
        thresholds["per_asset"][sym] = {
            "max_daily_losses": max(3, int(stats["losses"] * 0.08)),  # 8% of total losses per day
            "min_daily_wr": round(stats["win_rate"] / 100 * 0.70, 2),
            "max_loss_streak": max(2, int(stats["losses"] * 0.03)),
            "backtest_wr": stats["win_rate"] / 100,
            "backtest_trades": stats["trades"],
        }
    
    return thresholds


def main():
    print("="*60)
    print("CEREBUS PORTFOLIO MC — LIVE CONFIG")
    print("="*60)
    
    # Step 1: Load all trade P&Ls
    print("\n[1] Loading trade P&Ls from per-asset MC results...")
    all_trades = load_all_portfolio_trades()
    
    if not all_trades:
        print("ERROR: No trades loaded")
        return
    
    # Step 2: Run portfolio MC
    print(f"\n[2] Running Monte Carlo ({N_SIMULATIONS} sims)...")
    mc_result = run_portfolio_mc(all_trades, N_SIMULATIONS)
    
    mc = mc_result["monte_carlo"]
    pool = mc_result["pooled_stats"]
    
    print(f"\n  RESULTS:")
    print(f"  Pooled: {pool['total_trades']} trades | WR {pool['win_rate']:.1f}% | PF {pool['profit_factor']:.1f}")
    print(f"  Terminal PnL median: {mc['terminal_pnl_median']:.1f}p")
    print(f"  Terminal PnL 5th: {mc['terminal_pnl_5th']:.1f}p")
    print(f"  Max DD 95th: {mc['max_dd_95th']:.1f}p")
    print(f"  Max DD worst: {mc['max_dd_worst']:.1f}p")
    print(f"  Max loss streak P95: {mc['max_loss_streak_95th']}")
    print(f"  Max loss streak worst: {mc['max_loss_streak_worst']}")
    
    # Step 3: Generate thresholds
    print("\n[3] Generating thresholds...")
    thresholds = generate_thresholds(mc_result)
    mc_result["thresholds"] = thresholds
    
    print(f"  Daily losses (P95): {thresholds['max_daily_losses']}")
    print(f"  Daily losses (hard): {thresholds['max_daily_losses_hard']}")
    print(f"  Daily WR (min): {thresholds['min_daily_wr']:.0%}")
    print(f"  Daily WR (hard): {thresholds['min_daily_wr_hard']:.0%}")
    print(f"  Loss streak (P95): {thresholds['max_loss_streak']}")
    print(f"  Loss streak (hard): {thresholds['max_loss_streak_hard']}")
    
    # Save results
    out_path = PORTFOLIO_MC_DIR / "portfolio_mc_results.json"
    with open(out_path, "w") as f:
        json.dump(mc_result, f, indent=2, default=str)
    
    # Save thresholds separately for mc_comparator
    thresh_path = PORTFOLIO_MC_DIR / "portfolio_thresholds.json"
    with open(thresh_path, "w") as f:
        json.dump(thresholds, f, indent=2, default=str)
    
    print(f"\n✅ Results: {out_path}")
    print(f"✅ Thresholds: {thresh_path}")
    print("="*60)
    
    return mc_result


if __name__ == "__main__":
    main()
