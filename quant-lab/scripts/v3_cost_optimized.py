#!/usr/bin/env python3
"""
v3 Cost-Optimized Projection — More aggressive fixes for strategies that still fail
===================================================================================
Key insight: The 2.9 pip cost per trade means avg win MUST be >> 2.9 pips.
Strategies with avg win < 10p need either much wider TP or much higher WR.
"""

import json
from pathlib import Path

COST_PER_TRADE = 2.9  # pips

def project(name, trades, wr, avg_win, avg_loss, 
            trade_mult, wr_delta, avg_win_mult, avg_loss_mult):
    """Project performance with given parameter changes."""
    new_trades = int(trades * trade_mult)
    new_wr = min(95, wr + wr_delta)
    new_wins = int(new_trades * new_wr / 100)
    new_losses = new_trades - new_wins
    new_avg_win = avg_win * avg_win_mult
    new_avg_loss = abs(avg_loss) * avg_loss_mult
    
    gross_pnl = new_wins * new_avg_win - new_losses * new_avg_loss
    total_cost = new_trades * COST_PER_TRADE
    net_pnl = gross_pnl - total_cost
    
    adj_win = max(0.1, new_avg_win - COST_PER_TRADE)
    adj_loss = new_avg_loss + COST_PER_TRADE
    pf_after = (new_wins * adj_win) / (new_losses * adj_loss) if new_losses > 0 and new_avg_loss > 0 else 999
    
    return {
        "name": name, "trades": new_trades, "wr": round(new_wr, 1),
        "avg_win": round(new_avg_win, 2), "avg_loss": round(new_avg_loss, 2),
        "gross_pnl": round(gross_pnl, 1), "cost": round(total_cost, 1),
        "net_pnl": round(net_pnl, 1), "pf": round(pf_after, 2),
        "survives": pf_after > 1.0, "profitable": pf_after > 1.5,
    }

print("=" * 100)
print("v3 COST-OPTIMIZED PROJECTION")
print("=" * 100)
print()

# === STRATEGIES THAT PASSED IN v2 (confirm) ===
print("--- CONFIRMED PROFITABLE (from v2) ---")
print()

# BSC: 1686 trades, 43.1% WR, 25.34p avg win, -16.87p avg loss
r = project("Blind_Structural_Chain", 1686, 43.1, 25.34, -16.87, 0.75, 17, 0.90, 0.75)
print(f"BSC: trades={r['trades']}, WR={r['wr']}%, avg_win={r['avg_win']}p, avg_loss={r['avg_loss']}p, PF={r['pf']}, net={r['net_pnl']}p -> {'OK' if r['profitable'] else 'FAIL'}")

# P90P: 255 trades, 20% WR, 24.12p avg win, -5.29p avg loss (INVERTED)
r = project("P90P_Distribution", 255, 20.0, 24.12, -5.29, 0.60, 35, 0.65, 1.10)
print(f"P90P: trades={r['trades']}, WR={r['wr']}%, avg_win={r['avg_win']}p, avg_loss={r['avg_loss']}p, PF={r['pf']}, net={r['net_pnl']}p -> {'OK' if r['profitable'] else 'FAIL'}")

# Fractal: 808 trades, 43.7% WR, 22.39p avg win, -16.91p avg loss
r = project("Fractal_Resolution", 808, 43.7, 22.39, -16.91, 0.40, 10, 1.10, 0.80)
print(f"Fractal: trades={r['trades']}, WR={r['wr']}%, avg_win={r['avg_win']}p, avg_loss={r['avg_loss']}p, PF={r['pf']}, net={r['net_pnl']}p -> {'OK' if r['profitable'] else 'FAIL'}")

print()
print("--- STRATEGIES THAT NEED MORE AGGRESSIVE FIXES ---")
print()

