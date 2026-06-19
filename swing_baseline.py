import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def run_raw_breakout(csv_path, timeframe_hours, pip_size, asset_name):
    """
    Raw unfiltered breakout baseline — enter on breakout close, no DZ, no filters.
    This is what the Architect said gets ~60% WR on the raw test.
    """
    try:
        df = pd.read_csv(csv_path, sep='\t', skiprows=1,
                         names=['date','time','open','high','low','close','vol','spread','x'])
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

    df['dt'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    df = df.set_index('dt').sort_index()
    df = df[~df.index.duplicated(keep='first')]
    for col in ['open','high','low','close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    lookback = 8 if timeframe_hours == 4 else 24
    df['rh'] = df['high'].rolling(window=lookback).max()
    df['rl'] = df['low'].rolling(window=lookback).min()
    df['rr_pips'] = (df['rh'] - df['rl']) / pip_size
    df['prev_rh'] = df['rh'].shift(1)
    df['prev_rl'] = df['rl'].shift(1)
    df['prev_rr'] = df['rr_pips'].shift(1)

    # Raw breakout: close outside previous coil
    df['sig_long'] = df['close'] > df['prev_rh']
    df['sig_short'] = df['close'] < df['prev_rl']

    signals = df[df['sig_long'] | df['sig_short']].copy()
    trades = []
    scan_bars = 24 if timeframe_hours == 4 else 48

    for idx, row in signals.iterrows():
        is_long = row['sig_long']
        entry = row['close']
        coil_range = row['prev_rr']

        if coil_range < 10: continue  # noise filter

        if is_long:
            target = entry + (coil_range * pip_size)
            stop = row['prev_rh']
        else:
            target = entry - (coil_range * pip_size)
            stop = row['prev_rl']

        loc = df.index.get_loc(idx)
        future = df.iloc[loc+1:loc+1+scan_bars]

        outcome = 'TIMEOUT'
        for f_idx, f_row in future.iterrows():
            if is_long and f_row['high'] >= target:
                outcome = 'WIN'; break
            if not is_long and f_row['low'] <= target:
                outcome = 'WIN'; break
            if is_long and f_row['close'] <= stop:
                outcome = 'LOSS'; break
            if not is_long and f_row['close'] >= stop:
                outcome = 'LOSS'; break

        risk = abs(entry - stop) / pip_size
        reward = abs(target - entry) / pip_size
        r_mult = (reward/risk) if outcome == 'WIN' else -1.0 if outcome == 'LOSS' else 0

        trades.append({'outcome': outcome, 'r_mult': r_mult, 'coil_range': coil_range})

    if not trades:
        return None

    t_df = pd.DataFrame(trades)
    wins = t_df[t_df['outcome'] == 'WIN']
    total = len(t_df)
    wr = (len(wins) / total) * 100
    avg_r = t_df['r_mult'].mean()
    pf = wins['r_mult'].sum() / abs(t_df[t_df['outcome']=='LOSS']['r_mult'].sum()) if len(t_df[t_df['outcome']=='LOSS']) > 0 else 0

    print(f"{asset_name:15s} | Trades: {total:5d} | WR: {wr:5.1f}% | AvgR: {avg_r:6.2f} | PF: {pf:6.2f}")
    return t_df

print("="*70)
print("RAW UNFILTERED BREAKOUT BASELINE (1x Range Target, Close-Only SL)")
print("="*70)
print(f"{'Asset':15s} | {'Trades':>5s} | {'WR':>5s} | {'AvgR':>6s} | {'PF':>6s}")
print("-"*70)

assets = [
    (r"C:\Users\wifik\Downloads\EURUSD.PRO_H4_202301020000_202606020000.csv", 4, 0.0001, 'EURUSD_H4'),
    (r"C:\Users\wifik\Downloads\EURUSD.PRO_H1_202301020000_202606020000.csv", 1, 0.0001, 'EURUSD_H1'),
    (r"C:\Users\wifik\Downloads\USDCHF.PRO_H4_202301020000_202606020000.csv", 4, 0.0001, 'USDCHF_H4'),
    (r"C:\Users\wifik\Downloads\USDCHF.PRO_H1_202301020000_202606020000.csv", 1, 0.0001, 'USDCHF_H1'),
    (r"C:\Users\wifik\Downloads\BTCUSD_H4_202301010000_202606020000.csv", 4, 1.0, 'BTCUSD_H4'),
    (r"C:\Users\wifik\Downloads\BTCUSD_H1_202301010000_202606020000.csv", 1, 1.0, 'BTCUSD_H1'),
    (r"C:\Users\wifik\Downloads\XAUUSD.PRO_H4_202301030000_202606020000.csv", 4, 0.1, 'XAUUSD_H4'),
    (r"C:\Users\wifik\Downloads\XAUUSD.PRO_H1_202301030100_202606012300.csv", 1, 0.1, 'XAUUSD_H1'),
    (r"C:\Users\wifik\Downloads\US500_H4_202301030000_202606020000.csv", 4, 1.0, 'US500_H4'),
    (r"C:\Users\wifik\Downloads\US500_H1_202301030100_202606012300.csv", 1, 1.0, 'US500_H1'),
    (r"C:\Users\wifik\Downloads\USTEC100_H4_202301030000_202606020000.csv", 4, 1.0, 'USTEC100_H4'),
    (r"C:\Users\wifik\Downloads\USTEC100_H1_202301030100_202606012300.csv", 1, 1.0, 'USTEC100_H1'),
]

for path, tf, pip, name in assets:
    run_raw_breakout(path, tf, pip, name)
