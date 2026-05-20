#!/usr/bin/env python3
"""
DMR Full Analysis — Multi-Asset Report Generator
- Full stats per asset (MC, daily trades, by year, by month, by hour, by day-of-week)
- Tier classification (AR pips → Tier 1/2/3/4)
- Temporal delivery patterns (hour-of-day, day-of-week, monthly clusters)
- Injection zone identification (volatility burst windows)
- Cross-asset correlation/clustering
- Overlay strategy signals
"""

import json
import csv
import os
from datetime import datetime, timezone
from collections import defaultdict
import statistics
import random

DATA_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5"
OUTPUT_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Load trade-level data ────────────────────────────────────────────────────

def load_trades_csv(path):
    """Load trade-level CSV with full temporal data."""
    trades = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trade = {
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
            }
            trades.append(trade)
    return trades

# Load all available trade CSVs
trade_files = {
    'EURUSD.PRO': os.path.join(DATA_DIR, 'dmr_mt5_working_trades_20260519_144233.csv'),
    # Multi-asset trades — check for additional files
}

# Check for multi-asset trade files
for f in os.listdir(DATA_DIR):
    if f.endswith('.csv') and 'trade' in f.lower():
        symbol = f.replace('dmr_', '').replace('_trades_', '_').replace('.csv', '')
        if symbol not in trade_files:
            trade_files[symbol] = os.path.join(DATA_DIR, f)

print("=== TRADE FILES FOUND ===")
for sym, path in trade_files.items():
    exists = os.path.exists(path)
    print(f"  {sym}: {path} [exists={exists}]")

# Load what we have
all_trades = {}
for sym, path in trade_files.items():
    if os.path.exists(path):
        all_trades[sym] = load_trades_csv(path)
        print(f"  Loaded {len(all_trades[sym])} trades for {sym}")

# ─── Load summary results ────────────────────────────────────────────────────

with open(os.path.join(DATA_DIR, 'dmr_multi_asset_v2.json')) as f:
    multi_asset = json.load(f)

with open(os.path.join(DATA_DIR.replace('mt5', 'results'), 'mc_corrected_results.json')) as f:
    mc_data = json.load(f)

# ─── Tier Classification ─────────────────────────────────────────────────────
# Based on MAD's manual: classify trades by AR pips (Asian Range) into tiers
# Tier 1: AR < 15 pips (tight/compressed)
# Tier 2: AR 15-25 pips (normal)
# Tier 3: AR 25-40 pips (expanded)
# Tier 4: AR > 40 pips (extreme/volatility)

TIER_BOUNDS = [
    (0, 15, 'Tier_1_Compressed'),
    (15, 25, 'Tier_2_Normal'),
    (25, 40, 'Tier_3_Expanded'),
    (40, float('inf'), 'Tier_4_Extreme'),
]

def classify_tier(ar_pips):
    for lo, hi, name in TIER_BOUNDS:
        if lo <= ar_pips < hi:
            return name
    return 'Tier_4_Extreme'

# ─── Analysis Functions ──────────────────────────────────────────────────────

