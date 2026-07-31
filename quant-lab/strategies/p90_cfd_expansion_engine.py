"""
P90 CFD Expansion Engine (Strategy #1)
========================================
Manual Reference: CEREBUS FX v4 Part 1, Section 3
Target Stats: 85-90% WR, ~1.78 PF

Logic:
1. Asian Range: 7PM-3AM EST, lock at 3AM
2. P90 Window: 2AM-11AM EST, body >= threshold
3. Entry: On P90 candle CLOSE outside Asian band
   - Signal 1 (40%): at P90 close
   - Signal 2 (40%): simultaneous add at P90 close (same candle, larger size)
   - Signal 3 (20%): +45 min add if price extended +8 pips
4. SL: 80% of P90 body from entry (Signal 1&2), Breakeven+2p (Signal 3)
5. TP1: -25% of Asian Range (close 50%)
6. TP2: -50% of Asian Range (close remaining)
7. Hard Exit: 12PM EST - close ALL
8. Kill Switch: 132% Asian Range violation
9. Regime filter: at 8:45AM, if daily range < 1.5x Asian range, reduce size 50%
"""
import sys, json
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import *
import pandas as pd
import numpy as np

STRATEGY_NAME = "p90_cfd_expansion_engine"
TARGET_STATS = {
    'win_rate_pct': 87.5,  # midpoint of 85-90%
    'profit_factor': 1.78,
    'note': '85-90% WR, ~1.78 PF, EURUSD.PRO 2024-2025'
}

