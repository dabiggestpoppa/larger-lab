import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Deep diagnostic: understand the breakout leg and DZ geometry
csv_path = r'C:\Users\wifik\Downloads\EURUSD.PRO_H4_202301020000_202606020000.csv'
df = pd.read_csv(csv_path, sep='\t', skiprows=1, names=['date','time','open','high','low','close','vol','spread','x'])
df['dt'] = pd.to_datetime(df['date'] + ' ' + df['time'])
df = df.set_index('dt').sort_index()
df = df[~df.index.duplicated(keep='first')]
for col in ['open','high','low','close']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

pip_size = 0.0001
lookback = 8

df['rh'] = df['high'].rolling(window=lookback).max()
df['rl'] = df['low'].rolling(window=lookback).min()
df['rr_pips'] = (df['rh'] - df['rl']) / pip_size
df['prev_rh'] = df['rh'].shift(1)
df['prev_rl'] = df['rl'].shift(1)
df['prev_rr'] = df['rr_pips'].shift(1)
df['body_pips'] = (df['close'] - df['open']).abs() / pip_size
df['is_bull'] = df['close'] > df['open']
df['is_attack_day'] = df.index.dayofweek.isin([1, 2])
regime_gate = df['prev_rr'].quantile(0.66)

df['break_long'] = (df['close'] > df['prev_rh']) & df['is_attack_day'] & (df['prev_rr'] < regime_gate)
df['break_short'] = (df['close'] < df['prev_rl']) & df['is_attack_day'] & (df['prev_rr'] < regime_gate)

signals = df[df['break_long'] | df['break_short']].copy()

print(f"Total signals: {len(signals)}")
print(f"Regime gate: {regime_gate:.1f} pips\n")

# Analyze the breakout leg geometry for first 10 signals
for count, (idx, row) in enumerate(signals.iterrows()):
    if count >= 10: break
    is_long = row['break_long']
    entry = row['close']
    prev_rh = row['prev_rh']
    prev_rl = row['prev_rl']
    coil_rr = row['prev_rr']
    body = row['body_pips']

    if is_long:
        # Breakout leg = how far above prev_rh did we close?
        leg_pips = (entry - prev_rh) / pip_size
        # The "full move" from prev_rh to entry
        # DZ should be a pullback FROM entry TOWARD prev_rh
        # 32% pullback from entry = entry - 0.32 * leg
        # 50% pullback from entry = entry - 0.50 * leg
        dz_near = entry - (leg_pips * 0.32 * pip_size)
        dz_far = entry - (leg_pips * 0.50 * pip_size)
        trap = entry - (leg_pips * 0.62 * pip_size)
        dir_str = 'LONG'
    else:
        leg_pips = (prev_rl - entry) / pip_size
        dz_near = entry + (leg_pips * 0.32 * pip_size)
        dz_far = entry + (leg_pips * 0.50 * pip_size)
        trap = entry + (leg_pips * 0.62 * pip_size)
        dir_str = 'SHORT'

    # The DZ width
    dz_width = abs(dz_near - dz_far) / pip_size

    print(f"Signal {count+1}: {idx} | {dir_str}")
    print(f"  Entry: {entry:.5f} | Prev RH: {prev_rh:.5f} | Prev RL: {prev_rl:.5f}")
    print(f"  Coil: {coil_rr:.1f}p | Body: {body:.1f}p | Breakout leg: {leg_pips:.1f}p")
    print(f"  DZ: {min(dz_near, dz_far):.5f} - {max(dz_near, dz_far):.5f} (width: {dz_width:.1f}p)")
    print(f"  Trap: {trap:.5f}")

    # Check: is the DZ actually between entry and the coil boundary?
    if is_long:
        coil_boundary = prev_rh
        between_check = min(dz_near, dz_far) >= coil_boundary
    else:
        coil_boundary = prev_rl
        between_check = max(dz_near, dz_far) <= coil_boundary

    print(f"  Coil boundary: {coil_boundary:.5f} | DZ between entry & boundary: {between_check}")

    # Now check what happens in the next 5 bars
    loc = df.index.get_loc(idx)
    future = df.iloc[loc+1:loc+6]
    for fi, (fidx, frow) in enumerate(future.iterrows()):
        in_dz = min(dz_near, dz_far) <= frow['close'] <= max(dz_near, dz_far)
        is_opp = (frow['close'] < frow['open']) if is_long else (frow['close'] > frow['open'])
        print(f"    Bar {fi+1} ({fidx.strftime('%m/%d %H:%M')}): O={frow['open']:.5f} H={frow['high']:.5f} L={frow['low']:.5f} C={frow['close']:.5f} | inDZ={in_dz} | isOpp={is_opp}")
    print()

# Key question: what % of breakout legs are < 5 pips (i.e., barely outside coil)?
print("\n--- Breakout leg distribution ---")
long_signals = signals[signals['break_long']]
short_signals = signals[signals['break_short']]

if len(long_signals) > 0:
    long_legs = (long_signals['close'] - long_signals['prev_rh']) / pip_size
    print(f"Long legs: mean={long_legs.mean():.1f}p median={long_legs.median():.1f}p min={long_legs.min():.1f}p max={long_legs.max():.1f}p")
    print(f"  < 5p: {(long_legs < 5).sum()} / {len(long_legs)}")
    print(f"  < 10p: {(long_legs < 10).sum()} / {len(long_legs)}")

if len(short_signals) > 0:
    short_legs = (short_signals['prev_rl'] - short_signals['close']) / pip_size
    print(f"Short legs: mean={short_legs.mean():.1f}p median={short_legs.median():.1f}p min={short_legs.min():.1f}p max={short_legs.max():.1f}p")
    print(f"  < 5p: {(short_legs < 5).sum()} / {len(short_legs)}")
    print(f"  < 10p: {(short_legs < 10).sum()} / {len(short_legs)}")
