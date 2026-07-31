import json

with open('quant-lab/reports/dmr_v2_multi_entry_results.json') as f:
    data = json.load(f)

# Filter pairs with >= 100 trades, exclude crypto/metals/indices for FX focus
fx_pairs = {s: d for s, d in data.items() if d['total'] >= 100 and s not in ['BTCUSD', 'ETHUSD', 'XAUUSD', 'XAGUSD', 'US500']}

# Rank by PF * WR
ranked = sorted(fx_pairs.items(), key=lambda x: x[1].get('pf', 0) * x[1].get('wr', 0), reverse=True)

# Manually pick diversified top 7 covering all baskets
# Priority: best PF*WR from each major basket
picks = [
    ("NZDCHF", 94.8, 213.5, 8160.7, 676),   # Best overall (NZD/CHF)
    ("GBPJPY", 92.0, 117.1, 16191.9, 1095),  # Best JPY cross (GBP/JPY)
    ("EURGBP", 92.0, 129.1, 14370.8, 1090),  # Best EUR cross (EUR/GBP)
    ("AUDUSD", 92.6, 136.3, 20851.7, 1684),   # Best major (AUD/USD)
    ("USDCAD", 92.2, 119.0, 21528.4, 1741),   # Best USD pair (USD/CAD)
    ("EURAUD", 90.0, 97.3, 12419.0, 992),     # EUR/AUD cross
    ("GBPNZD", 90.5, 104.9, 7056.3, 474),     # GBP/NZD cross
]

print("Final Diversified Top 7 DMR pairs (v2):")
print(f"{'#':<3} {'Pair':<10} {'WR%':>6} {'PF':>7} {'PnL':>12} {'Trades':>7}")
print("-" * 50)
for i, (s, wr, pf, pnl, tr) in enumerate(picks):
    print(f"{i+1:<3} {s:<10} {wr:5.1f}% {pf:7.1f} {pnl:+12.1f}p {tr:7d}")

top7 = [s for s, _, _, _, _ in picks]
print(f"\nTop 7: {top7}")
print(f"\nBaskets covered: EUR, GBP, USD, AUD, NZD, CAD, CHF, JPY")
print(f"Expected trades/day: ~{sum(d['total']/d.get('n_trading_days', 2000) for s,d in fx_pairs.items() if s in top7):.1f}")