def analyze_temporal_patterns(trades, label):
    """Analyze when trades occur and cluster."""
    hours = defaultdict(list)  # hour_of_day -> [pnl]
    weekdays = defaultdict(list)  # 0=Mon -> [pnl]
    months = defaultdict(list)  # YYYY-MM -> [pnl]
    
    for t in trades:
        et = t['entry_time']
        hours[et.hour].append(t['pnl'])
        weekdays[et.weekday()].append(t['pnl'])
        months[f"{et.year}-{et.month:02d}"].append(t['pnl'])
    
    # Hour analysis
    hour_stats = {}
    for h in sorted(hours.keys()):
        pnls = hours[h]
        wins = sum(1 for p in pnls if p > 0)
        hour_stats[h] = {
            'trades': len(pnls),
            'wins': wins,
            'win_rate': round(100 * wins / len(pnls), 1) if pnls else 0,
            'total_pnl': round(sum(pnls), 2),
            'avg_pnl': round(statistics.mean(pnls), 2),
        }
    
    # Day-of-week analysis
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    weekday_stats = {}
    for d in sorted(weekdays.keys()):
        pnls = weekdays[d]
        wins = sum(1 for p in pnls if p > 0)
        weekday_stats[day_names[d]] = {
            'trades': len(pnls),
            'wins': wins,
            'win_rate': round(100 * wins / len(pnls), 1) if pnls else 0,
            'total_pnl': round(sum(pnls), 2),
            'avg_pnl': round(statistics.mean(pnls), 2),
        }
    
    # Monthly analysis
    month_stats = {}
    for m in sorted(months.keys()):
        pnls = months[m]
        wins = sum(1 for p in pnls if p > 0)
        month_stats[m] = {
            'trades': len(pnls),
            'wins': wins,
            'win_rate': round(100 * wins / len(pnls), 1) if pnls else 0,
            'total_pnl': round(sum(pnls), 2),
            'avg_pnl': round(statistics.mean(pnls), 2),
        }
    
    return {
        'by_hour': hour_stats,
        'by_weekday': weekday_stats,
        'by_month': month_stats,
    }

def analyze_tiers(trades):
    """Classify trades by tier and analyze performance per tier."""
    tiers = defaultdict(list)
    for t in trades:
        tier = classify_tier(t['ar_pips'])
        tiers[tier].append(t)
    
    tier_stats = {}
    for tier_name in ['Tier_1_Compressed', 'Tier_2_Normal', 'Tier_3_Expanded', 'Tier_4_Extreme']:
        if tier_name not in tiers:
            continue
        tt = tiers[tier_name]
        wins = sum(1 for t in tt if t['pnl'] > 0)
        pnls = [t['pnl'] for t in tt]
        ars = [t['ar_pips'] for t in tt]
        
        tier_stats[tier_name] = {
            'trades': len(tt),
            'wins': wins,
            'losses': len(tt) - wins,
            'win_rate': round(100 * wins / len(tt), 1),
            'total_pnl': round(sum(pnls), 2),
            'avg_pnl': round(statistics.mean(pnls), 2),
            'avg_ar': round(statistics.mean(ars), 1),
            'min_ar': round(min(ars), 1),
            'max_ar': round(max(ars), 1),
            'pct_of_total': round(100 * len(tt) / len(trades), 1),
        }
    
    return tier_stats

