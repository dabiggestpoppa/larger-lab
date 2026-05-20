#!/usr/bin/env python3
"""
DMR Full Analysis v2 — Multi-Asset Report Generator
Runs trade-level backtest on ALL assets with full logging, then analyzes:
- Full stats per asset (MC, daily trades, by year, by month, by hour, by DOW)
- Tier classification (AR pips → Tier 1/2/3/4)
- Temporal delivery patterns (hour-of-day, day-of-week, monthly clusters)
- Injection zone identification (volatility burst windows)
- Cross-asset correlation/clustering
"""

import sys, json, csv, os, random, statistics
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

DATA_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5"
OUTPUT_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)

TIMEFRAME = mt5.TIMEFRAME_M5
FROM_DATE = datetime(2022, 1, 1, tzinfo=timezone.utc)
TO_DATE = datetime(2026, 5, 19, tzinfo=timezone.utc)

SYMBOL_CONFIGS = {
    'EURUSD.PRO': {'pip_mult': 10000, 'digits': 5, 'name': 'EUR/USD'},
    'USDCHF.PRO': {'pip_mult': 10000, 'digits': 5, 'name': 'USD/CHF'},
    'CHFJPY.PRO': {'pip_mult': 100,   'digits': 3, 'name': 'CHF/JPY'},
    'XAUUSD.PRO': {'pip_mult': 1,     'digits': 2, 'name': 'XAU/USD'},
}

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

def get_est_hour(utc_dt):
    return (utc_dt.hour - 5) % 24

def p90_threshold(est_hour):
    if est_hour < 2 or est_hour >= 11: return 999.0
    if est_hour < 4: return 4.1
    if est_hour < 6: return 4.6
    if est_hour < 8: return 4.6
    if est_hour < 10: return 5.9
    if est_hour < 11: return 6.2
    return 999.0

