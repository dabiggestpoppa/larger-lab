"""Generate clean cost analysis summary from corrected data."""
import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\cost_analysis_native.json') as f:
    data = json.load(f)

# Sort by adjusted WR descending
sorted_pairs = sorted(data.items(), key=lambda x: x[1]['adjusted']['wr'], reverse=True)

print("=" * 110)
print("CORRECTED COST ANALYSIS — All 36 Pairs (native configs, $7/lot commission, 0.01 lot)")
print("=" * 110)
print()
print(f"{'Pair':<10} {'Trades':>6} | {'Raw WR':>7} {'Raw PF':>7} | {'Adj WR':>7} {'Adj PF':>7} | {'WR Δ':>6} {'PF Δ':>7} | {'Cost':>6} | {'PnL%':>7}")
print("-" * 110)

for pair, d in sorted_pairs:
    raw = d['raw']
    adj = d['adjusted']
    costs = d['costs']
    delta = d['delta']
    
    if raw['trades'] == 0:
        print(f"{pair:<10} {'N/A':>6} | {'NO TRADES':>20}")
        continue
    
    print(f"{pair:<10} {raw['trades']:>6} | {raw['wr']:>6.1f}% {raw['pf']:>7.1f} | {adj['wr']:>6.1f}% {adj['pf']:>7.1f} | {delta['wr_change']:>+5.1f} {delta['pf_change']:>+7.1f} | {costs['total_cost_pips_per_trade']:>5.2f}p | {delta['pnl_change_pct']:>+6.1f}%")

print()
print("=" * 110)
print("SUMMARY STATISTICS")
print("=" * 110)

# Forex only (exclude metals, crypto, indices with 0 trades)
forex = {k: v for k, v in data.items() if v['raw']['trades'] > 0 and not any(x in k for x in ['XAU', 'XAG', 'BTC', 'ETH', 'US500', 'DE30', 'FR40', 'HK50'])}
metals_crypto = {k: v for k, v in data.items() if v['raw']['trades'] > 0 and any(x in k for x in ['XAU', 'XAG', 'BTC', 'ETH'])}
indices = {k: v for k, v in data.items() if v['raw']['trades'] > 0 and any(x in k for x in ['US500', 'DE30', 'FR40', 'HK50'])}

for name, subset in [("FOREX (28 pairs)", forex), ("METALS/CRYPTO", metals_crypto), ("INDICES", indices)]:
    if not subset:
        continue
    wr_deltas = [v['delta']['wr_change'] for v in subset.values()]
    pf_deltas = [v['delta']['pf_change'] for v in subset.values()]
    pnl_deltas = [v['delta']['pnl_change_pct'] for v in subset.values()]
    adj_wrs = [v['adjusted']['wr'] for v in subset.values()]
    
    print(f"\n{name}:")
    print(f"  WR drop:   min={min(wr_deltas):+.1f}  max={max(wr_deltas):+.1f}  avg={sum(wr_deltas)/len(wr_deltas):+.1f}")
    print(f"  PF drop:   min={min(pf_deltas):+.1f}  max={max(pf_deltas):+.1f}  avg={sum(pf_deltas)/len(pf_deltas):+.1f}")
    print(f"  PnL cost:  min={min(pnl_deltas):+.1f}%  max={max(pnl_deltas):+.1f}%  avg={sum(pnl_deltas)/len(pnl_deltas):+.1f}%")
    print(f"  Adj WR:    min={min(adj_wrs):.1f}%  max={max(adj_wrs):.1f}%")

# Pairs below 79% adjusted WR
print()
print("PAIRS BELOW 79% ADJUSTED WR:")
below_79 = [(k, v) for k, v in sorted_pairs if v['raw']['trades'] > 0 and v['adjusted']['wr'] < 79.0]
if below_79:
    for pair, d in below_79:
        print(f"  {pair}: {d['raw']['wr']:.1f}% → {d['adjusted']['wr']:.1f}% (Δ{d['delta']['wr_change']:+.1f})")
else:
    print("  NONE — all pairs above 79%")

print()
print("TOP 10 BY ADJUSTED WR:")
for i, (pair, d) in enumerate(sorted_pairs[:10]):
    if d['raw']['trades'] > 0:
        print(f"  {i+1}. {pair}: {d['adjusted']['wr']:.1f}% WR, {d['adjusted']['pf']:.1f} PF, {d['adjusted']['trades']} trades")