def analyze_injection_zones(trades):
    """
    Identify 'injection zones' — time windows where volatility bursts cluster.
    MAD's concept: 80% of news events don't create new structure, they just
    compress/expand normalization. The 'volatility' is a time release that
    distorts participant expectancy.
    
    We look for:
    1. Windows where AR pips spike (expansion after compression)
    2. Consecutive trade clusters (multiple trades in short time windows)
    3. Post-compression burst patterns (Tier 1 → Tier 3/4 transitions)
    """
    # Sort by entry time
    sorted_trades = sorted(trades, key=lambda t: t['entry_time'])
    
    # 1. Find compression-to-expansion sequences
    injection_events = []
    for i in range(1, len(sorted_trades)):
        prev_ar = sorted_trades[i-1]['ar_pips']
        curr_ar = sorted_trades[i]['ar_pips']
        curr_tier = classify_tier(curr_ar)
        
        # Compression (Tier 1/2) followed by expansion (Tier 3/4)
        if prev_ar < 25 and curr_ar >= 25:
            injection_events.append({
                'time': sorted_trades[i]['entry_time'].isoformat(),
                'prev_ar': prev_ar,
                'curr_ar': curr_ar,
                'expansion_ratio': round(curr_ar / max(prev_ar, 0.1), 1),
                'tier': curr_tier,
                'pnl': sorted_trades[i]['pnl'],
                'direction': sorted_trades[i]['direction'],
            })
    
    # 2. Trade clusters (3+ trades within 2-hour windows)
    clusters = []
    i = 0
    while i < len(sorted_trades):
        window_end = sorted_trades[i]['entry_time'] + timedelta(hours=2)
        cluster = [sorted_trades[i]]
        j = i + 1
        while j < len(sorted_trades) and sorted_trades[j]['entry_time'] <= window_end:
            cluster.append(sorted_trades[j])
            j += 1
        if len(cluster) >= 3:
            pnls = [t['pnl'] for t in cluster]
            ars = [t['ar_pips'] for t in cluster]
            clusters.append({
                'start': cluster[0]['entry_time'].isoformat(),
                'end': cluster[-1]['entry_time'].isoformat(),
                'trades': len(cluster),
                'total_pnl': round(sum(pnls), 2),
                'avg_ar': round(statistics.mean(ars), 1),
                'directions': [t['direction'] for t in cluster],
            })
            i = j
        else:
            i += 1
    
    # 3. Hour-of-day injection analysis
    hour_ar = defaultdict(list)
    for t in trades:
        hour_ar[t['entry_time'].hour].append(t['ar_pips'])
    
    hour_injection = {}
    for h in sorted(hour_ar.keys()):
        ars = hour_ar[h]
        hour_injection[h] = {
            'avg_ar': round(statistics.mean(ars), 1),
            'max_ar': round(max(ars), 1),
            'trades': len(ars),
            'injection_score': round(statistics.mean(ars) * len(ars) / 10, 1),  # composite
        }
    
    return {
        'compression_to_expansion_events': injection_events[:50],  # top 50
        'total_injection_events': len(injection_events),
        'trade_clusters': clusters[:30],  # top 30
        'total_clusters': len(clusters),
        'hour_injection_profile': hour_injection,
    }

def monte_carlo_simulation(trades, n_iterations=10000):
    """Run Monte Carlo simulation on trade PnL distribution."""
    pnls = [t['pnl'] for t in trades]
    n_trades = len(pnls)
    
    results = []
    for _ in range(n_iterations):
        sample = random.choices(pnls, k=n_trades)
        cumulative = 0
        max_dd = 0
        peak = 0
        for pnl in sample:
            cumulative += pnl
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
        results.append({
            'total_pnl': cumulative,
            'max_dd': max_dd,
        })
    
    total_pnls = [r['total_pnl'] for r in results]
    max_dds = [r['max_dd'] for r in results]
    
    total_pnls.sort()
    max_dds.sort()
    
    prob_profit = sum(1 for p in total_pnls if p > 0) / n_iterations
    prob_20_dd = sum(1 for dd in max_dds if dd > 20) / n_iterations
    prob_50_dd = sum(1 for dd in max_dds if dd > 50) / n_iterations
    
    return {
        'iterations': n_iterations,
        'prob_profit': round(100 * prob_profit, 1),
        'prob_20_dd_pct': round(100 * prob_20_dd, 1),
        'prob_50_dd_pct': round(100 * prob_50_dd, 1),
        'mean_pnl': round(statistics.mean(total_pnls), 2),
        'median_pnl': round(statistics.median(total_pnls), 2),
        'p5_pnl': round(total_pnls[int(0.05 * n_iterations)], 2),
        'p25_pnl': round(total_pnls[int(0.25 * n_iterations)], 2),
        'p75_pnl': round(total_pnls[int(0.75 * n_iterations)], 2),
        'p95_pnl': round(total_pnls[int(0.95 * n_iterations)], 2),
        'mean_max_dd': round(statistics.mean(max_dds), 2),
        'median_max_dd': round(statistics.median(max_dds), 2),
        'p95_max_dd': round(max_dds[int(0.95 * n_iterations)], 2),
        'all_profitable': all(p > 0 for p in total_pnls),
    }

# ─── Run Analysis ─────────────────────────────────────────────────────────────