def p90_cfd_expansion_day(day_bars, ar_info):
    """
    Process one trading day for the P90 CFD Expansion Engine.
    Returns list of trade dicts.
    """
    trades = []
    
    ah = ar_info['ah']
    al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    tier = ar_info['tier']
    
    if tier == 'NO_GO':
        return trades
    
    # Size multiplier based on tier
    tier_mult = {'T1': 1.0, 'T2': 0.75, 'T3': 0.50}.get(tier, 0.0)
    if tier_mult == 0:
        return trades
    
    # TP levels
    tp1_price_move = (ar_pips * 0.25) / 10000.0
    tp2_price_move = (ar_pips * 0.50) / 10000.0
    
    # Kill switch level (132% of Asian Range)
    if ar_info.get('direction', 1) >= 0:  # We'll determine from first P90
        kill_zone_bull = ah + (ar_pips * 1.32) / 10000.0
        kill_zone_bear = al - (ar_pips * 1.32) / 10000.0
    
    state = {
        'direction': 0,       # 0=none, +1=LONG, -1=SHORT
        'signals_fired': 0,
        'tp1_hit': False,
        'tp2_hit': False,
        'kill_switch': False,
        'p90_price': 0.0,
        'p90_body_pips': 0.0,
        'p90_time': None,
        'regime_confirmed': True,  # default, updated at 8:45AM
        'first_entry_price': 0.0,
        'active_positions': 0,    # number of lots (each = tier_mult * 0.01 lot)
        'sl_level': 0.0,
        'entries': [],            # list of (price, size_pct, sl_level)
        'peak_favorable': 0.0,    # peak favorable move in pips
    }
    
    for _, bar in day_bars.iterrows():
        eh = int(bar['est_hour'])
        
        # --- Regime check at 8:45AM (EST hour 8) ---
        if eh == 8 and not state['tp1_hit']:
            daily_high = day_bars[day_bars['est_hour'] <= 8]['high'].max()
            daily_low = day_bars[day_bars['est_hour'] <= 8]['low'].min()
            daily_range_pips = (daily_high - daily_low) * 10000.0
            if ar_pips > 0 and daily_range_pips / ar_pips < 1.5:
                state['regime_confirmed'] = False
        
        # --- Hard Exit at 12PM EST ---
        if eh >= HARD_EXIT_EST and state['active_positions'] > 0:
            exit_price = bar['close']
            for entry in state['entries']:
                pnl = (exit_price - entry['price']) * state['direction'] * 10000.0
                spread_cost = 0.5  # 0.5 pip spread cost
                pnl -= spread_cost
                trades.append({
                    'date': str(bar['est_date']),
                    'direction': state['direction'],
                    'entry_price': entry['price'],
                    'exit_price': exit_price,
                    'pnl_pips': pnl,
                    'exit_reason': 'hard_exit_12pm',
                    'signal_type': entry['signal_type'],
                    'tier': tier,
                })
            state['active_positions'] = 0
            state['entries'] = []
            continue
        
        # --- Kill Switch check ---
        if state['active_positions'] > 0:
            kill_level_long = ah + (ar_pips * 1.32) / 10000.0
            kill_level_short = al - (ar_pips * 1.32) / 10000.0
            
            if state['direction'] == 1 and bar['close'] > kill_level_long:
                # Kill switch triggered - close all
                for entry in state['entries']:
                    pnl = (kill_level_long - entry['price']) * 10000.0 - 0.5
                    trades.append({
                        'date': str(bar['est_date']),
                        'direction': 1,
                        'entry_price': entry['price'],
                        'exit_price': kill_level_long,
                        'pnl_pips': pnl,
                        'exit_reason': 'kill_switch_132',
                        'signal_type': entry['signal_type'],
                        'tier': tier,
                    })
                state['active_positions'] = 0
                state['entries'] = []
                continue
            
            if state['direction'] == -1 and bar['close'] < kill_level_short:
                for entry in state['entries']:
                    pnl = (entry['price'] - kill_level_short) * 10000.0 - 0.5
                    trades.append({
                        'date': str(bar['est_date']),
                        'direction': -1,
                        'entry_price': entry['price'],
                        'exit_price': kill_level_short,
                        'pnl_pips': pnl,
                        'exit_reason': 'kill_switch_132',
                        'signal_type': entry['signal_type'],
                        'tier': tier,
                    })
                state['active_positions'] = 0
                state['entries'] = []
                continue
        
        # --- TP Management ---
        if state['active_positions'] > 0:
            direction = state['direction']
            entry_price = state['first_entry_price']
            
            tp1 = entry_price + direction * tp1_price_move
            tp2 = entry_price + direction * tp2_price_move
            
            current_pnl_pips = (bar['close'] - entry_price) * direction * 10000.0
            state['peak_favorable'] = max(state['peak_favorable'], current_pnl_pips)
            
            if not state['tp1_hit']:
                if (direction == 1 and bar['high'] >= tp1) or \
                   (direction == -1 and bar['low'] <= tp1):
                    state['tp1_hit'] = True
                    # Close 50% of positions
                    half = len(state['entries']) // 2
                    if half == 0 and len(state['entries']) > 0:
                        half = 1
                    for i, entry in enumerate(state['entries']):
                        if i < half:
                            pnl = (tp1 - entry['price']) * direction * 10000.0 - 0.5
                            trades.append({
                                'date': str(bar['est_date']),
                                'direction': direction,
                                'entry_price': entry['price'],
                                'exit_price': tp1,
                                'pnl_pips': pnl,
                                'exit_reason': 'tp1_ar25',
                                'signal_type': entry['signal_type'],
                                'tier': tier,
                            })
                    state['entries'] = state['entries'][half:]
                    state['active_positions'] = len(state['entries'])
                    # Move SL to breakeven
                    for e in state['entries']:
                        e['sl_level'] = entry_price
            
            if state['tp1_hit'] and not state['tp2_hit']:
                if (direction == 1 and bar['high'] >= tp2) or \
                   (direction == -1 and bar['low'] <= tp2):
                    state['tp2_hit'] = True
                    # Close all remaining
                    for entry in state['entries']:
                        pnl = (tp2 - entry['price']) * direction * 10000.0 - 0.5
                        trades.append({
                            'date': str(bar['est_date']),
                            'direction': direction,
                            'entry_price': entry['price'],
                            'exit_price': tp2,
                            'pnl_pips': pnl,
                            'exit_reason': 'tp2_ar50',
                            'signal_type': entry['signal_type'],
                            'tier': tier,
                        })
                    state['active_positions'] = 0
                    state['entries'] = []
                    continue
            
            # --- SL Check ---
            if state['active_positions'] > 0 and not state['tp1_hit']:
                for entry in state['entries'][:]:
                    sl = entry['sl_level']
                    if (direction == 1 and bar['low'] <= sl) or \
                       (direction == -1 and bar['high'] >= sl):
                        pnl = (sl - entry['price']) * direction * 10000.0 - 0.5
                        trades.append({
                            'date': str(bar['est_date']),
                            'direction': direction,
                            'entry_price': entry['price'],
                            'exit_price': sl,
                            'pnl_pips': pnl,
                            'exit_reason': 'sl_80pct_body',
                            'signal_type': entry['signal_type'],
                            'tier': tier,
                        })
                        state['entries'].remove(entry)
                        state['active_positions'] = len(state['entries'])
        
        # --- P90 Detection & Entry ---
        if P90_WINDOW_START_EST <= eh < P90_WINDOW_END_EST and state['active_positions'] < 3:
            is_p90, p90_dir, body_pips = detect_p90(bar)
            
            if is_p90:
                # Check close outside Asian band
                bar_status = classify_p90_relative_to_barrier(bar, ah, al)
                
                above = bar_status == 'above'
                below = bar_status == 'below'
                
                if not above and not below:
                    continue
                
                signal_dir = 1 if above else -1
                
                # First P90 sets direction
                if state['direction'] == 0:
                    state['direction'] = signal_dir
                    state['p90_price'] = bar['close']
                    state['p90_body_pips'] = body_pips
                    state['p90_time'] = bar['timestamp']
                    state['first_entry_price'] = bar['close']
                    state['peak_favorable'] = 0.0
                    
                    # Signal 1 (40%) + Signal 2 (40%) at P90 close
                    reg_mult = 1.0 if state['regime_confirmed'] else 0.5
                    size = tier_mult * reg_mult
                    
                    sl_dist = body_pips * 0.80 / 10000.0
                    sl_level = bar['close'] - signal_dir * sl_dist
                    
                    # Signal 1
                    entry1 = {'price': bar['close'], 'size_pct': 0.4 * size,
                              'sl_level': sl_level, 'signal_type': 'signal1'}
                    state['entries'].append(entry1)
                    
                    # Signal 2 (simultaneous)
                    entry2 = {'price': bar['close'], 'size_pct': 0.4 * size,
                              'sl_level': sl_level, 'signal_type': 'signal2'}
                    state['entries'].append(entry2)
                    
                    state['active_positions'] = len(state['entries'])
                    state['signals_fired'] = 2
                
                elif signal_dir == state['direction']:
                    # Same direction P90 - cascade check
                    if state['p90_time'] is not None:
                        elapsed = (bar['timestamp'] - state['p90_time']).total_seconds() / 60.0
                        if elapsed <= 120 and state['signals_fired'] < 4:
                            # Cascade P90 - same direction
                            reg_mult = 1.0 if state['regime_confirmed'] else 0.5
                            size = tier_mult * reg_mult
                            
                            # Size: 2nd cascade = 20%, 3rd cascade = 10%
                            if state['signals_fired'] == 2:
                                pct = 0.2
                            else:
                                pct = 0.1
                            
                            # For cascade: SL = 168% of THIS P90 body (wider)
                            sl_dist = body_pips * 1.68 / 10000.0
                            sl_level = bar['close'] - signal_dir * sl_dist
                            
                            entry = {'price': bar['close'], 'size_pct': pct * size,
                                     'sl_level': sl_level, 'signal_type': f'cascade_{state["signals_fired"]}'}
                            state['entries'].append(entry)
                            state['active_positions'] = len(state['entries'])
                            state['signals_fired'] += 1
                
                # 45-min add check
                if state['p90_time'] is not None and state['signals_fired'] == 2:
                    elapsed = (bar['timestamp'] - state['p90_time']).total_seconds() / 60.0
                    if 40 <= elapsed <= 50 and not state.get('add45_fired', False):
                        current_move = (bar['close'] - state['first_entry_price']) * state['direction'] * 10000.0
                        if current_move >= 8.0:
                            reg_mult = 1.0 if state['regime_confirmed'] else 0.5
                            size = tier_mult * reg_mult
                            entry = {'price': bar['close'], 'size_pct': 0.2 * size,
                                     'sl_level': state['first_entry_price'] + 2.0/10000.0 * state['direction'],
                                     'signal_type': 'add_45min'}
                            state['entries'].append(entry)
                            state['active_positions'] = len(state['entries'])
                            state['signals_fired'] = 3
                            state['add45_fired'] = True
    
    return trades


