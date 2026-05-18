#!/usr/bin/env python3
"""
v2 Cost Projection — Model the expected impact of v2 fixes on each strategy
============================================================================
Uses v4b backtest results as baseline, then models the effect of:
- Reduced trade frequency (fewer trades = less cost drag)
- Improved win rate (trend filter, confirmation candles, etc.)
- Better risk/reward (wider TP, tighter SL)
- Time-based exits (eliminate end_data losses)
"""

import json
from pathlib import Path

# v4b baseline results
BASELINE = {
    "Blind_Structural_Chain": {"trades": 1686, "wins": 727, "losses": 959, "wr": 43.1,
                                "pnl": 2248.13, "avg_win": 25.34, "avg_loss": -16.87, "pf": 1.14,
                                "end_data": 489, "tp": 401, "sl": 796},
    "Stall_Harvest": {"trades": 242, "wins": 97, "losses": 145, "wr": 40.1,
                      "pnl": -3.24, "avg_win": 6.86, "avg_loss": -4.61, "pf": 1.0,
                      "end_data": 1, "tp": 96, "sl": 145},
    "Failure_Repair": {"trades": 436, "wins": 218, "losses": 218, "wr": 50.0,
                       "pnl": 817.29, "avg_win": 8.37, "avg_loss": -4.62, "pf": 1.81,
                       "end_data": 2, "tp": 217, "sl": 217},
    "Dual_Engine": {"trades": 973, "wins": 498, "losses": 475, "wr": 51.2,
                    "pnl": 756.96, "avg_win": 4.04, "avg_loss": -2.65, "pf": 1.60,
                    "end_data": 1, "tp": 497, "sl": 475},
    "Two_Plays": {"trades": 392, "wins": 166, "losses": 226, "wr": 42.3,
                  "pnl": 52.67, "avg_win": 7.96, "avg_loss": -5.62, "pf": 1.04,
                  "end_data": 3, "tp": 164, "sl": 225},
    "P90P_Distribution": {"trades": 255, "wins": 51, "losses": 204, "wr": 20.0,
                          "pnl": 149.85, "avg_win": 24.12, "avg_loss": -5.29, "pf": 1.14,
                          "end_data": 6, "tp": 47, "sl": 202},
    "Fractal_Resolution": {"trades": 808, "wins": 353, "losses": 455, "wr": 43.7,
                           "pnl": 206.69, "avg_win": 22.39, "avg_loss": -16.91, "pf": 1.03,
                           "end_data": 150, "tp": 251, "sl": 407},
    "Constraint_Anchor": {"trades": 1214, "wins": 439, "losses": 775, "wr": 36.2,
                          "pnl": -248.84, "avg_win": 5.17, "avg_loss": -3.25, "pf": 0.90,
                          "end_data": 0, "tp": 0, "sl": 0, "tp_partial": 1214},
}

COST_PER_TRADE = 2.9  # pips

def project_v2(name, baseline, trade_mult, wr_delta, avg_win_mult, avg_loss_mult, end_data_elim=True):
    """
    Project v2 performance based on parameter changes.
    
    trade_mult: multiplier for trade count (e.g., 0.6 = 40% reduction)
    wr_delta: change in win rate (e.g., +10 = +10 percentage points)
    avg_win_mult: multiplier for avg win size
    avg_loss_mult: multiplier for avg loss size (positive = smaller losses)
    end_data_elim: whether end_data exits are eliminated
    """
    b = baseline.copy()
    
    # New trade count
    new_trades = int(b["trades"] * trade_mult)
    
    # New win rate
    new_wr = min(95, b["wr"] + wr_delta)
    
    # New win/loss counts
    new_wins = int(new_trades * new_wr / 100)
    new_losses = new_trades - new_wins
    
    # New avg win/loss
    new_avg_win = b["avg_win"] * avg_win_mult
    new_avg_loss = abs(b["avg_loss"]) * avg_loss_mult  # positive number
    
    # Handle end_data exits
    end_data_count = b.get("end_data", 0)
    if end_data_elim and end_data_count > 0:
        # Assume 60% of end_data would become losses, 40% winners
        end_data_as_losses = int(end_data_count * 0.6 * trade_mult)
        end_data_as_wins = int(end_data_count * 0.4 * trade_mult)
        # These are already counted in wins/losses above, but we adjust
        # The time exit converts them to resolved trades
        pass
    
    # Gross PnL
    gross_win_pnl = new_wins * new_avg_win
    gross_loss_pnl = new_losses * new_avg_loss
    gross_pnl = gross_win_pnl - gross_loss_pnl
    
    # Cost impact
    total_cost = new_trades * COST_PER_TRADE
    net_pnl = gross_pnl - total_cost
    
    # PF after costs
    if new_avg_win > COST_PER_TRADE:
        adj_avg_win = new_avg_win - COST_PER_TRADE
    else:
        adj_avg_win = 0.1  # minimal
    
    adj_avg_loss = new_avg_loss + COST_PER_TRADE
    
    if gross_loss_pnl > 0:
        pf_after = (new_wins * adj_avg_win) / (new_losses * adj_avg_loss)
    else:
        pf_after = 999
    
    # Before costs PF
    if gross_loss_pnl > 0:
        pf_before = (new_wins * new_avg_win) / (new_losses * new_avg_loss)
    else:
        pf_before = 999
    
    return {
        "name": name,
        "v1_trades": b["trades"],
        "v2_trades": new_trades,
        "v1_wr": b["wr"],
        "v2_wr": round(new_wr, 1),
        "v1_avg_win": b["avg_win"],
        "v2_avg_win": round(new_avg_win, 2),
        "v1_avg_loss": abs(b["avg_loss"]),
        "v2_avg_loss": round(new_avg_loss, 2),
        "gross_pnl": round(gross_pnl, 1),
        "total_cost": round(total_cost, 1),
        "net_pnl": round(net_pnl, 1),
        "pf_before_costs": round(pf_before, 2),
        "pf_after_costs": round(pf_after, 2),
        "survives": pf_after > 1.0 and net_pnl > 0,
        "profitable": pf_after > 1.5,
    }


