#!/usr/bin/env python3
"""Deep analysis of EURUSD.PRO trade data."""
import json, csv, os, random, statistics
from datetime import datetime, timedelta
from collections import defaultdict

CSV_PATH = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_mt5_working_trades_20260519_144233.csv"
OUTPUT_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports"

trades = []
with open(CSV_PATH, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        trades.append({
            'pnl': float(row['pnl']),
            'result': row['result'],
            'reason': row['reason'],
            'exit_price': float(row['exit_price']),
            'exit_time': datetime.fromisoformat(row['exit_time']),
            'entry_time': datetime.fromisoformat(row['entry_time']),
            'ar_pips': float(row['ar_pips']),
            'direction': row['direction'],
            'p90_direction': row['p90_direction'],
            'deep_state': float(row['deep_state']),
            'activation': float(row['activation']),
        })

for t in trades:
    t['est_hour'] = (t['entry_time'].hour - 5) % 24
    t['weekday'] = t['entry_time'].weekday()
    t['month'] = t['entry_time'].month
    t['year'] = t['entry_time'].year
    t['date'] = t['entry_time'].strftime('%Y-%m-%d')

TIER_BOUNDS = [(0, 15, 'T1_Compressed'), (15, 25, 'T2_Normal'), (25, 40, 'T3_Expanded'), (40, 999, 'T4_Extreme')]
def get_tier(ar):
    for lo, hi, name in TIER_BOUNDS:
        if lo <= ar < hi: return name
    return 'T4_Extreme'

for t in trades:
    t['tier'] = get_tier(t['ar_pips'])

pnls = [t['pnl'] for t in trades]
wins = sum(1 for p in pnls if p > 0)
losses = len(pnls) - wins
win_pnls = [p for p in pnls if p > 0]
loss_pnls = [p for p in pnls if p <= 0]
total_pnl = sum(pnls)
pf = sum(win_pnls)/abs(sum(loss_pnls)) if loss_pnls and sum(loss_pnls) != 0 else 0

cum, peak, max_dd = 0, 0, 0
for t in sorted(trades, key=lambda x: x['entry_time']):
    cum += t['pnl']
    if cum > peak: peak = cum
    dd = peak - cum
    if dd > max_dd: max_dd = dd

day_names = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

print("="*60)
print("EURUSD.PRO DEEP ANALYSIS")
print("="*60)
print("Trades: %d (%dW / %dL)" % (len(trades), wins, losses))
print("WR: %.1f%%" % (100*wins/len(trades)))
print("PnL: %.2f | PF: %.1f | MaxDD: %.2f" % (total_pnl, pf, max_dd))
print("Avg Win: %.2f | Avg Loss: %.2f" % (statistics.mean(win_pnls), statistics.mean(loss_pnls)))

dates = [t['entry_time'] for t in trades]
start_d = min(dates).strftime('%Y-%m-%d')
end_d = max(dates).strftime('%Y-%m-%d')
days = (max(dates) - min(dates)).days
print("Period: %s to %s (%d days)" % (start_d, end_d, days))
print("Avg trades/day: %.3f" % (len(trades)/max(days,1)))
print("Avg trades/week: %.1f" % (len(trades)/max(days,1)*7))

# By hour
print("\n" + "="*60)
print("BY HOUR OF DAY (EST)")
print("="*60)
by_hour = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0.0, 'ar': []})
for t in trades:
    h = t['est_hour']
    by_hour[h]['trades'] += 1
    by_hour[h]['pnl'] += t['pnl']
    by_hour[h]['ar'].append(t['ar_pips'])
    if t['pnl'] > 0: by_hour[h]['wins'] += 1

print("%-8s %-8s %-8s %-10s %-8s %-8s" % ("Hour", "Trades", "WR", "PnL", "AvgPnL", "AvgAR"))
for h in sorted(by_hour.keys()):
    d = by_hour[h]
    wr = 100*d['wins']/d['trades'] if d['trades'] else 0
    avg_pnl = d['pnl']/d['trades'] if d['trades'] else 0
    avg_ar = statistics.mean(d['ar']) if d['ar'] else 0
    print("%02d:00    %-8d %-7.1f%% %-10.2f %-8.2f %-8.1f" % (h, d['trades'], wr, d['pnl'], avg_pnl, avg_ar))

# By day of week
print("\n" + "="*60)
print("BY DAY OF WEEK")
print("="*60)
by_dow = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0.0})
for t in trades:
    d = day_names[t['weekday']]
    by_dow[d]['trades'] += 1
    by_dow[d]['pnl'] += t['pnl']
    if t['pnl'] > 0: by_dow[d]['wins'] += 1

