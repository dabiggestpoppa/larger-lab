"""Final cost analysis summary — PER-PAIR native configs, ar_max=999.
Engine fix: trigger stays at T1 value (not updated on tier reclass)."""
import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\cost_analysis_native_nogate.json') as f:
    data = json.load(f)

print('=' * 110)
print('CEREBUS COST ANALYSIS — PER-PAIR NATIVE CONFIGS + AR_MAX=999 (NO AR GATE)')
print('=' * 110)
print()
print('Engine fix: trigger_pips stays at T1 value across all loop iterations')
print('           (previously was being bumped up on tier reclassification)')
print('Config: Each pair uses its own native AU and trigger from asset_configs.py')
print('Cost model: spread (pips) + $7/lot commission, 0.01 lots')
print()

# EURUSD validation
if 'EURUSD' in data:
    r = data['EURUSD']
    print('EURUSD VALIDATION vs SWEEP BASELINE:')
    print('  Trades: %d (sweep: 5,593, delta: %+.1f%%)' % (r['raw']['trades'], (r['raw']['trades'] - 5593)/5593.0*100))
    print('  Raw WR: %.1f%% (sweep: 82.9%%)' % r['raw']['wr'])
    print('  Raw PF: %.2f (sweep: 12.5)' % r['raw']['pf'])
    print('  Adj PF: %.2f (after costs)' % r['adjusted']['pf'])
    print()

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
        verdict = 'OK' if r['adjusted']['pf'] > 1.5 else 'MARGINAL' if r['adjusted']['pf'] > 1.0 else 'DEAD'
        print('%-10s | %-5s %-5s | %-6d | %-8.1f %-8.1f | %-8.1f %-8.1f | %-6.2f | %-8.1f%% %s' % (
            pair,
            data[pair].get('native_au', '?'),
            data[pair].get('native_trig', '?'),
            r['raw']['trades'], r['raw']['wr'], r['adjusted']['wr'],
            r['raw']['pf'], r['adjusted']['pf'],
            r['costs']['total_cost_pips_per_trade'],
            r['delta']['pnl_change_pct'], verdict))
    print()

# Add native config info
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
from asset_configs import ASSET_CONFIGS
for pair in data:
    cfg = ASSET_CONFIGS.get(pair, {})
    tiers = cfg.get('tiers', {})
    t1 = tiers.get('T1', {})
    data[pair]['native_au'] = t1.get('au', '?')
    data[pair]['native_trig'] = t1.get('trigger', '?')

print_section('FOREX MAJORS', majors)
print_section('FOREX CROSSES', crosses)
print_section('METALS / CRYPTO', metals_crypto)
print_section('INDICES', indices)

# Summary
ok = sum(1 for d in data.values() if d['adjusted']['pf'] > 1.5)
marginal = sum(1 for d in data.values() if 1.0 < d['adjusted']['pf'] <= 1.5)
dead = sum(1 for d in data.values() if d['adjusted']['pf'] <= 1.0)
zero = sum(1 for d in data.values() if d['raw']['trades'] == 0)

print('=' * 110)
print('SUMMARY')
print('=' * 110)
print('Total: %d | OK: %d | Marginal: %d | Dead: %d | Zero trades: %d' % (len(data), ok, marginal, dead, zero))

# Forex-only
forex = {p: data[p] for p in majors + crosses if p in data and data[p]['raw']['trades'] > 0}
forex_ok = sum(1 for d in forex.values() if d['adjusted']['pf'] > 1.5)
print()
print('FOREX-ONLY (%d pairs):' % len(forex))
print('  OK: %d | Marginal: %d | Dead: %d' % (forex_ok, len(forex) - forex_ok - sum(1 for d in forex.values() if d['adjusted']['pf'] <= 1.0), sum(1 for d in forex.values() if d['adjusted']['pf'] <= 1.0)))
avg_cost = sum(d['costs']['total_cost_pips_per_trade'] for d in forex.values()) / len(forex)
print('  Avg cost per trade: %.2f pips' % avg_cost)

# Top 10
print()
print('TOP 15 by adjusted PF (after costs):')
sorted_pf = sorted([(p, d) for p, d in data.items() if d['raw']['trades'] > 0], key=lambda x: x[1]['adjusted']['pf'], reverse=True)
for i, (pair, r) in enumerate(sorted_pf[:15]):
    print('  %2d. %-10s PF=%5.2f (raw %5.2f) | WR=%5.1f%% (raw %5.1f%%) | tr=%-5d | cost=%.2fp' % (
        i+1, pair, r['adjusted']['pf'], r['raw']['pf'],
        r['adjusted']['wr'], r['raw']['wr'],
        r['raw']['trades'], r['costs']['total_cost_pips_per_trade']))
