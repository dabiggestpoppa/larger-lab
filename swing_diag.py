import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

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
df['hold_long'] = df['break_long'] & (df['close'].shift(1) > df['prev_rh'].shift(1))
df['hold_short'] = df['break_short'] & (df['close'].shift(1) < df['prev_rl'].shift(1))

signals = df[df['hold_long'] | df['hold_short']].copy()
print(f'Signals after all filters: {len(signals)}')
print(f'Regime gate: {regime_gate:.1f} pips')

# Trace first 5 signals
count = 0
for idx, row in signals.iterrows():
    if count >= 5: break
    is_long = row['hold_long']
    entry = row['close']
    body = row['body_pips']
    coil = row['prev_rr']

    dz_upper = entry - (body * 0.32 * pip_size * (1 if is_long else -1))
    dz_lower = entry - (body * 0.50 * pip_size * (1 if is_long else -1))
    if not is_long:
        dz_upper, dz_lower = dz_lower, dz_upper

    trap = entry - (body * 0.62 * pip_size * (1 if is_long else -1))
    target_dist = coil * 1.5 * pip_size
    target = entry + (target_dist * (1 if is_long else -1))

    loc = df.index.get_loc(idx)
    future = df.iloc[loc+1:loc+13]

    dir_str = 'LONG' if is_long else 'SHORT'
    print(f'\n--- Signal {count+1}: {idx} | {dir_str} ---')
    print(f'  Entry: {entry:.5f} | Body: {body:.1f}p | Coil: {coil:.1f}p')
    print(f'  DZ: {dz_lower:.5f} - {dz_upper:.5f}')
    print(f'  Trap zone: {trap:.5f}')
    print(f'  Target: {target:.5f}')

    occ_found = False
    for fi, (fidx, frow) in enumerate(future.iterrows()):
        is_opp = (frow['close'] < frow['open']) if is_long else (frow['close'] > frow['open'])
        in_dz = dz_lower <= frow['close'] <= dz_upper

        if not occ_found:
            if is_long and frow['close'] < trap:
                print(f'  Bar {fi+1} ({fidx}): TRAP_ZONE. Close={frow["close"]:.5f} < Trap={trap:.5f}')
                break
            if not is_long and frow['close'] > trap:
                print(f'  Bar {fi+1} ({fidx}): TRAP_ZONE. Close={frow["close"]:.5f} > Trap={trap:.5f}')
                break
            if is_opp and in_dz:
                occ_found = True
                sl_val = frow['low'] if is_long else frow['high']
                print(f'  Bar {fi+1} ({fidx}): OCC FOUND. Close={frow["close"]:.5f} in DZ. SL={sl_val:.5f}')
                continue
            else:
                reasons = []
                if not is_opp:
                    reasons.append('not_opp')
                if not in_dz:
                    reasons.append(f'close={frow["close"]:.5f} outside DZ [{dz_lower:.5f}-{dz_upper:.5f}]')
                print(f'  Bar {fi+1} ({fidx}): No OCC. {" | ".join(reasons)}')
        else:
            if is_long and frow['high'] >= target:
                print(f'  Bar {fi+1}: TP HIT')
                break
            if not is_long and frow['low'] <= target:
                print(f'  Bar {fi+1}: TP HIT')
                break
            sl_val = frow['low'] if is_long else frow['high']
            if is_long and frow['close'] <= sl_val:
                print(f'  Bar {fi+1}: SL HIT at {sl_val:.5f}')
                break
            if not is_long and frow['close'] >= sl_val:
                print(f'  Bar {fi+1}: SL HIT at {sl_val:.5f}')
                break

    if not occ_found:
        print(f'  >> NO OCC in 12 bars. Trade skipped.')
    count += 1

# Also check: what % of signals have body < 5 pips (noise filter)
print(f'\n--- Noise filter stats ---')
print(f'Signals with body < 5p: {(signals["body_pips"] < 5).sum()} / {len(signals)}')
print(f'Signals with body >= 5p: {(signals["body_pips"] >= 5).sum()} / {len(signals)}')
print(f'Avg body size: {signals["body_pips"].mean():.1f} pips')
print(f'Median body size: {signals["body_pips"].median():.1f} pips')
