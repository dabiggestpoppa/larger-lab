"""Diagnose: find WHY Nautilus gets more trades than Python for XAUUSD."""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab')
sys.path.insert(0, 'quant-lab/engines')
sys.path.insert(0, 'quant-lab/configs')
sys.path.insert(0, 'quant-lab/strategies')

from quant_lab.configs.asset_configs import ASSET_CONFIGS
from symmetry_trap_strategy import SYMBOL_TIER_CONFIGS, DEFAULT_TIER_CONFIG, PIP_DIVISORS

py_cfg = ASSET_CONFIGS['XAUUSD']
nt_cfg = SYMBOL_TIER_CONFIGS.get('XAUUSD', DEFAULT_TIER_CONFIG)

print('=== Config Comparison ===')
print(f'Python pip_value: {py_cfg["pip_value"]}')
print(f'Nautilus pip_divisor for XAUUSD: {PIP_DIVISORS.get("XAUUSD", "NOT FOUND")}')
print(f'Nautilus pip_divisor for XAU/USD: {PIP_DIVISORS.get("XAU/USD", "NOT FOUND")}')
print()
print(f'Python tiers: {py_cfg["tiers"]}')
print(f'Nautilus tiers: {nt_cfg}')
print()

# PIP SIZE COMPARISON
# Python engine: pip_size = 0.1 (config pip_value)
# Nautilus: pip_divisor = 10.0 for XAUUSD
# In Nautilus: pips = price_delta * pip_divisor = price_delta * 10.0
# In Python: pips = price_delta / pip_size = price_delta / 0.1 = price_delta * 10.0
# So they should be equivalent... but let's verify

# CRITICAL: Does the Nautilus strategy actually USE XAUUSD tiers?
# The config.tier_config_override runner passes the tiers from ASSET_CONFIGS
# which has 'tiers' key. Let me check:

print('=== Nautilus XAUUSD Tier Source ===')
# When run_cerebus_backtest_fixed.py runs with XAUUSD:
# ASSET_CONFIGS['XAUUSD'] = {'name': 'XAU/USD', 'pip_value': 0.1, 'tiers': {...}}
# config.tier_config_override = cfg['tiers']  <-- passes ONLY the tiers dict

# BUT WAIT: asset_configs config has 'name': 'XAU/USD'
# In Nautilus strategy, sym_key = instrument_id.symbol.replace('/', '').replace('.', '')
# If instrument_id is 'XAUUSD', sym_key = 'XAUUSD'
# Lookup: SYMBOL_TIER_CONFIGS.get('XAUUSD') = the XAUUSD entry
# BUT if tier_config_override is provided, it uses that instead

# So BOTH use the same tiers. The difference must be in bar processing.

# Let me check: Nautilus processes bars differently
# Key difference I noticed: the run() method in symmetry_trap_backtest groups by EST date
# and processes ALL bars (including Asian) through the engine after init.
# But the skips the first few Asian bars since session is not active until init.

# Actually, WAIT. Let me re-read the run() method more carefully.
from symmetry_trap_backtest import load_m5_csv, SymmetryTrapBacktest

# Load a small slice of XAUUSD data and trace through
bars, sym = load_m5_csv('quant-lab/data/XAUUSD_M5.csv')
print(f'Total bars: {len(bars)}')
'Date range: {} to {}'.format(bars[0].timestamp, bars[-1].timestamp)

# Let me trace the first few days manually to count sessions and trades
from datetime import timedelta, time as dtime
from collections import defaultdict

# Group bars by EST date
days = defaultdict(list)
for b in bars:
    est_dt = b.timestamp + timedelta(hours=-5)  # est_offset = -5
    dk = est_dt.strftime('%Y-%m-%d')
    days[dk].append(b)

# Simulate the campaign runner for first 10 days
from symmetry_trap import SymmetryTrapEngine, EngineState
from quant_lab.configs.asset_configs import ASSET_CONFIGS

engine = SymmetryTrapEngine(pip_size=0.1, config=ASSET_CONFIGS['XAUUSD'])
trades_count = 0
sessions_active = 0
sessions_nogo = 0
total_days = 0

# Trace first 30 days
for dk in sorted(days.keys())[:30]:
    day_bars = sorted(days[dk], key=lambda b: b.timestamp)
    
    # Find Asian range
    ah, al = 0.0, 99999.0
    for b in day_bars:
        est_h = (b.timestamp.hour - 5) % 24
        if est_h >= 19 or est_h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    
    if ah <= 0 or al >= 99999:
        continue
    
    total_days += 1
    engine.initialize_session(ah, al)
    
    if not engine.session_active:
        sessions_nogo += 1
        continue
    
    sessions_active += 1
    day_trades = 0
    
    for bar in day_bars:
        bar_est_h = (bar.timestamp.hour - 5) % 24
        if bar_est_h >= 12 and engine.state == EngineState.SEARCH:
            break
        sig = engine.process_bar(bar)
        if sig and sig.event in ('TP_HIT', 'SL_HIT'):
            day_trades += 1
        elif sig and sig.event == 'KILL_SWITCH':
            pass  # kill switch doesn't count as completed trade
    
    trades_count += day_trades
    if day_trades == 0:
        # Why? Check if impulse was ever detected
        pass

print(f'\nFirst 30 days trace:')
print(f'Days with data: {total_days}, Active: {sessions_active}, NO-GO: {sessions_nogo}')
print(f'Trades in active sessions: {trades_count}')
print(f'Trades per active session: {trades_count/max(sessions_active,1):.2f}')

