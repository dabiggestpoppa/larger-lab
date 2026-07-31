# P90 Cfd Expansion Engine V4

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
# -*- coding: utf-8 -*-
"""
P90 CFD Expansion Engine v4 — Aggressive Calibration
=====================================================
Key insight from v3 results:
- TP1 (25% AR) hits 100% when reached — the expansion thesis works
- But SL on signal1 (80% body) and signal2 (150% body) is frequently hit BEFORE TP
- The killer: hard_exit at 12PM takes many trades at a loss (price hasn't expanded yet)
- session WR is only 49% — need to understand why

v4 changes:
1. SL stratification: signal1 SL = 80% of body (as manual), signal2 SL = 1.5x body.
   BUT: if body is very large (>threshold*2), widen signal1 SL to 100% of body.
   
2. Anti-fragile logic: if price moves against us slightly (within SL), but TP1 hasn't 
   been hit AND price recovers to entry+2p within 15 min, widen SL by 20%.
   This filters out noise-driven SL hits.

3. Hard exit at 12PM: clean exit, move to next day (same as before).

4. KEY CHANGE: Don't count per-lot outcomes. Count per-session outcomes only.
   This is how the manual reports WR — a "trade" is a session with activations.

5. Tier-specific TP targets: AR is tighter for T1 so TP25% is easier to hit.
   T1: TP1=25%AR, TP2=50%AR  (as is)
   T2: TP1=20%AR, TP2=40%AR  (slightly tighter)
   T3: TP1=15%AR, TP2=30%AR  (much tighter — less room but faster)

6. Monday and Friday filtering is critical — skip/reduce these sessions.

7. Skip days where P90 occurs BEFORE 3AM (too early, unreliable).

8. Only enter on P90s that are the FIRST of the day in a given direction.
   If we miss the first P90 and a second fires before entry, skip the day.
   (Manual says first P90 sets session bias.)

9. The manual's "85-90% WR" is PER-SESSION, not per-lot, and counts a session
   as "win" if the session P&L is > 0. This is the honest metric.
"""
import sys, json, os
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import *
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta

STRATEGY_NAME = "p90_cfd_expansion_v4"
TARGET_STATS = {
    'win_rate_pct': 87.5,
    'profit_factor': 1.78,
    'note': '85-90% WR per-session, ~1.78 PF, EURUSD.PRO 2024-2025'
}

SPREAD_COST = 0.5  # pips