print("%-6s %-8s %-8s %-10s %-8s" % ("Day", "Trades", "WR", "PnL", "AvgPnL"))
for d in day_names:
    if d in by_dow:
        dd = by_dow[d]
        wr = 100*dd['wins']/dd['trades']
        avg = dd['pnl']/dd['trades']
        print("%-6s %-8d %-7.1f%% %-10.2f %-8.2f" % (d, dd['trades'], wr, dd['pnl'], avg))

# By year
print("\n" + "="*60)
print("BY YEAR")
print("="*60)
by_year = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0.0})
for t in trades:
    by_year[t['year']]['trades'] += 1
    by_year[t['year']]['pnl'] += t['pnl']
    if t['pnl'] > 0: by_year[t['year']]['wins'] += 1

for y in sorted(by_year.keys()):
    d = by_year[y]
    wr = 100*d['wins']/d['trades']
    print("%d: %d trades, WR=%.1f%%, PnL=%.2f" % (y, d['trades'], wr, d['pnl']))

# By tier
print("\n" + "="*60)
print("BY TIER (AR Classification)")
print("="*60)
by_tier = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0.0, 'ar': [], 'hours': [], 'dows': []})
for t in trades:
    by_tier[t['tier']]['trades'] += 1
    by_tier[t['tier']]['pnl'] += t['pnl']
    by_tier[t['tier']]['ar'].append(t['ar_pips'])
    by_tier[t['tier']]['hours'].append(t['est_hour'])
    by_tier[t['tier']]['dows'].append(t['weekday'])
    if t['pnl'] > 0: by_tier[t['tier']]['wins'] += 1

for tn in ['T1_Compressed','T2_Normal','T3_Expanded','T4_Extreme']:
    if tn not in by_tier: continue
    d = by_tier[tn]
    wr = 100*d['wins']/d['trades']
    avg_ar = statistics.mean(d['ar'])
    pct = 100*d['trades']/len(trades)
    hour_counts = defaultdict(int)
    for h in d['hours']: hour_counts[h] += 1
    peak_h = max(hour_counts, key=hour_counts.get) if hour_counts else 0
    dow_counts = defaultdict(int)
    for w in d['dows']: dow_counts[w] += 1
    peak_d = day_names[max(dow_counts, key=dow_counts.get)] if dow_counts else 'N/A'
    print("\n  %s: %d trades (%.1f%%), WR=%.1f%%, PnL=%.2f" % (tn, d['trades'], pct, wr, d['pnl']))
    print("    AR: %.1f-%.1f (avg %.1f)" % (min(d['ar']), max(d['ar']), avg_ar))
    print("    Peak hour: %02d:00 | Peak day: %s" % (peak_h, peak_d))
    print("    Avg PnL/trade: %.2f" % (d['pnl']/d['trades']))

# Injection zones
print("\n" + "="*60)
print("INJECTION ZONES (Compression -> Expansion)")
print("="*60)
sorted_t = sorted(trades, key=lambda x: x['entry_time'])
injections = []
for i in range(1, len(sorted_t)):
    if sorted_t[i-1]['ar_pips'] < 25 and sorted_t[i]['ar_pips'] >= 25:
        injections.append({
            'time': sorted_t[i]['entry_time'].isoformat(),
            'prev_ar': sorted_t[i-1]['ar_pips'],
            'curr_ar': sorted_t[i]['ar_pips'],
            'ratio': round(sorted_t[i]['ar_pips']/max(sorted_t[i-1]['ar_pips'],0.1),1),
            'tier': sorted_t[i]['tier'],
            'pnl': sorted_t[i]['pnl'],
            'hour': sorted_t[i]['est_hour'],
        })

print("Total injection events: %d" % len(injections))
if injections:
    inj_pnls = [x['pnl'] for x in injections]
    inj_wins = sum(1 for p in inj_pnls if p > 0)
    print("During injections: WR=%.1f%%, Avg PnL=%.2f" % (100*inj_wins/len(injections), statistics.mean(inj_pnls)))
    inj_hours = defaultdict(lambda: {'count': 0, 'pnl': 0.0})
    for x in injections:
        inj_hours[x['hour']]['count'] += 1
        inj_hours[x['hour']]['pnl'] += x['pnl']
    print("\n  Injection events by hour:")
    for h in sorted(inj_hours.keys()):
        d = inj_hours[h]
        print("    %02d:00: %d events, PnL=%.2f" % (h, d['count'], d['pnl']))
    ratios = [x['ratio'] for x in injections]
    print("\n  Expansion ratio: Avg=%.1fx, Max=%.1fx" % (statistics.mean(ratios), max(ratios)))