def run_backtest_with_trades(symbol, cfg):
    """Run DMR backtest and return trade-level data."""
    pip_mult = cfg['pip_mult']
    
    if not mt5.initialize():
        print(f"  ERROR: MT5 init failed for {symbol}")
        return []
    
    # Check symbol available
    info = mt5.symbol_info(symbol)
    if info is None:
        print(f"  WARNING: {symbol} not found, trying alternatives...")
        # Try common alternatives
        alts = [symbol.replace('.PRO', ''), symbol.replace('.PRO', '.Raw'), symbol.replace('.PRO', '.Std')]
        for alt in alts:
            info = mt5.symbol_info(alt)
            if info is not None:
                symbol = alt
                print(f"  Using alternative: {symbol}")
                break
        if info is None:
            print(f"  ERROR: No symbol found for {symbol}")
            mt5.shutdown()
            return []
    
    rates = mt5.copy_rates_range(symbol, TIMEFRAME, FROM_DATE, TO_DATE)
    mt5.shutdown()
    
    if rates is None or len(rates) == 0:
        print(f"  ERROR: No data for {symbol}")
        return []
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['est_h'] = df['time'].apply(get_est_hour)
    df['date'] = df['time'].dt.date
    
    trades = []
    dates = sorted(df['date'].unique())
    
    for i, date in enumerate(dates):
        df_day = df[df['date'] == date]
        
        # Asian range: 2-8 AM EST
        asian = df_day[(df_day['est_h'] >= 2) & (df_day['est_h'] < 8)]
        if asian.empty:
            continue
        
        ar_high = asian['high'].max()
        ar_low = asian['low'].min()
        ar_pips = (ar_high - ar_low) * pip_mult
        
        if ar_pips < 3.0:  # minimum AR filter
            continue
        
        # Post-Asian session: 8-11 AM EST
        post = df_day[(df_day['est_h'] >= 8) & (df_day['est_h'] < 11)]
        if post.empty:
            continue
        
        # Deep state: furthest point from Asian range
        first_post = post.iloc[0]
        ref_price = first_post['close']
        
        # Track post-Asian price action
        deep_state = ref_price
        direction = None
        
        for idx, row in post.iterrows():
            est_h = row['est_h']
            p90_thresh = p90_threshold(est_h)
            if p90_thresh >= 999:
                break
            
            # Check if price has moved beyond P90 threshold from Asian range
            move_from_high = (ar_high - row['low']) * pip_mult
            move_from_low = (row['high'] - ar_low) * pip_mult
            
            if move_from_high >= p90_thresh:
                # Price dropped below P90 from high → SHORT signal (mean reversion up)
                deep_state = row['low']
                direction = 'SHORT'
                entry_price = row['close']
                entry_time = row['time']
                
                # SL at 220% of AR below entry
                sl_dist = ar_pips * 2.2 / pip_mult
                sl = entry_price - sl_dist
                # TP at activation (Asian range boundary)
                tp = ar_low
                
                # Manage trade: check remaining bars today
                remaining = df_day[df_day['time'] > entry_time]
                for jdx, rrow in remaining.iterrows():
                    if rrow['low'] <= sl:
                        pnl = (sl - entry_price) * pip_mult
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': rrow['time'],
                            'pnl': round(pnl, 2),
                            'result': 'L',
                            'reason': 'sl',
                            'direction': direction,
                            'ar_pips': round(ar_pips, 1),
                            'deep_state': round(deep_state, cfg['digits']),
                            'activation': round(tp, cfg['digits']),
                            'entry_price': round(entry_price, cfg['digits']),
                            'exit_price': round(sl, cfg['digits']),
                            'est_hour': est_h,
                        })
                        break
                    if rrow['high'] >= tp:
                        pnl = (tp - entry_price) * pip_mult
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': rrow['time'],
                            'pnl': round(pnl, 2),
                            'result': 'W',
                            'reason': 'tp',
                            'direction': direction,
                            'ar_pips': round(ar_pips, 1),
                            'deep_state': round(deep_state, cfg['digits']),
                            'activation': round(tp, cfg['digits']),
                            'entry_price': round(entry_price, cfg['digits']),
                            'exit_price': round(tp, cfg['digits']),
                            'est_hour': est_h,
                        })
                        break
                break  # one trade per day
                
            elif move_from_low >= p90_thresh:
                # Price rose above P90 from low → LONG signal (mean reversion down)
                deep_state = row['high']
                direction = 'LONG'
                entry_price = row['close']
                entry_time = row['time']
                
                sl_dist = ar_pips * 2.2 / pip_mult
                sl = entry_price + sl_dist
                tp = ar_high
                
                remaining = df_day[df_day['time'] > entry_time]
                for jdx, rrow in remaining.iterrows():
                    if rrow['high'] >= sl:
                        pnl = (entry_price - sl) * pip_mult
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': rrow['time'],
                            'pnl': round(pnl, 2),
                            'result': 'L',
                            'reason': 'sl',
                            'direction': direction,
                            'ar_pips': round(ar_pips, 1),
                            'deep_state': round(deep_state, cfg['digits']),
                            'activation': round(tp, cfg['digits']),
                            'entry_price': round(entry_price, cfg['digits']),
                            'exit_price': round(sl, cfg['digits']),
                            'est_hour': est_h,
                        })
                        break
                    if rrow['low'] <= tp:
                        pnl = (entry_price - tp) * pip_mult
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': rrow['time'],
                            'pnl': round(pnl, 2),
                            'result': 'W',
                            'reason': 'tp',
                            'direction': direction,
                            'ar_pips': round(ar_pips, 1),
                            'deep_state': round(deep_state, cfg['digits']),
                            'activation': round(tp, cfg['digits']),
                            'entry_price': round(entry_price, cfg['digits']),
                            'exit_price': round(tp, cfg['digits']),
                            'est_hour': est_h,
                        })
                        break
                break  # one trade per day
    
    return trades

