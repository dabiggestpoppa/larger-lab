import json

prev = json.load(open('quant-lab/reports/st_multi_asset_results_PREVIOUS_20260531.json'))
# New results are in st_multi_asset_results.json (overwritten by latest run)
# Also check st_only_multi_asset_results.json
import os
new_file = 'quant-lab/reports/st_only_multi_asset_results.json' if os.path.exists('quant-lab/reports/st_only_multi_asset_results.json') else 'quant-lab/reports/st_multi_asset_results.json'
new = json.load(open(new_file))

prev_map = {r['asset_key']: r for r in prev['results']}
new_map = {r['asset_key']: r for r in new['results']}

print("=== ST-ONLY BACKTEST: PREVIOUS (2026-05-31) vs NEW (2026-06-03, with spread buffer fixes) ===")
print()
print(f"{'Asset':<10} {'Prev WR':>8} {'New WR':>8} {'Delta':>8} {'Prev PnL':>12} {'New PnL':>12} {'Delta':>12} {'Prev Tr':>8} {'New Tr':>8}")
print("-" * 95)

total_prev_pnl = 0
total_new_pnl = 0
total_prev_trades = 0
total_new_trades = 0

all_keys = sorted(set(list(prev_map.keys()) + list(new_map.keys())))
for key in all_keys:
    p = prev_map.get(key)
    n = new_map.get(key)
    if p and n:
        delta_wr = n['win_rate'] - p['win_rate']
        delta_pnl = n['pnl_pips'] - p['pnl_pips']
        total_prev_pnl += p['pnl_pips']
        total_new_pnl += n['pnl_pips']
        total_prev_trades += p['total_trades']
        total_new_trades += n['total_trades']
        print(f"{key:<10} {p['win_rate']:>7.1f}% {n['win_rate']:>7.1f}% {delta_wr:>+7.1f}% {p['pnl_pips']:>+11.1f} {n['pnl_pips']:>+11.1f} {delta_pnl:>+11.1f} {p['total_trades']:>7} {n['total_trades']:>7}")
    elif p:
        print(f"{key:<10} {p['win_rate']:>7.1f}% {'N/A':>8} {'N/A':>8} {p['pnl_pips']:>+11.1f} {'N/A':>12} {'N/A':>12} {p['total_trades']:>7} {'N/A':>8}")
    elif n:
        print(f"{key:<10} {'N/A':>8} {n['win_rate']:>7.1f}% {'N/A':>8} {'N/A':>12} {n['pnl_pips']:>+11.1f} {'N/A':>12} {'N/A':>8} {n['total_trades']:>7}")

print("-" * 95)
print(f"{'TOTAL':<10} {'':>8} {'':>8} {'':>8} {total_prev_pnl:>+11.1f} {total_new_pnl:>+11.1f} {total_new_pnl-total_prev_pnl:>+11.1f} {total_prev_trades:>7} {total_new_trades:>7}")
print()

# Tier comparison
print("=== TIER COMPARISON ===")
for tier in ['T1', 'T2', 'T3']:
    prev_t = sum(r['tier_stats'].get(tier, {}).get('pnl', 0) for r in prev['results'] if r.get('tier_stats'))
    new_t = sum(r['tier_stats'].get(tier, {}).get('pnl', 0) for r in new['results'] if r.get('tier_stats'))
    prev_wr_list = [r['tier_stats'][tier]['wr'] for r in prev['results'] if r.get('tier_stats') and tier in r['tier_stats']]
    new_wr_list = [r['tier_stats'][tier]['wr'] for r in new['results'] if r.get('tier_stats') and tier in r['tier_stats']]
    prev_wr = sum(prev_wr_list)/len(prev_wr_list) if prev_wr_list else 0
    new_wr = sum(new_wr_list)/len(new_wr_list) if new_wr_list else 0
    print(f"  {tier}: WR {prev_wr:.1f}% -> {new_wr:.1f}% ({new_wr-prev_wr:+.1f}%) | PnL {prev_t:+.1f} -> {new_t:+.1f} ({new_t-prev_t:+.1f})")

print()
print("=== KEY CHANGES IN NEW RUN ===")
print("- Spread buffer added to SL (GBP crosses 3p, JPY pairs 2p, majors 1.5p, metals 15p)")
print("- Min SL buffer floor enforced (GBP crosses 12p, JPY pairs 6p, majors 8p)")
print("- SL = OCC extreme + spread buffer (was OCC exact with no buffer)")
print("- These fixes push SL further from entry -> fewer false stop-outs but also fewer trades qualify")