# Trade clusters
print("\n" + "="*60)
print("TRADE CLUSTERS (3+ trades within 2 hours)")
print("="*60)
clusters = []
i = 0
while i < len(sorted_t):
    window = sorted_t[i]['entry_time'] + timedelta(hours=2)
    cluster = [sorted_t[i]]
    j = i + 1
    while j < len(sorted_t) and sorted_t[j]['entry_time'] <= window:
        cluster.append(sorted_t[j])
        j += 1
    if len(cluster) >= 3:
        cp = [t['pnl'] for t in cluster]
        ca = [t['ar_pips'] for t in cluster]
        clusters.append({
            'start': cluster[0]['entry_time'].isoformat(),
            'end': cluster[-1]['entry_time'].isoformat(),
            'trades': len(cluster),
            'pnl': round(sum(cp), 2),
            'avg_ar': round(statistics.mean(ca), 1),
            'hours': [t['est_hour'] for t in cluster],
        })
        i = j
    else:
        i += 1

print("Total clusters: %d" % len(clusters))
if clusters:
    cluster_pnls = [c['pnl'] for c in clusters]
    print("Cluster PnL: Avg=%.2f, Total=%.2f" % (statistics.mean(cluster_pnls), sum(cluster_pnls)))
    for c in clusters[:15]:
        print("  %s -> %s: %d trades, PnL=%.2f, AR=%.1f" % (c['start'], c['end'], c['trades'], c['pnl'], c['avg_ar']))

# Monte Carlo
print("\n" + "="*60)
print("MONTE CARLO SIMULATION (10,000 iterations)")
print("="*60)
random.seed(42)
mc = []
for _ in range(10000):
    sample = random.choices(pnls, k=len(pnls))
    cum, pk, dd = 0, 0, 0
    for p in sample:
        cum += p
        if cum > pk: pk = cum
        d = pk - cum
        if d > dd: dd = d
    mc.append((cum, dd))

mc_pnls = sorted([m[0] for m in mc])
mc_dds = sorted([m[1] for m in mc])
n_mc = len(mc_pnls)

print("Prob Profit: %.1f%%" % (100*sum(1 for p in mc_pnls if p > 0)/n_mc))
print("Mean PnL: %.2f | Median: %.2f | Std: %.2f" % (statistics.mean(mc_pnls), statistics.median(mc_pnls), statistics.stdev(mc_pnls)))
print("P1: %.2f | P5: %.2f | P25: %.2f" % (mc_pnls[int(0.01*n_mc)], mc_pnls[int(0.05*n_mc)], mc_pnls[int(0.25*n_mc)]))
print("P75: %.2f | P95: %.2f | P99: %.2f" % (mc_pnls[int(0.75*n_mc)], mc_pnls[int(0.95*n_mc)], mc_pnls[int(0.99*n_mc)]))
print("Mean MaxDD: %.2f | Median MaxDD: %.2f" % (statistics.mean(mc_dds), statistics.median(mc_dds)))
print("P95 MaxDD: %.2f | P99 MaxDD: %.2f" % (mc_dds[int(0.95*n_mc)], mc_dds[int(0.99*n_mc)]))
print("All profitable: %s" % all(p > 0 for p in mc_pnls))
print("Sharpe (approx): %.2f" % (statistics.mean(mc_pnls)/max(statistics.stdev(mc_pnls),0.01)))

# Direction analysis
print("\n" + "="*60)
print("BY DIRECTION")
print("="*60)
by_dir = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0.0})
for t in trades:
    by_dir[t['direction']]['trades'] += 1
    by_dir[t['direction']]['pnl'] += t['pnl']
    if t['pnl'] > 0: by_dir[t['direction']]['wins'] += 1

for d in ['LONG','SHORT']:
    if d in by_dir:
        dd = by_dir[d]
        wr = 100*dd['wins']/dd['trades']
        print("%s: %d trades, WR=%.1f%%, PnL=%.2f, Avg=%.2f" % (d, dd['trades'], wr, dd['pnl'], dd['pnl']/dd['trades']))

# Streak analysis
print("\n" + "="*60)
print("STREAK ANALYSIS")
print("="*60)
max_ws = max_ls = curr_w = curr_l = 0
for t in sorted(trades, key=lambda x: x['entry_time']):
    if t['pnl'] > 0:
        curr_w += 1
        curr_l = 0
        if curr_w > max_ws: max_ws = curr_w
    else:
        curr_l += 1
        curr_w = 0
        if curr_l > max_ls: max_ls = curr_l
print("Max win streak: %d" % max_ws)
print("Max loss streak: %d" % max_ls)

