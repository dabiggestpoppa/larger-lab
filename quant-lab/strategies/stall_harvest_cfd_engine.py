# -*- coding: utf-8 -*-
"""
Stall-Harvest CFD Engine (Strategy #3)
========================================
Manual Reference: CEREBUS FX v4 Part 4 - Stall-Harvest Trading System
Target Stats: 86% WR, ~1.66 PF, Expected Weekly Return +38-48R

CONCEPT:
When the resolution output touches the 168% Stall Zone, it often stalls
(before either continuing or reversing). The Stall-Harvest captures the
move AFTER the stall — it enters WITH the direction of resolution at the
168% limit level, riding the continuation.

This is NOT mean reversion. It plays the CONTINUATION after the stall.

Stall Zone characteristics:
- 34.2% of P90s reach Stall Zone State (168% within 35 min)
- 65.8% of P90s expand through (168% NOT hit)
- 86% of stall events result in profitable expansion or rebalancing

Session Windows (EST):
- 2-4 AM: 94.2% WR, 31.1% stall rate (best)
- 4-7 AM: 88.6% WR, 35.4% stall rate
- 7-11 AM: 82.4% WR, 38.2% stall rate

CFD Execution Protocol:
1. LIMIT ACTIVATION at 168% Stall Zone
   - Bullish: Low - (Body x 1.68)  [below the candle low]
   - Bearish: High + (Body x 1.68)  [above the candle high]
2. BOUNDARY (SL) at 200% Deep State + 1.5x candle body buffer
3. TARGET: -50% Daily Range (reward-to-risk 1:4 to 1:6)

Position Sizing:
1. S1 (40%): 80% Fib Constraint Boundary
2. S2 (40%): 1.5x Constraint Boundary
3. S3 (20%): 45-min add activation

Kill Switches:
- Asian Range > 45pips: NO-GO
- 132% Kill-Switch State: Close All
- After 11 AM EST: No new activations
- M5 close beyond 200% Deep State: Abort

Distinction from P90 CFD Expansion:
- P90 CFD: Enter AT P90 close (momentum from breakout)
- Stall-Harvest: Enter AT 168% stall zone (continuation AFTER stall)
- The P90 candle signals direction; the stall zone is the entry level
"""
import sys, json, os
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import *
import pandas as pd
import numpy as np
from datetime import date, datetime

STRATEGY_NAME = "stall_harvest_cfd_v1"
TARGET_STATS = {
    'win_rate_pct': 86.0,
    'profit_factor': 1.66,
    'note': '86% WR, ~1.66 PF, EURUSD.PRO 2024-2025'
}

SPREAD_COST = 0.5  # pips

# Session stall rates and WR by time-of-day (from manual)
SESSION_PROFILES = {
    # 2-4 AM: best session
    'early': {'est_range': (2, 4), 'stall_rate': 0.311, 'wr': 0.942},
    # 4-7 AM: good session
    'mid':   {'est_range': (4, 7), 'stall_rate': 0.354, 'wr': 0.886},
    # 7-11 AM: okay session
    'late':  {'est_range': (7, 11), 'stall_rate': 0.382, 'wr': 0.824},
}


def compute_stall_zone_levels(p90_low, p90_high, p90_body, direction):
    """
    Compute 168% Stall Zone and 200% Deep State levels.
    
    For a BULLISH P90 (close > open):
    - 168% Stall Zone = Low - (Body × 1.68) [below the low]
    - 200% Deep State = Low - (Body × 2.00)
    
    For a BEARISH P90 (close < open):
    - 168% Stall Zone = High + (Body × 1.68) [above the high]
    - 200% Deep State = High + (Body × 2.00)
    """
    body_price = p90_body / 10000.0
    
    if direction == 1:  # Bullish P90
        stall_zone = p90_low - body_price * 1.68
        deep_state = p90_low - body_price * 2.00
        sl_level = deep_state - body_price * 1.50  # 200% + 1.5x body buffer
    else:  # Bearish P90
        stall_zone = p90_high + body_price * 1.68
        deep_state = p90_high + body_price * 2.00
        sl_level = deep_state + body_price * 1.50  # 200% + 1.5x body buffer
    
    return {
        'stall_zone': stall_zone,
        'deep_state': deep_state,
        'sl_level': sl_level,
    }