def run_p90_cfd_backtest(df, start_date=None, end_date=None):
    """Run the P90 CFD Expansion Engine backtest"""
    if start_date:
        df = df[df['est_date'] >= start_date]
    if end_date:
        df = df[df['est_date'] <= end_date]
    
    all_trades = []
    days_processed = 0
    
    for date_key in sorted(df['est_date'].unique()):
        day_bars = df[df['est_date'] == date_key].sort_values('timestamp').reset_index(drop=True)
        if len(day_bars) < 10:
            continue
        
        ar_info = compute_asian_range(df, date_key)
        if ar_info is None:
            continue
        
        # Determine direction from first P90 of the day for kill switch
        first_p90_dir = 0
        for _, bar in day_bars.iterrows():
            eh = int(bar['est_hour'])
            if P90_WINDOW_START_EST <= eh < P90_WINDOW_END_EST:
                is_p90, p90_dir, body_pips = detect_p90(bar)
                if is_p90:
                    bar_status = classify_p90_relative_to_barrier(bar, ar_info['ah'], ar_info['al'])
                    if bar_status in ('above', 'below'):
                        first_p90_dir = 1 if bar_status == 'above' else -1
                        break
        ar_info['direction'] = first_p90_dir
        
        trades = p90_cfd_expansion_day(day_bars, ar_info)
        if trades:
            all_trades.extend(trades)
        days_processed += 1
    
    return all_trades, days_processed