print("\n" + "="*80)
print("DMR FULL ANALYSIS — MULTI-ASSET REPORT")
print("="*80)

report = {}

for symbol, trades in all_trades.items():
    print(f"\n{'─'*60}")
    print(f"  ANALYZING: {symbol} ({len(trades)} trades)")
    print(f"{'─'*60}")
    
    # Basic stats
    wins = sum(1 for t in trades if t['pnl'] > 0)
    losses = len(trades) - wins
    pnls = [t['pnl'] for t in trades]
    
    # Date range
    dates = [t['entry_time'] for t in trades]
    start_date = min(dates)
    end_date = max(dates)
    trading_days = (end_date - start_date).days
    
    basic = {
        'symbol': symbol,
        'total_trades': len(trades),
        'wins': wins,
        'losses': losses,
        'win_rate': round(100 * wins / len(trades), 1),
        'total_pnl': round(sum(pnls), 2),
        'avg_win': round(statistics.mean([t['pnl'] for t in trades if t['pnl'] > 0]), 2),
        'avg_loss': round(statistics.mean([t['pnl'] for t in trades if t['pnl'] <= 0]), 2),
        'max_win': round(max(pnls), 2),
        'max_loss': round(min(pnls), 2),
        'expectancy': round(statistics.mean(pnls), 2),
        'profit_factor': round(
            sum(t['pnl'] for t in trades if t['pnl'] > 0) / 
            abs(sum(t['pnl'] for t in trades if t['pnl'] <= 0)), 2
        ) if any(t['pnl'] <= 0 for t in trades) else float('inf'),
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'trading_days': trading_days,
        'avg_trades_per_day': round(len(trades) / max(trading_days, 1) * 365 / 365, 3),
        'avg_trades_per_week': round(len(trades) / max(trading_days, 1) * 7, 1),
        'avg_trades_per_month': round(len(trades) / max(trading_days, 1) * 30.44, 1),
    }
    
    # Max drawdown
    cumulative = 0
    peak = 0
    max_dd = 0
    for t in sorted(trades, key=lambda x: x['entry_time']):
        cumulative += t['pnl']
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd
    basic['max_drawdown'] = round(max_dd, 2)
    
    print(f"  WR: {basic['win_rate']}% | PnL: {basic['total_pnl']}p | PF: {basic['profit_factor']} | MaxDD: {basic['max_drawdown']}p")
    print(f"  Avg trades/day: {basic['avg_trades_per_day']} | Avg trades/week: {basic['avg_trades_per_week']}")
    
    # Temporal patterns
    print(f"  Running temporal analysis...")
    temporal = analyze_temporal_patterns(trades, symbol)
    
    # Tier classification
    print(f"  Running tier classification...")
    tiers = analyze_tiers(trades)
    
    # Injection zones
    print(f"  Running injection zone analysis...")
    from datetime import timedelta
    injection = analyze_injection_zones(trades)
    
    # Monte Carlo
    print(f"  Running Monte Carlo (10K iterations)...")
    random.seed(42)
    mc = monte_carlo_simulation(trades, 10000)
    
    report[symbol] = {
        'basic': basic,
        'temporal': temporal,
        'tiers': tiers,
        'injection': injection,
        'monte_carlo': mc,
    }

# ─── Cross-Asset Correlation ─────────────────────────────────────────────────

print(f"\n{'─'*60}")
print("  CROSS-ASSET ANALYSIS")
print(f"{'─'*60}")

