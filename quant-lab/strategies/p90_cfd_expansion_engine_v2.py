# -*- coding: utf-8 -*-
"""
P90 CFD Expansion Engine v2 (Strategy #1)
==========================================
Manual Reference: CEREBUS FX v4 Part 1, Section 3 + P90_STRATEGY_GUIDE.md
Target Stats: 85-90% WR, ~1.78 PF

CRITICAL: This is a MOMENTUM strategy — enter WITH the P90 breakout direction.
The P90 candle breaks out of the Asian band → ride the expansion.

Logic:
1. Asian Range: 7PM-3AM EST (19:00-03:00), lock at 3AM
2. Tier classification: T1<20p / T2 20-30p / T3 30-45p / NO-GO >45p
3. P90 Window: 2AM-11AM EST, body >= threshold, close OUTSIDE Asian band
4. Entry: WITH P90 direction (momentum, not mean reversion)
   - Signal 1 (40%): at P90 close, SL = 80% of P90 body
   - Signal 2 (40%): simultaneous, SL = 1.5x P90 body
   - Signal 3 (+45min, 30%): if price extended +8p from entry, SL = breakeven
5. TP1: entry - 25% of Asian Range (in P90 direction) → close 50%
6. TP2: entry - 50% of Asian Range → close remaining
7. Hard Exit: 12PM EST
8. Kill Switch: 132% of Asian Range violation
9. Opposite P90 = trim/exit, NOT reverse
"""
import sys, json, os
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import *
import pandas as pd
import numpy as np
from datetime import date, datetime

STRATEGY_NAME = "p90_cfd_expansion_v2"
TARGET_STATS = {
    'win_rate_pct': 87.5,  # midpoint of 85-90%
    'profit_factor': 1.78,
    'note': '85-90% WR, ~1.78 PF, EURUSD.PRO 2024-2025'
}

# P90 time thresholds (same as DMR)
P90_THRESH = {2:4.1, 3:4.1, 4:4.6, 5:4.6, 6:4.6, 7:5.9, 8:5.9, 9:6.2, 10:6.2}

