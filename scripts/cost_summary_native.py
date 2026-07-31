"""Cost analysis summary — PER-PAIR native configs."""
import json, sys

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\cost_analysis_native.json') as f:
    data = json.load(f)

# Load sweep baseline for comparison
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json') as f:
    sweep = json.load(f)

print('=' * 110)
print('CEREBUS COST ANALYSIS — PER-PAIR NATIVE CONFIGS (36 PAIRS)')
print('=' * 110)
print()
print('Config: Each pair uses its own native AU, trigger, ar_max from asset_configs.py')
print('Cost model: spread (pips) + $7/lot commission, 0.01 lots')
print()

# Group by category
majors = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCAD']
crosses = ['EURGBP', 'EURJPY', 'EURCHF', 'EURCAD', 'EURNZD', 'EURAUD',
           'GBPJPY', 'GBPCHF', 'GBPCAD', 'GBPAUD', 'GBPNZD',
           'AUDJPY', 'AUDCHF', 'AUDCAD', 'AUDNZD',
           'NZDJPY', 'NZDCHF', 'NZDCAD',
           'CADJPY', 'CADCHF', 'CHFJPY']
metals_crypto = ['XAUUSD', 'XAGUSD', 'BTCUSD', 'ETHUSD']
indices = ['US500', 'DE30', 'FR40', 'HK50']

def print_section(title, pairs):
    print('── %s --' % title)
    print('%-10s | %-5s %-5s | %-6s | %-8s %-8s | %-8s %-8s | %-6s | %-8s' % (
        'Pair', 'AU', 'Trig', 'Trades', 'Raw_WR', 'Adj_WR', 'Raw_PF', 'Adj_PF', 'Cost/t', 'PnL_Cost'))
    print('-' * 110)
    for pair in pairs:
        if pair not in data:
            continue
        r = data[pair]
        # Get native config
        sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
        from asset_configs import ASSET_CONFIGS
        au = ASSET_CONFIGS.get(pair, {}).get('tiers', {}).get('T1', {}).get('au', '?')
        trig = ASSET_CONFIGS.get(pair, {}).get('tiers', {}).get('T1', {}).get('trigger', '?')
        
        verdict = 'OK' if r['adjusted']['pf'] > 1.5 else 'MARGINAL' if r['adjusted']['pf'] > 1.0 else 'DEAD'
        
        print('%-10s | %-5s %-5s | %-6d | %-8.1f %-8.1f | %-8.1f %-8.1f | %-6.2f | %-8.1f%% %s' % (
            pair, au, trig, r['raw']['trades'],
            r['raw']['wr'], r['adjusted']['wr'],
            r['raw']['pf'], r['adjusted']['pf'],
            r['costs']['total_cost_pips_per_trade'],
            r['delta']['pnl_change_pct'], verdict))
    print()

print_section('FOREX MAJORS', majors)
print_section('FOREX CROSSES', crosses)
print_section('METALS / CRYPTO', metals_crypto)
print_section('INDICES', indices)

# Summary
print('=' * 110)
print('SUMMARY')
print('=' * 110)

ok = sum(1 for d in data.values() if d['adjusted']['pf'] > 1.5)
marginal = sum(1 for d in data.values() if 1.0 < d['adjusted']['pf'] <= 1.5)
dead = sum(1 for d in data.values() if d['adjusted']['pf'] <= 1.0)
zero = sum(1 for d in data.values() if d['raw']['trades'] == 0)

print('Total: %d | OK: %d | Marginal: %d | Dead: %d | Zero trades: %d' % (len(data), ok, marginal, dead, zero))

# Top 10 by adjusted PF
print()
print('TOP 15 by adjusted PF (after costs):')
sorted_pf = sorted([(p, d) for p, d in data.items() if d['raw']['trades'] > 0], key=lambda x: x[1]['adjusted']['pf'], reverse=True)
for i, (pair, r) in enumerate(sorted_pf[:15]):
    print('  %2d. %-10s PF=%5.2f (raw %5.2f) | WR=%5.1f%% (raw %5.1f%%) | trades=%-5d | cost=%.2fp | %s' % (
        i+1, pair, r['adjusted']['pf'], r['raw']['pf'],
        r['adjusted']['wr'], r['raw']['wr'],
        r['raw']['trades'],
        r['costs']['total_cost_pips_per_trade'],
        'OK' if r['adjusted']['pf'] > 1.5 else 'MARGINAL' if r['adjusted']['pf'] > 1.0 else 'DEAD'))

# Forex-only summary
forex_pairs = majors + crosses
forex_data = {p: data[p] for p in forex_pairs if p in data and data[p]['raw']['trades'] > 0}
print()
print('FOREX-ONLY SUMMARY (%d pairs with trades):' % len(forex_data))
forex_ok = sum(1 for d in forex_data.values() if d['adjusted']['pf'] > 1.5)
forex_dead = sum(1 for d in forex_data.values() if d['adjusted']['pf'] <= 1.0)
print('  OK: %d | Marginal: %d | Dead: %d' % (forex_ok, len(forex_data) - forex_ok - forex_dead, forex_dead))
avg_cost = sum(d['costs']['total_cost_pips_per_trade'] for d in forex_data.values()) / len(forex_data)
print('  Avg cost per trade: %.2f pips' % avg_cost)
avg_pnl_cost = sum(d['delta']['pnl_change_pct'] for d in forex_data.values()) / len(forex_data)
print('  Avg PnL cost: %.1f%%' % avg_pnl_cost)