# Save JSON
analysis = {
    'basic': {
        'symbol': 'EURUSD.PRO',
        'total_trades': len(trades),
        'wins': wins,
        'losses': losses,
        'win_rate': round(100*wins/len(trades), 1),
        'total_pnl': round(total_pnl, 2),
        'avg_win': round(statistics.mean(win_pnls), 2),
        'avg_loss': round(statistics.mean(loss_pnls), 2),
        'max_win': round(max(pnls), 2),
        'max_loss': round(min(pnls), 2),
        'expectancy': round(statistics.mean(pnls), 2),
        'profit_factor': round(pf, 2),
        'max_drawdown': round(max_dd, 2),
        'start_date': start_d,
        'end_date': end_d,
        'trading_days': days,
        'avg_trades_per_day': round(len(trades)/max(days,1), 3),
        'avg_trades_per_week': round(len(trades)/max(days,1)*7, 1),
    },
    'by_hour': {"%02d:00" % h: {
        'trades': by_hour[h]['trades'],
        'wins': by_hour[h]['wins'],
        'win_rate': round(100*by_hour[h]['wins']/by_hour[h]['trades'], 1),
        'total_pnl': round(by_hour[h]['pnl'], 2),
        'avg_pnl': round(by_hour[h]['pnl']/by_hour[h]['trades'], 2),
        'avg_ar': round(statistics.mean(by_hour[h]['ar']), 1),
    } for h in sorted(by_hour.keys())},
    'by_dow': {d: {
        'trades': by_dow[d]['trades'],
        'wins': by_dow[d]['wins'],
        'win_rate': round(100*by_dow[d]['wins']/by_dow[d]['trades'], 1),
        'total_pnl': round(by_dow[d]['pnl'], 2),
    } for d in day_names if d in by_dow},
    'by_year': {str(y): {
        'trades': by_year[y]['trades'],
        'wins': by_year[y]['wins'],
        'win_rate': round(100*by_year[y]['wins']/by_year[y]['trades'], 1),
        'total_pnl': round(by_year[y]['pnl'], 2),
    } for y in sorted(by_year.keys())},
    'tiers': {tn: {
        'trades': by_tier[tn]['trades'],
        'wins': by_tier[tn]['wins'],
        'win_rate': round(100*by_tier[tn]['wins']/by_tier[tn]['trades'], 1),
        'total_pnl': round(by_tier[tn]['pnl'], 2),
        'avg_ar': round(statistics.mean(by_tier[tn]['ar']), 1),
        'min_ar': round(min(by_tier[tn]['ar']), 1),
        'max_ar': round(max(by_tier[tn]['ar']), 1),
        'pct': round(100*by_tier[tn]['trades']/len(trades), 1),
    } for tn in ['T1_Compressed','T2_Normal','T3_Expanded','T4_Extreme'] if tn in by_tier},
    'injection_events': injections,
    'clusters': clusters,
    'monte_carlo': {
        'prob_profit': round(100*sum(1 for p in mc_pnls if p > 0)/n_mc, 1),
        'mean_pnl': round(statistics.mean(mc_pnls), 2),
        'median_pnl': round(statistics.median(mc_pnls), 2),
        'std_pnl': round(statistics.stdev(mc_pnls), 2),
        'p1_pnl': round(mc_pnls[int(0.01*n_mc)], 2),
        'p5_pnl': round(mc_pnls[int(0.05*n_mc)], 2),
        'p25_pnl': round(mc_pnls[int(0.25*n_mc)], 2),
        'p75_pnl': round(mc_pnls[int(0.75*n_mc)], 2),
        'p95_pnl': round(mc_pnls[int(0.95*n_mc)], 2),
        'p99_pnl': round(mc_pnls[int(0.99*n_mc)], 2),
        'mean_max_dd': round(statistics.mean(mc_dds), 2),
        'median_max_dd': round(statistics.median(mc_dds), 2),
        'p95_max_dd': round(mc_dds[int(0.95*n_mc)], 2),
        'p99_max_dd': round(mc_dds[int(0.99*n_mc)], 2),
        'all_profitable': all(p > 0 for p in mc_pnls),
        'sharpe': round(statistics.mean(mc_pnls)/max(statistics.stdev(mc_pnls),0.01), 2),
    },
}

with open(os.path.join(OUTPUT_DIR, 'EURUSD_DEEP_ANALYSIS.json'), 'w') as f:
    json.dump(analysis, f, indent=2, default=str)

print("\n" + "="*60)
print("Analysis saved to %s/EURUSD_DEEP_ANALYSIS.json" % OUTPUT_DIR)
