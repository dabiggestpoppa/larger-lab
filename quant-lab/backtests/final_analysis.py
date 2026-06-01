# -*- coding: utf-8 -*-
"""
Final analysis: Identify the EXACT causes of Nautilus extra trades.

We know:
- Python: 1379 trades, 738 sessions (EST date grouping)  
- Nautilus: 2186 trades, 804 sessions (UTC date grouping)
- Nautilus has 318 sessions Python doesn't see
- Matched sessions: Python often has MORE trades per session

Three hypotheses for Nautilus extra trades:
A) More sessions activated (due to different day grouping)
B) More trades per session (Nautilus processes more bars per session)
C) Different Asian range → different tier → different entry threshold

We test each.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from datetime import datetime, timedelta, timezone as tz
from collections import defaultdict, Counter

LAB = Path("C:/Users/wifik/Desktop/projects/larger-lab")
sys.path.insert(0, str(LAB / "quant-lab/engines"))

from symmetry_trap_backtest import load_m5_csv, SymmetryTrapBacktest
from symmetry_trap import Bar

# Load data with proper parser
bars, sym = load_m5_csv(str(LAB / "quant-lab/data/EURUSD_M5.csv"))

# === 1. Run Python with FULL per-session detail ===
py_bt = SymmetryTrapBacktest(pip_size=0.0001)

est_offset = -5
days = {}
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=est_offset)
    dk = est_dt.strftime("%Y-%m-%d")
    if dk not in days:
        days[dk] = []
    days[dk].append(bar)

# For each session, record: date, Asian range, tier, bars processed, trades, NO-GO status
py_sessions = {}  # date -> {trades, tier, au, trigger, ar, bars_count, active}

from symmetry_trap import SymmetryTrapEngine, EngineState

for dk in sorted(days.keys()):
    day_bars = sorted(days[dk], key=lambda b: b.timestamp)
    
    # Asian range (EST hour >= 19 or < 3)
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour + est_offset) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    if ah <= 0 or al >= 99999:
        continue
    
    ar_pips = (ah - al) / 0.0001
    
    engine = SymmetryTrapEngine(pip_size=0.0001)
    engine.initialize_session(ah, al)
    
    session_info = {
        'date': dk, 'ar_pips': round(ar_pips, 1), 'tier': engine.tier_name,
        'au_pips': engine.au_pips, 'trigger_pips': engine.trigger_pips,
        'active': engine.session_active, 'no_go': engine.tier_name == 'NO_GO',
        'trades': 0, 'bars_processed': 0,
        'first_bar_ts': str(day_bars[0].timestamp),
        'last_bar_ts': str(day_bars[-1].timestamp),
    }
    
    if engine.session_active:
        for bar in day_bars:
            bar_est_h = (bar.timestamp.hour + est_offset) % 24
            if bar_est_h >= 12 and engine.state == EngineState.SEARCH:
                break
            session_info['bars_processed'] += 1
            signal = engine.process_bar(bar)
            if signal and signal.event in ("TP_HIT", "SL_HIT", "KILL_SWITCH"):
                session_info['trades'] += 1
    
    py_sessions[dk] = session_info

print(f"=== PYTHON SESSIONS ===")
active_py = {k: v for k, v in py_sessions.items() if v['active']}
no_go_py = {k: v for k, v in py_sessions.items() if v['no_go']}
inactive_py = {k: v for k, v in py_sessions.items() if not v['active'] and not v['no_go']}

print(f"Total sessions: {len(py_sessions)}")
print(f"Active: {len(active_py)} | NO-GO: {len(no_go_py)} | No Asian data: {len(inactive_py)}")

py_total_trades = sum(v['trades'] for v in py_sessions.values())
print(f"Total trades: {py_total_trades}")

# === 2. Simulate Nautilus session logic ===
# Nautilus uses UTC date for day grouping
# Nautilus processes: UTC date D = bars from D 00:00 UTC to D 23:59 UTC
# Asian in Nautilus: 7PM-3AM EST = UTC hour 0-7 (EST = UTC-5)

# For each UTC date, gather bars and run the same engine
naut_days = {}
for bar in bars:
    dk = bar.timestamp.strftime("%Y-%m-%d")  # UTC date = CSV date (since CSV is naive, treated as UTC)
    if dk not in naut_days:
        naut_days[dk] = []
    naut_days[dk].append(bar)

naut_sessions = {}
for dk in sorted(naut_days.keys()):
    day_bars = sorted(naut_days[dk], key=lambda b: b.timestamp)
    
    # Nautilus Asian: EST hour >= 19 or < 3
    # EST hour = (UTC_hour + (-5)) % 24
    ah, al = 0.0, 99999.0
    for b in day_bars:
        utc_h = b.timestamp.hour
        est_h = (utc_h - 5) % 24
        if est_h >= 19 or est_h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    if ah <= 0 or al >= 99999:
        continue
    
    ar_pips = (ah - al) / 0.0001
    
    engine = SymmetryTrapEngine(pip_size=0.0001)
    engine.initialize_session(ah, al)
    
    session_info = {
        'date': dk, 'ar_pips': round(ar_pips, 1), 'tier': engine.tier_name,
        'au_pips': engine.au_pips, 'trigger_pips': engine.trigger_pips,
        'active': engine.session_active, 'no_go': engine.tier_name == 'NO_GO',
        'trades': 0, 'bars_processed': 0,
        'first_bar_ts': str(day_bars[0].timestamp),
        'last_bar_ts': str(day_bars[-1].timestamp),
    }
    
    if engine.session_active:
        for bar in day_bars:
            utc_h = bar.timestamp.hour
            est_h = (utc_h - 5) % 24
            # Nautilus hard reset: if est_hour >= 12, close all and stop
            if est_h >= 12:
                break
            session_info['bars_processed'] += 1
            signal = engine.process_bar(bar)
            if signal and signal.event in ("TP_HIT", "SL_HIT", "KILL_SWITCH"):
                session_info['trades'] += 1
    
    naut_sessions[dk] = session_info

print(f"\n=== NAUTILUS SESSIONS (simulated with Python engine) ===")
active_naut = {k: v for k, v in naut_sessions.items() if v['active']}
no_go_naut = {k: v for k, v in naut_sessions.items() if v['no_go']}

print(f"Total sessions: {len(naut_sessions)}")
print(f"Active: {len(active_naut)} | NO-GO: {len(no_go_naut)}")
naut_total_trades = sum(v['trades'] for v in naut_sessions.values())
print(f"Total trades: {naut_total_trades}")

# === 3. Compare ===
print(f"\n=== COMPARISON ===")
print(f"Python sessions: {len(active_py)} | trades: {py_total_trades}")
print(f"Naut sessions:   {len(active_naut)} | trades: {naut_total_trades}")
print(f"Session diff:    {len(active_naut) - len(active_py)} more in Nautilus")
print(f"Trade diff:      {naut_total_trades - py_total_trades} more in Nautilus")
print(f"Nautilus/Python: {naut_total_trades/max(py_total_trades,1):.2f}x")

# Compare same-date sessions
matched = 0
py_more = 0
naut_more = 0
same = 0
for dk in sorted(set(active_py.keys()) & set(active_naut.keys())):
    py_t = active_py[dk]['trades']
    naut_t = active_naut[dk]['trades']
    matched += 1
    if py_t > naut_t:
        py_more += 1
    elif naut_t > py_t:
        naut_more += 1
    else:
        same += 1

print(f"\n=== MATCHED SESSIONS ({matched}) ===")
print(f"Python more trades: {py_more} | Nautilus more: {naut_more} | Same: {same}")

# Sessions only in Nautilus
only_naut = set(active_naut.keys()) - set(active_py.keys())
only_py = set(active_py.keys()) - set(active_naut.keys())
print(f"\nOnly in Nautilus: {len(only_naut)} sessions, {sum(active_naut[k]['trades'] for k in only_naut)} trades")
print(f"Only in Python: {len(only_py)} sessions, {sum(active_py[k]['trades'] for k in only_py)} trades")

# Show top "only in Nautilus" sessions
print(f"\nTop 10 Nautilus-only sessions:")
for dk in sorted(only_naut, key=lambda k: -active_naut[k]['trades'])[:10]:
    s = active_naut[dk]
    print(f"  {dk}: {s['trades']} trades, AR={s['ar_pips']}p, tier={s['tier']}, "
          f"bars={s['bars_processed']}, range={s['first_bar_ts'][:10]} to {s['last_bar_ts'][:10]}")

# Do these Nautilus-only sessions have Python data on ADJACENT dates?
print(f"\n=== Do Nautilus-only dates have Python data on adjacent dates? ===")
for dk in sorted(only_naut)[:5]:
    dk_dt = datetime.strptime(dk, "%Y-%m-%d")
    prev_dk = (dk_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    next_dk = (dk_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    py_prev = py_sessions.get(prev_dk, {}).get('trades', 'N/A')
    py_next = py_sessions.get(next_dk, {}).get('trades', 'N/A')
    print(f"  Naut {dk}: prev Py {prev_dk}={py_prev}, next Py {next_dk}={py_next}")
    # Check bar range
    naut_bars = sorted(naut_days[dk], key=lambda b: b.timestamp)
    print(f"    Naut bars: {naut_bars[0].timestamp} to {naut_bars[-1].timestamp}")
    # What Python date would cover these bars?
    sample_ts = naut_bars[0].timestamp
    py_est_date = (sample_ts + timedelta(hours=-5)).strftime("%Y-%m-%d")
    print(f"    First bar maps to Python EST date: {py_est_date}")

print("\nDone.")
