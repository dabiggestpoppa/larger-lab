import json

with open('quant-lab/reports/dmr_v2_multi_entry_results.json') as f:
    data = json.load(f)

# Filter pairs with >= 100 trades
meaningful = {s: d for s, d in data.items() if d['total'] >= 100}

# Rank by PF * WR
ranked = sorted(meaningful.items(), key=lambda x: x[1].get('pf', 0) * x[1].get('wr', 0), reverse=True)

# Pick diversified top 7 (one per currency basket priority)
baskets = {
    "EUR": ["EURUSD", "EURGBP", "EURJPY", "EURAUD", "EURCHF", "EURNZD"],
    "GBP": ["GBPUSD", "GBPJPY", "GBPAUD", "GBPCHF", "GBPNZD"],
    "USD": ["EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD"],
    "JPY": ["EURJPY", "GBPJPY", "USDJPY", "AUDJPY", "CHFJPY", "NZDJPY", "CADJPY"],
    "AUD": ["AUDUSD", "EURAUD", "GBPAUD", "AUDJPY", "AUDNZD", "AUDCAD", "AUDCHF"],
    "NZD": ["NZDUSD", "EURNZD", "GBPNZD", "AUDNZD", "NZDCHF", "NZDJPY", "NZDCAD"],
    "CAD": ["USDCAD", "AUDCAD", "NZDCAD", "CADCHF", "CADJPY"],
    "CHF": ["USDCHF", "EURCHF", "GBPCHF", "AUDCHF", "CADCHF", "NZDCHF", "CHFJPY"],
}

selected = []
used_baskets = set()

# First pass: pick best from each basket
for sym, d in ranked:
    if sym in [s for s, _ in selected]:
        continue
    # Find which baskets this pair belongs to
    pair_baskets = [b for b, pairs in baskets.items() if sym in pairs]
    # Pick if it adds new basket coverage
    new_baskets = [b for b in pair_baskets if b not in used_baskets]
    if new_baskets or len(selected) < 7:
        selected.append((sym, d))
        used_baskets.update(pair_baskets)
    if len(selected) >= 7:
        break

print("Diversified Top 7 DMR pairs (v2, >= 100 trades):")
print(f"{'#':<3} {'Pair':<10} {'WR%':>6} {'PF':>7} {'PnL':>12} {'Trades':>7} {'Baskets'}")
print("-" * 65)
for i, (s, d) in enumerate(selected):
    pair_baskets = [b for b, pairs in baskets.items() if s in pairs]
    print(f"{i+1:<3} {s:<10} {d['wr']:5.1f}% {d['pf']:7.1f} {d['pnl']:+12.1f}p {d['total']:7d} {', '.join(pair_baskets)}")

top7 = [s for s, _ in selected]
print(f"\nTop 7: {top7}")