def analyze_all(trades, symbol):
    """Full analysis on trade-level data."""
    if not trades:
        return None
    
    pnls = [t['pnl'] for t in trades]
    wins = sum(1 for p in pnls if p > 0)
    losses = len(pnls) - wins
    
    dates = [t['entry_time'] for t in trades]
    start_date = min(dates)
    end_date = max(dates)
    trading_days = (end_date - start_date).days
    
    # Max DD
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
    
    win_pnls = [p for p in pnls if p > 0]
    loss_pnls = [p for p in pnls if p <= 0]
    
    basic = {
        'symbol': symbol,
        'total_trades': len(trades),
        'wins': wins,
        'losses': losses,
        'win_rate': round(100 * wins / len(trades), 1),
        'total_pnl': round(sum(pnls), 2),
        'avg_win': round(statistics.mean(win_pnls), 2) if win_pnls else 0,
        'avg_loss': round(statistics.mean(loss_pnls), 2) if loss_pnls else 0,
        'max_win': round(max(pnls), 2),
        'max_loss': round(min(pnls), 2),
        'expectancy': round(statistics.mean(pnls), 2),
        'profit_factor': round(sum(win_pnls) / abs(sum(loss_pnls)), 2) if loss_pnls and sum(loss_pnls) != 0 else float('inf'),
        'max_drawdown': round(max_dd, 2),
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'trading_days': trading_days,
        'avg_trades_per_day': round(len(trades) / max(trading_days, 1), 3),
        'avg_trades_per_week': round(len(trades) / max(trading_days, 1) * 7, 1),
        'avg_trades_per_month': round(len(trades) / max(trading_days, 1) * 30.44, 1),
    }
    
    # By year
    by_year = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0})
    for t in trades:
        y = str(t['entry_time'].year)
        by_year[y]['trades'] += 1
        by_year[y]['pnl'] += t['pnl']
        if t['pnl'] > 0:
            by_year[y]['wins'] += 1
    basic['by_year'] = {k: {
        'trades': v['trades'],
        'wins': v['wins'],
        'win_rate': round(100 * v['wins'] / v['trades'], 1),
        'pnl': round(v['pnl'], 2),
    } for k, v in sorted(by_year.items())}
    
    # By month
    by_month = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0})
    for t in trades:
        m = t['entry_time'].strftime('%Y-%m')
        by_month[m]['trades'] += 1
        by_month[m]['pnl'] += t['pnl']
        if t['pnl'] > 0:
            by_month[m]['wins'] += 1
    
    # By hour of day
    by_hour = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0, 'ar_sum': 0})
    for t in trades:
        h = t['est_hour']
        by_hour[h]['trades'] += 1
        by_hour[h]['pnl'] += t['pnl']
        by_hour[h]['ar_sum'] += t['ar_pips']
        if t['pnl'] > 0:
            by_hour[h]['wins'] += 1
    
    hour_stats = {}
    for h in sorted(by_hour.keys()):
        d = by_hour[h]
        hour_stats[f"{h:02d}:00"] = {
            'trades': d['trades'],
            'wins': d['wins'],
            'win_rate': round(100 * d['wins'] / d['trades'], 1),
            'total_pnl': round(d['pnl'], 2),
            'avg_pnl': round(d['pnl'] / d['trades'], 2),
            'avg_ar': round(d['ar_sum'] / d['trades'], 1),
        }
    
    # By day of week
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    by_dow = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0})
    for t in trades:
        dow = day_names[t['entry_time'].weekday()]
        by_dow[dow]['trades'] += 1
        by_dow[dow]['pnl'] += t['pnl']
        if t['pnl'] > 0:
            by_dow[dow]['wins'] += 1
    
    dow_stats = {}
    for d in day_names:
        if d in by_dow:
            dd = by_dow[d]
            dow_stats[d] = {
                'trades': dd['trades'],
                'wins': dd['wins'],
                'win_rate': round(100 * dd['wins'] / dd['trades'], 1),
                'total_pnl': round(dd['pnl'], 2),
                'avg_pnl': round(dd['pnl'] / dd['trades'], 2),
            }
    
    # Tier classification
    tiers = defaultdict(list)
    for t in trades:
        tier = classify_tier(t['ar_pips'])
        tiers[tier].append(t)
    
    tier_stats = {}
    for tier_name in ['Tier_1_Compressed', 'Tier_2_Normal', 'Tier_3_Expanded', 'Tier_4_Extreme']:
        if tier_name not in tiers:
            continue
        tt = tiers[tier_name]
        tpnls = [t['pnl'] for t in tt]
        tars = [t['ar_pips'] for t in tt]
        twins = sum(1 for p in tpnls if p > 0)
        
        # Temporal distribution of this tier
        tier_hours = defaultdict(int)
        tier_dows = defaultdict(int)
        for t in tt:
            tier_hours[t['est_hour']] += 1
            tier_dows[day_names[t['entry_time'].weekday()]] += 1
        
        tier_stats[tier_name] = {
            'trades': len(tt),
            'wins': twins,
            'losses': len(tt) - twins,
            'win_rate': round(100 * twins / len(tt), 1),
            'total_pnl': round(sum(tpnls), 2),
            'avg_pnl': round(statistics.mean(tpnls), 2),
            'avg_ar': round(statistics.mean(tars), 1),
            'min_ar': round(min(tars), 1),
            'max_ar': round(max(tars), 1),
            'pct_of_total': round(100 * len(tt) / len(trades), 1),
            'peak_hour': max(tier_hours, key=tier_hours.get) if tier_hours else None,
            'peak_dow': max(tier_dows, key=tier_dows.get) if tier_dows else None,
            'by_hour': {f"{h:02d}:00": c for h, c in sorted(tier_hours.items())},
            'by_dow': dict(tier_dows),
        }
    
    # Injection zone analysis
    sorted_trades = sorted(trades, key=lambda t: t['entry_time'])
    
    # Compression → Expansion events
    injection_events = []
    for i in range(1, len(sorted_trades)):
        prev_ar = sorted_trades[i-1]['ar_pips']
        curr_ar = sorted_trades[i]['ar_pips']
        if prev_ar < 25 and curr_ar >= 25:
            injection_events.append({
                'time': sorted_trades[i]['entry_time'].isoformat(),
                'prev_ar': prev_ar,
                'curr_ar': curr_ar,
                'expansion_ratio': round(curr_ar / max(prev_ar, 0.1), 1),
                'tier': classify_tier(curr_ar),
                'pnl': sorted_trades[i]['pnl'],
                'direction': sorted_trades[i]['direction'],
                'est_hour': sorted_trades[i]['est_hour'],
            })
    
    # Trade clusters (3+ trades within 2 hours)
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
            cpnls = [t['pnl'] for t in cluster]
            cars = [t['ar_pips'] for t in cluster]
            clusters.append({
                'start': cluster[0]['entry_time'].isoformat(),
                'end': cluster[-1]['entry_time'].isoformat(),
                'trades': len(cluster),
                'total_pnl': round(sum(cpnls), 2),
                'avg_ar': round(statistics.mean(cars), 1),
                'directions': [t['direction'] for t in cluster],
                'hours': [t['est_hour'] for t in cluster],
            })
            i = j
        else:
            i += 1
    
    # Hour injection score
    hour_ar = defaultdict(list)
    for t in trades:
        hour_ar[t['est_hour']].append(t['ar_pips'])
    
    hour_injection = {}
    for h in sorted(hour_ar.keys()):
        ars = hour_ar[h]
        hour_injection[f"{h:02d}:00"] = {
            'avg_ar': round(statistics.mean(ars), 1),
            'max_ar': round(max(ars), 1),
            'trades': len(ars),
            'injection_score': round(statistics.mean(ars) * len(ars) / 10, 1),
        }
    
    injection = {
        'compression_to_expansion_events': injection_events[:100],
        'total_injection_events': len(injection_events),
        'trade_clusters': clusters[:50],
        'total_clusters': len(clusters),
        'hour_injection_profile': hour_injection,
    }
    
    # Monte Carlo
    random.seed(42)
    mc_results = []
    for _ in range(10000):
        sample = random.choices(pnls, k=len(pnls))
        cum = 0
        peak_mc = 0
        max_dd_mc = 0
        for p in sample:
            cum += p
            if cum > peak_mc:
                peak_mc = cum
            dd = peak_mc - cum
            if dd > max_dd_mc:
                max_dd_mc = dd
        mc_results.append({'total_pnl': cum, 'max_dd': max_dd_mc})
    
    mc_pnls = sorted([r['total_pnl'] for r in mc_results])
    mc_dds = sorted([r['max_dd'] for r in mc_results])
    n = len(mc_pnls)
    
    mc = {
        'iterations': 10000,
        'prob_profit': round(100 * sum(1 for p in mc_pnls if p > 0) / n, 1),
        'prob_20_dd_pct': round(100 * sum(1 for dd in mc_dds if dd > 20) / n, 1),
        'prob_50_dd_pct': round(100 * sum(1 for dd in mc_dds if dd > 50) / n, 1),
        'mean_pnl': round(statistics.mean(mc_pnls), 2),
        'median_pnl': round(statistics.median(mc_pnls), 2),
        'std_pnl': round(statistics.stdev(mc_pnls), 2),
        'p1_pnl': round(mc_pnls[int(0.01 * n)], 2),
        'p5_pnl': round(mc_pnls[int(0.05 * n)], 2),
        'p25_pnl': round(mc_pnls[int(0.25 * n)], 2),
        'p75_pnl': round(mc_pnls[int(0.75 * n)], 2),
        'p95_pnl': round(mc_pnls[int(0.95 * n)], 2),
        'p99_pnl': round(mc_pnls[int(0.99 * n)], 2),
        'mean_max_dd': round(statistics.mean(mc_dds), 2),
        'median_max_dd': round(statistics.median(mc_dds), 2),
        'p95_max_dd': round(mc_dds[int(0.95 * n)], 2),
        'p99_max_dd': round(mc_dds[int(0.99 * n)], 2),
        'all_profitable': all(p > 0 for p in mc_pnls),
        'sharpe_approx': round(statistics.mean(mc_pnls) / max(statistics.stdev(mc_pnls), 0.01), 2),
    }
    
    return {
        'basic': basic,
        'by_hour': hour_stats,
        'by_dow': dow_stats,
        'tiers': tier_stats,
        'injection': injection,
        'monte_carlo': mc,
    }

