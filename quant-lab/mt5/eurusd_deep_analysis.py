#!/usr/bin/env python3
"""Deep analysis of EURUSD.PRO trade data — no MT5 needed."""
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

# Add EST hour
for t in trades:
    t['est_hour'] = (t['entry_time'].hour - 5) % 24
    t['weekday'] = t['entry_time'].weekday()
    t['month'] = t['entry_time'].month
    t['year'] = t['entry_time'].year
    t['date'] = t['entry_time'].strftime('%Y-%m-%d')

TIER_BOUNDS = [(0, 15, 'T1_Compressed'), (15, 25, 'T2_Normal'), (25, 40, 'T3_Expanded'), (40, 999, 'T4_Extreme')]
def tier(ar):
    for lo, hi, name in TIER_BOUNDS:
        if lo <= ar < hi: return name
    return 'T4_Extreme'

for t in trades:
    t['tier'] = tier(t['ar_pips'])

pnls = [t['pnl'] for t in trades]
wins = sum(1 for p in pnls if p > 0)
losses = len(pnls) - wins

# Max DD
cum, peak, max_dd = 0, 0, 0
for t in sorted(trades, key=lambda x: x['entry_time']):
    cum += t['pnl']
    if cum > peak: peak = cum
    dd = peak - cum
    if dd > max_dd: max_dd = dd

win_pnls = [p for p in pnls if p > 0]
loss_pnls = [p for p in pnls if p <= 0]

print(f"EURUSD.PRO: {len(trades)} trades, {wins}W/{losses}L, WR={100*wins/len(trades):.1f}%")
total_pnl = sum(pnls)
profit_factor = sum(win_pnls)/abs(sum(loss_pnls)) if loss_pnls and sum(loss_pnls) != 0 else 0
print(f"PnL: {total_pnl:.2f} | PF: {profit_factor:.1f} | MaxDD: {max_dd:.2f}")

# By hour
print(f"\n{'='*60}")
print("BY HOUR OF DAY (EST)")
print(f"{'='*60}")
by_hour = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0, 'ar': []})
for t in trades:
    h = t['est_hour']
    by_hour[h]['trades'] += 1
    by_hour[h]['pnl'] += t['pnl']
    by_hour[h]['ar'].append(t['ar_pips'])
    if t['pnl'] > 0: by_hour[h]['wins'] += 1

print(f"{'Hour':>6} {'Trades':>8} {'WR':>6} {'PnL':>10} {'AvgPnL':>8} {'AvgAR':>7}")
for h in sorted(by_hour.keys()):
    d = by_hour[h]
    wr = 100*d['wins']/d['trades'] if d['trades'] else 0
    avg_pnl = d['pnl']/d['trades'] if d['trades'] else 0
    avg_ar = statistics.mean(d['ar']) if d['ar'] else 0
    print(f"{h:02d}:00  {d['trades']:>8} {wr:>5.1f}% {d['pnl']:>10.2f} {avg_pnl:>8.2f} {avg_ar:>7.1f}")

# By day of week
print(f"\n{'='*60}")
print("BY DAY OF WEEK")
print(f"{'='*60}")
day_names = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
by_dow = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0})
for t in trades:
    d = day_names[t['weekday']]
    by_dow[d]['trades'] += 1
    by_dow[d]['pnl'] += t['pnl']
    if t['pnl'] > 0: by_dow[d]['wins'] += 1

print(f"{'Day':>6} {'Trades':>8} {'WR':>6} {'PnL':>10} {'AvgPnL':>8}")
for d in day_names:
    if d in by_dow:
        dd = by_dow[d]
        wr = 100*dd['wins']/dd['trades']
        avg = dd['pnl']/dd['trades']
        print(f"{d:>6} {dd['trades']:>8} {wr:>5.1f}% {dd['pnl']:>10.2f} {avg:>8.2f}")