if __name__ == "__main__":
    print("="*60)
    print("P90 CFD EXPANSION ENGINE - Backtest")
    print("="*60)
    
    df = load_data()
    
    print("\nRunning on 2024-2025 data...")
    all_trades, days = run_p90_cfd_backtest(df, date(2024, 1, 1), date(2025, 12, 31))
    
    if not all_trades:
        print("No trades generated!")
        sys.exit(1)
    
    trades_df = pd.DataFrame(all_trades)
    stats = compute_stats(trades_df, STRATEGY_NAME)
    
    print(f"\nDays processed: {days}")
    print(f"Total trades: {stats['total_trades']}")
    print(f"Win Rate: {stats['win_rate_pct']}% (target: 85-90%)")
    print(f"Profit Factor: {stats['profit_factor']} (target: ~1.78)")
    print(f"Total Pips: {stats['total_pips']}")
    print(f"Avg pips/trade: {stats['avg_pips_per_trade']}")
    
    # Write report
    report_path = write_report(STRATEGY_NAME, stats, TARGET_STATS, trades_df)
    print(f"\nReport: {report_path}")
    
    # Print exit reason breakdown
    print("\nExit Reason Breakdown:")
    for reason, count in trades_df['exit_reason'].value_counts().items():
        avg = trades_df[trades_df['exit_reason']==reason]['pnl_pips'].mean()
        print(f"  {reason}: {count} trades, avg {avg:.1f} pips")
