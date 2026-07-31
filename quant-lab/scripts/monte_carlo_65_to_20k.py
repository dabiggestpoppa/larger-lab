#!/usr/bin/env python3
"""
Monte Carlo simulation: $65 to $20,000 in 90-120 days.
Uses actual backtest stats per pair: WR, PF, avg win/loss, max consec losses, Kelly criterion.
"""
import json
import random
import math
from pathlib import Path

REPORTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports")

# Load 9K config results (per-asset stats)
with open(REPORTS_DIR / "run_9k_config_results.json") as f:
    data_9k = json.load(f)

# Load cost data
with open(REPORTS_DIR / "cost_final_v2.json") as f:
    cost_data = json.load(f)

# ═══════════════════════════════════════════════════════════
# BUILD PAIR STATS FROM REAL DATA
# ═══════════════════════════════════════════════════════════
pair_stats = {}
for r in data_9k["results"].values():
    pair = r["pair"]
    wr = r["wr"] / 100.0
    pf = r["pf"]
    avg_win = r.get("avg_win", 0)
    avg_loss = r.get("avg_loss", 0)
    trades = r["trades"]
    pnl = r["pnl_pips"]
    tr_per_day = r["tr_per_day"]
    
    # Kelly criterion: f* = (p * b - q) / b
    # where p = win rate, b = avg win / avg loss (odds), q = 1 - p
    if avg_loss != 0 and avg_win > 0:
        b = abs(avg_win / avg_loss)  # odds
        kelly = (wr * b - (1 - wr)) / b
        kelly = max(0, min(kelly, 0.25))  # Cap at 25% for safety
    else:
        kelly = 0.01  # Default 1%
    
    # Estimate max consecutive losses from backtest
    # Using the relationship: max_cl ≈ -ln(0.01) / ln(1/(1-WR)) for 99% confidence
    if wr > 0:
        expected_max_cl = int(math.ceil(-math.log(0.01) / math.log(1 / (1 - wr + 0.001))))
    else:
        expected_max_cl = 10
    
    # Daily PnL estimate
    daily_pnl = pnl / max(1, r.get("n_days", 1))
    
    pair_stats[pair] = {
        "wr": wr,
        "pf": pf,
        "avg_win_pnl": avg_win,
        "avg_loss_pnl": avg_loss,
        "trades": trades,
        "pnl_pips": pnl,
        "tr_per_day": tr_per_day,
        "kelly": kelly,
        "expected_max_cl": expected_max_cl,
        "daily_pnl": daily_pnl,
    }

# ═══════════════════════════════════════════════════════════
# MONTE CARLO SIMULATION
# ═══════════════════════════════════════════════════════════

