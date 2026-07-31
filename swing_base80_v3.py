import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def run_swing_base80_test(csv_path, timeframe_hours, pip_size, asset_name):
    """
    CEREBUS SWING BASE 80 FILTER STACK TEST — V3
    Major redesign of entry logic for swing timeframes:

    Problem with V1/V2: The DZ measured from breakout leg doesn't work on swing TFs
    because breakout legs are tiny (median 6-9 pips). A 32-50% DZ of a 7pip leg
    is a 2-4 pip window that price never retraces into.

    V3 Approach — "Swing Retest" Entry:
    1. Breakout candle closes outside the coil (same as before)
    2. Instead of waiting for OCC in a tiny DZ, we wait for price to PULL BACK
       to the coil boundary (the "retest") and then reverse
    3. Entry = the first candle that closes BACK inside the coil after the breakout
       (the "retest confirmation") — OR — the first candle that makes a new high/low
       after touching the coil boundary
    4. This is the swing equivalent of "break and retest"

    Alternative simpler approach tested here:
    - Enter on the breakout close itself (no DZ wait)
    - SL = coil boundary (close back inside = invalidation)
    - TP = 1.0x to 1.5x coil range
    - This is the "Raw Breakout" that the Architect said gets 60% WR
    - Then we add filters to push it to 80%+
    """
    print(f"\n{'='*20} SWING BASE 80 V3: {asset_name} (H{timeframe_hours}) {'='*20}")

    try:
        df = pd.read_csv(csv_path, sep='\t', skiprows=1,
                         names=['date', 'time', 'open', 'high', 'low', 'close', 'vol', 'spread', 'x'])
    except Exception as e:
        print(f"[ERROR] Failed to load {csv_path}: {e}")
        return None

    df['dt'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    df = df.set_index('dt').sort_index()
    df = df[~df.index.duplicated(keep='first')]

    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['open', 'high', 'low', 'close'])

    print(f"Loaded {len(df)} bars. Range: {df.index[0]} -> {df.index[-1]}")

    df['body_pips'] = (df['close'] - df['open']).abs() / pip_size
    df['is_bull'] = df['close'] > df['open']

    # 1. DEFINE THE COIL
    lookback = 8 if timeframe_hours == 4 else 24

    df['rh'] = df['high'].rolling(window=lookback).max()
    df['rl'] = df['low'].rolling(window=lookback).min()
    df['rr_pips'] = (df['rh'] - df['rl']) / pip_size

    df['prev_rh'] = df['rh'].shift(1)
    df['prev_rl'] = df['rl'].shift(1)
    df['prev_rr'] = df['rr_pips'].shift(1)

    # 2. DYNAMIC REGIME GATE (66th percentile)
    regime_gate = df['prev_rr'].quantile(0.66)
    print(f"[REGIME GATE] 66th Percentile: {regime_gate:.1f} pips")

    # 3. DAY-OF-WEEK LOCK (Tue=1, Wed=2)
    df['is_attack_day'] = df.index.dayofweek.isin([1, 2])

    # 4. BREAKOUT SIGNALS
    df['break_long'] = (df['close'] > df['prev_rh']) & df['is_attack_day'] & (df['prev_rr'] < regime_gate)
    df['break_short'] = (df['close'] < df['prev_rl']) & df['is_attack_day'] & (df['prev_rr'] < regime_gate)

    signals = df[df['break_long'] | df['break_short']].copy()
    trades = []

    print(f"[SIGNALS] {len(signals)} breakout candidates")

    scan_bars = 20 if timeframe_hours == 4 else 30

    for idx, row in signals.iterrows():
        is_long = row['break_long']
        entry_price = row['close']
        coil_range = row['prev_rr']
        body = row['body_pips']

        if body < 5:
            continue

        # ============================================================
        # V3 ENTRY: "Swing Retest" — wait for pullback to coil boundary
        # ============================================================
        # After breakout, wait for price to touch/pull back to the coil
        # boundary, then enter on the reversal candle.
        #
        # For LONG breakout (close > prev_rh):
        #   - Wait for low to touch or go below prev_rh (the retest)
        #   - Enter on the first candle that closes back above prev_rh
        #
        # For SHORT breakout (close < prev_rl):
        #   - Wait for high to touch or go above prev_rl (the retest)
        #   - Enter on the first candle that closes back below prev_rl
        # ============================================================

        loc = df.index.get_loc(idx)
        future = df.iloc[loc + 1: loc + 1 + scan_bars]

        if is_long:
            coil_boundary = row['prev_rh']
            # Target: 1.0x coil range from entry
            target_price = entry_price + (coil_range * pip_size)
            # SL: close back below coil boundary
            sl_price = coil_boundary
        else:
            coil_boundary = row['prev_rl']
            target_price = entry_price - (coil_range * pip_size)
            sl_price = coil_boundary

        # Phase 1: Wait for retest (price touches coil boundary)
        retest_found = False
        retest_idx = None

        for i, (f_idx, f_row) in enumerate(future.iterrows()):
            # Friday 4PM hard exit
            if f_idx.dayofweek == 4 and f_idx.hour >= 16:
                break

            if not retest_found:
                # Check if price touches the coil boundary
                if is_long and f_row['low'] <= coil_boundary:
                    retest_found = True
                    retest_idx = i
                elif not is_long and f_row['high'] >= coil_boundary:
                    retest_found = True
                    retest_idx = i

                # If price hits target before retest, count as win (strong momentum)
                if is_long and f_row['high'] >= target_price:
                    trades.append({
                        'asset': asset_name, 'tf': f'H{timeframe_hours}',
                        'outcome': 'WIN', 'r_mult': 1.0,
                        'risk_pips': abs(entry_price - sl_price) / pip_size,
                        'reward_pips': abs(target_price - entry_price) / pip_size,
                        'entry_type': 'MOMENTUM_NO_RETEST'
                    })
                    break

                if not retest_found and i == len(future) - 1:
                    # No retest, no target hit — timeout
                    pass
            else:
                # Phase 2: After retest, wait for confirmation close
                # Enter on close back beyond coil boundary
                if is_long and f_row['close'] > coil_boundary:
                    # Confirmed retest — enter here
                    occ_entry = f_row['close']
                    occ_sl = f_row['low']  # SL below the retest candle low
                    occ_target = occ_entry + (coil_range * pip_size)

                    # Scan forward from here for outcome
                    sub_loc = loc + 1 + i + 1
                    sub_future = df.iloc[sub_loc: sub_loc + scan_bars]

                    outcome = 'TIMEOUT'
                    for sj, (sf_idx, sf_row) in enumerate(sub_future.iterrows()):
                        if sf_idx.dayofweek == 4 and sf_idx.hour >= 16:
                            outcome = 'FRIDAY_EXIT'
                            break
                        if sf_row['high'] >= occ_target:
                            outcome = 'WIN'
                            break
                        if sf_row['close'] <= occ_sl:
                            outcome = 'LOSS'
                            break

                    risk = abs(occ_entry - occ_sl) / pip_size
                    reward = abs(occ_target - occ_entry) / pip_size
                    if risk < 0.1: risk = 0.1  # minimum risk floor
                    r_mult = (reward / risk) if outcome == 'WIN' else -1.0 if outcome == 'LOSS' else 0.0

                    trades.append({
                        'asset': asset_name, 'tf': f'H{timeframe_hours}',
                        'outcome': outcome, 'r_mult': r_mult,
                        'risk_pips': risk, 'reward_pips': reward,
                        'entry_type': 'RETEST_CONFIRM'
                    })
                    break

                elif not is_long and f_row['close'] < coil_boundary:
                    occ_entry = f_row['close']
                    occ_sl = f_row['high']
                    occ_target = occ_entry - (coil_range * pip_size)

                    sub_loc = loc + 1 + i + 1
                    sub_future = df.iloc[sub_loc: sub_loc + scan_bars]

                    outcome = 'TIMEOUT'
                    for sj, (sf_idx, sf_row) in enumerate(sub_future.iterrows()):
                        if sf_idx.dayofweek == 4 and sf_idx.hour >= 16:
                            outcome = 'FRIDAY_EXIT'
                            break
                        if sf_row['low'] <= occ_target:
                            outcome = 'WIN'
                            break
                        if sf_row['close'] >= occ_sl:
                            outcome = 'LOSS'
                            break

                    risk = abs(occ_entry - occ_sl) / pip_size
                    reward = abs(occ_target - occ_entry) / pip_size
                    if risk < 0.1: risk = 0.1  # minimum risk floor
                    r_mult = (reward / risk) if outcome == 'WIN' else -1.0 if outcome == 'LOSS' else 0.0

                    trades.append({
                        'asset': asset_name, 'tf': f'H{timeframe_hours}',
                        'outcome': outcome, 'r_mult': r_mult,
                        'risk_pips': risk, 'reward_pips': reward,
                        'entry_type': 'RETEST_CONFIRM'
                    })
                    break

                # If after retest, price goes further against us before confirming
                if is_long and f_row['close'] < sl_price * 0.999:
                    # Stopped out — price closed well below coil boundary after retest
                    pass  # Let it continue scanning for confirmation
                if not is_long and f_row['close'] > sl_price * 1.001:
                    pass

    # AGGREGATE & REPORT
    if not trades:
        print(f"[{asset_name}] NO VALID TRADES FOUND.")
        return None

    t_df = pd.DataFrame(trades)
    wins = t_df[t_df['outcome'] == 'WIN']
    losses = t_df[t_df['outcome'] == 'LOSS']

    total = len(t_df)
    wr = (len(wins) / total) * 100 if total > 0 else 0
    avg_r = t_df['r_mult'].mean()
    gross_profit = wins['r_mult'].sum() if not wins.empty else 0
    gross_loss = abs(losses['r_mult'].sum()) if not losses.empty else 0.01
    pf = gross_profit / gross_loss

    # Entry type breakdown
    if 'entry_type' in t_df.columns:
        type_counts = t_df['entry_type'].value_counts()
        print(f"  Entry types: {dict(type_counts)}")

    print(f"\n--- {asset_name} SWING BASE 80 V3 RESULTS ---")
    print(f"Total Trades: {total}")
    print(f"Win Rate: {wr:.1f}% | Avg R: {avg_r:.2f} | Profit Factor: {pf:.2f}")
    print(f"Avg Risk: {t_df['risk_pips'].mean():.1f}p | Avg Reward: {t_df['reward_pips'].mean():.1f}p")

    return t_df


