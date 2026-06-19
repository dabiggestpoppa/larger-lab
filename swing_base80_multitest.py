import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def run_swing_base80_test(csv_path, timeframe_hours, pip_size, asset_name):
    """
    CEREBUS SWING BASE 80 FILTER STACK TEST
    Scales the Symmetry Trap to H1/H4 using Rolling Volatility Coils.
    """
    print(f"\n{'='*20} INITIATING SWING BASE 80 TEST: {asset_name} (H{timeframe_hours}) {'='*20}")
    
    # 1. ROBUST MT5 DATA LOADER (tab-separated, skip header row)
    try:
        df = pd.read_csv(csv_path, sep='\t', skiprows=1,
                         names=['date', 'time', 'open', 'high', 'low', 'close', 'vol', 'spread', 'x'])
    except Exception as e:
        print(f"[ERROR] Failed to load {csv_path}: {e}")
        return None

    df['dt'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    df = df.set_index('dt').sort_index()
    df = df[~df.index.duplicated(keep='first')]
    
    # Ensure numeric types
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    
    print(f"Loaded {len(df)} bars. Range: {df.index[0]} -> {df.index[-1]}")
    
    # Calculate body and range in pips
    df['body_pips'] = (df['close'] - df['open']).abs() / pip_size
    df['is_bull'] = df['close'] > df['open']
    
    # 2. DEFINE THE COIL (ROLLING RANGE)
    # H4 = 8 bars (32h) | H1 = 24 bars (24h)
    lookback = 8 if timeframe_hours == 4 else 24
    
    df['rh'] = df['high'].rolling(window=lookback).max()
    df['rl'] = df['low'].rolling(window=lookback).min()
    df['rr_pips'] = (df['rh'] - df['rl']) / pip_size
    
    # Shift to get the PREVIOUS coil boundaries (The Step to break)
    df['prev_rh'] = df['rh'].shift(1)
    df['prev_rl'] = df['rl'].shift(1)
    df['prev_rr'] = df['rr_pips'].shift(1)
    
    # DYNAMIC REGIME GATE: Calculate 66th percentile of rolling ranges
    regime_gate_threshold = df['prev_rr'].quantile(0.66)
    print(f"[REGIME GATE] 66th Percentile (Swing T3 Boundary): {regime_gate_threshold:.1f} pips")
    
    # 3. APPLY FILTER 1: DAY-OF-WEEK LOCK (Tue/Wed Only)
    df['is_attack_day'] = df.index.dayofweek.isin([1, 2])
    
    # 4. IDENTIFY BREAKOUT CANDIDATES
    df['break_long'] = (df['close'] > df['prev_rh']) & df['is_attack_day'] & (df['prev_rr'] < regime_gate_threshold)
    df['break_short'] = (df['close'] < df['prev_rl']) & df['is_attack_day'] & (df['prev_rr'] < regime_gate_threshold)
    
    # 5. APPLY FILTER 3: 2-BAR HOLD CONFIRMATION
    df['hold_long'] = df['break_long'] & (df['close'].shift(1) > df['prev_rh'].shift(1))
    df['hold_short'] = df['break_short'] & (df['close'].shift(1) < df['prev_rl'].shift(1))
    
    signals = df[df['hold_long'] | df['hold_short']].copy()
    trades = []
    
    print(f"[FILTERS APPLIED] Testing {len(signals)} validated Swing Base 80 setups...")
    
    # 6. EXECUTE BINARY EXCURSION (DZ ENTRY & CLOSE-ONLY SL)
    for idx, row in signals.iterrows():
        is_long = row['hold_long']
        entry_price = row['close']
        coil_range_pips = row['prev_rr']
        breakout_body_pips = row['body_pips']
        
        # Skip if breakout candle is too small (noise)
        if breakout_body_pips < 5: continue
        
        # Calculate Density Zone (32% - 50% of breakout body)
        dz_upper = entry_price - (breakout_body_pips * 0.32 * pip_size * (1 if is_long else -1))
        dz_lower = entry_price - (breakout_body_pips * 0.50 * pip_size * (1 if is_long else -1))
        if not is_long:
            dz_upper, dz_lower = dz_lower, dz_upper
        
        # Trap Zone (>62% pullback invalidates the setup)
        trap_zone = entry_price - (breakout_body_pips * 0.62 * pip_size * (1 if is_long else -1))
        
        # Target: 1.5x the Coil Range (Macro Distribution)
        target_dist = coil_range_pips * 1.5 * pip_size
        target_price = entry_price + (target_dist * (1 if is_long else -1))
        
        # Stop Loss: EXACT OCC Extreme (Zero Buffer, Close-Only)
        sl_price = row['open'] if is_long else row['open']
        
        # Scan Forward: Up to 12 bars (48h for H4, 12h for H1) or Friday Close
        loc = df.index.get_loc(idx)
        future = df.iloc[loc+1 : loc+13]
        
        outcome = 'TIMEOUT'
        exit_price = entry_price
        occ_found = False
        occ_entry_price = None
        occ_sl_price = None
        
        for i, (f_idx, f_row) in enumerate(future.iterrows()):
            # Friday 12:00 PM EST Hard Exit
            if f_idx.dayofweek == 4 and f_idx.hour >= 16:
                outcome = 'FRIDAY_EXIT'; exit_price = f_row['close']; break
            
            if not occ_found:
                # Check Trap Zone (Close > 62% pullback)
                if is_long and f_row['close'] < trap_zone:
                    outcome = 'TRAP_ZONE'; break
                if not is_long and f_row['close'] > trap_zone:
                    outcome = 'TRAP_ZONE'; break
                
                # Check for OCC (Opposite candle closing inside DZ)
                is_opp_candle = (f_row['close'] < f_row['open']) if is_long else (f_row['close'] > f_row['open'])
                in_dz = dz_lower <= f_row['close'] <= dz_upper
                
                if is_opp_candle and in_dz:
                    occ_found = True
                    occ_entry_price = f_row['close']
                    occ_sl_price = f_row['low'] if is_long else f_row['high']
                    target_price = occ_entry_price + (target_dist * (1 if is_long else -1))
                    sl_price = occ_sl_price
                    continue
            else:
                # OCC FOUND: Now manage the trade
                if is_long and f_row['high'] >= target_price:
                    outcome = 'WIN'; exit_price = target_price; break
                if not is_long and f_row['low'] <= target_price:
                    outcome = 'WIN'; exit_price = target_price; break
                if is_long and f_row['close'] <= sl_price:
                    outcome = 'LOSS'; exit_price = sl_price; break
                if not is_long and f_row['close'] >= sl_price:
                    outcome = 'LOSS'; exit_price = sl_price; break
        
        if occ_found and outcome == 'TIMEOUT':
            outcome = 'TIMEOUT'
            exit_price = future.iloc[-1]['close'] if not future.empty else entry_price

        if occ_found:
            risk = abs(occ_entry_price - sl_price) / pip_size
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
    
    # 7. AGGREGATE & REPORT
    if not trades:
        print(f"[{asset_name}] NO VALID TRADES FOUND. Check pip_size or data density.")
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
    
    print(f"\n--- {asset_name} SWING BASE 80 RESULTS ---")
    print(f"Total Setups: {total_trades} | Trap Zones: {len(t_df[t_df['outcome']=='TRAP_ZONE'])}")
    print(f"Win Rate: {wr:.1f}% | Avg R: {avg_r:.2f} | Profit Factor: {pf:.2f}")
    print(f"Avg Risk: {t_df['risk_pips'].mean():.1f} pips | Avg Reward: {t_df['reward_pips'].mean():.1f} pips")
    
    return t_df

# ==========================================
# EXECUTION BLOCK -- ALL 12 FILES
# ==========================================
if __name__ == "__main__":
    assets_to_test = [
        # (CSV_PATH, TIMEFRAME_HOURS, PIP_SIZE, ASSET_NAME)
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
        print("\n" + "="*60)
        print("MASTER SWING PORTFOLIO SUMMARY")
        print("="*60)
        summary = final_df.groupby('asset').agg(
            Trades=('outcome', 'count'),
            WinRate=('outcome', lambda x: (x == 'WIN').mean() * 100),
            Avg_R=('r_mult', 'mean'),
            PF=('r_mult', lambda x: x[x > 0].sum() / abs(x[x < 0].sum()) if x[x < 0].sum() != 0 else 0)
        ).round(2)
        print(summary.to_string())
        print("="*60)