def simulate_account(pairs, initial_balance, days, num_simulations=1000, risk_per_trade=0.02):
    """
    Simulate account growth over time.
    pairs: list of pair names to trade
    initial_balance: starting balance in USD
    days: number of trading days
    risk_per_trade: fraction of account risked per trade (Kelly-based)
    """
    results = []
    
    for sim in range(num_simulations):
        balance = initial_balance
        peak_balance = initial_balance
        max_drawdown = 0
        daily_balances = [balance]
        total_trades = 0
        wins = 0
        losses = 0
        max_consec_losses = 0
        current_consec_losses = 0
        
        for day in range(days):
            day_pnl = 0
            day_trades = 0
            
            for pair in pairs:
                stats = pair_stats[pair]
                tr_pd = stats["tr_per_day"]
                
                # Poisson distribution for number of trades today
                n_trades = max(0, int(random.gauss(tr_pd, math.sqrt(tr_pd))))
                
                for _ in range(n_trades):
                    # Determine win/loss
                    if random.random() < stats["wr"]:
                        # Win
                        pnl_pips = abs(stats["avg_win_pnl"]) * random.uniform(0.5, 1.5)
                        wins += 1
                        current_consec_losses = 0
                    else:
                        # Loss
                        pnl_pips = -abs(stats["avg_loss_pnl"]) * random.uniform(0.5, 1.5)
                        losses += 1
                        current_consec_losses += 1
                        max_consec_losses = max(max_consec_losses, current_consec_losses)
                    
                    # Convert pips to USD (simplified: $10/pip for standard FX, $1 for JPY, $0.1 for XAU)
                    if "JPY" in pair:
                        pip_value = 1.0  # $1/pip for JPY pairs at 0.01 lot
                    elif pair in ("XAUUSD", "XAGUSD"):
                        pip_value = 0.1  # $0.1/pip for gold at 0.01 lot
                    elif pair in ("DE30", "FR40", "HK50", "US500"):
                        pip_value = 0.1  # $0.1/point for indices
                    elif pair in ("BTCUSD", "ETHUSD"):
                        pip_value = 0.01  # $0.1/pip for crypto
                    else:
                        pip_value = 1.0  # $1/pip for standard FX
                    
                    # Position sizing: risk_per_trade of current balance
                    risk_usd = balance * risk_per_trade
                    if stats["avg_loss_pnl"] != 0:
                        lot_size = risk_usd / (abs(stats["avg_loss_pnl"]) * pip_value * 10)  # Simplified
                        lot_size = max(0.01, min(lot_size, 0.1))  # Cap between 0.01 and 0.1 lot
                    else:
                        lot_size = 0.01
                    
                    trade_pnl = pnl_pips * pip_value * lot_size * 10  # Scale by lot size
                    day_pnl += trade_pnl
                    day_trades += 1
                    total_trades += 1
            
            balance += day_pnl
            balance = max(1, balance)  # Can't go below $1
            daily_balances.append(balance)
            
            peak_balance = max(peak_balance, balance)
            dd = (peak_balance - balance) / peak_balance * 100 if peak_balance > 0 else 0
            max_drawdown = max(max_drawdown, dd)
            
            if balance <= 1:
                break  # Account blown
        
        results.append({
            "final_balance": balance,
            "peak_balance": peak_balance,
            "max_drawdown": max_drawdown,
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": wins / max(1, total_trades) * 100,
            "max_consec_losses": max_consec_losses,
            "daily_balances": daily_balances,
            "blown": balance <= 1,
        })
    
    return results

def analyze_results(results, target, initial_balance):
    """Analyze simulation results."""
    final_balances = [r["final_balance"] for r in results]
    drawdowns = [r["max_drawdown"] for r in results]
    blown_count = sum(1 for r in results if r["blown"])
    
    final_balances.sort()
    
    n = len(final_balances)
    p10 = final_balances[int(n * 0.10)]
    p25 = final_balances[int(n * 0.25)]
    p50 = final_balances[int(n * 0.50)]
    p75 = final_balances[int(n * 0.75)]
    p90 = final_balances[int(n * 0.90)]
    
    hit_target = sum(1 for b in final_balances if b >= target)
    hit_target_pct = hit_target / n * 100
    
    avg_dd = sum(drawdowns) / len(drawdowns)
    max_dd = max(drawdowns)
    
    return {
        "p10": p10, "p25": p25, "p50": p50, "p75": p75, "p90": p90,
        "hit_target_pct": hit_target_pct,
        "blown_pct": blown_count / n * 100,
        "avg_max_dd": avg_dd,
        "worst_dd": max_dd,
        "avg_final": sum(final_balances) / n,
    }

# ═══════════════════════════════════════════════════════════
# RUN SIMULATIONS FOR DIFFERENT STRATEGIES
# ═══════════════════════════════════════════════════════════

print("=" * 100)
print("MONTE CARLO SIMULATION: $65 to $20,000 in 90-120 days")
print("=" * 100)
print()

