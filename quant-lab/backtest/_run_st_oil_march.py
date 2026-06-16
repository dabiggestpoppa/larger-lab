"""
ST (Symmetry Trap) backtest for OILUSD starting from March 2026.
Tests tier/AU system: T1 (AR<=35p/$0.35), T2 (AR<=55p/$0.55), T3 (AR<=80p/$0.80)
"""
import sys, csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
EST = timezone(timedelta(hours=-5))

OIL_PIP = 0.01  # 1 cent = 1 pip in MT5 terms
# But OILUSD price is ~$70-90, so AR in pips = AR_in_dollars / 0.01
# e.g., AR of $2.90 = 290 pips

# Adjusted tiers for OILUSD CURRENT regime
# In pips (where price ~$70, 1 pip = $0.01)
TIERS = {
    "T1": {"ar_max": 350.0, "au": 175.0, "trigger": 210.0},   # AR $3.50, AU $1.75, Trig $2.10
    "T2": {"ar_max": 550.0, "au": 275.0, "trigger": 330.0},   # AR $5.50, AU $2.75, Trig $3.30
    "T3": {"ar_max": 800.0, "au": 400.0, "trigger": 480.0},   # AR $8.00, AU $4.00, Trig $4.80
}

def load_bars(csv_path):
    bars = []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts_raw = row.get('timestamp') or row.get('time') or row.get('date')
                if not ts_raw: continue
                ts_raw = ts_raw.strip()
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S%z']:
                    try:
                        ts = datetime.strptime(ts_raw, fmt)
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=UTC)
                        break
                    except ValueError:
                        continue
                else:
                    try:
                        ts = datetime.fromtimestamp(int(float(ts_raw)), tz=UTC)
                    except:
                        continue
                o = float(row.get('open') or row.get('Open'))
                h = float(row.get('high') or row.get('High'))
                lo = float(row.get('low') or row.get('Low'))
                cl = float(row.get('close') or row.get('Close'))
                bars.append((ts, o, h, lo, cl))
            except:
                continue
    bars.sort(key=lambda b: b[0])
    return bars

def get_daily_asian(bars, trade_date):
    """Get Asian Range for a trading day (7PM-3AM EST = 00:00-08:00 UTC)"""
    asian_bars = []
    for ts, o, h, lo, cl in bars:
        if ts.date() == trade_date and ts.hour >= 0 and ts.hour < 8:
            asian_bars.append((ts, o, h, lo, cl))
    if len(asian_bars) < 2:
        return None
    ah = max(b[2] for b in asian_bars)
    al = min(b[3] for b in asian_bars)
    ar = ah - al
    close = asian_bars[-1][4]
    return {'high': ah, 'low': al, 'range': ar, 'close': close}

def classify_tier(ar):
    """Classify AR into tier"""
    if ar <= TIERS['T1']['ar_max'] * OIL_PIP:
        return 'T1'
    elif ar <= TIERS['T2']['ar_max'] * OIL_PIP:
        return 'T2'
    elif ar <= TIERS['T3']['ar_max'] * OIL_PIP:
        return 'T3'
    else:
        return 'NO_GO'

def run_st_backtest(bars, start_date=None):
    """Run Symmetry Trap backtest"""
    # Get unique trading days
    all_dates = sorted(set(ts.date() for ts, _, _, _, _ in bars))
    
    if start_date:
        all_dates = [d for d in all_dates if d >= start_date]
    
    results = []
    
    for trade_date in all_dates:
        # Get Asian Range
        asian = get_daily_asian(bars, trade_date)
        if asian is None:
            continue
        
        ar = asian['range']
        tier = classify_tier(ar)
        
        if tier == 'NO_GO':
            results.append({
                'date': trade_date,
                'tier': tier,
                'ar_pips': ar / OIL_PIP,
                'ar_dollars': ar,
                'au': None,
                'trigger': None,
                'direction': None,
                'h25': None,
                'h50': None,
                'rekey': None,
                'outcome': 'NO_GO'
            })
            continue
        
        tier_config = TIERS[tier]
        au = tier_config['au'] * OIL_PIP
        trigger = tier_config['trigger'] * OIL_PIP
        
        # Determine bias from Asian session
        asian_mid = asian['low'] + ar / 2
        direction = 1 if asian['close'] > asian_mid else -1
        
        # Get activation window (3AM-12PM EST = 08:00-17:00 UTC)
        activation_bars = []
        for ts, o, h, lo, cl in bars:
            if ts.date() == trade_date and ts.hour >= 8 and ts.hour < 17:
                activation_bars.append((ts, o, h, lo, cl))
        
        if len(activation_bars) == 0:
            continue
        
        entry = activation_bars[0][1]  # Open of first activation bar
        
        # Targets
        if direction == 1:  # Bullish
            target_25 = entry + ar * 0.25
            target_50 = entry + ar * 0.50
            kill_switch = entry - ar * 1.32
        else:  # Bearish
            target_25 = entry - ar * 0.25
            target_50 = entry - ar * 0.50
            kill_switch = entry + ar * 1.32
        
        # Check outcomes
        h25 = False
        h50 = False
        rekey = False
        
        for ts, o, h, lo, cl in activation_bars:
            if direction == 1:
                if h >= target_25: h25 = True
                if h >= target_50: h50 = True
                if lo <= kill_switch: rekey = True
            else:
                if lo <= target_25: h25 = True
                if lo <= target_50: h50 = True
                if h >= kill_switch: rekey = True
        
        outcome = 'WIN' if h25 else 'LOSS'
        
        results.append({
            'date': trade_date,
            'tier': tier,
            'ar_pips': ar / OIL_PIP,
            'ar_dollars': ar,
            'au': au,
            'trigger': trigger,
            'direction': 'BULL' if direction == 1 else 'BEAR',
            'entry': entry,
            'target_25': target_25,
            'target_50': target_50,
            'kill_switch': kill_switch,
            'h25': h25,
            'h50': h50,
            'rekey': rekey,
            'outcome': outcome
        })
    
    return results

