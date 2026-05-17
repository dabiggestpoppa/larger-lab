#!/usr/bin/env python3
"""Verify P90 cascade backtest results for integrity."""
import json
from collections import defaultdict

with open('p90_cascade_results.json') as f:
    data = json.load(f)

r = data['results']
trades = data['trades']

print("=== SUMMARY VERIFICATION ===")
print(f"Total trades: {r['total_trades']}")
print(f"Wins: {r['wins']} + Losses: {r['losses']} = {r['wins']+r['losses']}")
total_check = r['wins'] + r['losses']
wr_check = r['wins'] / total_check * 100 if total_check > 0 else 0
print(f"Win rate recalculated: {wr_check:.1f}% (reported: {r['win_rate']}%)")
print(f"Total P&L: {r['total_pnl_pips']}")

# Verify P&L sum from individual trades
total = sum(t['pnl_pips'] for t in trades)
print(f"\n=== P&L VERIFICATION ===")
print(f"Sum of all trade P&L: {total:.2f} pips")
print(f"Reported total: {r['total_pnl_pips']} pips")
print(f"Match: {abs(total - r['total_pnl_pips']) < 1}")

# Verify avg win/loss
wins = [t['pnl_pips'] for t in trades if t['pnl_pips'] > 0]
losses = [t['pnl_pips'] for t in trades if t['pnl_pips'] <= 0]
avg_win = sum(wins) / len(wins) if wins else 0
avg_loss = sum(losses) / len(losses) if losses else 0
print(f"Avg win recalculated: {avg_win:.2f} (reported: {r['avg_win_pips']})")
print(f"Avg loss recalculated: {avg_loss:.2f} (reported: {r['avg_loss_pips']})")

# Profit factor
gp = sum(wins) if wins else 0
gl = abs(sum(losses)) if losses else 1
pf = gp / gl if gl > 0 else 0
print(f"Profit factor recalculated: {pf:.2f} (reported: {r['profit_factor']})")

print("\n=== BY ACTIVATION TYPE ===")
for at, d in r['by_activation_type'].items():
    print(f"  {at:15s}: {d['trades']:3d} trades | {d['win_rate']:5.1f}% WR | {d['pnl_pips']:+8.2f} pips")

print("\n=== EXIT REASONS ===")
for er, cnt in sorted(r['by_exit_reason'].items(), key=lambda x: -x[1]):
    pct = cnt / len(trades) * 100
    print(f"  {er:25s}: {cnt:4d} ({pct:.1f}%)")

print("\n=== DEEP CHECKS ===")

# 1. Check hold_time P&L contribution
hold_trades = [t for t in trades if t['exit_reason'] == 'hold_time']
hold_pnl = sum(t['pnl_pips'] for t in hold_trades)
hold_wins = sum(1 for t in hold_trades if t['pnl_pips'] > 0)
print(f"hold_time: {len(hold_trades)} trades, {hold_wins}W/{len(hold_trades)-hold_wins}L, {hold_pnl:+.2f}p")
print(f"  -> hold_time is {hold_pnl/r['total_pnl_pips']*100:.0f}% of total P&L")

# 2. Check if removing hold_time still profitable
non_hold_pnl = total - hold_pnl
print(f"  -> P&L without hold_time: {non_hold_pnl:+.2f}p")

# 3. Check cascade_2 edge
c2 = [t for t in trades if t['activation_type'] == 'cascade_2']
c2_sl = [t for t in c2 if t['exit_reason'] == 'sl']
c2_tp = [t for t in c2 if t['exit_reason'] == 'tp_50']
c2_hold = [t for t in c2 if t['exit_reason'] == 'hold_time']
print(f"\ncascade_2 breakdown:")
print(f"  tp_50: {len(c2_tp)} trades, {sum(t['pnl_pips'] for t in c2_tp):+.2f}p")
print(f"  sl:    {len(c2_sl)} trades, {sum(t['pnl_pips'] for t in c2_sl):+.2f}p")
print(f"  hold:  {len(c2_hold)} trades, {sum(t['pnl_pips'] for t in c2_hold):+.2f}p")

# 4. Check initial trades
init = [t for t in trades if t['activation_type'] == 'initial']
init_sl = [t for t in init if t['exit_reason'] == 'sl']
init_tp = [t for t in init if t['exit_reason'] == 'tp_50']
init_hold = [t for t in init if t['exit_reason'] == 'hold_time']
print(f"\ninitial breakdown:")
print(f"  tp_50: {len(init_tp)} trades, {sum(t['pnl_pips'] for t in init_tp):+.2f}p")
print(f"  sl:    {len(init_sl)} trades, {sum(t['pnl_pips'] for t in init_sl):+.2f}p")
print(f"  hold:  {len(init_hold)} trades, {sum(t['pnl_pips'] for t in init_hold):+.2f}p")

# 5. Check for trades with same entry time (overlapping positions)
entry_times = defaultdict(int)
for t in trades:
    entry_times[t['entry_time']] += 1
multi_entries = {k: v for k, v in entry_times.items() if v > 1}
print(f"\nOverlapping entry times: {len(multi_entries)}")
if multi_entries:
    for k, v in list(multi_entries.items())[:5]:
        print(f"  {k}: {v} trades")

# 6. Check SL distance vs TP distance for initial trades
print("\n=== SL vs TP DISTANCE (initial trades sample) ==")
for t in init[:5]:
    sl_dist = abs(t['sl_price'] - t['entry_price']) * 10000
    tp_dist = abs(t['tp_price'] - t['entry_price']) * 10000
    print(f"  {t['direction']:5s} entry={t['entry_price']:.5f} SL_dist={sl_dist:.1f}p TP_dist={tp_dist:.1f}p ratio={tp_dist/sl_dist:.2f}")

# 7. Risk:reward analysis
print("\n=== RISK:REWARD ANALYSIS ===")
sl_distances = []
tp_distances = []
for t in init:
    sl_d = abs(t['sl_price'] - t['entry_price']) * 10000
    tp_d = abs(t['tp_price'] - t['entry_price']) * 10000
    sl_distances.append(sl_d)
    tp_distances.append(tp_d)
if sl_distances:
    avg_sl = sum(sl_distances) / len(sl_distances)
    avg_tp = sum(tp_distances) / len(tp_distances)
    print(f"Initial trades - Avg SL distance: {avg_sl:.1f}p, Avg TP distance: {avg_tp:.1f}p")
    print(f"R:R ratio: {avg_tp/avg_sl:.2f} (need >{1/0.349:.2f} to breakeven at 34.9% WR)")

# 8. Check if results are actually profitable after realistic costs
print("\n=== REALISTIC COST ANALYSIS ===")
spread_cost = 0.5  # EUR/USD M5 typical spread
slippage = 0.3
total_cost_per_trade = (spread_cost + slippage) * 2  # round trip
total_cost = total_cost_per_trade * len(trades)
print(f"Estimated round-trip cost: {total_cost_per_trade}p per trade")
print(f"Total cost for {len(trades)} trades: {total_cost:.0f}p")
print(f"P&L after costs: {total - total_cost:+.2f}p")
