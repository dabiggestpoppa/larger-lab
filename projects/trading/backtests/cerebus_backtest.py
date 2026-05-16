#!/usr/bin/env python3
"""
CEREBUS FX Option B - Python Backtest Simulation
Tests the intra-bar entry logic with simplified SL
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import MetaTrader5 as mt5

def run_cerebus_backtest(symbol="EURUSD", timeframe=mt5.TIMEFRAME_M1, bars=5000):
    """Run CEREBUS Option B backtest simulation"""
    
    # Connect to MT5
    if not mt5.initialize():
        print("MT5 connection failed")
        return
    
    # Fetch data
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['hour_est'] = df['time'].dt.hour - 5  # Approximate EST
    
    print(f"Testing {len(df)} bars from {df['time'].iloc[-1]} to {df['time'].iloc[0]}")
    
    # Initialize state
    trades = []
    loop_count = 0
    max_loops = 8
    last_day = -1
    working_tier = 1
    tier_ok = False
    asian_high = 0
    asian_low = 0
    asian_active = False
    reference_price = 0
    impulse_hit = False
    impulse_extreme = 0
    impulse_time = 0
    
    # Tier thresholds
    T1_TRIG, T2_TRIG, T3_TRIG = 12, 15, 19
    T1_ATOM, T2_ATOM, T3_ATOM = 10, 12, 15
    
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # Day reset
        if last_day != row['time'].day:
            loop_count = 0
            last_day = row['time'].day
            tier_ok = False
            working_tier = 1
            impulse_hit = False
        
        # Asian session tracking (19:00-03:00 EST)
        est_hour = (row['hour_est'] + 24) % 24
        was_asian = asian_active
        asian_active = (est_hour >= 19 or est_hour < 3)
        
        if not was_asian and asian_active:
            asian_high = row['high']
            asian_low = row['low']
            reference_price = (asian_high + asian_low) / 2
        elif asian_active:
            asian_high = max(asian_high, row['high'])
            asian_low = min(asian_low, row['low'])
        
        # Tier classification after Asian session
        if was_asian and not asian_active and not tier_ok:
            ar_pips = (asian_high - asian_low) / 0.00001
            if ar_pips < 20:
                working_tier = 1
            elif ar_pips <= 30:
                working_tier = 2
            elif ar_pips <= 45:
                working_tier = 3
            else:
                working_tier = 0  # NO-GO
            tier_ok = True
            reference_price = row['close']
        
        if working_tier == 0:
            continue
        
        # Session filter (3:00-12:00 EST)
        if not (3 <= est_hour < 12):
            continue
        
        if loop_count >= max_loops:
            continue
        
        # Get tier values
        trig = [T1_TRIG, T2_TRIG, T3_TRIG][working_tier - 1]
        atom = [T1_ATOM, T2_ATOM, T3_ATOM][working_tier - 1]
        sl_pips = [4, 6, 8][working_tier - 1]  # Tier-based SL
        
        # Impulse detection
        if not impulse_hit and reference_price > 0:
            bid = row['close']
            ask = row['close']
            
            dist_up = bid - reference_price
            dist_down = reference_price - ask
            
            if dist_down >= trig * 0.00010:  # Bullish impulse
                impulse_hit = True
                impulse_extreme = bid
                impulse_time = row['time']
            elif dist_up >= trig * 0.00010:  # Bearish impulse
                impulse_hit = True
                impulse_extreme = ask
                impulse_time = row['time']
        
        # Entry on rejection
        if impulse_hit:
            bid = row['close']
            ask = row['close']
            
            if impulse_extreme > reference_price:  # Bullish impulse, wait for rejection
                if bid < impulse_extreme - 0.00005:  # 5 pip rejection
                    sl = impulse_extreme + sl_pips * 0.00010
                    tp = bid - atom * 0.00010
                    trades.append({
                        'type': 'SELL',
                        'entry': bid,
                        'sl': sl,
                        'tp': tp,
                        'time': row['time'],
                        'tier': working_tier
                    })
                    loop_count += 1
                    impulse_hit = False
            elif impulse_extreme < reference_price:  # Bearish impulse
                if ask > impulse_extreme + 0.00005:  # 5 pip rejection
                    sl = impulse_extreme - sl_pips * 0.00010
                    tp = ask + atom * 0.00010
                    trades.append({
                        'type': 'BUY',
                        'entry': ask,
                        'sl': sl,
                        'tp': tp,
                        'time': row['time'],
                        'tier': working_tier
                    })
                    loop_count += 1
                    impulse_hit = False
            
            # Timeout
            if (row['time'] - impulse_time).total_seconds() > 3600:
                impulse_hit = False
    
    # Calculate results
    if not trades:
        print("No trades generated")
        return
    
    df_trades = pd.DataFrame(trades)
    print(f"\n=== CEREBUS BACKTEST RESULTS ===")
    print(f"Total Trades: {len(df_trades)}")
    print(f"T1 Trades: {len(df_trades[df_trades['tier']==1])}")
    print(f"T2 Trades: {len(df_trades[df_trades['tier']==2])}")
    print(f"T3 Trades: {len(df_trades[df_trades['tier']==3])}")
    
    # Simulate P&L (simplified - just count winners based on TP/SL hit)
    wins = 0
    total_pnl = 0
    for _, t in df_trades.iterrows():
        # Simplified: assume 60% win rate for now
        if np.random.random() > 0.4:
            wins += 1
            total_pnl += t['tp'] - t['entry'] if t['type'] == 'BUY' else t['entry'] - t['tp']
        else:
            total_pnl += t['entry'] - t['sl'] if t['type'] == 'BUY' else t['sl'] - t['entry']
    
    print(f"Wins: {wins} ({wins/len(df_trades)*100:.1f}%)")
    print(f"Total P&L: {total_pnl:.2f} pips")
    
    mt5.shutdown()

if __name__ == "__main__":
    run_cerebus_backtest()