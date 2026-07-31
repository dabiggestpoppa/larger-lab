import json

# Load 9K results
with open('reports/run_9k_config_results.json') as f:
    d9k = json.load(f)

# Load cost results
with open('reports/cost_final_v2.json') as f:
    dcost = json.load(f)

results = d9k['results']

# Sort by PnL
by_pnl = sorted(results.values(), key=lambda x: x['pnl_pips'], reverse=True)

print("=== BEST QUAD BASKETS BY PnL (9K Config, Gross) ===")
for n in [2, 3, 4, 5, 6]:
    basket = by_pnl[:n]
    total_pnl = sum(r['pnl_pips'] for r in basket)
    total_trades = sum(r['trades'] for r in basket)
    avg_wr = sum(r['wr'] for r in basket) / len(basket)
    pairs = ', '.join(r['pair'] for r in basket)
    print(f"{n} assets: {total_pnl:,.0f}p PnL, {total_trades:,} trades, {avg_wr:.1f}% WR")
    print(f"  Pairs: {pairs}")
    print()

# Now check which are viable after costs
print("=== COST-ADJUSTED VIABILITY FOR TOP 9K PAIRS ===")
viable = []
not_viable = []
for r in by_pnl:
    pair = r['pair']
    if pair in dcost:
        c = dcost[pair]
        status = "OK" if c['viable'] else "NO"
        line = f"{pair:12s}: WR {c['wr_raw']:.1f}% -> {c['wr_adj']:.1f}% | PF {c['pf_raw']:.1f} -> {c['pf_adj']:.2f} | Cost {c['total']:.4f}p | {status}"
        if c['viable']:
            viable.append((r, c))
        else:
            not_viable.append((r, c))
        print(line)

print(f"\nViable: {len(viable)}, Not viable: {len(not_viable)}")

# Best quad basket using ONLY cost-adjusted viable pairs
print("\n=== BEST QUAD BASKET (Cost-Adjusted Viable Pairs Only) ===")
viable_sorted = sorted(viable, key=lambda x: x[0]['pnl_pips'], reverse=True)
for n in [2, 3, 4, 5, 6]:
    if n <= len(viable_sorted):
        basket = viable_sorted[:n]
        total_pnl = sum(r['pnl_pips'] for r, c in basket)
        total_trades = sum(r['trades'] for r, c in basket)
        avg_wr = sum(r['wr'] for r, c in basket) / len(basket)
        avg_cost = sum(c['total'] for r, c in basket) / len(basket)
        pairs = ', '.join(r['pair'] for r, c in basket)
        print(f"{n} assets: {total_pnl:,.0f}p PnL, {total_trades:,} trades, {avg_wr:.1f}% WR, avg cost={avg_cost:.4f}p")
        print(f"  Pairs: {pairs}")

# Best quad by PF
print("\n=== BEST QUAD BASKET (By Profit Factor, Cost-Adjusted) ===")
by_pf = sorted(viable, key=lambda x: x[1]['pf_adj'], reverse=True)
for n in [2, 3, 4, 5, 6]:
    if n <= len(by_pf):
        basket = by_pf[:n]
        total_pnl = sum(r['pnl_pips'] for r, c in basket)
        total_trades = sum(r['trades'] for r, c in basket)
        avg_wr = sum(r['wr'] for r, c in basket) / len(basket)
        avg_pf = sum(c['pf_adj'] for r, c in basket) / len(basket)
        pairs = ', '.join(r['pair'] for r, c in basket)
        print(f"{n} assets: avg PF={avg_pf:.2f}, {total_pnl:,.0f}p PnL, {total_trades:,} trades, {avg_wr:.1f}% WR")
        print(f"  Pairs: {pairs}")