# By tier
print(f"\n{'='*60}")
print("BY TIER (AR Classification)")
print(f"{'='*60}")
by_tier = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0, 'ar': [], 'hours': [], 'dows': []})
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
    # Peak hour
    hour_counts = defaultdict(int)
    for h in d['hours']: hour_counts[h] += 1
    peak_h = max(hour_counts, key=hour_counts.get)
    # Peak day
    dow_counts = defaultdict(int)
    for w in d['dows']: dow_counts[w] += 1
    peak_d = day_names[max(dow_counts, key=dow_counts.get)]
    print(f"\n  {tn}: {d['trades']} trades ({pct:.1f}%), WR={wr:.1f}%, PnL={d['pnl']:.2f}")
    print(f"    AR range: {min(d['ar']):.1f}-{max(d['ar']):.1f}, Avg: {avg_ar:.1f}")
    print(f"    Peak hour: {peak_h:02d}:00 | Peak day: {peak_d}")
    print(f"    Avg PnL/trade: {d['pnl']/d['trades']:.2f}")

# Injection zones
print(f"\n{'='*60}")
print("INJECTION ZONES (Compression -> Expansion)")
print(f"{'='*60")
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

print(f"Total injection events: {len(injections)}")
if injections:
    inj_pnls = [x['pnl'] for x in injections]
    inj_wins = sum(1 for p in inj_pnls if p > 0)
    print(f"During injections: WR={100*inj_wins/len(injections):.1f}%, Avg PnL={statistics.mean(inj_pnls):.2f}")
    
    # Injection by hour
    inj_hours = defaultdict(lambda: {'count': 0, 'pnl': 0})
    for x in injections:
        inj_hours[x['hour']]['count'] += 1
        inj_hours[x['hour']]['pnl'] += x['pnl']
    print(f"\n  Injection events by hour:")
    for h in sorted(inj_hours.keys()):
        d = inj_hours[h]
        print(f"    {h:02d}:00: {d['count']} events, PnL={d['pnl']:.2f}")
    
    # Expansion ratio distribution
    ratios = [x['ratio'] for x in injections]
    print(f"\n  Expansion ratio: Avg={statistics.mean(ratios):.1f}x, Max={max(ratios):.1f}x")

# Trade clusters
print(f"\n{'='*60}")
print("TRADE CLUSTERS (3+ trades within 2 hours)")
print(f"{'='*60}")
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

print(f"Total clusters: {len(clusters)}")
if clusters:
    cluster_pnls = [c['pnl'] for c in clusters]
    print(f"Cluster PnL: Avg={statistics.mean(cluster_pnls):.2f}, Total={sum(cluster_pnls):.2f}")
    for c in clusters[:10]:
        print(f"  {c['start']} → {c['end']}: {c['trades']} trades, PnL={c['pnl']:.2f}, AR={c['avg_ar']:.1f}")

# Monte Carlo
print(f"\n{'='*60}")
print("MONTE CARLO SIMULATION (10,000 iterations)")
print(f"{'='*60}")
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
n = len(mc_pnls)

print(f"Prob Profit: {100*sum(1 for p in mc_pnls if p > 0)/n:.1f}%")
print(f"Mean PnL: {statistics.mean(mc_pnls):.2f} | Median: {statistics.median(mc_pnls):.2f}")
print(f"Std PnL: {statistics.stdev(mc_pnls):.2f}")
print(f"P1: {mc_pnls[int(0.01*n)]:.2f} | P5: {mc_pnls[int(0.05*n)]:.2f} | P25: {mc_pnls[int(0.25*n)]:.2f}")
print(f"P75: {mc_pnls[int(0.75*n)]:.2f} | P95: {mc_pnls[int(0.95*n)]:.2f} | P99: {mc_pnls[int(0.99*n)]:.2f}")
print(f"Mean MaxDD: {statistics.mean(mc_dds):.2f} | Median MaxDD: {statistics.median(mc_dds):.2f}")
print(f"P95 MaxDD: {mc_dds[int(0.95*n)]:.2f} | P99 MaxDD: {mc_dds[int(0.99*n)]:.2f}")
print(f"All profitable: {all(p > 0 for p in mc_pnls)}")
print(f"Sharpe (approx): {statistics.mean(mc_pnls)/max(statistics.stdev(mc_pnls),0.01):.2f}")