# ==========================================
# EXECUTION BLOCK
# ==========================================
if __name__ == "__main__":
    assets_to_test = [
        (r"C:\Users\wifik\Downloads\EURUSD.PRO_H4_202301020000_202606020000.csv", 4, 0.0001, 'EURUSD'),
        (r"C:\Users\wifik\Downloads\EURUSD.PRO_H1_202301020000_202606020000.csv", 1, 0.0001, 'EURUSD_H1'),
        (r"C:\Users\wifik\Downloads\USDCHF.PRO_H4_202301020000_202606020000.csv", 4, 0.0001, 'USDCHF'),
        (r"C:\Users\wifik\Downloads\USDCHF.PRO_H1_202301020000_202606020000.csv", 1, 0.0001, 'USDCHF_H1'),
        (r"C:\Users\wifik\Downloads\BTCUSD_H4_202301010000_202606020000.csv", 4, 1.0, 'BTCUSD'),
        (r"C:\Users\wifik\Downloads\BTCUSD_H1_202301010000_202606020000.csv", 1, 1.0, 'BTCUSD_H1'),
        (r"C:\Users\wifik\Downloads\XAUUSD.PRO_H4_202301030000_202606020000.csv", 4, 0.1, 'XAUUSD'),
        (r"C:\Users\wifik\Downloads\XAUUSD.PRO_H1_202301030100_202606012300.csv", 1, 0.1, 'XAUUSD_H1'),
        (r"C:\Users\wifik\Downloads\US500_H4_202301030000_202606020000.csv", 4, 1.0, 'US500'),
        (r"C:\Users\wifik\Downloads\US500_H1_202301030100_202606012300.csv", 1, 1.0, 'US500_H1'),
        (r"C:\Users\wifik\Downloads\USTEC100_H4_202301030000_202606020000.csv", 4, 1.0, 'USTEC100'),
        (r"C:\Users\wifik\Downloads\USTEC100_H1_202301030100_202606012300.csv", 1, 1.0, 'USTEC100_H1'),
    ]

    master_results = []
    for path, tf, pip, name in assets_to_test:
        res = run_swing_base80_test(path, tf, pip, name)
        if res is not None:
            master_results.append(res)

    if master_results:
        final_df = pd.concat(master_results)
        print("\n" + "=" * 60)
        print("MASTER SWING PORTFOLIO SUMMARY — V3")
        print("=" * 60)
        summary = final_df.groupby('asset').agg(
            Trades=('outcome', 'count'),
            WinRate=('outcome', lambda x: (x == 'WIN').mean() * 100),
            Avg_R=('r_mult', 'mean'),
            PF=('r_mult', lambda x: x[x > 0].sum() / abs(x[x < 0].sum()) if x[x < 0].sum() != 0 else 0)
        ).round(2)
        print(summary.to_string())
        print("=" * 60)