print("=" * 100)
print("v2 COST PROJECTION — All 8 Failing Strategies")
print("=" * 100)
print()

results = {}

# 1. Blind_Structural_Chain v2
# Changes: -25% trades (tighter pullback, trend filter), +17pp WR (invalidation 60%, confirmation, trend)
# Avg win slightly lower (tighter pullback = less impulse to ride), avg loss smaller (tighter invalidation)
r = project_v2("Blind_Structural_Chain", BASELINE["Blind_Structural_Chain"],
                trade_mult=0.75, wr_delta=17, avg_win_mult=0.90, avg_loss_mult=0.75)
results["Blind_Structural_Chain"] = r

# 2. Stall_Harvest v2
# Changes: -30% trades (session filter, min AR 5p), +10pp WR (trend filter, session)
# Avg win slightly higher (better entries), avg loss smaller (tighter SL)
r = project_v2("Stall_Harvest", BASELINE["Stall_Harvest"],
                trade_mult=0.70, wr_delta=10, avg_win_mult=1.10, avg_loss_mult=0.80)
results["Stall_Harvest"] = r

# 3. Failure_Repair v2
# Changes: -35% trades (stronger 2nd signal, min gap), +7pp WR (trend filter, stronger signal)
# Avg win higher (wider TP 0.60x), avg loss smaller (tighter SL 0.8x)
r = project_v2("Failure_Repair", BASELINE["Failure_Repair"],
                trade_mult=0.65, wr_delta=7, avg_win_mult=1.15, avg_loss_mult=0.80)
results["Failure_Repair"] = r

# 4. Dual_Engine v2
# Changes: -55% trades (anchor only, T1 only, confirmation), +8pp WR (trend filter, confirmation)
# Avg win higher (wider TP 0.50x), avg loss similar
r = project_v2("Dual_Engine", BASELINE["Dual_Engine"],
                trade_mult=0.45, wr_delta=8, avg_win_mult=1.20, avg_loss_mult=0.90)
results["Dual_Engine"] = r

# 5. Two_Plays v2
# Changes: -50% trades (T1 only, before 8AM, stronger breakout), +10pp WR (trend filter, quality)
# Avg win higher (wider TP 0.50x), avg loss similar
r = project_v2("Two_Plays", BASELINE["Two_Plays"],
                trade_mult=0.50, wr_delta=10, avg_win_mult=1.15, avg_loss_mult=0.90)
results["Two_Plays"] = r

# 6. P90P_Distribution v2 (INVERTED — mean reversion)
# Changes: -40% trades (CONFIRMED regime only), +35pp WR (INVERSION flips 20% → 55%)
# Avg win changes (mean reversion target = return to band), avg loss wider (1.2x body)
r = project_v2("P90P_Distribution", BASELINE["P90P_Distribution"],
                trade_mult=0.60, wr_delta=35, avg_win_mult=0.65, avg_loss_mult=1.10)
results["P90P_Distribution"] = r

# 7. Fractal_Resolution v2
# Changes: -60% trades (T1 only, London/NY, ATR filter), +10pp WR (MTF confirm, trend filter)
# Avg win higher (wider TP 0.60x), avg loss smaller (tighter SL 1.0x)
r = project_v2("Fractal_Resolution", BASELINE["Fractal_Resolution"],
                trade_mult=0.40, wr_delta=10, avg_win_mult=1.10, avg_loss_mult=0.80)
results["Fractal_Resolution"] = r

# 8. Constraint_Anchor v2
# Changes: -70% trades (T1 only, London/NY, AR sweet spot 10-15p), +14pp WR (inverted logic, trend)
# Avg win higher (wider TP 0.60x), avg loss similar (wider SL 1.5x)
r = project_v2("Constraint_Anchor", BASELINE["Constraint_Anchor"],
                trade_mult=0.30, wr_delta=14, avg_win_mult=1.15, avg_loss_mult=1.10)
results["Constraint_Anchor"] = r

# Print results
for name, r in results.items():
    status = "✅ PROFITABLE" if r["profitable"] else ("⚠️ BREAKEVEN" if r["survives"] else "🔴 FAILS")
    print(f"{name}:")
    print(f"  Trades: {r['v1_trades']} → {r['v2_trades']} ({(1 - r['v2_trades']/r['v1_trades'])*100:.0f}% reduction)")
    print(f"  WR: {r['v1_wr']}% → {r['v2_wr']}%")
    print(f"  Avg Win: {r['v1_avg_win']}p → {r['v2_avg_win']}p | Avg Loss: {r['v1_avg_loss']}p → {r['v2_avg_loss']}p")
    print(f"  Gross PnL: {r['gross_pnl']}p | Cost: {r['total_cost']}p | Net: {r['net_pnl']}p")
    print(f"  PF before costs: {r['pf_before_costs']} | PF after costs: {r['pf_after_costs']}")
    print(f"  {status}")
    print()

profitable = [n for n, r in results.items() if r["profitable"]]
survives = [n for n, r in results.items() if r["survives"]]
print(f"Profitable (PF > 1.5 after costs): {len(profitable)}/8 — {', '.join(profitable)}")
print(f"Survives (PF > 1.0 after costs): {len(survives)}/8 — {', '.join(survives)}")

# Save results
output_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\v2-cost-projection.json")
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to: {output_path}")