def get_session_tier(est_hour):
    """Classify current bar into session tier"""
    if 2 <= est_hour < 4:
        return 'early'
    elif 4 <= est_hour < 7:
        return 'mid'
    elif 7 <= est_hour < 11:
        return 'late'
    return None


def run_day(day_bars, ar_info):
    """
    Process one trading day for Stall-Harvest CFD.
    Returns (session_trades, lot_trades).
    
    Key: We need price to TOUCH the 168% stall zone for activation.
    Once touched, we enter at the stall zone level (limit order fill).
    """
    sessions = []
    lots = []

    ah = ar_info['ah']
    al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    tier = ar_info['tier']
    date_key = ar_info.get('date_key', None)

    if tier == 'NO_GO' or ar_pips < 3:
        return sessions, lots

    # Asian range > 45p = NO-GO (same as all CEREBUS strategies)

    tier_mult = {'T1': 1.0, 'T2': 0.75, 'T3': 0.50}.get(tier, 0.0)
    if tier_mult == 0:
        return sessions, lots

    # Monday reduction
    monday_mult = 1.0
    if date_key is not None:
        from datetime import date as dt_date
        if isinstance(date_key, str):
            date_key = dt_date.fromisoformat(date_key)
        if date_key.weekday() == 0:
            monday_mult = 0.75

    # Daily range target (for TP)
    # T1: ~72p expected daily range, T2: ~58p, T3: ~48p
    daily_range_est = {'T1': 72.0, 'T2': 58.0, 'T3': 48.0}.get(tier, 60.0)
    tp_move = (daily_range_est * 0.50) / 10000.0  # TP = -50% daily range

    # State variables
    direction = 0              # 0=none, +1=long, -1=short
    active = False             # Is position active?
    entry_price = 0.0
    stall_zone_level = 0.0
    deep_state_level = 0.0
    sl_level = 0.0
    p90_detected = False
    p90_body_pips = 0.0
    p90_direction = 0
    stall_touched = False      # Has price touched 168% stall zone?
    limit_filled = False       # Has limit order been filled?
    active_lots = []
    regime_mult = 1.0

    for _, bar in day_bars.iterrows():
        eh = int(bar['est_hour'])
        bar_close = bar['close']
        bar_high = bar['high']
        bar_low = bar['low']

        # No new activations after 11AM
        if eh >= 11 and not active:
            continue
        if eh >= 11 and active:
            # Hold existing position but no new entries
            pass

        # === REGIME CHECK at 8AM ===
        if eh == 8 and not p90_detected:
            bars_so_far = day_bars[day_bars['est_hour'] <= 8]
            if len(bars_so_far) > 0:
                dr = (bars_so_far['high'].max() - bars_so_far['low'].min()) * 10000.0
                if ar_pips > 0 and dr / ar_pips < 1.5:
                    regime_mult = 0.5

        # === HARD EXIT at 12PM ===
        if eh >= HARD_EXIT_EST and active_lots:
            for lot in active_lots:
                pnl = (bar_close - lot['price']) * direction * 10000.0 - SPREAD_COST
                lots.append({
                    'date': str(bar['est_date']), 'direction': direction,
                    'entry_price': lot['price'], 'exit_price': bar_close,
                    'pnl_pips': pnl, 'exit_reason': 'hard_exit_12pm',
                    'signal_type': lot['signal_type'], 'tier': tier,
                })
            session_pnl = sum(l['pnl_pips'] for l in lots if l['date'] == str(bar['est_date']))
            sessions.append({
                'date': str(bar['est_date']), 'direction': direction,
                'session_pnl_pips': session_pnl, 'n_lots': len(lots),
                'tier': tier, 'session': 'unknown', 'exit_reason': 'hard_exit_12pm',
            })
            active_lots = []
            direction = 0
            active = False
            limit_filled = False
            stall_touched = False
            continue

        # === KILL SWITCH: M5 close beyond 200% Deep State ===
        if limit_filled and active_lots:
            if direction == 1 and bar_close < deep_state_level:
                # Bullish: close fell below deep state → abort
                for lot in active_lots:
                    pnl = (bar_close - lot['price']) * 10000.0 - SPREAD_COST
                    lots.append({
                        'date': str(bar['est_date']), 'direction': 1,
                        'entry_price': lot['price'], 'exit_price': bar_close,
                        'pnl_pips': pnl, 'exit_reason': 'kill_state_200',
                        'signal_type': lot['signal_type'], 'tier': tier,
                    })
                session_pnl = sum(l['pnl_pips'] for l in lots if l['date'] == str(bar['est_date']))
                sessions.append({
                    'date': str(bar['est_date']), 'direction': 1,
                    'session_pnl_pips': session_pnl, 'n_lots': len(lots),
                    'tier': tier, 'session': 'unknown', 'exit_reason': 'kill_state_200',
                })
                active_lots = []
                direction = 0
                active = False
                limit_filled = False
                continue
            elif direction == -1 and bar_close > deep_state_level:
                for lot in active_lots:
                    pnl = (lot['price'] - bar_close) * 10000.0 - SPREAD_COST
                    lots.append({
                        'date': str(bar['est_date']), 'direction': -1,
                        'entry_price': lot['price'], 'exit_price': bar_close,
                        'pnl_pips': pnl, 'exit_reason': 'kill_state_200',
                        'signal_type': lot['signal_type'], 'tier': tier,
                    })
                session_pnl = sum(l['pnl_pips'] for l in lots if l['date'] == str(bar['est_date']))
                sessions.append({
                    'date': str(bar['est_date']), 'direction': -1,
                    'session_pnl_pips': session_pnl, 'n_lots': len(lots),
                    'tier': tier, 'session': 'unknown', 'exit_reason': 'kill_state_200',
                })
                active_lots = []
                direction = 0
                active = False
                limit_filled = False
                continue

        # === 132% KILL SWITCH ===
        if limit_filled and active_lots:
            kill_move = (ar_pips * 1.32) / 10000.0
            if direction == 1:
                kill_level = entry_price + kill_move
                if bar_close > kill_level:
                    for lot in active_lots:
                        pnl = (kill_level - lot['price']) * 10000.0 - SPREAD_COST
                        lots.append({
                            'date': str(bar['est_date']), 'direction': 1,
                            'entry_price': lot['price'], 'exit_price': kill_level,
                            'pnl_pips': pnl, 'exit_reason': 'kill_switch_132',
                            'signal_type': lot['signal_type'], 'tier': tier,
                        })
                    active_lots = []
                    direction = 0
                    active = False
                    limit_filled = False
                    continue
            elif direction == -1:
                kill_level = entry_price - kill_move
                if bar_close < kill_level:
                    for lot in active_lots:
                        pnl = (lot['price'] - kill_level) * 10000.0 - SPREAD_COST
                        lots.append({
                            'date': str(bar['est_date']), 'direction': -1,
                            'entry_price': lot['price'], 'exit_price': kill_level,
                            'pnl_pips': pnl, 'exit_reason': 'kill_switch_132',
                            'signal_type': lot['signal_type'], 'tier': tier,
                        })
                    active_lots = []
                    direction = 0
                    active = False
                    limit_filled = False
                    continue

        # === TP MANAGEMENT ===
        if limit_filled and active_lots:
            tp_level = entry_price + direction * tp_move
            if (direction == 1 and bar_high >= tp_level) or \
               (direction == -1 and bar_low <= tp_level):
                for lot in active_lots:
                    pnl = (tp_level - lot['price']) * direction * 10000.0 - SPREAD_COST
                    lots.append({
                        'date': str(bar['est_date']), 'direction': direction,
                        'entry_price': lot['price'], 'exit_price': tp_level,
                        'pnl_pips': pnl, 'exit_reason': 'tp_-50pct_daily',
                        'signal_type': lot['signal_type'], 'tier': tier,
                    })
                session_pnl = sum(l['pnl_pips'] for l in lots if l['date'] == str(bar['est_date']))
                sessions.append({
                    'date': str(bar['est_date']), 'direction': direction,
                    'session_pnl_pips': session_pnl, 'n_lots': len(lots),
                    'tier': tier, 'session': 'unknown', 'exit_reason': 'tp',
                })
                active_lots = []
                direction = 0
                active = False
                limit_filled = False
                continue

        # === SL CHECK ===
        if limit_filled and active_lots:
            sl_triggered = False
            if direction == 1 and bar_low <= sl_level:
                sl_triggered = True
            elif direction == -1 and bar_high >= sl_level:
                sl_triggered = True

            if sl_triggered:
                exit_p = sl_level if direction == 1 else sl_level
                for lot in active_lots:
                    pnl = (exit_p - lot['price']) * direction * 10000.0 - SPREAD_COST
                    lots.append({
                        'date': str(bar['est_date']), 'direction': direction,
                        'entry_price': lot['price'], 'exit_price': exit_p,
                        'pnl_pips': pnl, 'exit_reason': 'sl_deep_state',
                        'signal_type': lot['signal_type'], 'tier': tier,
                    })
                session_pnl = sum(l['pnl_pips'] for l in lots if l['date'] == str(bar['est_date']))
                sessions.append({
                    'date': str(bar['est_date']), 'direction': direction,
                    'session_pnl_pips': session_pnl, 'n_lots': len(lots),
                    'tier': tier, 'session': 'unknown', 'exit_reason': 'sl',
                })
                active_lots = []
                direction = 0
                active = False
                limit_filled = False
                continue

        # === STALL ZONE TOUCH DETECTION ===
        if stall_touched and not limit_filled and p90_detected:
            # Check if price has touched the stall zone level
            if direction == 1 and bar_low <= stall_zone_level:
                # Bullish: price touched stall zone below → limit filled
                limit_filled = True
                entry_price = stall_zone_level
                size_mult = tier_mult * regime_mult * monday_mult

                active_lots.append({
                    'price': stall_zone_level, 'size_pct': 0.4 * size_mult,
                    'sl': sl_level, 'signal_type': 'stall_signal1'
                })
                active_lots.append({
                    'price': stall_zone_level, 'size_pct': 0.4 * size_mult,
                    'sl': sl_level, 'signal_type': 'stall_signal2'
                })
            elif direction == -1 and bar_high >= stall_zone_level:
                limit_filled = True
                entry_price = stall_zone_level
                size_mult = tier_mult * regime_mult * monday_mult

                active_lots.append({
                    'price': stall_zone_level, 'size_pct': 0.4 * size_mult,
                    'sl': sl_level, 'signal_type': 'stall_signal1'
                })
                active_lots.append({
                    'price': stall_zone_level, 'size_pct': 0.4 * size_mult,
                    'sl': sl_level, 'signal_type': 'stall_signal2'
                })

        # === P90 DETECTION — triggers stall zone setup ===
        if eh >= P90_WINDOW_START_EST and eh < P90_WINDOW_END_EST:
            is_p90, p90_dir, body_pips = detect_p90(bar)
            if not is_p90:
                continue

            bar_status = classify_p90_relative_to_barrier(bar, ah, al)
            if bar_status not in ('above', 'below'):
                continue

            signal_dir = 1 if bar_status == 'above' else -1

            # Only take first P90 in session (sets bias)
            if not p90_detected:
                p90_detected = True
                p90_body_pips = body_pips
                p90_direction = signal_dir
                direction = signal_dir

                # Compute stall zone levels
                levels = compute_stall_zone_levels(bar_low, bar_high, body_pips, signal_dir)
                stall_zone_level = levels['stall_zone']
                deep_state_level = levels['deep_state']
                sl_level = levels['sl_level']

                # Mark stall as watching (not yet touched)
                stall_touched = False

                # Check if stall zone is already touched on this bar
                if direction == 1 and bar_low <= stall_zone_level:
                    stall_touched = True
                elif direction == -1 and bar_high >= stall_zone_level:
                    stall_touched = True

    return sessions, lots