# Now: Nautilus got 1,718 trades, Python got 604.
# Ratio: 1718/604 = 2.84x more in Nautilus
# This is WAY more than the expected ~5% tolerance.

# MAD said: "it's not a bug, it's the code working. our python was just under delivering"
# This means the Nautilus result is CORRECT and Python is MISSING trades.
# So the Python engine is being too restrictive somewhere.

# Let me check: Does Nautilus init swing_origin from the init bar itself?
# In the Python run() method, initialize_session is called, then bars are processed.
# The first bar AFTER init sets swing_origin = bar.close (line 287-288 of process_bar)
# But what if Nautilus sets it from the init bar?

# Let me check Nautilus on_bar flow more carefully
print('\n=== Nautilus on_bar session init flow ===')
# In Nautilus on_bar(), at 3AM:
# if not self.asian_locked and est_hour >= self.asian_end_hour:
#     ... session init ...
#     self.swing_origin = float(bar.close)
#     return  # <-- SKIPS the rest of on_bar for init bar

# So Nautilus sets swing_origin from the FIRST 3AM bar close, then RETURNS
# (doesn't process impulse detection on that bar)
# The NEXT bar will be processed with swing_origin already set

# In the Python run() method:
# initialize_session() is called BEFORE the loop, sets state to SEARCH
# Then the loop processes ALL day_bars including Asian ones
# First Asian bar: engine.process_bar() -> session_active=True (if active session)
#   -> swing_origin is None -> sets swing_origin = bar.close -> returns None (SEARCH, no impulse yet)
#   This means swing_origin is set to an Asian bar close!

# After init, when 3AM bar comes (same bar that Nautilus uses for init):
# If it's an Asian bar (still in Asian session?), swing_origin was already set
# Then NEXT post-3AM bar comes, impulse detection runs against Asian close origin

# KEY DIFFERENCE:
# Nautilus: swing_origin = first 3AM bar close (end of Asian range)
# Python campaign: swing_origin = first Asian bar close (could be 7PM bar)

# This means Python measures impulse from a potentially LOWER origin (if 7PM bar is lower than 3AM bar)
# which means impulse trigger is EASIER to hit -> MORE trades expected, not fewer

# But wait, Python got FEWER trades (604) vs Nautilus (1718).
# So the swing origin difference can't explain it.

# Let me check if Nautilus is actually using DIFFERENT tier thresholds
# by looking at the Nautilus results log more carefully.

print('\n=== Re-examining: Nautilus Nautilus tier config ===')
# When the runner passes tier_config_override=cfg['tiers']:
nts = {'T1': {'ar_max': 32.0, 'au': 16.0, 'trigger': 19.0},
       'T2': {'ar_max': 58.0, 'au': 29.0, 'trigger': 35.0},
       'T3': {'ar_max': 95.0, 'au': 48.0, 'trigger': 58.0}}
print(f'Nautilus override tiers: {nts}')
print(f'Python engine tiers:     {py_cfg["tiers"]}')
print(f'Match: {nts == py_cfg["tiers"]}')

# OK the tiers match. So the difference must be in the impulse/retrace/OCC logic.
# Let me compare the RETRACE threshold logic side by side.

print('\n=== RETRACE LOGIC COMPARISON ===')
print()
print('Python WAIT_RETRACE:')
print('  Loop 1: min_retrace=0.32, max_retrace=0.50')
print('  Loop 2+: min_retrace=0.20, max_retrace=0.50')
print('  OR AU penetration (pullback >= AU)')
print()
print('Nautilus WAIT_RETRACE:')
print('  Loop 1: min_retrace=0.32, max_retrace=0.50')
print('  Loop 2+: min_retrace=0.20, max_retrace=0.50')
print('  OR AU penetration')
print()
print('These look IDENTICAL.')

# Let me check: does Nautilus handle the cascade_bias bypass?
# Python has: cascade_bypass (line 387-391 of symmetry_trap.py)
# Nautilus: does NOT have cascade_bypass in _state_wait_retrace
# This would mean Nautilus has FEWER retrace qualifications, not more.

# WAIT - that means if anything, Nautilus should have FEWER trades, not more.
# But Nautilus has 1,718 vs Python's 604. That's opposite of what cascade_bypass would cause.

# Let me think about this differently...
# MAD said Nautilus is RIGHT and Python is under-delivering.
# What if the Nautilus config override is not being used correctly?
# What if Nautilus falls back to DEFAULT_TIER_CONFIG (EURUSD tiers)?

print('\n=== What if Nautilus uses WRONG tiers? ===')
print(f'EURUSD tiers: {DEFAULT_TIER_CONFIG}')
print(f'XAUUSD tiers: {nt_cfg}')
print()
print('EURUSD T1 ar_max=20.0, XAUUSD T1 ar_max=32.0')
print('EURUSD T2 ar_max=30.0, XAUUSD T2 ar_max=58.0')
print('EURUSD T3 ar_max=45.0, XAUUSD T3 ar_max=95.0')
print()
print('If Nautilus used EURUSD tiers for XAUUSD:')
print('  - Fewer sessions would be NO-GO (EURUSD tiers are TIGHTER)')
print(f'  - Wait... actually with tighter tiers, MORE would be NO-GO')
print()
print('Actually, the au/trigger values differ:')
for t in ['T1', 'T2', 'T3']:
    print(f'  {t}: EURUSD trigger={DEFAULT_TIER_CONFIG[t]["trigger"]} vs XAUUSD trigger={nt_cfg[t]["trigger"]}')
    print(f'  {t}: EURUSD au={DEFAULT_TIER_CONFIG[t]["au"]} vs XAUUSD au={nt_cfg[t]["au"]}')
