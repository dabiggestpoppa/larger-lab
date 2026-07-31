"""Generate cost analysis summary report."""
import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\cost_analysis_all.json') as f:
    data = json.load(f)

print('=' * 100)
print('CEREBUS COST ANALYSIS — FULL UNIVERSE (36 PAIRS)')
print('=' * 100)
print()
print('Config: ar_max=999 (no AR gate), t1=12, 4PM cutoff, 0.01 lots')
print('Cost model: spread (pips) + $7/lot commission')
print()

# ── FOREX MAJORS ──
print('── FOREX MAJORS ──')
print('%-10s | %-6s | %-8s %-8s | %-8s %-8s | %-6s | %-8s | %s' % (
    'Pair', 'Trades', 'Raw_WR', 'Adj_WR', 'Raw_PF', 'Adj_PF', 'Cost/t', 'PnL_Cost', 'Verdict'))
print('-' * 100)
for pair in ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCAD']:
    if pair in data:
        r = data[pair]
        verdict = 'OK' if r['adjusted']['pf'] > 1.5 else 'MARGINAL' if r['adjusted']['pf'] > 1.0 else 'DEAD'
        print('%-10s | %-6d | %-8.1f %-8.1f | %-8.1f %-8.1f | %-6.2f | %-8.1f%% | %s' % (
            pair, r['raw']['trades'],
            r['raw']['wr'], r['adjusted']['wr'],
            r['raw']['pf'], r['adjusted']['pf'],
            r['costs']['total_cost_pips_per_trade'],
            r['delta']['pnl_change_pct'], verdict))

# ── FOREX CROSSES ──
print()
print('── FOREX CROSSES ──')
print('%-10s | %-6s | %-8s %-8s | %-8s %-8s | %-6s | %-8s | %s' % (
    'Pair', 'Trades', 'Raw_WR', 'Adj_WR', 'Raw_PF', 'Adj_PF', 'Cost/t', 'PnL_Cost', 'Verdict'))
print('-' * 100)
for pair in ['EURGBP', 'EURJPY', 'EURCHF', 'EURCAD', 'EURNZD', 'EURAUD',
             'GBPJPY', 'GBPCHF', 'GBPCAD', 'GBPAUD', 'GBPNZD',
             'AUDJPY', 'AUDCHF', 'AUDCAD', 'AUDNZD',
             'NZDJPY', 'NZDCHF', 'NZDCAD',
             'CADJPY', 'CADCHF', 'CHFJPY']:
    if pair in data:
        r = data[pair]
        verdict = 'OK' if r['adjusted']['pf'] > 1.5 else 'MARGINAL' if r['adjusted']['pf'] > 1.0 else 'DEAD'
        print('%-10s | %-6d | %-8.1f %-8.1f | %-8.1f %-8.1f | %-6.2f | %-8.1f%% | %s' % (
            pair, r['raw']['trades'],
            r['raw']['wr'], r['adjusted']['wr'],
            r['raw']['pf'], r['adjusted']['pf'],
            r['costs']['total_cost_pips_per_trade'],
            r['delta']['pnl_change_pct'], verdict))

# ── METALS / CRYPTO / INDICES ──
print()
print('── METALS / CRYPTO / INDICES ──')
print('%-10s | %-6s | %-8s %-8s | %-8s %-8s | %-6s | %-8s | %s' % (
    'Pair', 'Trades', 'Raw_WR', 'Adj_WR', 'Raw_PF', 'Adj_PF', 'Cost/t', 'PnL_Cost', 'Verdict'))
print('-' * 100)
for pair in ['XAUUSD', 'XAGUSD', 'BTCUSD', 'ETHUSD', 'US500', 'DE30', 'FR40', 'HK50']:
    if pair in data:
        r = data[pair]
        verdict = 'OK' if r['adjusted']['pf'] > 1.5 else 'MARGINAL' if r['adjusted']['pf'] > 1.0 else 'DEAD'
        print('%-10s | %-6d | %-8.1f %-8.1f | %-8.1f %-8.1f | %-6.2f | %-8.1f%% | %s' % (
            pair, r['raw']['trades'],
            r['raw']['wr'], r['adjusted']['wr'],
            r['raw']['pf'], r['adjusted']['pf'],
            r['costs']['total_cost_pips_per_trade'],
            r['delta']['pnl_change_pct'], verdict))

# ── SUMMARY STATS ──
print()
print('=' * 100)
print('SUMMARY')
print('=' * 100)

total_raw_trades = sum(d['raw']['trades'] for d in data.values())
total_raw_pnl = sum(d['raw']['pnl_pips'] for d in data.values())
total_adj_pnl = sum(d['adjusted']['pnl_pips'] for d in data.values())

ok_pairs = sum(1 for d in data.values() if d['adjusted']['pf'] > 1.5)
marginal_pairs = sum(1 for d in data.values() if 1.0 < d['adjusted']['pf'] <= 1.5)
dead_pairs = sum(1 for d in data.values() if d['adjusted']['pf'] <= 1.0)

print('Total pairs: %d' % len(data))
print('Raw total trades: %d' % total_raw_trades)
print('Raw total PnL: %.0f pips' % total_raw_pnl)
print('Adj total PnL: %.0f pips' % total_adj_pnl)
print('Total PnL cost: %.1f%%' % ((total_adj_pnl - total_raw_pnl) / abs(total_raw_pnl) * 100))
print()
print('OK (PF>1.5): %d pairs' % ok_pairs)
print('MARGINAL (1.0<PF<=1.5): %d pairs' % marginal_pairs)
print('DEAD (PF<=1.0): %d pairs' % dead_pairs)

# Best and worst
print()
print('TOP 10 by adjusted PF:')
sorted_by_pf = sorted(data.items(), key=lambda x: x[1]['adjusted']['pf'], reverse=True)
for i, (pair, r) in enumerate(sorted_by_pf[:10]):
    print('  %d. %-10s PF=%.2f (raw %.2f) | WR=%.1f%% (raw %.1f%%) | cost=%.2fp' % (
        i+1, pair, r['adjusted']['pf'], r['raw']['pf'],
        r['adjusted']['wr'], r['raw']['wr'],
        r['costs']['total_cost_pips_per_trade']))

print()
print('BOTTOM 5 by adjusted PF:')
for i, (pair, r) in enumerate(sorted_by_pf[-5:]):
    print('  %d. %-10s PF=%.2f (raw %.2f) | WR=%.1f%% (raw %.1f%%) | cost=%.2fp' % (
        i+1, pair, r['adjusted']['pf'], r['raw']['pf'],
        r['adjusted']['wr'], r['raw']['wr'],
        r['costs']['total_cost_pips_per_trade']))