def run_stall_harvest_backtest(df, start_date=None, end_date=None):
    if start_date:
        df = df[df['est_date'] >= start_date]
    if end_date:
        df = df[df['est_date'] <= end_date]

    all_sessions = []
    all_lots = []
    days_processed = 0

    for date_key in sorted(df['est_date'].unique()):
        day_bars = df[df['est_date'] == date_key].sort_values('timestamp').reset_index(drop=True)
        if len(day_bars) < 10:
            continue

        ar_info = compute_asian_range(df, date_key)
        if ar_info is None:
            continue
        ar_info['date_key'] = date_key

        sess, lots = run_day(day_bars, ar_info)
        if sess:
            all_sessions.extend(sess)
        if lots:
            all_lots.extend(lots)
        days_processed += 1

    return all_sessions, all_lots, days_processed


def compute_session_stats(sessions, strategy_name):
    if not sessions:
        return {'error': 'no sessions'}
    df = pd.DataFrame(sessions)
    wins = df[df['session_pnl_pips'] > 0]
    losses = df[df['session_pnl_pips'] <= 0]
    total = len(df)
    win_rate = len(wins) / total * 100.0
    gross_profit = wins['session_pnl_pips'].sum() if len(wins) > 0 else 0
    gross_loss = abs(losses['session_pnl_pips'].sum()) if len(losses) > 0 else 0.001
    pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    total_pips = df['session_pnl_pips'].sum()
    avg_r = df['session_pnl_pips'].mean()
    return {
        'strategy': strategy_name,
        'total_sessions': total,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate_pct': round(win_rate, 1),
        'profit_factor': round(pf, 2),
        'total_pips': round(total_pips, 1),
        'avg_pips_per_session': round(avg_r, 2),
    }


