"""
Backtest CEREBUS Symmetry Option B Strategy
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def run_backtest():
    # Connect to MT5
    if not mt5.initialize():
        print('MT5 initialize failed')
        return
    
    # Get EURUSD data - M5 for 3 months
    rates = mt5.copy_rates_from_pos('EURUSD', mt5.TIMEFRAME_M5, 0, 5000)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    print(f'Data range: {df["time"].min()} to {df["time"].max()}')
    print(f'Total bars: {len(df)}')
    
    # CEREBUS Strategy Simulation
    # Parameters
    T1_Trig = 12  # pips
    T2_Trig = 15
    T3_Trig = 19
    T1_Atom = 10
    T2_Atom = 12
    T3_Atom = 15
    
    # State variables
    asian_high = 0
    asian_low = 0
    asian_active = False
    tier = 1
    tier_ok = False
    reference_price = 0
    impulse_hit = False
    impulse_extreme = 0
    position = 0  # 0 = flat, 1 = long, -1 = short
    entry_price = 0
    sl_price = 0
    tp_price = 0
    
    trades = []
    equity = [10000]
    
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # Check Asian session (19:00-03:00 EST)
        est_hour = (row['time'].hour - 5 + 24) % 24
        was_asian = asian_active
        asian_active = (est_hour >= 19 or est_hour < 3)
        
        if not was_asian and asian_active:
            asian_high = row['high']
            asian_low = row['low']
            reference_price = (asian_high + asian_low) / 2
        elif asian_active:
            asian_high = max(asian_high, row['high'])
            asian_low = min(asian_low, row['low'])
        
        # Asian session ended - determine tier
        if was_asian and not asian_active and not tier_ok:
            ar_pips = (asian_high - asian_low) / 0.00010  # Convert to pips
            if ar_pips < 20:
                tier = 1
            elif ar_pips <= 30:
                tier = 2
            elif ar_pips <= 45:
                tier = 3
            else:
                tier = 0  # NO-GO
            tier_ok = True
            reference_price = row['close']
        
        if tier == 0:
            continue
        
        # Check 12PM EST hard exit
        if est_hour >= 12:
            if position != 0:
                # Close position
                pnl = (row['close'] - entry_price) * 100000 * position
                equity.append(equity[-1] + pnl)
                trades.append({'type': 'EXIT', 'price': row['close'], 'pnl': pnl})
                position = 0
            continue
        
        # Get tier thresholds
        trig = [T1_Trig, T2_Trig, T3_Trig][tier-1] if tier > 0 else 0
        atom = [T1_Atom, T2_Atom, T3_Atom][tier-1] if tier > 0 else 0
        trig_points = trig * 0.00010
        
        # Detect impulse
        if not impulse_hit and reference_price > 0:
            dist_up = row['high'] - reference_price
            dist_down = reference_price - row['low']
            
            if dist_down >= trig_points:
                impulse_hit = True
                impulse_extreme = row['low']
            elif dist_up >= trig_points:
                impulse_hit = True
                impulse_extreme = row['high']
        
        # Detect rejection and enter
        if impulse_hit and position == 0:
            rejection = 0.00005
            
            if impulse_extreme > reference_price:  # Bearish impulse
                if row['low'] < impulse_extreme - rejection:
                    # Enter SHORT
                    position = -1
                    entry_price = row['close']
                    sl_price = impulse_extreme + (impulse_extreme - reference_price) * 0.8
                    tp_price = entry_price - atom * 0.00010
                    trades.append({'type': 'SELL', 'price': entry_price, 'sl': sl_price, 'tp': tp_price})
                    impulse_hit = False
            elif impulse_extreme < reference_price:  # Bullish impulse
                if row['high'] > impulse_extreme + rejection:
                    # Enter LONG
                    position = 1
                    entry_price = row['close']
                    sl_price = impulse_extreme - (reference_price - impulse_extreme) * 0.8
                    tp_price = entry_price + atom * 0.00010
                    trades.append({'type': 'BUY', 'price': entry_price, 'sl': sl_price, 'tp': tp_price})
                    impulse_hit = False
        
        # Check SL/TP
        if position != 0:
            if position == 1 and (row['low'] <= sl_price or row['high'] >= tp_price):
                pnl = (tp_price if row['high'] >= tp_price else sl_price - entry_price) * 100000
                equity.append(equity[-1] + pnl)
                trades.append({'type': 'EXIT', 'price': tp_price if row['high'] >= tp_price else sl_price, 'pnl': pnl})
                position = 0
            elif position == -1 and (row['high'] >= sl_price or row['low'] <= tp_price):
                pnl = (entry_price - (tp_price if row['low'] <= tp_price else sl_price)) * 100000
                equity.append(equity[-1] + pnl)
                trades.append({'type': 'EXIT', 'price': tp_price if row['low'] <= tp_price else sl_price, 'pnl': pnl})
                position = 0
    
    # Results
    total_pnl = equity[-1] - 10000
    print(f'\n=== BACKTEST RESULTS ===')
    print(f'Final Equity: ${equity[-1]:.2f}')
    print(f'Net P&L: ${total_pnl:.2f}')
    print(f'Total Trades: {len([t for t in trades if t["type"] != "EXIT"])}')
    print(f'Win Rate: {len([t for t in trades if t.get("pnl", 0) > 0]) / max(1, len([t for t in trades if "pnl" in t])) * 100:.1f}%')
    
    mt5.shutdown()

if __name__ == '__main__':
    run_backtest()