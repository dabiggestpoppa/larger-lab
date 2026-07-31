"""XAUUSD Python ST engine - full funnel diagnostic (ASCII safe)."""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab/engines')
sys.path.insert(0, 'quant-lab/configs')

from datetime import timedelta
from collections import defaultdict, Counter
from symmetry_trap import SymmetryTrapEngine, Bar, EngineState, TradeDirection
from symmetry_trap_backtest import load_m5_csv
from quant_lab.configs.asset_configs import ASSET_CONFIGS

bars, _ = load_m5_csv('quant-lab/data/XAUUSD_M5.csv')
cfg = ASSET_CONFIGS['XAUUSD']

days = defaultdict(list)
for b in bars:
    est_dt = b.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    days[dk].append(b)

engine = SymmetryTrapEngine(pip_size=0.1, config=cfg)

r = dict(total_days=0, nogo=0, active=0, active_no_trade=0, active_with_trade=0,
         total_entries=0, total_tp=0, total_sl=0, total_ks=0,
         sessions_with_impulse=0, sessions_with_retrace=0, sessions_with_occ=0)

session_stats = []

for dk in sorted(days.keys()):
    day_bars = sorted(days[dk], key=lambda b: b.timestamp)
    ah, al = 0.0, 99999.0
    for b in day_bars:
        est_h = (b.timestamp.hour - 5) % 24
        if est_h >= 19 or est_h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    if ah <= 0 or al >= 99999:
        continue

    r['total_days'] += 1
    engine.initialize_session(ah, al)
    if not engine.session_active:
        r['nogo'] += 1
        continue

    r['active'] += 1
    day_entries = day_tp = day_sl = day_ks = 0
    had_impulse = had_retrace = had_occ = False

    for bar in day_bars:
        bar_est_h = (bar.timestamp.hour - 5) % 24
        if bar_est_h >= 12 and engine.state == EngineState.SEARCH:
            break
        prev_state = engine.state
        sig = engine.process_bar(bar)
        if engine.state == EngineState.WAIT_RETRACE and prev_state == EngineState.SEARCH:
            had_impulse = True
        if engine.state == EngineState.WAIT_OCC and prev_state == EngineState.WAIT_RETRACE:
            had_retrace = True
        if engine.state == EngineState.IN_TRADE and prev_state == EngineState.WAIT_OCC:
            had_occ = True
        if sig:
            if sig.event == 'ENTRY': day_entries += 1
            elif sig.event == 'TP_HIT': day_tp += 1
            elif sig.event == 'SL_HIT': day_sl += 1
            elif sig.event == 'KILL_SWITCH': day_ks += 1

    if had_impulse: r['sessions_with_impulse'] += 1
    if had_retrace: r['sessions_with_retrace'] += 1
    if had_occ: r['sessions_with_occ'] += 1
    r['total_entries'] += day_entries
    r['total_tp'] += day_tp
    r['total_sl'] += day_sl
    r['total_ks'] += day_ks

    if day_entries == 0:
        r['active_no_trade'] += 1
    else:
        r['active_with_trade'] += 1

    session_stats.append({
        'date': dk, 'entries': day_entries, 'tp': day_tp, 'sl': day_sl,
        'ks': day_ks, 'tier': engine.tier_name,
        'had_impulse': had_impulse, 'had_retrace': had_retrace,
        'had_occ': had_occ, 'final_state': engine.state.value,
        'ar': engine.asian_range_pips
    })

print("=== XAUUSD PYTHON ENGINE FUNNEL ===")
print(f"Total days: {r['total_days']}")
print(f"NO-GO: {r['nogo']} ({r['nogo']/r['total_days']*100:.1f}%)")
print(f"Active: {r['active']} ({r['active']/r['total_days']*100:.1f}%)")
print(f"  With trades: {r['active_with_trade']}")
print(f"  No trades: {r['active_no_trade']}")
print(f"Total entries: {r['total_entries']}")
print(f"Completed: TP={r['total_tp']} SL={r['total_sl']} KS={r['total_ks']}")
print(f"  Total completed: {r['total_tp']+r['total_sl']}")
print(f"")
print(f"Sessions with impulse: {r['sessions_with_impulse']}/{r['active']} ({r['sessions_with_impulse']/max(r['active'],1)*100:.1f}%)")
print(f"Sessions with retrace: {r['sessions_with_retrace']}/{r['sessions_with_impulse']} ({r['sessions_with_retrace']/max(r['sessions_with_impulse'],1)*100:.1f}%)")
print(f"Sessions with entry: {r['sessions_with_occ']}/{r['sessions_with_retrace']} ({r['sessions_with_occ']/max(r['sessions_with_retrace'],1)*100:.1f}%)")
print("")

# Why no-trade sessions fail
no_trade = [s for s in session_stats if s['entries'] == 0]
trade = [s for s in session_stats if s['entries'] > 0]
nt_no_impulse = sum(1 for s in no_trade if not s['had_impulse'])
nt_impulse_no_retrace = sum(1 for s in no_trade if s['had_impulse'] and not s['had_retrace'])
nt_retrace_no_occ = sum(1 for s in no_trade if s['had_retrace'] and not s['had_occ'])
print("=== NO-TRADE SESSION BREAKDOWN ===")
print(f"No impulse at all: {nt_no_impulse}")
print(f"Impulse but no retrace: {nt_impulse_no_retrace}")
print(f"Retrace but no OCC: {nt_retrace_no_occ}")
print(f"Other/unknown: {len(no_trade) - nt_no_impulse - nt_impulse_no_retrace - nt_retrace_no_occ}")

# Tier distribution
nt_tiers = Counter(s['tier'] for s in no_trade)
t_tiers = Counter(s['tier'] for s in trade)
print(f"\nNo-trade tiers: {dict(nt_tiers)}")
print(f"Trade tiers: {dict(t_tiers)}")

# AR distribution for no-trade vs trade
if no_trade:
    nt_ars = [s['ar'] for s in no_trade]
    print(f"\nNo-trade AR: min={min(nt_ars):.1f} median={sorted(nt_ars)[len(nt_ars)//2]:.1f} max={max(nt_ars):.1f}")
if trade:
    t_ars = [s['ar'] for s in trade]
    print(f"Trade AR: min={min(t_ars):.1f} median={sorted(t_ars)[len(t_ars)//2]:.1f} max={max(t_ars):.1f}")

# Sample no-trade sessions
print("\n=== SAMPLE NO-TRADE SESSIONS ===")
for s in no_trade[:10]:
    print(f"  {s['date']}: tier={s['tier']}, AR={s['ar']:.1f}p, imp={s['had_impulse']}, ret={s['had_retrace']}, occ={s['had_occ']}, final={s['final_state']}")

print("\n=== SAMPLE TRADE SESSIONS ===")
for s in trade[:10]:
    print(f"  {s['date']}: tier={s['tier']}, AR={s['ar']:.1f}p, entries={s['entries']}, tp={s['tp']}, sl={s['sl']}, ks={s['ks']}")