if __name__ == "__main__":
    print("=" * 60)
    print("STALL-HARVEST CFD ENGINE v1 — Backtest")
    print("=" * 60)

    df = load_data()
    print("\nRunning 2024-2025...")
    sessions, lots, days = run_stall_harvest_backtest(df, date(2024, 1, 1), date(2025, 12, 31))

    if not lots:
        print("No trades generated!")
        sys.exit(1)

    lot_df = pd.DataFrame(lots)
    lot_stats = compute_stats(lot_df, STRATEGY_NAME)
    print(f"\n--- LOT-LEVEL ---")
    print(f"Days: {days}, Lots: {lot_stats['total_trades']}, "
          f"WR: {lot_stats['win_rate_pct']}%, Pips: {lot_stats['total_pips']}")

    if sessions:
        sess_stats = compute_session_stats(sessions, STRATEGY_NAME)
        print(f"\n--- SESSION-LEVEL ---")
        print(f"Sessions: {sess_stats['total_sessions']}")
        print(f"Win Rate: {sess_stats['win_rate_pct']}% (target: 86%)")
        print(f"PF: {sess_stats['profit_factor']} (target: 1.66)")
        print(f"Total Pips: {sess_stats['total_pips']}")
        print(f"Avg pips/session: {sess_stats['avg_pips_per_session']}")

        sess_df = pd.DataFrame(sessions)
        print("\nExit Breakdown:")
        for reason, count in sess_df['exit_reason'].value_counts().items():
            avg = sess_df[sess_df['exit_reason'] == reason]['session_pnl_pips'].mean()
            wr = (sess_df[sess_df['exit_reason'] == reason]['session_pnl_pips'] > 0).mean() * 100
            print(f"  {reason}: {count}, avg {avg:.1f}p, WR {wr:.0f}%")

        print("\nTier Breakdown:")
        for t in sorted(sess_df['tier'].unique()):
            tf = sess_df[sess_df['tier'] == t]
            wr = (tf['session_pnl_pips'] > 0).mean() * 100
            print(f"  {t}: {len(tf)}, WR {wr:.1f}%, avg {tf['session_pnl_pips'].mean():.1f}p")

        sess_df['year'] = pd.to_datetime(sess_df['date']).dt.year
        print("\nYearly:")
        for y in sorted(sess_df['year'].unique()):
            yf = sess_df[sess_df['year'] == y]
            wr = (yf['session_pnl_pips'] > 0).mean() * 100
            print(f"  {y}: {len(yf)}, WR {wr:.1f}%, total {yf['session_pnl_pips'].sum():.1f}p")

        report_path = write_report(STRATEGY_NAME, sess_stats, TARGET_STATS, lot_df)
        print(f"\nReport: {report_path}")
        sess_path = REPORTS_DIR / f"{STRATEGY_NAME}_sessions.csv"
        sess_df.to_csv(sess_path, index=False)
    else:
        print("No sessions generated!")