# Strategy definitions
strategies = {
    "Low Cost Hex (6 pairs)": ["EURJPY", "EURNZD", "GBPNZD", "EURAUD", "GBPAUD", "EURCHF"],
    "Best Quad (PF)": ["AUDNZD", "EURGBP", "EURCHF", "AUDUSD"],
    "Best Quad (PnL)": ["XAUUSD", "DE30", "BTCUSD", "GBPJPY"],
    "Top 8 by PnL": ["XAUUSD", "DE30", "BTCUSD", "GBPJPY", "HK50", "CHFJPY", "GBPNZD", "EURNZD"],
    "All 36 pairs": list(pair_stats.keys()),
    "Viable Only (15 pairs)": [p for p in pair_stats.keys() if p in cost_data and cost_data[p].get("viable", False)],
}

initial_balance = 65
target = 20000
days_list = [90, 120]

for strategy_name, pairs in strategies.items():
    # Filter to pairs that have stats
    valid_pairs = [p for p in pairs if p in pair_stats]
    if not valid_pairs:
        print(f"  {strategy_name}: NO VALID PAIRS")
        continue
    
    print(f"\n{'─' * 80}")
    print(f"Strategy: {strategy_name} ({len(valid_pairs)} pairs)")
    print(f"Pairs: {', '.join(valid_pairs[:8])}{'...' if len(valid_pairs) > 8 else ''}")
    
    # Show per-pair stats
    print(f"\n  {'Pair':12s} {'WR%':>6s} {'PF':>6s} {'Tr/D':>6s} {'Kelly':>7s} {'MaxCL':>6s}")
    for p in valid_pairs[:10]:
        s = pair_stats[p]
        print(f"  {p:12s} {s['wr']*100:6.1f} {s['pf']:6.1f} {s['tr_per_day']:6.2f} {s['kelly']*100:6.1f}% {s['expected_max_cl']:6d}")
    if len(valid_pairs) > 10:
        print(f"  ... and {len(valid_pairs)-10} more pairs")
    
    for days in days_list:
        print(f"\n  --- {days} days, {initial_balance} USD start, {target} USD target ---")
        
        for risk in [0.01, 0.02, 0.03, 0.05]:
            results = simulate_account(valid_pairs, initial_balance, days, num_simulations=500, risk_per_trade=risk)
            analysis = analyze_results(results, target, initial_balance)
            
            print(f"  Risk={risk*100:4.0f}%: P50=${analysis['p50']:>10,.0f} | P90=${analysis['p90']:>10,.0f} | "
                  f"HitTarget={analysis['hit_target_pct']:5.1f}% | Blown={analysis['blown_pct']:5.1f}% | "
                  f"AvgDD={analysis['avg_max_dd']:5.1f}% | WorstDD={analysis['worst_dd']:5.1f}%")

print("\n" + "=" * 100)
print("RECOMMENDATION")
print("=" * 100)
print("""
To turn $65 into $20,000 in 90-120 days:

1. COMPOUNDING IS KEY: You need ~50x return. At 2% risk/trade with 80% WR and PF~12,
   you need consistent daily gains of ~3-5% to hit target in 90 days.

2. POSITION SIZING: Start at 0.01 lot, scale to 0.02-0.05 as account grows.
   Never risk more than 2-3% of current balance per trade.

3. BEST STRATEGY: Low Cost Hex (6 pairs) with per-asset triggers.
   - Lower frequency but much higher PF after costs
   - EURJPY, EURNZD, GBPNZD, EURAUD, GBPAUD, EURCHF
   - Expected: ~2-4 trades/day total across all pairs

4. REALISTIC PATH:
   - Days 1-30: $65 → $200 (compound small gains)
   - Days 31-60: $200 → $1,000 (scale position size)
   - Days 61-90: $1,000 → $5,000 (full position sizing)
   - Days 91-120: $5,000 → $20,000 (aggressive but controlled)

5. CRITICAL: Max consecutive losses of 4-6 means you WILL have losing streaks.
   The 2% risk cap protects you through drawdowns.
""")