# By year
print(f"\n{'='*60}")
print("BY YEAR")
print(f"{'='*60}")
by_year = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0})
for t in trades:
    by_year[t['year']]['trades'] += 1
    by_year[t['year']]['pnl'] += t['pnl']
    if t['pnl'] > 0: by_year[t['year']]['wins'] += 1

for y in sorted(by_year.keys()):
    d = by_year[y]
    wr = 100*d['wins']/d['trades']
    print(f"  {y}: {d['trades']} trades, WR={wr:.1f}%, PnL={d['pnl']:.2f}")

# Direction analysis
print(f"\n{'='*60}")
print("BY DIRECTION")
print(f"{'='*60}")
by_dir = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0})
for t in trades:
    by_dir[t['direction']]['trades'] += 1
    by_dir[t['direction']]['pnl'] += t['pnl']
    if t['pnl'] > 0: by_dir[t['direction']]['wins'] += 1

for d in ['LONG','SHORT']:
    if d in by_dir:
        dd = by_dir[d]
        wr = 100*dd['wins']/dd['trades']
        print(f"  {d}: {dd['trades']} trades, WR={wr:.1f}%, PnL={dd['pnl']:.2f}, Avg={dd['pnl']/dd['trades']:.2f}")

# Consecutive wins/losses
print(f"\n{'='*60}")
print("STREAK ANALYSIS")
print(f"{'='*60}")
sorted_t2 = sorted(trades, key=lambda x: x['entry_time'])
max_win_streak = max_loss_streak = curr_win = curr_loss = 0
for t in sorted_t2:
    if t['pnl'] > 0:
        curr_win += 1
        curr_loss = 0
        if curr_win > max_win_streak: max_win_streak = curr_win
    else:
        curr_loss += 1
        curr_win = 0
        if curr_loss > max_loss_streak: max_loss_streak = curr_loss

print(f"Max win streak: {max_win_streak}")
print(f"Max loss streak: {max_loss_streak}")

# Save all analysis to JSON
analysis = {
    'basic': {
        'symbol': 'EURUSD.PRO',
        'total_trades': len(trades),
        'wins': wins,
        'losses': losses,
        'win_rate': round(100*wins/len(trades), 1),
        'total_pnl': round(sum(pnls), 2),
        'avg_win': round(statistics.mean(win_pnls), 2),
        'avg_loss': round(statistics.mean(loss_pnls), 2),
        'max_win': round(max(pnls), 2),
        'max_loss': round(min(pnls), 2),
        'expectancy': round(statistics.mean(pnls), 2),
        'profit_factor': round(sum(win_pnls)/abs(sum(loss_pnls)), 2),
        'max_drawdown': round(max_dd, 2),
    },
    'by_hour': {f"{h:02d}:00": {
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
        'prob_profit': round(100*sum(1 for p in mc_pnls if p > 0)/n, 1),
        'mean_pnl': round(statistics.mean(mc_pnls), 2),
        'median_pnl': round(statistics.median(mc_pnls), 2),
        'p5_pnl': round(mc_pnls[int(0.05*n)], 2),
        'p25_pnl': round(mc_pnls[int(0.25*n)], 2),
        'p75_pnl': round(mc_pnls[int(0.75*n)], 2),
        'p95_pnl': round(mc_pnls[int(0.95*n)], 2),
        'mean_max_dd': round(statistics.mean(mc_dds), 2),
        'p95_max_dd': round(mc_dds[int(0.95*n)], 2),
        'all_profitable': all(p > 0 for p in mc_pnls),
    },
}

with open(os.path.join(OUTPUT_DIR, 'EURUSD_DEEP_ANALYSIS.json'), 'w') as f:
    json.dump(analysis, f, indent=2, default=str)

print(f"\n{'='*60}")
print(f"Analysis saved to {OUTPUT_DIR}/EURUSD_DEEP_ANALYSIS.json")
