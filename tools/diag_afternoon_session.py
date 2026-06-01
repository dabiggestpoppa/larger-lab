"""
Simulate the Nautilus 12PM reset behavior to see if it creates
afternoon sessions that produce additional trades.
"""
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

# Group by EST date
days = defaultdict(list)
for b in bars:
    est_dt = b.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    days[dk].append(b)

# Simulate Nautilus-like behavior:
# Session 1: 3AM to noon (traditional)
# 12PM reset, then Session 2: noon+ to 5PM (NEW)
# Track trades separately

engine = SymmetryTrapEngine(pip_size=0.1, config=cfg)
s1_trades = 0
s2_trades = 0
s1_sessions = 0
s2_sessions = 0
s2_active = 0
s2_no_trade = 0

for dk in sorted(days.keys()):
    day_bars = sorted(days[dk], key=lambda b: b.timestamp)

    # === SESSION 1: 3AM - 12PM (same as Python) ===
    ah, al = 0.0, 99999.0
    for b in day_bars:
        est_h = (b.timestamp.hour - 5) % 24
        if est_h >= 19 or est_h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    if ah <= 0 or al >= 99999:
        continue

    engine.initialize_session(ah, al)
    if not engine.session_active:
        continue

    s1_sessions += 1
    s1_entries = 0

    for bar in day_bars:
        bar_est_h = (bar.timestamp.hour - 5) % 24
        if bar_est_h >= 12 and engine.state == EngineState.SEARCH:
            break
        sig = engine.process_bar(bar)
        if sig and sig.event == 'ENTRY':
            s1_entries += 1

    s1_trades += s1_entries

    # === SESSION 2: 12PM+ (Nautilus behavior after hard reset) ===
    # At 12PM, Nautilus calls _reset_all_state() then processes next bar
    # The next bar at est_hour >= 3 (always true for afternoon) triggers init
    # But the Asian range is from 12PM onwards (no real Asian range)
    # Nautilus uses bars from 12PM+ to compute AR

    # Simulate: collect bars from 12PM to 5PM as the "afternoon Asian range"
    afternoon_bars = []
    for bar in day_bars:
        bar_est_h = (bar.timestamp.hour - 5) % 24
        if bar_est_h >= 12 and bar_est_h < 17:
            afternoon_bars.append(bar)

    if not afternoon_bars:
        continue

    # In Nautilus, the 12PM reset sets asian_high=0, asian_low=99999
    # Then each bar in 12-5PM range updates asian_high/asian_low
    # At est_hour >= 3 (always true at 12PM+), session init triggers
    # But asian_locked was set to False by _reset_all_state
    # So any bar at est_hour >= 3 triggers init

    # The key question: what AR does the afternoon session compute?
    # In Nautilus, after 12PM reset:
    # - asian_high = 0.0, asian_low = 99999.0
    # - For each bar > 12PM, it updates asian range
    # - BUT: the "in_asian" check is (est_hour >= 19 or est_hour < 3)
    # - 12PM-5PM is NOT in Asian, so bars skip Phase 1 (Asian tracking)
    # - They hit Phase 2 (session init): asian_locked=False, est_hour>=3 → enter init
    # - AR = asian_high - asian_low = 0 - 99999 = NEGATIVE → WRONG!

    # Actually wait... after reset, asian_high=0 and asian_low=99999
    # Then the first afternoon bar hits Phase 2 immediately (est_hour=12 >= 3)
    # asian_locked is False → enters init
    # AR = asian_high - asian_low = 0 - 99999 = -99999 → impossibly negative

    # But _price_to_pips would convert this to a huge negative pip value
    # Then classify_tier checks ar_max >= asian_range_pips...
    # A negative AR would be < all ar_max values → always T1

    # But actually... let me re-read the Nautilus session init more carefully

    # Actually, I think the issue is different. Let me re-read the Nautilus code.
    # After _reset_all_state(), current_date = None
    # Next bar: bar_date != None → _reset_all_state() → current_date = bar_date
    # Then: est_hour >= 12 → hard reset again! → infinite loop?

    # Wait no — _reset_all_state() is called, then current_date = bar_date
    # NOW the 12PM check fires AGAIN (est_hour >= 12):
    #   if session_active: close positions → _reset_all_state() → return
    # So EVERY bar at est_hour >= 12 keeps resetting!
    # This means afternoon sessions NEVER start because every bar triggers reset

    # Hmm but that contradicts what I thought earlier...
    # Let me trace more carefully with actual code flow:
    # Bar at 12:05 EST:
    #   1. est_hour = 12 >= 12 → yes
    #   2. if session_active: close positions (session was active from morning)
    #   3. _reset_all_state() → current_date = None, session_active = False
    #   4. return

    # Bar at 12:10 EST:
    #   1. est_hour = 12 >= 12 → yes
    #   2. if session_active: NO (was reset to False)
    #   3. _reset_all_state() → still False, no effect
    #   4. return

    # So Nautilus NEVER processes bars after 12PM! The hard reset is EVERY bar.
    # That means the afternoon session idea is WRONG.

    # Then what explains Nautilus having 2.84x more trades?

print("Key insight: Nautilus hard reset at 12PM means it processes NO bars after noon.")
print("Same as Python's break at 12PM when state=SEARCH.")
print("")
print(f"Session 1 total trades (Python): {s1_trades}")
print(f"Session 1 active sessions: {s1_sessions}")
print("")
print("The afternoon session hypothesis is REJECTED.")
print("Need a different explanation for the 2.84x gap.")
