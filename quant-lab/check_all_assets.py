import json
import sys
from pathlib import Path

sys.path.insert(0, 'configs')
from asset_configs import ASSET_CONFIGS

old = json.load(open('reports/cost_analysis_all.json'))
spreads = json.load(open('reports/historical_spreads_v2.json'))

# All pairs in old cost analysis
all_pairs = sorted(old.keys())

def get_pip_value(pair):
    if pair in ASSET_CONFIGS:
        return ASSET_CONFIGS[pair].get('pip_value', 10.0)
    if 'JPY' in pair:
        return 1000.0
    return 10.0

def normalize_spread(pair, raw_spread):
    if raw_spread is None:
        return None
    if 'JPY' in pair:
        return raw_spread
    if raw_spread > 1:
        return raw_spread / 10.0
    return raw_spread

print("=" * 110)
print("ALL ASSETS — COST-ADJUSTED (Historical CSV Spread + Flat $0.07 Commission)")
print("=" * 110)
print(f"{'Pair':12s} {'Type':>6s} {'WR_raw':>8s} {'WR_adj':>8s} {'PF_raw':>8s} {'PF_adj':>8s} {'Cost':>8s} {'Spread':>9s} {'Status':>8s}")
print(f"{'':12s} {'':6s} {'':8s} {'':8s} {'':8s} {'':8s} {'(pips)':>8s} {'Src':>9s} {'':8s}")
print("-" * 110)

results = {}

for pair in all_pairs:
    raw = old[pair]['raw']
    trades = raw['trades']
    wr_raw = raw['wr']
    pf_raw = raw['pf']
    pnl_raw = raw['pnl_pips']
    avg_w = raw['avg_win']
    
    # Determine type
    if pair in ('BTCUSD', 'ETHUSD', 'BNBUSD', 'SOLUSD', 'LTCUSD', 'BCHUSD'):
        ptype = "CRYPTO"
    elif pair in ('XAUUSD', 'XAGUSD'):
        ptype = "METAL"
    elif pair in ('DE30', 'FR40', 'HK50', 'US500', 'NAS100'):
        ptype = "INDEX"
    else:
        ptype = "FX"
    
    # Spread
    if pair in spreads and spreads[pair]['avg_spread'] is not None:
        spread = normalize_spread(pair, spreads[pair]['avg_spread'])
        src = "CSV"
    else:
        spread = old[pair]['costs']['spread_pips_per_trade']
        src = "MT5"
    
    # Commission: flat $0.07 per trade -> pips
    pip_val = get_pip_value(pair)
    comm = 0.07 / pip_val
    
    total = spread + comm
    
    # Adjusted PnL
    pnl_adj = pnl_raw - (total * trades)
    
    # Adjusted WR (approximate)
    if avg_w > total and avg_w > 0:
        p_survive = max(0.0, (avg_w - total) / avg_w)
    else:
        p_survive = 0.0
    
    n_wins = int(trades * wr_raw / 100)
    adj_wins = int(n_wins * p_survive)
    wr_adj = (adj_wins / trades * 100) if trades > 0 else 0
    
    # Adjusted PF
    n_losses = trades - n_wins
    adj_win_pnl = adj_wins * (avg_w - total)
    adj_loss_pnl = (n_losses + (n_wins - adj_wins)) * (raw['avg_loss'] - total)
    if adj_loss_pnl < 0:
        pf_adj = adj_win_pnl / abs(adj_loss_pnl) if adj_loss_pnl != 0 else 999
    else:
        pf_adj = 999
    
    pnl_chg_pct = (-total * trades / pnl_raw * 100) if pnl_raw != 0 else 0
    
    status = "OK" if pf_adj > 8.0 and wr_adj > 75 else "FAIL"
    
    print(f"{pair:12s} {ptype:>6s} {wr_raw:8.1f} {wr_adj:8.1f} {pf_raw:8.1f} {pf_adj:8.2f} {total:8.4f} {src:>9s} {status:>8s}")
    
    results[pair] = {
        'type': ptype,
        'spread_pips': round(spread, 4),
        'commission_pips': round(comm, 4),
        'total_cost_pips': round(total, 4),
        'spread_source': src,
        'raw_wr': wr_raw,
        'adj_wr': round(wr_adj, 1),
        'raw_pf': pf_raw,
        'adj_pf': round(pf_adj, 2),
        'pnl_change_pct': round(pnl_chg_pct, 1),
        'viable': pf_adj > 8.0 and wr_adj > 75,
    }

# Summary by type
print("\n" + "=" * 110)
print("SUMMARY BY TYPE")
print("=" * 110)

for ptype in ['FX', 'CRYPTO', 'METAL', 'INDEX']:
    type_pairs = [(p, results[p]) for p in results if results[p]['type'] == ptype]
    viable = [(p, r) for p, r in type_pairs if r['viable']]
    not_viable = [(p, r) for p, r in type_pairs if not r['viable']]
    
    print(f"\n{ptype}: {len(viable)}/{len(type_pairs)} viable")
    if viable:
        print(f"  VIABLE:")
        for p, r in sorted(viable, key=lambda x: x[1]['adj_pf'], reverse=True):
            print(f"    {p:12s}: WR={r['adj_wr']:5.1f}%  PF={r['adj_pf']:6.2f}  Cost={r['total_cost_pips']:.4f}p  Src={r['spread_source']}")
    if not_viable:
        print(f"  NOT VIABLE:")
        for p, r in sorted(not_viable, key=lambda x: x[1]['adj_pf'], reverse=True):
            print(f"    {p:12s}: WR={r['adj_wr']:5.1f}%  PF={r['adj_pf']:6.2f}  Cost={r['total_cost_pips']:.4f}p  Src={r['spread_source']}")

# Save
with open('reports/cost_analysis_all_fixed.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to: reports/cost_analysis_all_fixed.json")
