import json

d = json.load(open('reports/cost_analysis_fixed.json'))
old = json.load(open('reports/cost_analysis_all.json'))

print("=" * 100)
print("METALS, INDICES & CRYPTO — COST-ADJUSTED RESULTS")
print("=" * 100)

# Check which of these are in our fixed analysis
targets = ['XAUUSD', 'XAGUSD', 'DE30', 'FR40', 'HK50', 'US500', 'NAS100', 
           'BTCUSD', 'ETHUSD', 'BNBUSD', 'SOLUSD', 'LTCUSD', 'BCHUSD',
           'OILUSD', 'LCOUSD']

print("\n--- From FIXED cost analysis (historical CSV spread + flat $0.07 commission) ---")
print(f"{'Pair':12s} {'WR_raw':>8s} {'WR_adj':>8s} {'PF_raw':>8s} {'PF_adj':>8s} {'Cost':>8s} {'Src':>9s} {'Status':>10s}")
print("-" * 90)

for p in targets:
    if p in d:
        r = d[p]
        status = "OK" if r['adj_pf'] > 8.0 and r['adj_wr'] > 75 else "FAIL"
        print(f"{p:12s} {r['raw_wr']:8.1f} {r['adj_wr']:8.1f} {r['raw_pf']:8.1f} {r['adj_pf']:8.2f} {r['total_cost_pips']:8.4f} {r['spread_source']:>9s} {status:>10s}")
    elif p in old:
        # Not in fixed analysis — show old data
        raw = old[p]['raw']
        adj = old[p]['adjusted']
        costs = old[p]['costs']
        print(f"{p:12s} {raw['wr']:8.1f} {adj['wr']:8.1f} {raw['pf']:8.1f} {adj['pf']:8.2f} {costs['total_cost_pips_per_trade']:8.4f} {'OLD MT5':>9s} {'N/A':>10s}")

# Also check what spread values the CSVs have for these
print("\n--- Historical spread from CSV ---")
spreads = json.load(open('reports/historical_spreads_v2.json'))
for p in targets:
    if p in spreads and spreads[p]['avg_spread'] is not None:
        s = spreads[p]
        print(f"{p:12s} spread={s['avg_spread']:10.2f}  samples={s['samples']:>8d}  file={s['file']:30s}  has_spread_col={s['has_spread_col']}")
    elif p in old:
        mt5 = old[p]['costs']['spread_pips_per_trade']
        print(f"{p:12s} NO CSV DATA — MT5 spread={mt5:.4f}p")
    else:
        print(f"{p:12s} NO DATA AT ALL")

# Check asset_configs for pip values
print("\n--- Pip values from asset_configs ---")
import sys; sys.path.insert(0, 'configs')
from asset_configs import ASSET_CONFIGS
for p in targets:
    if p in ASSET_CONFIGS:
        cfg = ASSET_CONFIGS[p]
        pv = cfg.get('pip_value', cfg.get('pip_size', '?'))
        print(f"{p:12s} pip_value={pv}  tiers={list(cfg.get('tiers', {}).keys())}")