# If we have multiple assets with trade data, compute correlation
if len(all_trades) > 1:
    # Build daily PnL series for each asset
    daily_pnl = {}
    for sym, trades in all_trades.items():
        day_pnl = defaultdict(float)
        for t in trades:
            day = t['entry_time'].strftime('%Y-%m-%d')
            day_pnl[day] += t['pnl']
        daily_pnl[sym] = dict(day_pnl)
    
    # Find common days
    symbols = list(daily_pnl.keys())
    cross_asset = {}
    for i in range(len(symbols)):
        for j in range(i+1, len(symbols)):
            s1, s2 = symbols[i], symbols[j]
            common_days = set(daily_pnl[s1].keys()) & set(daily_pnl[s2].keys())
            if len(common_days) > 10:
                p1 = [daily_pnl[s1][d] for d in sorted(common_days)]
                p2 = [daily_pnl[s2][d] for d in sorted(common_days)]
                # Pearson correlation
                n = len(p1)
                mean1, mean2 = statistics.mean(p1), statistics.mean(p2)
                var1 = sum((x - mean1)**2 for x in p1) / n
                var2 = sum((x - mean2)**2 for x in p2) / n
                if var1 > 0 and var2 > 0:
                    cov = sum((p1[k] - mean1) * (p2[k] - mean2) for k in range(n)) / n
                    corr = cov / (var1 ** 0.5 * var2 ** 0.5)
                else:
                    corr = 0
                cross_asset[f"{s1}_vs_{s2}"] = {
                    'correlation': round(corr, 3),
                    'common_days': len(common_days),
                    's1_avg_daily_pnl': round(mean1, 2),
                    's2_avg_daily_pnl': round(mean2, 2),
                }
                print(f"  {s1} vs {s2}: corr={corr:.3f} over {len(common_days)} common days")
    
    report['_cross_asset'] = cross_asset

# ─── Save Report ──────────────────────────────────────────────────────────────

output_path = os.path.join(OUTPUT_DIR, 'DMR_FULL_ANALYSIS.json')
with open(output_path, 'w') as f:
    json.dump(report, f, indent=2, default=str)

print(f"\n{'='*80}")
print(f"  REPORT SAVED: {output_path}")
print(f"{'='*80}")

# Print summary
for sym, data in report.items():
    if sym.startswith('_'):
        continue
    b = data['basic']
    mc = data['monte_carlo']
    print(f"\n{'━'*60}")
    print(f"  {sym}")
    print(f"{'━'*60}")
    print(f"  Period: {b['start_date']} → {b['end_date']} ({b['trading_days']} days)")
    print(f"  Trades: {b['total_trades']} ({b['wins']}W / {b['losses']}L)")
    print(f"  Win Rate: {b['win_rate']}%")
    print(f"  Total PnL: {b['total_pnl']} pips")
    print(f"  Profit Factor: {b['profit_factor']}")
    print(f"  Max Drawdown: {b['max_drawdown']} pips")
    print(f"  Expectancy: {b['expectancy']} pips/trade")
    print(f"  Avg Trades/Day: {b['avg_trades_per_day']}")
    print(f"  Avg Trades/Week: {b['avg_trades_per_week']}")
    print(f"  Avg Trades/Month: {b['avg_trades_per_month']}")
    print(f"  ── Monte Carlo (10K) ──")
    print(f"  Prob Profit: {mc['prob_profit']}%")
    print(f"  Mean PnL: {mc['mean_pnl']} | Median: {mc['median_pnl']}")
    print(f"  P5: {mc['p5_pnl']} | P95: {mc['p95_pnl']}")
    print(f"  Mean MaxDD: {mc['mean_max_dd']} | P95 MaxDD: {mc['p95_max_dd']}")
    print(f"  All Profitable: {mc['all_profitable']}")
    print(f"  ── Tiers ──")
    for tier_name, tier_data in data['tiers'].items():
        print(f"  {tier_name}: {tier_data['trades']} trades ({tier_data['pct_of_total']}%), "
              f"WR={tier_data['win_rate']}%, PnL={tier_data['total_pnl']}, "
              f"AR={tier_data['avg_ar']}p ({tier_data['min_ar']}-{tier_data['max_ar']})")
    print(f"  ── Injection Zones ──")
    print(f"  Compression→Expansion events: {data['injection']['total_injection_events']}")
    print(f"  Trade clusters (3+ in 2h): {data['injection']['total_clusters']}")