# === FAILURE_REPAIR: 436 trades, 50% WR, 8.37p avg win, -4.62p avg loss
# Problem: avg win 8.37p is too close to 2.9p cost. Need wider TP.
# v2 got PF 1.35. Need PF > 1.5.
# Solution: More aggressive TP (0.80x AR instead of 0.60x), stronger filters
print("Failure_Repair analysis:")
for tp_mult in [1.3, 1.5, 1.7, 2.0]:
    for trade_m in [0.50, 0.55, 0.60]:
        for wr_d in [8, 10, 12]:
            r = project("Failure_Repair", 436, 50.0, 8.37, -4.62, trade_m, wr_d, tp_mult, 0.75)
            if r['profitable']:
                print(f"  TP_mult={tp_mult}, trade_mult={trade_m}, wr_delta={wr_d}: PF={r['pf']}, net={r['net_pnl']}p, trades={r['trades']}, WR={r['wr']}%")
                break
        else:
            continue
        break
    else:
        continue
    break

# === DUAL_ENGINE: 973 trades, 51.2% WR, 4.04p avg win, -2.65p avg loss
# Problem: avg win 4.04p is WAY too close to 2.9p cost. Even with 55% trade reduction, PF=0.53
# This strategy's anchor entries have tiny wins. Need MASSIVE TP increase.
print("\nDual_Engine analysis:")
for tp_mult in [2.0, 2.5, 3.0, 3.5, 4.0]:
    for trade_m in [0.30, 0.35, 0.40]:
        for wr_d in [10, 12, 15]:
            r = project("Dual_Engine", 973, 51.2, 4.04, -2.65, trade_m, wr_d, tp_mult, 0.80)
            if r['profitable']:
                print(f"  TP_mult={tp_mult}, trade_mult={trade_m}, wr_delta={wr_d}: PF={r['pf']}, net={r['net_pnl']}p, trades={r['trades']}, WR={r['wr']}%")
                break
        else:
            continue
        break
    else:
        continue
    break

# === TWO_PLAYS: 392 trades, 42.3% WR, 7.96p avg win, -5.62p avg loss
# Problem: avg win 7.96p is marginal vs 2.9p cost
print("\nTwo_Plays analysis:")
for tp_mult in [1.3, 1.5, 1.7, 2.0]:
    for trade_m in [0.40, 0.45, 0.50]:
        for wr_d in [10, 12, 15]:
            r = project("Two_Plays", 392, 42.3, 7.96, -5.62, trade_m, wr_d, tp_mult, 0.80)
            if r['profitable']:
                print(f"  TP_mult={tp_mult}, trade_mult={trade_m}, wr_delta={wr_d}: PF={r['pf']}, net={r['net_pnl']}p, trades={r['trades']}, WR={r['wr']}%")
                break
        else:
            continue
        break
    else:
        continue
    break

# === STALL_HARVEST: 242 trades, 40.1% WR, 6.86p avg win, -4.61p avg loss
# Problem: avg win 6.86p is too close to 2.9p cost
print("\nStall_Harvest analysis:")
for tp_mult in [1.5, 1.7, 2.0, 2.5]:
    for trade_m in [0.50, 0.55, 0.60]:
        for wr_d in [12, 15, 18]:
            r = project("Stall_Harvest", 242, 40.1, 6.86, -4.61, trade_m, wr_d, tp_mult, 0.70)
            if r['profitable']:
                print(f"  TP_mult={tp_mult}, trade_mult={trade_m}, wr_delta={wr_d}: PF={r['pf']}, net={r['net_pnl']}p, trades={r['trades']}, WR={r['wr']}%")
                break
        else:
            continue
        break
    else:
        continue
    break

# === CONSTRAINT_ANCHOR: 1214 trades, 36.2% WR, 5.17p avg win, -3.25p avg loss
# Problem: avg win 5.17p is too close to 2.9p cost, AND was already losing before costs
print("\nConstraint_Anchor analysis:")
for tp_mult in [2.0, 2.5, 3.0, 3.5]:
    for trade_m in [0.20, 0.25, 0.30]:
        for wr_d in [15, 18, 20]:
            r = project("Constraint_Anchor", 1214, 36.2, 5.17, -3.25, trade_m, wr_d, tp_mult, 0.85)
            if r['profitable']:
                print(f"  TP_mult={tp_mult}, trade_mult={trade_m}, wr_delta={wr_d}: PF={r['pf']}, net={r['net_pnl']}p, trades={r['trades']}, WR={r['wr']}%")
                break
        else:
            continue
        break
    else:
        continue
    break

print()
print("=" * 100)
print("SUMMARY: Minimum parameters needed for each strategy to achieve PF > 1.5 after costs")
print("=" * 100)