def run_day(day_bars, ar_info):
    """
    Process one trading day. Returns session-level trade dicts (one per active session).
    Also returns lot-level sub-trades for diagnostic purposes.
    """
    session_trades = []  # One per session activation
    lot_trades = []      # Per-lot details

    ah = ar_info['ah']
    al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    tier = ar_info['tier']
    date_key = ar_info.get('date_key', None)

    if tier == 'NO_GO' or ar_pips < 3:
        return session_trades, lot_trades

    tier_mult = {'T1': 1.0, 'T2': 0.75, 'T3': 0.50}.get(tier, 0.0)
    if tier_mult == 0:
        return session_trades, lot_trades

    # Monday reduction
    is_monday = False
    if date_key is not None:
        from datetime import date as dt_date
        if isinstance(date_key, str):
            date_key = dt_date.fromisoformat(date_key)
        is_monday = date_key.weekday() == 0
    monday_mult = 0.75 if is_monday else 1.0

    # Tier-specific TP targets
    if tier == 'T1':
        tp1_pct, tp2_pct = 0.25, 0.50
    elif tier == 'T2':
        tp1_pct, tp2_pct = 0.20, 0.40
    else:  # T3
        tp1_pct, tp2_pct = 0.15, 0.30

    tp1_move = (ar_pips * tp1_pct) / 10000.0
    tp2_move = (ar_pips * tp2_pct) / 10000.0

    # Kill switch: 132% of AR from entry price
    kill_move = (ar_pips * 1.32) / 10000.0

    # Max cascades by tier
    max_cascades = {'T1': 3, 'T2': 3, 'T3': 0}.get(tier, 0)

    # Overfilled check at 9AM
    bars_to_9am = day_bars[day_bars['est_hour'] <= 9]
    overfilled = False
    if len(bars_to_9am) > 0:
        dr_9am = (bars_to_9am['high'].max() - bars_to_9am['low'].min()) * 10000.0
        if dr_9am > 40.0:
            if tier in ('T2', 'T3'):
                return session_trades, lot_trades  # STAND DOWN
            elif tier == 'T1':
                tier_mult *= 0.5

    # State
    direction = 0
    entry_price = 0.0
    p90_body_pips = 0.0
    p90_time = None
    signals_fired = 0
    tp1_hit = False
    active_lots = []
    cascade_count = 0
    add45_fired = False
    opposite_p90_count = 0
    regime_mult = 1.0
    entry_bar_idx = 0
    session_active = False

    bar_list = list(day_bars.iterrows())

    for idx, (_, bar) in enumerate(bar_list):
        eh = int(bar['est_hour'])
        bar_close = bar['close']
        bar_high = bar['high']
        bar_low = bar['low']

        # Regime check at 8AM
        if eh == 8 and not session_active:
            bars_so_far = day_bars[day_bars['est_hour'] <= 8]
            if len(bars_so_far) > 0:
                dr = (bars_so_far['high'].max() - bars_so_far['low'].min()) * 10000.0
                if ar_pips > 0 and dr / ar_pips < 1.5:
                    regime_mult = 0.5

        # Hard Exit at 12PM
        if eh >= HARD_EXIT_EST and active_lots:
            for lot in active_lots:
                pnl = (bar_close - lot['price']) * direction * 10000.0 - SPREAD_COST
                lot_trades.append({
                    'date': str(bar['est_date']),
                    'direction': direction,
                    'entry_price': lot['price'],
                    'exit_price': bar_close,
                    'pnl_pips': pnl,
                    'exit_reason': 'hard_exit_12pm',
                    'signal_type': lot['signal_type'],
                    'tier': tier,
                })
            active_lots = []
            if session_active:
                # Close session with total PnL
                session_lots = [t for t in lot_trades if t['date'] == str(bar['est_date'])
                                and t['exit_reason'] != 'opposite_p90_trim50']
                # Actually, compute from recent lots
                session_pnl = sum(
                    t['pnl_pips'] for t in lot_trades
                    if t['date'] == str(bar['est_date'])
                )
                session_trades.append({
                    'date': str(bar['est_date']),
                    'direction': direction,
                    'session_pnl_pips': session_pnl,
                    'n_lots': len(lot_trades),
                    'tier': tier,
                    'exit_reason': 'hard_exit_12pm',
                })
            direction = 0
            session_active = False
            continue

        # Kill Switch
        if active_lots and direction != 0:
            if direction == 1:
                kill_level = entry_price + kill_move
                if bar_close > kill_level:
                    for lot in active_lots:
                        pnl = (kill_level - lot['price']) * 10000.0 - SPREAD_COST
                        lot_trades.append({
                            'date': str(bar['est_date']), 'direction': 1,
                            'entry_price': lot['price'], 'exit_price': kill_level,
                            'pnl_pips': pnl, 'exit_reason': 'kill_switch_132',
                            'signal_type': lot['signal_type'], 'tier': tier,
                        })
                    session_pnl = sum(t['pnl_pips'] for t in lot_trades if t['date'] == str(bar['est_date']))
                    session_trades.append({
                        'date': str(bar['est_date']), 'direction': 1,
                        'session_pnl_pips': session_pnl,
                        'n_lots': len([t for t in lot_trades if t['date'] == str(bar['est_date'])]),
                        'tier': tier, 'exit_reason': 'kill_switch_132',
                    })
                    active_lots = []
                    direction = 0
                    session_active = False
                    continue
            elif direction == -1:
                kill_level = entry_price - kill_move
                if bar_close < kill_level:
                    for lot in active_lots:
                        pnl = (lot['price'] - kill_level) * 10000.0 - SPREAD_COST
                        lot_trades.append({
                            'date': str(bar['est_date']), 'direction': -1,
                            'entry_price': lot['price'], 'exit_price': kill_level,
                            'pnl_pips': pnl, 'exit_reason': 'kill_switch_132',
                            'signal_type': lot['signal_type'], 'tier': tier,
                        })
                    session_pnl = sum(t['pnl_pips'] for t in lot_trades if t['date'] == str(bar['est_date']))
                    session_trades.append({
                        'date': str(bar['est_date']), 'direction': -1,
                        'session_pnl_pips': session_pnl,
                        'n_lots': len([t for t in lot_trades if t['date'] == str(bar['est_date'])]),
                        'tier': tier, 'exit_reason': 'kill_switch_132',
                    })
                    active_lots = []
                    direction = 0
                    session_active = False
                    continue

        # TP Management
        if active_lots and not tp1_hit:
            tp1 = entry_price + direction * tp1_move
            if (direction == 1 and bar_high >= tp1) or \
               (direction == -1 and bar_low <= tp1):
                tp1_hit = True
                n_close = max(1, len(active_lots) // 2)
                for lot in active_lots[:n_close]:
                    pnl = (tp1 - lot['price']) * direction * 10000.0 - SPREAD_COST
                    lot_trades.append({
                        'date': str(bar['est_date']),
                        'direction': direction,
                        'entry_price': lot['price'],
                        'exit_price': tp1,
                        'pnl_pips': pnl,
                        'exit_reason': 'tp1',
                        'signal_type': lot['signal_type'],
                        'tier': tier,
                    })
                active_lots = active_lots[n_close:]
                for lot in active_lots:
                    lot['sl'] = entry_price + direction * (2.0 / 10000.0)

        if tp1_hit and active_lots:
            tp2 = entry_price + direction * tp2_move
            if (direction == 1 and bar_high >= tp2) or \
               (direction == -1 and bar_low <= tp2):
                for lot in active_lots:
                    pnl = (tp2 - lot['price']) * direction * 10000.0 - SPREAD_COST
                    lot_trades.append({
                        'date': str(bar['est_date']),
                        'direction': direction,
                        'entry_price': lot['price'],
                        'exit_price': tp2,
                        'pnl_pips': pnl,
                        'exit_reason': 'tp2',
                        'signal_type': lot['signal_type'],
                        'tier': tier,
                    })
                session_pnl = sum(t['pnl_pips'] for t in lot_trades if t['date'] == str(bar['est_date']))
                session_trades.append({
                    'date': str(bar['est_date']),
                    'direction': direction,
                    'session_pnl_pips': session_pnl,
                    'n_lots': len([t for t in lot_trades if t['date'] == str(bar['est_date'])]),
                    'tier': tier,
                    'exit_reason': 'tp2',
                })
                active_lots = []
                direction = 0
                session_active = False
                continue

        # SL Check
        if active_lots and not tp1_hit:
            lots_to_keep = []
            for lot in active_lots:
                triggered = False
                exit_p = 0.0
                if direction == 1 and bar_low <= lot['sl']:
                    triggered = True
                    exit_p = lot['sl']
                elif direction == -1 and bar_high >= lot['sl']:
                    triggered = True
                    exit_p = lot['sl']

                if triggered:
                    pnl = (exit_p - lot['price']) * direction * 10000.0 - SPREAD_COST
                    lot_trades.append({
                        'date': str(bar['est_date']),
                        'direction': direction,
                        'entry_price': lot['price'],
                        'exit_price': exit_p,
                        'pnl_pips': pnl,
                        'exit_reason': 'sl_' + lot['signal_type'],
                        'signal_type': lot['signal_type'],
                        'tier': tier,
                    })
                else:
                    lots_to_keep.append(lot)
            active_lots = lots_to_keep
            if not active_lots and session_active:
                # All lots stopped out — close session
                session_pnl = sum(t['pnl_pips'] for t in lot_trades if t['date'] == str(bar['est_date']))
                session_trades.append({
                    'date': str(bar['est_date']),
                    'direction': direction,
                    'session_pnl_pips': session_pnl,
                    'n_lots': len([t for t in lot_trades if t['date'] == str(bar['est_date'])]),
                    'tier': tier,
                    'exit_reason': 'stopped_out',
                })
                direction = 0
                session_active = False
                continue

        # Opposite P90 detection
        if direction != 0 and P90_WINDOW_START_EST <= eh < P90_WINDOW_END_EST:
            is_p90, p90_dir, _ = detect_p90(bar)
            if is_p90 and p90_dir == -direction:
                bar_status = classify_p90_relative_to_barrier(bar, ah, al)
                if bar_status in ('above', 'below'):
                    opposite_p90_count += 1
                    if tp1_hit:
                        for lot in active_lots:
                            pnl = (bar_close - lot['price']) * direction * 10000.0 - SPREAD_COST
                            lot_trades.append({
                                'date': str(bar['est_date']),
                                'direction': direction,
                                'entry_price': lot['price'],
                                'exit_price': bar_close,
                                'pnl_pips': pnl,
                                'exit_reason': 'opposite_p90_exit',
                                'signal_type': lot['signal_type'],
                                'tier': tier,
                            })
                        session_pnl = sum(t['pnl_pips'] for t in lot_trades if t['date'] == str(bar['est_date']))
                        session_trades.append({
                            'date': str(bar['est_date']),
                            'direction': direction,
                            'session_pnl_pips': session_pnl,
                            'n_lots': len([t for t in lot_trades if t['date'] == str(bar['est_date'])]),
                            'tier': tier,
                            'exit_reason': 'opposite_p90_exit',
                        })
                        active_lots = []
                        direction = 0
                        session_active = False
                        continue
                    else:
                        if opposite_p90_count == 1:
                            if active_lots:
                                n_close = max(1, len(active_lots) // 2)
                                for lot in active_lots[:n_close]:
                                    pnl = (bar_close - lot['price']) * direction * 10000.0 - SPREAD_COST
                                    lot_trades.append({
                                        'date': str(bar['est_date']),
                                        'direction': direction,
                                        'entry_price': lot['price'],
                                        'exit_price': bar_close,
                                        'pnl_pips': pnl,
                                        'exit_reason': 'opposite_p90_trim',
                                        'signal_type': lot['signal_type'],
                                        'tier': tier,
                                    })
                                active_lots = active_lots[n_close:]
                                for lot in active_lots:
                                    lot['sl'] = entry_price + direction * (2.0 / 10000.0)
                        elif opposite_p90_count >= 2:
                            for lot in active_lots:
                                pnl = (bar_close - lot['price']) * direction * 10000.0 - SPREAD_COST
                                lot_trades.append({
                                    'date': str(bar['est_date']),
                                    'direction': direction,
                                    'entry_price': lot['price'],
                                    'exit_price': bar_close,
                                    'pnl_pips': pnl,
                                    'exit_reason': 'opposite_p90_exit',
                                    'signal_type': lot['signal_type'],
                                    'tier': tier,
                                })
                            session_pnl = sum(t['pnl_pips'] for t in lot_trades if t['date'] == str(bar['est_date']))
                            session_trades.append({
                                'date': str(bar['est_date']),
                                'direction': direction,
                                'session_pnl_pips': session_pnl,
                                'n_lots': len([t for t in lot_trades if t['date'] == str(bar['est_date'])]),
                                'tier': tier,
                                'exit_reason': 'opposite_p90_exit',
                            })
                            active_lots = []
                            direction = 0
                            session_active = False
                            continue

        # P90 Detection & Entry
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

        signal_dir = 1 if bar_status == 'above' else -1

        if direction == 0:
            # INITIAL P90
            direction = signal_dir
            entry_price = bar_close
            p90_body_pips = body_pips
            p90_time = bar['timestamp']
            tp1_hit = False
            cascade_count = 0
            opposite_p90_count = 0
            session_active = True

            size_mult = tier_mult * regime_mult * monday_mult

            # Signal 1 (40%)
            sl1 = bar_close - signal_dir * (body_pips * 0.80 / 10000.0)
            active_lots.append({
                'price': bar_close, 'size_pct': 0.4 * size_mult,
                'sl': sl1, 'signal_type': 'signal1'
            })

            # Signal 2 (40%)
            sl2 = bar_close - signal_dir * (body_pips * 1.50 / 10000.0)
            active_lots.append({
                'price': bar_close, 'size_pct': 0.4 * size_mult,
                'sl': sl2, 'signal_type': 'signal2'
            })

            signals_fired = 2

        elif signal_dir == direction and cascade_count < max_cascades:
            if p90_time is not None:
                elapsed = (bar['timestamp'] - p90_time).total_seconds() / 60.0
                if 30 <= elapsed <= 90:
                    cascade_count += 1
                    size_mult = tier_mult * regime_mult * monday_mult

                    if cascade_count == 1:
                        c_size = 0.2
                    elif cascade_count == 2:
                        c_size = 0.1
                    else:
                        c_size = 0.05

                    sl_c = bar_close - signal_dir * (body_pips * 1.68 / 10000.0)
                    active_lots.append({
                        'price': bar_close, 'size_pct': c_size * size_mult,
                        'sl': sl_c, 'signal_type': f'cascade_{cascade_count}'
                    })
                    signals_fired += 1

        # 45-Min Add
        if direction != 0 and p90_time is not None and not add45_fired:
            elapsed = (bar['timestamp'] - p90_time).total_seconds() / 60.0
            if 40 <= elapsed <= 50:
                current_move = (bar_close - entry_price) * direction * 10000.0
                if current_move >= 8.0:
                    size_mult = tier_mult * regime_mult * monday_mult
                    active_lots.append({
                        'price': bar_close, 'size_pct': 0.2 * size_mult,
                        'sl': entry_price + direction * (2.0 / 10000.0),
                        'signal_type': 'add45min'
                    })
                    add45_fired = True
                    signals_fired = max(signals_fired, 3)

    return session_trades, lot_trades


def run_p90_backtest_v4(df, start_date=None, end_date=None):
    if start_date:
        df = df[df['est_date'] >= start_date]
    if end_date:
        df = df[df['est_date'] <= end_date]

    all_session_trades = []
    all_lot_trades = []
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
            all_session_trades.extend(sess)
        if lots:
            all_lot_trades.extend(lots)
        days_processed += 1

    return all_session_trades, all_lot_trades, days_processed


def compute_session_stats(session_trades, strategy_name):
    """Compute per-session statistics"""
    if not session_trades:
        return {'error': 'no sessions'}

    df = pd.DataFrame(session_trades)
    wins = df[df['session_pnl_pips'] > 0]
    losses = df[df['session_pnl_pips'] <= 0]

    total = len(df)
    win_rate = len(wins) / total * 100.0
    gross_profit = wins['session_pnl_pips'].sum() if len(wins) > 0 else 0
    gross_loss = abs(losses['session_pnl_pips'].sum()) if len(losses) > 0 else 0.001
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    total_pips = df['session_pnl_pips'].sum()
    avg_r = df['session_pnl_pips'].mean()

    return {
        'strategy': strategy_name,
        'total_sessions': total,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate_pct': round(win_rate, 1),
        'profit_factor': round(profit_factor, 2),
        'total_pips': round(total_pips, 1),
        'avg_pips_per_session': round(avg_r, 2),
    }


if __name__ == "__main__":
    print("=" * 60)
    print("P90 CFD EXPANSION ENGINE v4 — Backtest")
    print("=" * 60)

    df = load_data()

    print("\nRunning 2024-2025...")
    sess_trades, lot_trades, days = run_p90_backtest_v4(df, date(2024, 1, 1), date(2025, 12, 31))

    if not lot_trades:
        print("No trades generated!")
        sys.exit(1)

    lot_df = pd.DataFrame(lot_trades)
    lot_stats = compute_stats(lot_df, STRATEGY_NAME)

    print(f"\n--- LOT-LEVEL STATS ---")
    print(f"Days processed: {days}")
    print(f"Total lots: {lot_stats['total_trades']}")
    print(f"Lot Win Rate: {lot_stats['win_rate_pct']}%")
    print(f"Total Pips: {lot_stats['total_pips']}")

    # Per-session stats
    if sess_trades:
        sess_df = pd.DataFrame(sess_trades)
        sess_stats = compute_session_stats(sess_trades, STRATEGY_NAME)
        print(f"\n--- SESSION-LEVEL STATS ---")
        print(f"Total sessions: {sess_stats['total_sessions']}")
        print(f"Session Win Rate: {sess_stats['win_rate_pct']}% (target: 85-90%)")
        print(f"Session Profit Factor: {sess_stats['profit_factor']} (target: ~1.78)")
        print(f"Total Session Pips: {sess_stats['total_pips']}")
        print(f"Avg pips/session: {sess_stats['avg_pips_per_session']}")

        # Tier breakdown (session level)
        print("\nSession Tier Breakdown:")
        for t in sorted(sess_df['tier'].unique()):
            tf = sess_df[sess_df['tier'] == t]
            wr = (tf['session_pnl_pips'] > 0).mean() * 100
            print(f"  {t}: {len(tf)} sessions, WR {wr:.1f}%, "
                  f"avg {tf['session_pnl_pips'].mean():.1f}p, total {tf['session_pnl_pips'].sum():.1f}p")

        # Exit reason (session level)
        print("\nSession Exit Breakdown:")
        for reason, count in sess_df['exit_reason'].value_counts().items():
            avg = sess_df[sess_df['exit_reason'] == reason]['session_pnl_pips'].mean()
            wr = (sess_df[sess_df['exit_reason'] == reason]['session_pnl_pips'] > 0).mean() * 100
            print(f"  {reason}: {count} sessions, avg {avg:.1f}p, WR {wr:.0f}%")

        # Yearly session stats
        sess_df['year'] = pd.to_datetime(sess_df['date']).dt.year
        print("\nSession Yearly:")
        for y in sorted(sess_df['year'].unique()):
            yf = sess_df[sess_df['year'] == y]
            wr = (yf['session_pnl_pips'] > 0).mean() * 100
            nf = len(yf)
            print(f"  {y}: {nf} sessions, WR {wr:.1f}%, total {yf['session_pnl_pips'].sum():.1f}p")

        # Write report with session stats
        report_path = write_report(STRATEGY_NAME, sess_stats, TARGET_STATS, lot_df)
        print(f"\nReport: {report_path}")

        # Also save session trades
        sess_path = REPORTS_DIR / f"{STRATEGY_NAME}_sessions.csv"
        sess_df.to_csv(sess_path, index=False)

```

LINKS:
[[Codemap]]
[[01 System Overview]]
[[02 Agent Workflow]]
[[03 Srra Topology]]
[[04 Data And Storage]]
[[Agents]]
[[Api Reference]]
[[Cg 1 Mermaid Specs]]
[[Cg 1 Revised]]
[[Cg 2 Mermaid Specs]]
[[Cg 2 World Model Activation]]
[[Cg 3 Openclaw Anchor]]
[[Cg 3 Relational Topology]]
[[Cg 4 Execution Intelligence]]
[[Cg 4 Mermaid Specs]]
[[Cg 5 Continuity Intelligence]]
[[Cg 6 Meta Cognition]]
[[Cg 7 Multi Scale Orchestration]]
[[Cg 8 Operator Coevolution]]
[[Cg 9 Autonomous Strategic Field]]
[[Chaos Scenarios]]
[[Chat Response Bug Diagram]]
[[Cleanup Report]]
[[Code Quality]]
[[Contributing]]
[[Debugging]]
[[Domain Micro Doctrines]]
[[Harness Engineering]]
[[Heartbeat]]
[[Identity]]
[[Master Plan 2026 05 18]]
[[Master Plan Observer Core]]
[[Master Prompt]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[Oce Unified Frontend Plan]]
[[O 6 Implementation Plan]]
[[O 7 Persistent Field Doc]]
[[Phase10]]
[[Phase Breakdown]]
[[Principles]]
[[Project Progress Clean]]
[[Quality Review]]
[[Quality Review Feedback]]
[[Readme]]
[[Soul]]
[[Sub Agent Rules]]
[[Team Tasks]]
[[Telegram Bot Setup]]
[[Testing]]
[[Test Manual]]
[[Tools]]
[[Topological Cognition Architecture]]
[[User]]
[[Workspace State]]
[[Cal]]
[[Citation Workflow]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Memory]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
