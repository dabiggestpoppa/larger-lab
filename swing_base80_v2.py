import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def run_swing_base80_test(csv_path, timeframe_hours, pip_size, asset_name):
    """
    CEREBUS SWING BASE 80 FILTER STACK TEST — V2
    Fixes:
    1. DZ measured from full breakout leg (entry - coil boundary), not just body
    2. Trap zone scaled to full leg, not body
    3. Removed 2-bar hold (too aggressive for swing); breakout close IS the signal
    4. OCC scan window extended to 20 bars for H4 (80h), 30 for H1 (30h)
    """
    print(f"\n{'='*20} INITIATING SWING BASE 80 V2: {asset_name} (H{timeframe_hours}) {'='*20}")

    # 1. ROBUST MT5 DATA LOADER
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

    # 2. DEFINE THE COIL (ROLLING RANGE)
    lookback = 8 if timeframe_hours == 4 else 24

    df['rh'] = df['high'].rolling(window=lookback).max()
    df['rl'] = df['low'].rolling(window=lookback).min()
    df['rr_pips'] = (df['rh'] - df['rl']) / pip_size

    df['prev_rh'] = df['rh'].shift(1)
    df['prev_rl'] = df['rl'].shift(1)
    df['prev_rr'] = df['rr_pips'].shift(1)

    # DYNAMIC REGIME GATE
    regime_gate_threshold = df['prev_rr'].quantile(0.66)
    print(f"[REGIME GATE] 66th Percentile (Swing T3 Boundary): {regime_gate_threshold:.1f} pips")

    # 3. DAY-OF-WEEK LOCK (Tue/Wed Only)
    df['is_attack_day'] = df.index.dayofweek.isin([1, 2])

    # 4. BREAKOUT CANDIDATES (no 2-bar hold — breakout close IS the signal)
    df['break_long'] = (df['close'] > df['prev_rh']) & df['is_attack_day'] & (df['prev_rr'] < regime_gate_threshold)
    df['break_short'] = (df['close'] < df['prev_rl']) & df['is_attack_day'] & (df['prev_rr'] < regime_gate_threshold)

    signals = df[df['break_long'] | df['break_short']].copy()
    trades = []

    print(f"[FILTERS APPLIED] Testing {len(signals)} breakout signals...")

    # Scan window: 20 bars for H4 (80h), 30 bars for H1 (30h)
    scan_bars = 20 if timeframe_hours == 4 else 30

    for idx, row in signals.iterrows():
        is_long = row['break_long']
        entry_price = row['close']
        coil_range_pips = row['prev_rr']
        breakout_body_pips = row['body_pips']

        # Skip if breakout candle is too small (noise)
        if breakout_body_pips < 5:
            continue

        # ============================================================
        # FIX #1: DZ measured from FULL BREAKOUT LEG, not just body
        # The breakout leg = distance from coil boundary to entry
        # This is the actual "move" that price needs to retrace into
        # ============================================================
        if is_long:
            breakout_leg_pips = (entry_price - row['prev_rh']) / pip_size
            # For longs: leg = entry - prev_rh (how far above the coil high we closed)
            # If close is barely above, leg is small. If far above, leg is large.
            # Use the FULL leg from coil boundary to close
            leg_upper = entry_price
            leg_lower = row['prev_rh']
        else:
            breakout_leg_pips = (row['prev_rl'] - entry_price) / pip_size
            # For shorts: leg = prev_rl - entry (how far below the coil low we closed)
            leg_upper = row['prev_rl']
            leg_lower = entry_price

        # DZ = 32-50% retracement of the breakout leg
        # For long: DZ is between (entry - 50% of leg) and (entry - 32% of leg)
        # For short: DZ is between (entry + 32% of leg) and (entry + 50% of leg)
        leg_size = abs(leg_upper - leg_lower)

        dz_bound_far = entry_price - (leg_size * 0.50 * pip_size * (1 if is_long else -1))
        dz_bound_near = entry_price - (leg_size * 0.32 * pip_size * (1 if is_long else -1))

        if is_long:
            dz_lower = dz_bound_far
            dz_upper = dz_bound_near
        else:
            dz_lower = dz_bound_near
            dz_upper = dz_bound_far

        # ============================================================
        # FIX #2: Trap zone at 62% of FULL LEG (not body)
        # ============================================================
        trap_zone = entry_price - (leg_size * 0.62 * pip_size * (1 if is_long else -1))

        # Target: 1.5x the Coil Range
        target_dist = coil_range_pips * 1.5 * pip_size
        target_price = entry_price + (target_dist * (1 if is_long else -1))

        # Scan forward
        loc = df.index.get_loc(idx)
        future = df.iloc[loc + 1: loc + 1 + scan_bars]

        outcome = 'TIMEOUT'
        exit_price = entry_price
        occ_found = False
        occ_entry_price = None
        occ_sl_price = None

        for i, (f_idx, f_row) in enumerate(future.iterrows()):
            # Friday 4PM hard exit
            if f_idx.dayofweek == 4 and f_idx.hour >= 16:
                outcome = 'FRIDAY_EXIT'
                exit_price = f_row['close']
                break

            if not occ_found:
                # Check Trap Zone
                if is_long and f_row['close'] < trap_zone:
                    outcome = 'TRAP_ZONE'
                    break
                if not is_long and f_row['close'] > trap_zone:
                    outcome = 'TRAP_ZONE'
                    break

                # Check for OCC inside DZ
                is_opp_candle = (f_row['close'] < f_row['open']) if is_long else (f_row['close'] > f_row['open'])
                in_dz = dz_lower <= f_row['close'] <= dz_upper

                if is_opp_candle and in_dz:
                    occ_found = True
                    occ_entry_price = f_row['close']
                    occ_sl_price = f_row['low'] if is_long else f_row['high']
                    target_price = occ_entry_price + (target_dist * (1 if is_long else -1))
                    continue
            else:
                # Manage trade after OCC entry
                if is_long and f_row['high'] >= target_price:
                    outcome = 'WIN'
                    exit_price = target_price
                    break
                if not is_long and f_row['low'] <= target_price:
                    outcome = 'WIN'
                    exit_price = target_price
                    break
                if is_long and f_row['close'] <= occ_sl_price:
                    outcome = 'LOSS'
                    exit_price = occ_sl_price
                    break
                if not is_long and f_row['close'] >= occ_sl_price:
                    outcome = 'LOSS'
                    exit_price = occ_sl_price
                    break

        if occ_found and outcome == 'TIMEOUT':
            outcome = 'TIMEOUT'
            exit_price = future.iloc[-1]['close'] if not future.empty else entry_price

        if occ_found:
            risk = abs(occ_entry_price - occ_sl_price) / pip_size
            reward = abs(target_price - occ_entry_price) / pip_size
            r_mult = (reward / risk) if outcome == 'WIN' else -1.0 if outcome == 'LOSS' else 0.0

            trades.append({
                'asset': asset_name,
                'tf': f'H{timeframe_hours}',
                'outcome': outcome,
                'r_mult': r_mult,
                'risk_pips': risk,
                'reward_pips': reward
            })

    # AGGREGATE & REPORT
    if not trades:
        print(f"[{asset_name}] NO VALID TRADES FOUND.")
        return None

    t_df = pd.DataFrame(trades)
    wins = t_df[t_df['outcome'] == 'WIN']
    losses = t_df[t_df['outcome'] == 'LOSS']

    total_trades = len(t_df)
    wr = (len(wins) / total_trades) * 100 if total_trades > 0 else 0
    avg_r = t_df['r_mult'].mean()

    gross_profit = wins['r_mult'].sum() if not wins.empty else 0
    gross_loss = abs(losses['r_mult'].sum()) if not losses.empty else 0.01
    pf = gross_profit / gross_loss

    print(f"\n--- {asset_name} SWING BASE 80 V2 RESULTS ---")
    print(f"Total Trades: {total_trades} | Trap Zones: {len(t_df[t_df['outcome']=='TRAP_ZONE'])}")
    print(f"Win Rate: {wr:.1f}% | Avg R: {avg_r:.2f} | Profit Factor: {pf:.2f}")
    print(f"Avg Risk: {t_df['risk_pips'].mean():.1f} pips | Avg Reward: {t_df['reward_pips'].mean():.1f} pips")

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
        print("MASTER SWING PORTFOLIO SUMMARY — V2")
        print("=" * 60)
        summary = final_df.groupby('asset').agg(
            Trades=('outcome', 'count'),
            WinRate=('outcome', lambda x: (x == 'WIN').mean() * 100),
            Avg_R=('r_mult', 'mean'),
            PF=('r_mult', lambda x: x[x > 0].sum() / abs(x[x < 0].sum()) if x[x < 0].sum() != 0 else 0)
        ).round(2)
        print(summary.to_string())
        print("=" * 60)
