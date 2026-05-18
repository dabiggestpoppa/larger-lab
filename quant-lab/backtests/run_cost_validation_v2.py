#!/usr/bin/env python3
"""
Cost Validation v2 — Re-run all 10 strategies with real costs
=============================================================
Applies per-trade cost model to v4b backtest results.

Cost model:
- Spread: 0.2 pips (EUR/USD median)
- Commission: $7/lot round-turn → 0.7 pips at 0.05 lots
- Slippage: 1 pip entry + 1 pip exit = 2 pips
- Total fixed cost per trade: ~2.9 pips

Position sizing: 5% of equity per trade
Starting equity: $10,000
EUR/USD pip value: $10 per lot (standard), $1 per mini lot, $0.10 per micro lot
"""

import json
import sys
from pathlib import Path

# Load v4b results
RESULTS_PATH = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\optimizer_v4b_20260517_193302.json")

with open(RESULTS_PATH) as f:
    data = json.load(f)

# Cost model
SPREAD_PIPS = 0.2
SLIPPAGE_PIPS = 2.0  # 1 entry + 1 exit
COMMISSION_PIPS = 0.7  # $7/lot at 0.05 lots on EUR/USD
TOTAL_COST_PER_TRADE = SPREAD_PIPS + SLIPPAGE_PIPS + COMMISSION_PIPS  # 2.9 pips

# Position sizing: 5% of $10K = $500 risk per trade
# For EUR/USD: pip value at 0.05 lots = $0.50/pip
# $500 / $0.50 = 1000 pips max SL (not realistic)
# More realistic: fixed 0.05 lots → pip value = $0.50/pip
# Commission at 0.05 lots = $7 * 0.05 = $0.35 = 0.7 pips

STARTING_EQUITY = 10000
RISK_PCT = 0.05
PIP_VALUE_PER_LOT = 10.0  # EUR/USD standard lot
LOT_SIZE = 0.05  # Fixed for comparison with v4b
PIP_VALUE = PIP_VALUE_PER_LOT * LOT_SIZE  # $0.50/pip

results = {}

for name, r in data.items():
    trades = r.get('total_trades', 0)
    if trades == 0:
        continue
    
    pnl_pips = r['total_pnl']
    win_rate = r['win_rate']
    pf = r['profit_factor']
    max_dd = r['max_dd']
    
    # Calculate cost impact
    total_cost_pips = trades * TOTAL_COST_PER_TRADE
    pnl_after_costs = pnl_pips - total_cost_pips
    
    # Recalculate PF after costs
    # We need to approximate: subtract cost from each trade's PnL
    # For winners: new_win = old_win - cost
    # For losers: new_loss = old_loss - cost (cost makes losses bigger)
    exits = r.get('by_exit', {})
    wins = exits.get('tp', 0) + exits.get('tp_partial', 0)
    losses = exits.get('sl', 0)
    
    if wins > 0 and losses > 0:
        avg_win = pnl_pips * (pf / (pf + 1)) / wins if wins > 0 else 0
        avg_loss = pnl_pips * (1 / (pf + 1)) / losses if losses > 0 else 0
        
        # After costs: each trade loses TOTAL_COST_PER_TRADE pips
        new_avg_win = avg_win - TOTAL_COST_PER_TRADE
        new_avg_loss = -(abs(avg_loss) + TOTAL_COST_PER_TRADE)
        
        if new_avg_win > 0:
            new_pf = (wins * new_avg_win) / (losses * abs(new_avg_loss))
        else:
            new_pf = 0.0
    else:
        new_pf = 0.0
    
    # Estimate new WR (costs reduce net winners)
    # A trade that was winning by < TOTAL_COST_PER_TRADE becomes a loser
    # Approximate: shift ~2.5pp based on cost distribution
    new_wr = max(0, win_rate - 2.5)
    
    # Max DD estimate: costs add to drawdown proportionally
    new_max_dd = max_dd * (1 + total_cost_pips / abs(pnl_pips)) if pnl_pips != 0 else max_dd * 2
    
    # Annual return estimate (assuming 252 trading days, ~3 years of data)
    annual_return_pct = (pnl_after_costs / 252) * PIP_VALUE / STARTING_EQUITY * 100 * 252
    
    results[name] = {
        'trades': trades,
        'pnl_before': round(pnl_pips, 2),
        'pnl_after_costs': round(pnl_after_costs, 2),
        'total_cost_pips': round(total_cost_pips, 2),
        'pf_before': round(pf, 2),
        'pf_after': round(new_pf, 2),
        'wr_before': win_rate,
        'wr_after': round(new_wr, 1),
        'max_dd_before': round(max_dd, 2),
        'max_dd_after': round(new_max_dd, 2),
        'survives': pnl_after_costs > 0 and new_pf > 1.0,
    }

# Print results
print("=" * 90)
print("COST VALIDATION v2 — All 10 Strategies")
print(f"Cost per trade: {TOTAL_COST_PER_TRADE} pips (spread {SPREAD_PIPS} + slippage {SLIPPAGE_PIPS} + commission {COMMISSION_PIPS})")
print("=" * 90)
print()

for name, r in results.items():
    status = "✅ SURVIVES" if r['survives'] else "🔴 FAILS"
    print(f"{name}:")
    print(f"  Trades: {r['trades']} | Cost: {r['total_cost_pips']}p")
    print(f"  PnL: {r['pnl_before']}p → {r['pnl_after_costs']}p (Δ{r['pnl_after_costs'] - r['pnl_before']:.0f}p)")
    print(f"  PF: {r['pf_before']} → {r['pf_after']}")
    print(f"  WR: {r['wr_before']}% → {r['wr_after']}%")
    print(f"  MaxDD: {r['max_dd_before']}p → {r['max_dd_after']}p")
    print(f"  {status}")
    print()

survivors = [n for n, r in results.items() if r['survives']]
print(f"Survival Rate: {len(survivors)}/10 — {', '.join(survivors) if survivors else 'NONE'}")

# Save results
output_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\cost-validation-v2-results.json")
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to: {output_path}")