# ─── MAIN ────────────────────────────────────────────────────────────────────

print("="*80)
print("DMR FULL ANALYSIS v2 — MULTI-ASSET")
print("="*80)

all_results = {}
all_trades = {}

for symbol, cfg in SYMBOL_CONFIGS.items():
    print(f"\n{'─'*60}")
    print(f"  Running backtest: {symbol} ({cfg['name']})")
    print(f"{'─'*60}")
    
    trades = run_backtest_with_trades(symbol, cfg)
    
    if trades:
        # Save trade CSV
        csv_path = os.path.join(DATA_DIR, f'dmr_trades_{symbol.replace(".", "_")}.csv')
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=trades[0].keys())
            writer.writeheader()
            writer.writerows(trades)
        print(f"  Saved {len(trades)} trades to {csv_path}")
        
        all_trades[symbol] = trades
        result = analyze_all(trades, symbol)
        if result:
            all_results[symbol] = result
            b = result['basic']
            mc = result['monte_carlo']
            print(f"  WR: {b['win_rate']}% | PnL: {b['total_pnl']}p | PF: {b['profit_factor']} | MaxDD: {b['max_drawdown']}p")
            print(f"  Trades/day: {b['avg_trades_per_day']} | Trades/week: {b['avg_trades_per_week']}")
            print(f"  MC Prob Profit: {mc['prob_profit']}% | Mean PnL: {mc['mean_pnl']} | P5: {mc['p5_pnl']} | P95: {mc['p95_pnl']}")
            print(f"  MC Mean MaxDD: {mc['mean_max_dd']} | P95 MaxDD: {mc['p95_max_dd']}")
    else:
        print(f"  No trades generated for {symbol}")