def run_day(day_bars, ar_info):
    """Process one trading day. Returns list of closed trade dicts."""
    trades = []
    
    ah = ar_info['ah']   # Asian high
    al = ar_info['al']   # Asian low
    ar_pips = ar_info['ar_pips']
    tier = ar_info['tier']
    
    if tier == 'NO_GO' or ar_pips < 3:
        return trades
    
    tier_mult = {'T1': 1.0, 'T2': 0.75, 'T3': 0.50}.get(tier, 0.0)
    if tier_mult == 0:
        return trades
    
    # TP levels (from entry, in P90 direction)
    # LONG: TP above entry. SHORT: TP below entry.
    tp1_move = (ar_pips * 0.25) / 10000.0  # 25% of AR
    tp2_move = (ar_pips * 0.50) / 10000.0  # 50% of AR
    
    # Kill switch: 132% of AR from Asian band edge
    kill_above = ah + (ar_pips * 1.32) / 10000.0
    kill_below = al - (ar_pips * 1.32) / 10000.0
    
    # State
    direction = 0        # 0=none, +1=LONG, -1=SHORT
    entry_price = 0.0
    p90_body_pips = 0.0
    p90_time = None
    signals_fired = 0
    tp1_hit = False
    sl_level = 0.0       # active SL
    active_lots = []     # list of {'price','size_pct','sl'}
    total_size = 0.0
    add45_fired = False
    cascade_count = 0
    opposite_p90_seen = False
    prev_date = None
    
    for _, bar in day_bars.iterrows():
        eh = int(bar['est_hour'])
        spread_cost = 0.5  # pips
        
        # --- Opposite P90 detection (trim/exit, not reverse) ---
        if direction != 0 and eh >= P90_WINDOW_START_EST and eh < P90_WINDOW_END_EST:
            is_p90, p90_dir, body_pips = detect_p90(bar)
            if is_p90 and p90_dir == -direction:
                bar_status = classify_p90_relative_to_barrier(bar, ah, al)
                if bar_status in ('above', 'below'):
                    # Opposite P90 — exit ALL immediately (do NOT reverse)
                    for lot in active_lots:
                        pnl = (bar['close'] - lot['price']) * direction * 10000.0 - spread_cost
                        trades.append({
                            'date': str(bar['est_date']),
                            'direction': direction,
                            'entry_price': lot['price'],
                            'exit_price': bar['close'],
                            'pnl_pips': pnl,
                            'exit_reason': 'opposite_p90_exit',
                            'signal_type': lot['signal_type'],
                            'tier': tier,
                        })
                    active_lots = []
                    total_size = 0.0
                    direction = 0
                    continue
        
        # --- Regime check at 8AM EST ---
        regime_confirmed = True
        if eh == 8 and direction == 0:
            bars_so_far = day_bars[day_bars['est_hour'] <= 8]
            if len(bars_so_far) > 0:
                dr = (bars_so_far['high'].max() - bars_so_far['low'].min()) * 10000.0
                if ar_pips > 0 and dr / ar_pips < 1.5:
                    regime_confirmed = False
        
        # --- Overfilled check at 9AM EST ---
        if eh == 9 and direction == 0:
            bars_so_far = day_bars[day_bars['est_hour'] <= 9]
            if len(bars_so_far) > 0:
                dr = (bars_so_far['high'].max() - bars_so_far['low'].min()) * 10000.0
                if dr > 40 and tier in ('T2', 'T3'):
                    # STAND DOWN for T2/T3
                    continue
                if dr > 40 and tier == 'T1':
                    tier_mult = 0.5  # reduce to 50%
        
        # --- Hard Exit at 12PM EST ---
        if eh >= HARD_EXIT_EST and active_lots:
            for lot in active_lots:
                pnl = (bar['close'] - lot['price']) * direction * 10000.0 - spread_cost
                trades.append({
                    'date': str(bar['est_date']),
                    'direction': direction,
                    'entry_price': lot['price'],
                    'exit_price': bar['close'],
                    'pnl_pips': pnl,
                    'exit_reason': 'hard_exit_12pm',
                    'signal_type': lot['signal_type'],
                    'tier': tier,
                })
            active_lots = []
            total_size = 0.0
            continue
        
        # --- Kill Switch ---
        if active_lots:
            if direction == 1 and bar['close'] > kill_above:
                for lot in active_lots:
                    pnl = (kill_above - lot['price']) * 10000.0 - spread_cost
                    trades.append({
                        'date': str(bar['est_date']), 'direction': 1,
                        'entry_price': lot['price'], 'exit_price': kill_above,
                        'pnl_pips': pnl, 'exit_reason': 'kill_switch_132',
                        'signal_type': lot['signal_type'], 'tier': tier,
                    })
                active_lots = []
                total_size = 0.0
                continue
            if direction == -1 and bar['close'] < kill_below:
                for lot in active_lots:
                    pnl = (lot['price'] - kill_below) * 10000.0 - spread_cost
                    trades.append({
                        'date': str(bar['est_date']), 'direction': -1,
                        'entry_price': lot['price'], 'exit_price': kill_below,
                        'pnl_pips': pnl, 'exit_reason': 'kill_switch_132',
                        'signal_type': lot['signal_type'], 'tier': tier,
                    })
                active_lots = []
                total_size = 0.0
                continue
        
        # --- TP Management ---
        if active_lots and not tp1_hit:
            tp1 = entry_price + direction * tp1_move
            if (direction == 1 and bar['high'] >= tp1) or \
               (direction == -1 and bar['low'] <= tp1):
                tp1_hit = True
                # Close 50% of lots, move SL to breakeven for rest
                close_n = max(1, len(active_lots) // 2)
                for lot in active_lots[:close_n]:
                    pnl = (tp1 - lot['price']) * direction * 10000.0 - spread_cost
                    trades.append({
                        'date': str(bar['est_date']), 'direction': direction,
                        'entry_price': lot['price'], 'exit_price': tp1,
                        'pnl_pips': pnl, 'exit_reason': 'tp1_ar25',
                        'signal_type': lot['signal_type'], 'tier': tier,
                    })
                active_lots = active_lots[close_n:]
                # Move SL to breakeven for remaining
                for lot in active_lots:
                    lot['sl'] = entry_price
        
        if tp1_hit and active_lots:
            tp2 = entry_price + direction * tp2_move
            if (direction == 1 and bar['high'] >= tp2) or \
               (direction == -1 and bar['low'] <= tp2):
                for lot in active_lots:
                    pnl = (tp2 - lot['price']) * direction * 10000.0 - spread_cost
                    trades.append({
                        'date': str(bar['est_date']), 'direction': direction,
                        'entry_price': lot['price'], 'exit_price': tp2,
                        'pnl_pips': pnl, 'exit_reason': 'tp2_ar50',
                        'signal_type': lot['signal_type'], 'tier': tier,
                    })
                active_lots = []
                total_size = 0.0
                continue
        
        # --- SL Check ---
        if active_lots and not tp1_hit:
            lots_to_keep = []
            for lot in active_lots:
                if direction == 1 and bar['low'] <= lot['sl']:
                    pnl = (lot['sl'] - lot['price']) * 10000.0 - spread_cost
                    trades.append({
                        'date': str(bar['est_date']), 'direction': 1,
                        'entry_price': lot['price'], 'exit_price': lot['sl'],
                        'pnl_pips': pnl,
                        'exit_reason': 'sl_body80' if lot['signal_type'] == 'signal1' else 'sl_body150',
                        'signal_type': lot['signal_type'], 'tier': tier,
                    })
                elif direction == -1 and bar['high'] >= lot['sl']:
                    pnl = (lot['price'] - lot['sl']) * 10000.0 - spread_cost
                    trades.append({
                        'date': str(bar['est_date']), 'direction': -1,
                        'entry_price': lot['price'], 'exit_price': lot['sl'],
                        'pnl_pips': pnl,
                        'exit_reason': 'sl_body80' if lot['signal_type'] == 'signal1' else 'sl_body150',
                        'signal_type': lot['signal_type'], 'tier': tier,
                    })
                else:
                    lots_to_keep.append(lot)
            active_lots = lots_to_keep
            if not active_lots:
                total_size = 0.0
                continue
        
        # --- P90 Detection & Entry ---
        if eh < P90_WINDOW_START_EST or eh >= P90_WINDOW_END_EST:
            continue
        if signals_fired >= 5:
            continue
        
        is_p90, p90_dir, body_pips = detect_p90(bar)
        if not is_p90:
            continue
        
        bar_status = classify_p90_relative_to_barrier(bar, ah, al)
        if bar_status not in ('above', 'below'):
            continue
        
        # MOMENTUM: direction = WITH P90 breakout
        # Above Asian band → LONG, Below Asian band → SHORT
        signal_dir = 1 if bar_status == 'above' else -1
        
        if direction == 0:
            # === INITIAL P90 ===
            direction = signal_dir
            entry_price = bar['close']
            p90_body_pips = body_pips
            p90_time = bar['timestamp']
            tp1_hit = False
            cascade_count = 0
            
            reg_mult = 1.0 if regime_confirmed else 0.5
            # Monday reduce 25% — simplified, apply based on date
            size_mult = tier_mult * reg_mult
            
            # Signal 1 (40%): SL = 80% of body from entry (behind entry)
            sl1 = bar['close'] - signal_dir * (body_pips * 0.80 / 10000.0)
            active_lots.append({'price': bar['close'], 'size_pct': 0.4 * size_mult, 'sl': sl1, 'signal_type': 'signal1'})
            
            # Signal 2 (40%): SL = 1.5x body (wider, for the risk-tolerant portion)
            sl2 = bar['close'] - signal_dir * (body_pips * 1.50 / 10000.0)
            active_lots.append({'price': bar['close'], 'size_pct': 0.4 * size_mult, 'sl': sl2, 'signal_type': 'signal2'})
            
            total_size = sum(l['size_pct'] for l in active_lots)
            signals_fired = 2
            
        elif signal_dir == direction and cascade_count < 3:
            # === CASCADE P90 (same direction) ===
            if p90_time is not None:
                elapsed = (bar['timestamp'] - p90_time).total_seconds() / 60.0
                if 30 <= elapsed <= 120:
                    cascade_count += 1
                    if cascade_count > 2:
                        continue  # avoid 4th+ cascade
                    
                    reg_mult = 1.0  # after initial, regime already set
                    size_mult = tier_mult * reg_mult
                    c_size = 0.2 if cascade_count == 1 else 0.1
                    
                    sl_c = bar['close'] - signal_dir * (body_pips * 1.68 / 10000.0)
                    active_lots.append({
                        'price': bar['close'], 'size_pct': c_size * size_mult,
                        'sl': sl_c, 'signal_type': f'cascade_{cascade_count}'
                    })
                    total_size = sum(l['size_pct'] for l in active_lots)
                    signals_fired += 1
        
        # --- 45-Min Add ---
        if p90_time is not None and signals_fired == 2 and not add45_fired:
            elapsed = (bar['timestamp'] - p90_time).total_seconds() / 60.0
            if 40 <= elapsed <= 50:
                current_move = (bar['close'] - entry_price) * direction * 10000.0
                if current_move >= 8.0:
                    reg_mult = 1.0 if regime_confirmed else 0.5
                    size_mult = tier_mult * reg_mult
                    active_lots.append({
                        'price': bar['close'], 'size_pct': 0.3 * size_mult,
                        'sl': entry_price,  # breakeven
                        'signal_type': 'add45min'
                    })
                    total_size = sum(l['size_pct'] for l in active_lots)
                    signals_fired = 3
                    add45_fired = True
    
    return trades


def run_p90_backtest(df, start_date=None, end_date=None):
    """Run P90 CFD Expansion v2 backtest"""
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
        
        trades = run_day(day_bars, ar_info)
        if trades:
            all_trades.extend(trades)
        days_processed += 1
    
    return all_trades, days_processed


if __name__ == "__main__":
    print("="*60)
    print("P90 CFD EXPANSION ENGINE v2 — Backtest")
    print("="*60)
    
    df = load_data()
    
    # Run full 2023-2026 (MAD: at least 2 years)    
    print("\nRunning full 2023-2026...")
    all_trades, days = run_p90_backtest(df, date(2023, 7, 1), date(2026, 5, 31))
    
    if not all_trades:
        print("No trades generated!")
        sys.exit(1)
    
    trades_df = pd.DataFrame(all_trades)
    stats = compute_stats(trades_df, STRATEGY_NAME)
    
    print(f"\nDays processed: {days}")
    print(f"Total trades (lots): {stats['total_trades']}")
    print(f"Win Rate: {stats['win_rate_pct']}% (target: 85-90%)")
    print(f"Profit Factor: {stats['profit_factor']} (target: ~1.78)")
    print(f"Total Pips: {stats['total_pips']}")
    print(f"Avg pips/trade: {stats['avg_pips_per_trade']}")
    
    # Exit reason breakdown
    print("\nExit Reason Breakdown:")
    for reason, count in trades_df['exit_reason'].value_counts().items():
        avg = trades_df[trades_df['exit_reason']==reason]['pnl_pips'].mean()
        wr = (trades_df[trades_df['exit_reason']==reason]['pnl_pips'] > 0).mean() * 100
        print(f"  {reason}: {count} trades, avg {avg:.1f}p, WR {wr:.0f}%")
    
    # Tier breakdown
    print("\nTier Breakdown:")
    for t in trades_df['tier'].unique():
        tf = trades_df[trades_df['tier']==t]
        print(f"  {t}: {len(tf)} trades, WR {((tf['pnl_pips']>0).mean()*100):.1f}%, avg {tf['pnl_pips'].mean():.1f}p")
    
    # Yearly
    trades_df['year'] = pd.to_datetime(trades_df['date']).dt.year
    print("\nYearly:")
    for y in sorted(trades_df['year'].unique()):
        yf = trades_df[trades_df['year']==y]
        print(f"  {y}: {len(yf)} trades, WR {((yf['pnl_pips']>0).mean()*100):.1f}%, total {yf['pnl_pips'].sum():.1f}p")
    
    report_path = write_report(STRATEGY_NAME, stats, TARGET_STATS, trades_df)
    print(f"\nReport: {report_path}")