# Load data - use M5 for proper Asian Range calculation
bars = load_bars('quant-lab/data/OILUSDPRO_M5.csv')
print(f'Loaded {len(bars)} bars')
print(f'Date range: {bars[0][0].date()} to {bars[-1][0].date()}')

# Run from March 2026
start = datetime(2026, 3, 1).date()
results = run_st_backtest(bars, start_date=start)

print(f'\n=== ST OILUSD BACKTEST: March 2026 onwards ===')
print(f'Total sessions: {len(results)}')

# Filter out NO_GO
trades = [r for r in results if r['outcome'] != 'NO_GO']
no_go = [r for r in results if r['outcome'] == 'NO_GO']

print(f'Tradable sessions: {len(trades)}')
print(f'NO_GO sessions: {len(no_go)} ({len(no_go)/len(results)*100:.1f}%)')

if len(trades) > 0:
    wins = [r for r in trades if r['outcome'] == 'WIN']
    losses = [r for r in trades if r['outcome'] == 'LOSS']
    h25_count = sum(1 for r in trades if r['h25'])
    h50_count = sum(1 for r in trades if r['h50'])
    rekey_count = sum(1 for r in trades if r['rekey'])
    
    print(f'\n=== OVERALL ===')
    print(f'Wins: {len(wins)}/{len(trades)} = {len(wins)/len(trades)*100:.1f}%')
    print(f'-25% hit: {h25_count}/{len(trades)} = {h25_count/len(trades)*100:.1f}%')
    print(f'-50% hit: {h50_count}/{len(trades)} = {h50_count/len(trades)*100:.1f}%')
    print(f'Rekey: {rekey_count}/{len(trades)} = {rekey_count/len(trades)*100:.1f}%')
    
    # By tier
    print(f'\n=== BY TIER ===')
    for tier in ['T1', 'T2', 'T3']:
        tier_trades = [r for r in trades if r['tier'] == tier]
        if len(tier_trades) == 0:
            continue
        tier_wins = [r for r in tier_trades if r['outcome'] == 'WIN']
        tier_h25 = sum(1 for r in tier_trades if r['h25'])
        tier_h50 = sum(1 for r in tier_trades if r['h50'])
        tier_rekey = sum(1 for r in tier_trades if r['rekey'])
        avg_ar = sum(r['ar_dollars'] for r in tier_trades) / len(tier_trades)
        print(f'{tier}: {len(tier_trades)} trades | WR: {len(tier_wins)/len(tier_trades)*100:.1f}% | -25%: {tier_h25/len(tier_trades)*100:.1f}% | -50%: {tier_h50/len(tier_trades)*100:.1f}% | Rekey: {tier_rekey/len(tier_trades)*100:.1f}% | Avg AR: ${avg_ar:.2f}')
    
    # Monthly breakdown
    print(f'\n=== MONTHLY ===')
    months = {}
    for r in trades:
        month = r['date'].strftime('%Y-%m')
        if month not in months:
            months[month] = []
        months[month].append(r)
    
    for month in sorted(months.keys()):
        m_trades = months[month]
        m_wins = [r for r in m_trades if r['outcome'] == 'WIN']
        m_h25 = sum(1 for r in m_trades if r['h25'])
        m_h50 = sum(1 for r in m_trades if r['h50'])
        m_rekey = sum(1 for r in m_trades if r['rekey'])
        print(f'{month}: {len(m_trades)}d | WR: {len(m_wins)/len(m_trades)*100:.1f}% | -25%: {m_h25/len(m_trades)*100:.1f}% | -50%: {m_h50/len(m_trades)*100:.1f}% | Rekey: {m_rekey/len(m_trades)*100:.1f}%')
    
    # Weekly breakdown for March
    print(f'\n=== MARCH 2026 WEEKLY ===')
    march = [r for r in trades if r['date'].month == 3]
    weeks = {}
    for r in march:
        week = r['date'].isocalendar()[1]
        if week not in weeks:
            weeks[week] = []
        weeks[week].append(r)
    
    for week in sorted(weeks.keys()):
        w_trades = weeks[week]
        w_wins = [r for r in w_trades if r['outcome'] == 'WIN']
        w_h25 = sum(1 for r in w_trades if r['h25'])
        w_rekey = sum(1 for r in w_trades if r['rekey'])
        avg_ar = sum(r['ar_dollars'] for r in w_trades) / len(w_trades)
        print(f'W{week}: {len(w_trades)}d | WR: {len(w_wins)/len(w_trades)*100:.1f}% | -25%: {w_h25/len(w_trades)*100:.1f}% | Rekey: {w_rekey} | Avg AR: ${avg_ar:.2f}')
    
    # Rekey days detail
    rekey_days = [r for r in trades if r['rekey']]
    if rekey_days:
        print(f'\n=== REKEY DAYS ({len(rekey_days)}) ===')
        for r in rekey_days:
            print(f"  {r['date']} | {r['tier']} | AR: ${r['ar_dollars']:.2f} | {r['direction']} | Entry: {r['entry']:.2f} | KS: {r['kill_switch']:.2f}")

print('\nDone.')