# Cross-asset correlation
if len(all_trades) > 1:
    print(f"\n{'─'*60}")
    print("  CROSS-ASSET CORRELATION")
    print(f"{'─'*60}")
    
    daily_pnl = {}
    for sym, trades in all_trades.items():
        day_pnl = defaultdict(float)
        for t in trades:
            day = t['entry_time'].strftime('%Y-%m-%d')
            day_pnl[day] += t['pnl']
        daily_pnl[sym] = dict(day_pnl)
    
    symbols = list(daily_pnl.keys())
    cross = {}
    for i in range(len(symbols)):
        for j in range(i+1, len(symbols)):
            s1, s2 = symbols[i], symbols[j]
            common = set(daily_pnl[s1].keys()) & set(daily_pnl[s2].keys())
            if len(common) > 10:
                p1 = [daily_pnl[s1][d] for d in sorted(common)]
                p2 = [daily_pnl[s2][d] for d in sorted(common)]
                n = len(p1)
                m1, m2 = statistics.mean(p1), statistics.mean(p2)
                v1 = sum((x - m1)**2 for x in p1) / n
                v2 = sum((x - m2)**2 for x in p2) / n
                if v1 > 0 and v2 > 0:
                    cov = sum((p1[k] - m1) * (p2[k] - m2) for k in range(n)) / n
                    corr = cov / (v1**0.5 * v2**0.5)
                else:
                    corr = 0
                cross[f"{s1}_vs_{s2}"] = {
                    'correlation': round(corr, 3),
                    'common_days': len(common),
                    's1_avg_daily_pnl': round(m1, 2),
                    's2_avg_daily_pnl': round(m2, 2),
                }
                print(f"  {s1} vs {s2}: corr={corr:.3f} ({len(common)} common days)")
    
    all_results['_cross_asset'] = cross

# Save full report
report_path = os.path.join(OUTPUT_DIR, 'DMR_FULL_ANALYSIS.json')
with open(report_path, 'w') as f:
    json.dump(all_results, f, indent=2, default=str)

print(f"\n{'='*80}")
print(f"  FULL REPORT SAVED: {report_path}")
print(f"{'='*80}")
