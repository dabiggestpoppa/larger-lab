import json

with open('quant-lab/reports/dmr_reconstructed_results.json') as f:
    data = json.load(f)['results']

# Rank by PF * WR (composite score)
ranked = sorted(data.items(), key=lambda x: x[1].get('pf', 0) * x[1].get('wr', 0), reverse=True)

print("Top 7 DMR pairs by PF x WR (composite score):")
print(f"{'#':<3} {'Pair':<10} {'WR%':>6} {'PF':>7} {'PnL':>12} {'Trades':>7}")
print("-" * 50)
for i, (s, d) in enumerate(ranked[:7]):
    print(f"{i+1:<3} {s:<10} {d['wr']:5.1f}% {d['pf']:7.1f} {d['pnl']:+12.1f}p {d['total']:7d}")

print("\nSymbols for engine:")
top7 = [s for s, _ in ranked[:7]]
print(top7)
